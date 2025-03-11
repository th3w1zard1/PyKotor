#!/usr/bin/env python

# Author: Ryan Myers
# Models: Jeff Styers, Reagan Heller
#
# Last Updated: 2015-03-13
#
# This tutorial provides an example of creating a character
# and having it walk around on uneven terrain, as well
# as implementing a fully rotatable camera.
from __future__ import annotations

import sys

from typing import TYPE_CHECKING

from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import (
    AmbientLight,
    CollideMask,
    CollisionHandlerPusher,
    CollisionHandlerQueue,
    CollisionNode,
    CollisionRay,
    CollisionSphere,
    CollisionTraverser,
    DirectionalLight,
    NodePath,
    PandaNode,
    TextNode,
)

if TYPE_CHECKING:
    from direct.showbase.Loader import Loader
    from direct.showbase.ShowBase import _WindowType
    from direct.task.Task import Task
    from panda3d.core import CollisionEntry, LPoint3f, LVecBase3f

    base: ShowBase = ShowBase()
    render: NodePath = NodePath("render")  # idek. somehow this is always defined.
    loader: Loader = Loader(base)  # pyright: ignore[reportUnknownParameterType]


# Function to put instructions on the screen.
def add_instructions(pos: float, msg: str) -> OnscreenText:
    return OnscreenText(
        text=msg,
        style=1,
        fg=(1, 1, 1, 1),
        scale=0.05,
        shadow=(0, 0, 0, 1),
        parent=base.a2dTopLeft,
        pos=(0.08, -pos - 0.04),
        align=TextNode.ALeft,
    )


# Function to put title on the screen.
def add_title(text: str) -> OnscreenText:
    return OnscreenText(
        text=text,
        style=1,
        fg=(1, 1, 1, 1),
        scale=0.07,
        parent=base.a2dBottomRight,
        align=TextNode.ARight,
        pos=(-0.1, 0.09),
        shadow=(0, 0, 0, 1),
    )


