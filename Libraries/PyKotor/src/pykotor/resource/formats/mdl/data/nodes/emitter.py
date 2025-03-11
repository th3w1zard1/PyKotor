"""Emitter node data structure for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
from utility.common.geometry import Vector3


@dataclass
class MDLEmitterNode(MDLNode):
    """Emitter node in MDL format.

    Emitter nodes are used for particle effects and other visual effects. They
    control the emission of particles with properties like position, velocity,
    color, size, and lifetime.
    """

    # Emission properties
    emission_rate: float = 10.0  # Particles per second
    lifetime: float = 1.0  # Particle lifetime in seconds
    lifetime_random: float = 0.0  # Random variation in lifetime
    mass: float = 1.0  # Particle mass
    mass_random: float = 0.0  # Random variation in mass
    spread: float = 0.0  # Emission spread angle in radians
    velocity: float = 1.0  # Initial particle velocity
    velocity_random: float = 0.0  # Random variation in velocity

    # Blast properties
    blast_radius: float = 0.0  # Blast effect radius
    blast_length: float = 0.0  # Blast effect length
    branch_count: int = 1  # Number of effect branches
    control_point_smoothing: float = 0.0  # Control point smoothing factor

    # Grid properties
    grid_x: int = 1  # Grid cells in X direction
    grid_y: int = 1  # Grid cells in Y direction
    grid_width: float = 1.0  # Width of emission grid
    grid_height: float = 1.0  # Height of emission grid

    # Particle properties
    size: List[float] = field(default_factory=lambda: [1.0, 1.0])  # [min, max] particle size
    size_random: float = 0.0  # Random variation in size
    size_change: float = 0.0  # Size change over lifetime
    alpha: List[float] = field(default_factory=lambda: [1.0, 1.0])  # [start, end] alpha
    alpha_random: float = 0.0  # Random variation in alpha

    # Color properties
    color_start: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])  # Start RGB color
    color_end: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])  # End RGB color
    color_random: float = 0.0  # Random variation in color

    # Frame properties
    frame_start: int = 0  # Starting texture frame
    frame_end: int = 0  # Ending texture frame
    frame_random: bool = False  # Randomize frame selection
    frame_change: float = 0.0  # Frame change rate
    frame_blending: bool = False  # Enable frame blending

    # Physics properties
    gravity: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, -9.81))  # Gravity vector
    drag: float = 0.0  # Air resistance
    bounce: float = 0.0  # Surface bounce coefficient
    friction: float = 0.0  # Surface friction coefficient

    # Render properties
    render_order: int = 0  # Sorting order for transparency
    blend_mode: int = 0  # Blend mode (0=normal, 1=additive, 2=multiply)
    update_in_pause: bool = False  # Update when game is paused
    inherit_velocity: bool = False  # Inherit parent velocity
    inherit_rotation: bool = False  # Inherit parent rotation
    random_rotation: bool = False  # Randomize particle rotation
    loop_particles: bool = True  # Loop particle emission
    kill_oldest: bool = True  # Kill oldest particles when max reached
    target_camera: bool = False  # Orient towards camera

    # Script properties
    update_script: Optional[str] = None  # Update script name
    render_script: Optional[str] = None  # Render script name

    # Texture properties
    texture: str = ""  # Particle texture name
    texture_rows: int = 1  # Number of texture grid rows
    texture_cols: int = 1  # Number of texture grid columns
    two_sided_texture: bool = False  # Render texture on both sides
    depth_texture: Optional[str] = None  # Depth texture name
    depth_texture_enabled: bool = False  # Enable depth texture

    # Chunk properties
    chunk_name: Optional[str] = None  # Chunk effect name
    spawn_type: int = 0  # Spawn type (0=normal, 1=trail)

    # Particle limits
    max_particles: int = 100  # Maximum number of particles
    dead_space: float = 0.0  # Distance at which particles die

    # Emission shape
    shape_type: int = 0  # 0=point, 1=sphere, 2=box
    shape_size: Vector3 = field(default_factory=lambda: Vector3(1.0, 1.0, 1.0))  # Shape dimensions

    # Flags
    point_to_point: bool = False  # Point-to-point effect
    point_to_point_select: bool = False  # Allow point selection
    affected_by_wind: bool = False  # Affected by wind
    tinted: bool = False  # Apply tint color
    random_spawn: bool = False  # Random spawn positions
    inherit: bool = False  # Inherit parent properties
    inherit_local: bool = False  # Inherit in local space
    splat: bool = False  # Splat particles on surfaces
    inherit_part: bool = False  # Inherit particle properties

    def __post_init__(self):
        """Initialize base class."""
        super().__init__(self.name)

    def get_particle_size(self, age: float, random_seed: float = 0.0) -> float:
        """Get particle size at given age.

        Args:
            age: Age of particle in seconds
            random_seed: Random seed value (0-1)

        Returns:
            float: Particle size
        """
        # Get base size range
        size_min, size_max = self.size
        size = size_min + (size_max - size_min) * random_seed * self.size_random

        # Apply size change over time
        if self.lifetime > 0:
            t = age / self.lifetime
            size += self.size_change * t

        return max(0.0, size)

    def get_particle_alpha(self, age: float, random_seed: float = 0.0) -> float:
        """Get particle alpha at given age.

        Args:
            age: Age of particle in seconds
            random_seed: Random seed value (0-1)

        Returns:
            float: Particle alpha (0-1)
        """
        # Get base alpha range
        alpha_start, alpha_end = self.alpha
        alpha = alpha_start + (alpha_end - alpha_start) * random_seed * self.alpha_random

        # Interpolate between start and end alpha
        if self.lifetime > 0:
            t = age / self.lifetime
            alpha = alpha_start + (alpha_end - alpha_start) * t

        return max(0.0, min(1.0, alpha))

    def get_particle_color(self, age: float, random_seed: float = 0.0) -> List[float]:
        """Get particle color at given age.

        Args:
            age: Age of particle in seconds
            random_seed: Random seed value (0-1)

        Returns:
            List[float]: RGB color values (0-1)
        """
        # Interpolate between start and end colors
        if self.lifetime > 0:
            t = age / self.lifetime
            color = [self.color_start[i] + (self.color_end[i] - self.color_start[i]) * t for i in range(3)]
        else:
            color = list(self.color_start)

        # Apply random variation
        if self.color_random > 0:
            color = [max(0.0, min(1.0, c + (random_seed - 0.5) * self.color_random)) for c in color]

        return color

    def get_texture_frame(self, age: float) -> int:
        """Get texture frame at given age.

        Args:
            age: Age of particle in seconds

        Returns:
            int: Frame index
        """
        if self.frame_random:
            # Use age and frame change rate to cycle through frames
            if self.frame_change > 0 and self.lifetime > 0:
                t = (age * self.frame_change) % 1.0
                frame_count = self.frame_end - self.frame_start + 1
                frame_offset = int(t * frame_count)
                return self.frame_start + frame_offset
            return self.frame_start
        else:
            # Interpolate between start and end frames
            if self.frame_change > 0 and self.lifetime > 0:
                t = age / self.lifetime
                frame_count = self.frame_end - self.frame_start + 1
                frame_offset = int(t * frame_count)
                return min(self.frame_end, self.frame_start + frame_offset)
            return self.frame_start
