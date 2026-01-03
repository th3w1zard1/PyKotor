from __future__ import annotations

import os
import pathlib
import sys
import unittest

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[6].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING


from pykotor.resource.formats.gff.gff_data import GFF
from pykotor.resource.type import ResourceType
from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.are import ARE, construct_are, dismantle_are

if TYPE_CHECKING:
    from pykotor.resource.formats.gff import GFF
    from pykotor.resource.generics.are import ARE

# Inlined test.are content converted to XML format
TEST_ARE_XML = """<gff3>
  <struct id="-1">
    <sint32 label="ID">0</sint32>
    <sint32 label="Creator_ID">0</sint32>
    <uint32 label="Version">88</uint32>
    <exostring label="Tag">Untitled</exostring>
    <locstring label="Name" strref="75101" />
    <exostring label="Comments">comments</exostring>
    <struct label="Map" id="0">
      <sint32 label="MapResX">18</sint32>
      <sint32 label="NorthAxis">1</sint32>
      <float label="WorldPt1X">-14.180000305175781</float>
      <float label="WorldPt1Y">-15.0600004196167</float>
      <float label="WorldPt2X">13.279999732971191</float>
      <float label="WorldPt2Y">12.859999656677246</float>
      <float label="MapPt1X">0.3779999911785126</float>
      <float label="MapPt1Y">0.7680000066757202</float>
      <float label="MapPt2X">0.621999979019165</float>
      <float label="MapPt2Y">0.27300000190734863</float>
      <sint32 label="MapZoom">1</sint32>
      </struct>
    <list label="Expansion_List" />
    <uint32 label="Flags">0</uint32>
    <sint32 label="ModSpotCheck">0</sint32>
    <sint32 label="ModListenCheck">0</sint32>
    <float label="AlphaTest">0.20000000298023224</float>
    <sint32 label="CameraStyle">1</sint32>
    <resref label="DefaultEnvMap">defaultenvmap</resref>
    <resref label="Grass_TexName">grasstexture</resref>
    <float label="Grass_Density">1.0</float>
    <float label="Grass_QuadSize">1.0</float>
    <uint32 label="Grass_Ambient">16777215</uint32>
    <uint32 label="Grass_Diffuse">16777215</uint32>
    <uint32 label="Grass_Emissive">16777215</uint32>
    <float label="Grass_Prob_LL">0.25</float>
    <float label="Grass_Prob_LR">0.25</float>
    <float label="Grass_Prob_UL">0.25</float>
    <float label="Grass_Prob_UR">0.25</float>
    <uint32 label="MoonAmbientColor">0</uint32>
    <uint32 label="MoonDiffuseColor">0</uint32>
    <byte label="MoonFogOn">0</byte>
    <float label="MoonFogNear">99.0</float>
    <float label="MoonFogFar">100.0</float>
    <uint32 label="MoonFogColor">0</uint32>
    <byte label="MoonShadows">0</byte>
    <uint32 label="SunAmbientColor">16777215</uint32>
    <uint32 label="SunDiffuseColor">16777215</uint32>
    <byte label="SunFogOn">1</byte>
    <float label="SunFogNear">99.0</float>
    <float label="SunFogFar">100.0</float>
    <uint32 label="SunFogColor">16777215</uint32>
    <byte label="SunShadows">1</byte>
    <uint32 label="DynAmbientColor">16777215</uint32>
    <byte label="IsNight">0</byte>
    <byte label="LightingScheme">0</byte>
    <byte label="ShadowOpacity">205</byte>
    <byte label="DayNightCycle">0</byte>
    <sint32 label="ChanceRain">99</sint32>
    <sint32 label="ChanceSnow">99</sint32>
    <sint32 label="ChanceLightning">99</sint32>
    <sint32 label="WindPower">1</sint32>
    <uint16 label="LoadScreenID">0</uint16>
    <byte label="PlayerVsPlayer">3</byte>
    <byte label="NoRest">0</byte>
    <byte label="NoHangBack">0</byte>
    <byte label="PlayerOnly">0</byte>
    <byte label="Unescapable">1</byte>
    <byte label="DisableTransit">1</byte>
    <byte label="StealthXPEnabled">1</byte>
    <uint32 label="StealthXPLoss">25</uint32>
    <uint32 label="StealthXPMax">25</uint32>
    <sint32 label="DirtyARGBOne">123</sint32>
    <sint32 label="DirtySizeOne">1</sint32>
    <sint32 label="DirtyFormulaOne">1</sint32>
    <sint32 label="DirtyFuncOne">1</sint32>
    <sint32 label="DirtyARGBTwo">1234</sint32>
    <sint32 label="DirtySizeTwo">1</sint32>
    <sint32 label="DirtyFormulaTwo">1</sint32>
    <sint32 label="DirtyFuncTwo">1</sint32>
    <sint32 label="DirtyARGBThree">12345</sint32>
    <sint32 label="DirtySizeThree">1</sint32>
    <sint32 label="DirtyFormulaThre">1</sint32>
    <sint32 label="DirtyFuncThree">1</sint32>
    <list label="Rooms">
      <struct id="0">
        <exostring label="RoomName">002ebo</exostring>
        <sint32 label="EnvAudio">17</sint32>
        <float label="AmbientScale">0.9300000071525574</float>
        <sint32 label="ForceRating">1</sint32>
        <byte label="DisableWeather">1</byte>
        </struct>
      <struct id="0">
        <exostring label="RoomName">002ebo2</exostring>
        <sint32 label="EnvAudio">17</sint32>
        <float label="AmbientScale">0.9800000190734863</float>
        <sint32 label="ForceRating">2</sint32>
        <byte label="DisableWeather">0</byte>
        </struct>
      </list>
    <resref label="OnEnter">k_on_enter</resref>
    <resref label="OnExit">onexit</resref>
    <resref label="OnHeartbeat">onheartbeat</resref>
    <resref label="OnUserDefined">onuserdefined</resref>
    </struct>
  </gff3>"""