class RoamingRalphDemo(ShowBase):
    def __init__(
        self,
        fStartDirect: bool = True,
        window_type: _WindowType | None = None,
    ) -> None:
        # Set up the window, camera, etc.
        ShowBase.__init__(self, fStartDirect, window_type)

        # This is used to store which keys are currently pressed.
        self.key_map: dict[str, int] = {
            "left": 0,
            "right": 0,
            "forward": 0,
            "backward": 0,
            "cam-left": 0,
            "cam-right": 0,
        }

        # Post the instructions
        self.title: OnscreenText = add_title("Ursina Tutorial: Roaming Ralph (Walking on Uneven Terrain)")
        self.inst1: OnscreenText = add_instructions(0.06, "[ESC]: Quit")
        self.inst2: OnscreenText = add_instructions(0.12, "[Left Arrow]: Rotate Ralph Left")
        self.inst3: OnscreenText = add_instructions(0.18, "[Right Arrow]: Rotate Ralph Right")
        self.inst4: OnscreenText = add_instructions(0.24, "[Up Arrow]: Run Ralph Forward")
        self.inst5: OnscreenText = add_instructions(0.30, "[Down Arrow]: Walk Ralph Backward")
        self.inst6: OnscreenText = add_instructions(0.36, "[A]: Rotate Camera Left")
        self.inst7: OnscreenText = add_instructions(0.42, "[S]: Rotate Camera Right")

        # Set up the environment
        #
        # This environment model contains collision meshes.  If you look
        # in the egg file, you will see the following:
        #
        #    <Collide> { Polyset keep descend }
        #
        # This tag causes the following mesh to be converted to a collision
        # mesh -- a mesh which is optimized for collision, not rendering.
        # It also keeps the original mesh, so there are now two copies ---
        # one optimized for rendering, one for collisions.

        loaded_environment: NodePath[PandaNode] | None = loader.load_model("models/world")
        if loaded_environment is None:
            raise RuntimeError("Failed to load environment model")

        self.environ: NodePath[PandaNode] = loaded_environment
        self.environ.reparent_to(render)

        # We do not have a skybox, so we will just use a sky blue background color
        self.set_background_color(0.53, 0.80, 0.92, 1)

        # Create the main character, Ralph

        ralph_start_pos: LPoint3f = self.environ.find("**/start_point").get_pos()
        self.ralph: Actor = Actor("models/ralph", {"run": "models/ralph-run", "walk": "models/ralph-walk"})
        self.ralph.reparent_to(render)
        self.ralph.set_scale(0.2)
        self.ralph.set_pos(ralph_start_pos + (0, 0, 1.5))

        # Create a floater object, which floats 2 units above ralph.  We
        # use this as a target for the camera to look at.

        self.floater: NodePath[PandaNode] = NodePath(PandaNode("floater"))
        self.floater.reparent_to(self.ralph)
        self.floater.set_z(2.0)

        # Accept the control keys for movement and rotation

        self.accept("escape", sys.exit)
        self.accept("arrow_left", self.set_key, ["left", True])
        self.accept("arrow_right", self.set_key, ["right", True])
        self.accept("arrow_up", self.set_key, ["forward", True])
        self.accept("arrow_down", self.set_key, ["backward", True])
        self.accept("a", self.set_key, ["cam-left", True])
        self.accept("s", self.set_key, ["cam-right", True])
        self.accept("arrow_left-up", self.set_key, ["left", False])
        self.accept("arrow_right-up", self.set_key, ["right", False])
        self.accept("arrow_up-up", self.set_key, ["forward", False])
        self.accept("arrow_down-up", self.set_key, ["backward", False])
        self.accept("a-up", self.set_key, ["cam-left", False])
        self.accept("s-up", self.set_key, ["cam-right", False])

        taskMgr.add(self.move, "moveTask")

        # Set up the camera
        self.disable_mouse()
        self.camera.set_pos(self.ralph.get_x(), self.ralph.get_y() + 10, 2)

        self.c_trav: CollisionTraverser = CollisionTraverser()

        # Use a CollisionHandlerPusher to handle collisions between Ralph and
        # the environment. Ralph is added as a "from" object which will be
        # "pushed" out of the environment if he walks into obstacles.
        #
        # Ralph is composed of two spheres, one around the torso and one
        # around the head.  They are slightly oversized since we want Ralph to
        # keep some distance from obstacles.
        self.ralph_col: CollisionNode = CollisionNode("ralph")
        self.ralph_col.add_solid(CollisionSphere(center=(0, 0, 2), radius=1.5))
        self.ralph_col.add_solid(CollisionSphere(center=(0, -0.25, 4), radius=1.5))
        self.ralph_col.set_from_collide_mask(CollideMask.bit(0))
        self.ralph_col.set_into_collide_mask(CollideMask.all_off())
        self.ralph_col_np: NodePath[PandaNode] = self.ralph.attach_new_node(self.ralph_col)
        self.ralph_pusher: CollisionHandlerPusher = CollisionHandlerPusher()
        self.ralph_pusher.horizontal = True

        # Note that we need to add ralph both to the pusher and to the
        # traverser; the pusher needs to know which node to push back when a
        # collision occurs!
        self.ralph_pusher.add_collider(self.ralph_col_np, self.ralph)
        self.c_trav.add_collider(self.ralph_col_np, self.ralph_pusher)

        # We will detect the height of the terrain by creating a collision
        # ray and casting it downward toward the terrain.  One ray will
        # start above ralph's head, and the other will start above the camera.
        # A ray may hit the terrain, or it may hit a rock or a tree.  If it
        # hits the terrain, we can detect the height.
        self.ralph_ground_ray: CollisionRay = CollisionRay()
        self.ralph_ground_ray.set_origin(0, 0, 9)
        self.ralph_ground_ray.set_direction(0, 0, -1)
        self.ralph_ground_col: CollisionNode = CollisionNode("ralphRay")
        self.ralph_ground_col.add_solid(self.ralph_ground_ray)
        self.ralph_ground_col.set_from_collide_mask(CollideMask.bit(0))
        self.ralph_ground_col.set_into_collide_mask(CollideMask.all_off())
        self.ralph_ground_col_np: NodePath[PandaNode] = self.ralph.attach_new_node(self.ralph_ground_col)
        self.ralph_ground_handler: CollisionHandlerQueue = CollisionHandlerQueue()
        self.c_trav.add_collider(self.ralph_ground_col_np, self.ralph_ground_handler)

        self.cam_ground_ray: CollisionRay = CollisionRay()
        self.cam_ground_ray.set_origin(0, 0, 9)
        self.cam_ground_ray.set_direction(0, 0, -1)
        self.cam_ground_col: CollisionNode = CollisionNode("camRay")
        self.cam_ground_col.add_solid(self.cam_ground_ray)
        self.cam_ground_col.set_from_collide_mask(CollideMask.bit(0))
        self.cam_ground_col.set_into_collide_mask(CollideMask.all_off())
        self.cam_ground_col_np: NodePath[PandaNode] = self.camera.attach_new_node(self.cam_ground_col)
        self.cam_ground_handler: CollisionHandlerQueue = CollisionHandlerQueue()
        self.c_trav.add_collider(self.cam_ground_col_np, self.cam_ground_handler)

        # Uncomment this line to see the collision rays
        # self.ralphColNp.show()
        # self.camGroundColNp.show()

        # Uncomment this line to show a visual representation of the
        # collisions occuring
        # self.cTrav.showCollisions(render)

        # Create some lighting
        ambient_light: AmbientLight = AmbientLight("ambientLight")
        ambient_light.set_color((0.3, 0.3, 0.3, 1))
        directional_light: DirectionalLight = DirectionalLight("directionalLight")
        directional_light.set_direction((-5, -5, -5))
        directional_light.set_color((1, 1, 1, 1))
        directional_light.set_specular_color((1, 1, 1, 1))
        render.set_light(render.attach_new_node(ambient_light))
        render.set_light(render.attach_new_node(directional_light))

    # Records the state of the arrow keys
    def set_key(self, key: str, value: bool):
        self.key_map[key] = value

    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    async def move(
        self,
        task: Task,
    ):
        # Get the time that elapsed since last frame.  We multiply this with
        # the desired speed in order to find out with which distance to move
        # in order to achieve that desired speed.
        dt: float = base.clock.dt

        # If the camera-left key is pressed, move camera left.
        # If the camera-right key is pressed, move camera right.

        if self.key_map["cam-left"]:
            self.camera.set_x(self.camera, -20 * dt)
        if self.key_map["cam-right"]:
            self.camera.set_x(self.camera, +20 * dt)

        # If a move-key is pressed, move ralph in the specified direction.

        if self.key_map["left"]:
            self.ralph.set_h(self.ralph.get_h() + 300 * dt)
        if self.key_map["right"]:
            self.ralph.set_h(self.ralph.get_h() - 300 * dt)
        if self.key_map["forward"]:
            self.ralph.set_y(self.ralph, -20 * dt)
        if self.key_map["backward"]:
            self.ralph.set_y(self.ralph, +10 * dt)

        # If ralph is moving, loop the run animation.
        # If he is standing still, stop the animation.
        cur_anim: str | None = self.ralph.get_current_anim()

        if self.key_map["forward"]:
            if cur_anim != "run":
                self.ralph.loop("run")
        elif self.key_map["backward"]:
            # Play the walk animation backwards.
            if cur_anim != "walk":
                self.ralph.loop("walk")
            self.ralph.set_play_rate(-1.0, "walk")
        elif self.key_map["left"] or self.key_map["right"]:
            if cur_anim != "walk":
                self.ralph.loop("walk")
            self.ralph.set_play_rate(1.0, "walk")
        else:
            if cur_anim is not None:
                self.ralph.stop()
                self.ralph.pose("walk", 5)
                self.isMoving = False

        # If the camera is too far from ralph, move it closer.
        # If the camera is too close to ralph, move it farther.

        camvec: LVecBase3f = self.ralph.get_pos() - self.camera.get_pos()
        camvec.set_z(0)
        camdist: float = camvec.length()
        camvec.normalize()
        if camdist > 10.0:
            self.camera.set_pos(self.camera.get_pos() + camvec * (camdist - 10))
            camdist = 10.0
        if camdist < 5.0:
            self.camera.set_pos(self.camera.get_pos() - camvec * (5 - camdist))
            camdist = 5.0

        # Normally, we would have to call traverse() to check for collisions.
        # However, the class ShowBase that we inherit from has a task to do
        # this for us, if we assign a CollisionTraverser to self.cTrav.
        # self.cTrav.traverse(render)

        # Adjust ralph's Z coordinate.  If ralph's ray hit terrain,
        # update his Z

        entries: list[CollisionEntry] = list(self.ralph_ground_handler.entries)
        entries.sort(key=lambda x: x.get_surface_point(render).get_z())

        for entry in entries:
            if entry.get_into_node().name == "terrain":
                self.ralph.set_z(entry.get_surface_point(render).get_z())

        # Keep the camera at one unit above the terrain,
        # or two units above ralph, whichever is greater.

        entries: list[CollisionEntry] = list(self.cam_ground_handler.entries)
        entries.sort(key=lambda x: x.get_surface_point(render).get_z())

        for entry in entries:
            if entry.get_into_node().name == "terrain":
                self.camera.set_z(entry.get_surface_point(render).get_z() + 1.5)
        if self.camera.get_z() < self.ralph.get_z() + 2.0:
            self.camera.set_z(self.ralph.get_z() + 2.0)

        # The camera should look in ralph's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above ralph's head.
        self.camera.look_at(self.floater)

        return task.cont

print("Starting demo...")
demo: RoamingRalphDemo | None = None
if __name__ == "__main__":
    demo = RoamingRalphDemo()
    demo.run()
print("Demo finished.")