K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")


class TestARE(unittest.TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_io_construct(self):
        gff: GFF = read_gff(TEST_ARE_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        are: ARE = construct_are(gff)
        self.validate_io(are)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_ARE_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        gff = dismantle_are(construct_are(gff), Game.K2)
        are = construct_are(gff)
        self.validate_io(are)

    def test_file_io(self):
        """Test reading from a temporary file to ensure file-based reading still works."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.are.xml', delete=False, encoding='utf-8') as tmp:
            tmp.write(TEST_ARE_XML)
            tmp_path = tmp.name

        try:
            gff: GFF = read_gff(tmp_path, file_format=ResourceType.GFF_XML)
            are: ARE = construct_are(gff)
            self.validate_io(are)
        finally:
            os.unlink(tmp_path)

    def validate_io(self, are: ARE):
        assert are.unused_id == 0, f"{are.unused_id} != 0"
        assert are.creator_id == 0, f"{are.creator_id} != 0"
        assert are.tag == "Untitled", f"{are.tag} != Untitled"
        assert are.name.stringref == 75101, f"{are.name.stringref} != 75101"
        assert are.comment == "comments", f"{are.comment} != comments"
        assert are.flags == 0, f"{are.flags} != 0"
        assert are.mod_spot_check == 0, f"{are.mod_spot_check} != 0"
        assert are.mod_listen_check == 0, f"{are.mod_listen_check} != 0"
        assert are.alpha_test == 0.20000000298023224, f"{are.alpha_test} != 0.20000000298023224"
        assert are.camera_style == 1, f"{are.camera_style} != 1"
        assert are.default_envmap == "defaultenvmap", f"{are.default_envmap} != defaultenvmap"
        assert are.grass_texture == "grasstexture", f"{are.grass_texture} != grasstexture"
        assert are.grass_density == 1.0, f"{are.grass_density} != 1.0"
        assert are.grass_size == 1.0, f"{are.grass_size} != 1.0"
        assert are.grass_prob_ll == 0.25, f"{are.grass_prob_ll} != 0.25"
        assert are.grass_prob_lr == 0.25, f"{are.grass_prob_lr} != 0.25"
        assert are.grass_prob_ul == 0.25, f"{are.grass_prob_ul} != 0.25"
        assert are.grass_prob_ur == 0.25, f"{are.grass_prob_ur} != 0.25"
        assert are.moon_ambient == 0, f"{are.moon_ambient} != 0"
        assert are.moon_diffuse == 0, f"{are.moon_diffuse} != 0"
        assert are.moon_fog == 0, f"{are.moon_fog} != 0"
        assert are.moon_fog_near == 99.0, f"{are.moon_fog_near} != 99.0"
        assert are.moon_fog_far == 100.0, f"{are.moon_fog_far} != 100.0"
        assert are.moon_fog_color == 0, f"{are.moon_fog_color} != 0"
        assert are.moon_shadows == 0, f"{are.moon_shadows} != 0"
        assert are.fog_enabled == 1, f"{are.fog_enabled} != 1"
        assert are.fog_near == 99.0, f"{are.fog_near} != 99.0"
        assert are.fog_far == 100.0, f"{are.fog_far} != 100.0"
        assert are.shadows == 1, f"{are.shadows} != 1"
        assert are.is_night == 0, f"{are.is_night} != 0"
        assert are.lighting_scheme == 0, f"{are.lighting_scheme} != 0"
        assert are.shadow_opacity == 205, f"{are.shadow_opacity} != 205"
        assert are.day_night == 0, f"{are.day_night} != 0"
        assert are.chance_rain == 99, f"{are.chance_rain} != 99"
        assert are.chance_snow == 99, f"{are.chance_snow} != 99"
        assert are.chance_lightning == 99, f"{are.chance_lightning} != 99"
        assert are.wind_power == 1, f"{are.wind_power} != 1"
        assert are.loadscreen_id == 0, f"{are.loadscreen_id} != 0"
        assert are.player_vs_player == 3, f"{are.player_vs_player} != 3"
        assert are.no_rest == 0, f"{are.no_rest} != 0"
        assert are.no_hang_back == 0, f"{are.no_hang_back} != 0"
        assert are.player_only == 0, f"{are.player_only} != 0"
        assert are.unescapable == 1, f"{are.unescapable} != 1"
        assert are.disable_transit == 1, f"{are.disable_transit} != 1"
        assert are.stealth_xp == 1, f"{are.stealth_xp} != 1"
        assert are.stealth_xp_loss == 25, f"{are.stealth_xp_loss} != 25"
        assert are.stealth_xp_max == 25, f"{are.stealth_xp_max} != 25"
        assert are.dirty_size_1 == 1, f"{are.dirty_size_1} != 1"
        assert are.dirty_formula_1 == 1, f"{are.dirty_formula_1} != 1"
        assert are.dirty_func_1 == 1, f"{are.dirty_func_1} != 1"
        assert are.dirty_size_2 == 1, f"{are.dirty_size_2} != 1"
        assert are.dirty_formula_2 == 1, f"{are.dirty_formula_2} != 1"
        assert are.dirty_func_2 == 1, f"{are.dirty_func_2} != 1"
        assert are.dirty_size_3 == 1, f"{are.dirty_size_3} != 1"
        assert are.dirty_formula_3 == 1, f"{are.dirty_formula_3} != 1"
        assert are.dirty_func_3 == 1, f"{are.dirty_func_3} != 1"
        assert are.on_enter == "k_on_enter", f"{are.on_enter} != k_on_enter"
        assert are.on_exit == "onexit", f"{are.on_exit} != onexit"
        assert are.on_heartbeat == "onheartbeat", f"{are.on_heartbeat} != onheartbeat"
        assert are.on_user_defined == "onuserdefined", f"{are.on_user_defined} != onuserdefined"

        assert are.version == 88, f"{are.version} != 88"
        assert are.grass_ambient.bgr_integer() == 16777215, f"{are.grass_ambient.bgr_integer()} != 16777215"
        assert are.grass_diffuse.bgr_integer() == 16777215, f"{are.grass_diffuse.bgr_integer()} != 16777215"
        assert are.sun_ambient.bgr_integer() == 16777215, f"{are.sun_ambient.bgr_integer()} != 16777215"
        assert are.sun_diffuse.bgr_integer() == 16777215, f"{are.sun_diffuse.bgr_integer()} != 16777215"
        assert are.fog_color.bgr_integer() == 16777215, f"{are.fog_color.bgr_integer()} != 16777215"
        assert are.dynamic_light.bgr_integer() == 16777215, f"{are.dynamic_light.bgr_integer()} != 16777215"
        assert are.dirty_argb_1.bgr_integer() == 8060928, f"{are.dirty_argb_1.bgr_integer()} != 8060928"
        assert are.dirty_argb_2.bgr_integer() == 13763584, f"{are.dirty_argb_2.bgr_integer()} != 13763584"
        assert are.dirty_argb_3.bgr_integer() == 3747840, f"{are.dirty_argb_3.bgr_integer()} != 3747840"
        # TODO: Fix RGB/BGR mix up


if __name__ == "__main__":
    unittest.main()
