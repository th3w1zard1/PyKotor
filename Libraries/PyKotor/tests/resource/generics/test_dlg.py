from __future__ import annotations

import os
import pathlib
from pathlib import PureWindowsPath
import sys
import unittest
from unittest import TestCase
import pytest

from pykotor.common.language import Gender, Language, LocalizedString

THIS_SCRIPT_PATH: pathlib.Path = pathlib.Path(__file__).resolve()
PYKOTOR_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[4].joinpath("src")
UTILITY_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[6].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING

from pykotor.common.misc import Color, Game, ResRef
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.dlg import (
    DLG,
    DLGAnimation,
    DLGComputerType,
    DLGConversationType,
    DLGEntry,
    DLGLink,
    DLGNode,
    DLGReply,
    DLGStunt,
    construct_dlg,
    dismantle_dlg,
)
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:

    from pykotor.resource.formats.gff import GFF

TEST_FILE = "Libraries/PyKotor/tests/test_files/test.dlg"
TEST_K1_FILE = "Libraries/PyKotor/tests/test_files/test_k1.dlg"

TEST_DLG_XML = """<gff3>
  <struct id="-1">
    <uint32 label="DelayEntry">13</uint32>
    <uint32 label="DelayReply">14</uint32>
    <uint32 label="NumWords">1337</uint32>
    <resref label="EndConverAbort">abort</resref>
    <resref label="EndConversation">end</resref>
    <byte label="Skippable">1</byte>
    <resref label="AmbientTrack">track</resref>
    <byte label="AnimatedCut">123</byte>
    <resref label="CameraModel">camm</resref>
    <byte label="ComputerType">1</byte>
    <sint32 label="ConversationType">1</sint32>
    <list label="EntryList">
      <struct id="0">
        <exostring label="Speaker">bark</exostring>
        <exostring label="Listener">yoohoo</exostring>
        <list label="AnimList">
          <struct id="0">
            <exostring label="Participant">aaa</exostring>
            <uint16 label="Animation">1200</uint16>
            </struct>
          <struct id="0">
            <exostring label="Participant">bbb</exostring>
            <uint16 label="Animation">2400</uint16>
            </struct>
          </list>
        <locstring label="Text" strref="-1">
          <string language="0">Greetings</string>
          </locstring>
        <resref label="VO_ResRef">gand</resref>
        <resref label="Script">num1</resref>
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment">commentto</exostring>
        <resref label="Sound">gonk</resref>
        <exostring label="Quest">quest</exostring>
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <uint32 label="WaitFlags">1</uint32>
        <uint32 label="CameraAngle">14</uint32>
        <byte label="FadeType">1</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">0</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            <resref label="Active2" />
            <sint32 label="Param1">0</sint32>
            <sint32 label="Param1b">0</sint32>
            <sint32 label="Param2">0</sint32>
            <sint32 label="Param2b">0</sint32>
            <sint32 label="Param3">0</sint32>
            <sint32 label="Param3b">0</sint32>
            <sint32 label="Param4">0</sint32>
            <sint32 label="Param4b">0</sint32>
            <sint32 label="Param5">0</sint32>
            <sint32 label="Param5b">0</sint32>
            <exostring label="ParamStrA" />
            <exostring label="ParamStrB" />
            <byte label="Not">0</byte>
            <byte label="Not2">0</byte>
            <sint32 label="Logic">0</sint32>
            </struct>
          <struct id="1">
            <uint32 label="Index">1</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            <resref label="Active2" />
            <sint32 label="Param1">0</sint32>
            <sint32 label="Param1b">0</sint32>
            <sint32 label="Param2">0</sint32>
            <sint32 label="Param2b">0</sint32>
            <sint32 label="Param3">0</sint32>
            <sint32 label="Param3b">0</sint32>
            <sint32 label="Param4">0</sint32>
            <sint32 label="Param4b">0</sint32>
            <sint32 label="Param5">0</sint32>
            <sint32 label="Param5b">0</sint32>
            <exostring label="ParamStrA" />
            <exostring label="ParamStrB" />
            <byte label="Not">0</byte>
            <byte label="Not2">0</byte>
            <sint32 label="Logic">0</sint32>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        <sint32 label="ActionParam1">1</sint32>
        <sint32 label="ActionParam1b">2</sint32>
        <sint32 label="ActionParam2">3</sint32>
        <sint32 label="ActionParam2b">4</sint32>
        <sint32 label="ActionParam3">5</sint32>
        <sint32 label="ActionParam3b">6</sint32>
        <sint32 label="ActionParam4">7</sint32>
        <sint32 label="ActionParam4b">8</sint32>
        <sint32 label="ActionParam5">9</sint32>
        <sint32 label="ActionParam5b">11</sint32>
        <exostring label="ActionParamStrA">aaa</exostring>
        <exostring label="ActionParamStrB">bbb</exostring>
        <sint32 label="AlienRaceNode">1</sint32>
        <sint32 label="CamVidEffect">-1</sint32>
        <byte label="Changed">1</byte>
        <sint32 label="Emotion">4</sint32>
        <sint32 label="FacialAnim">2</sint32>
        <sint32 label="NodeID">1</sint32>
        <sint32 label="NodeUnskippable">1</sint32>
        <sint32 label="PostProcNode">3</sint32>
        <sint32 label="RecordNoOverri">1</sint32>
        <sint32 label="RecordVO">1</sint32>
        <resref label="Script2">num2</resref>
        <sint32 label="VOTextChanged">1</sint32>
        <sint32 label="CameraID">32</sint32>
        <sint32 label="RecordNoVOOverri">1</sint32>
        </struct>
      <struct id="1">
        <exostring label="Speaker" />
        <exostring label="Listener" />
        <list label="AnimList" />
        <locstring label="Text" strref="-1">
          <string language="0">Farewell</string>
          </locstring>
        <resref label="VO_ResRef" />
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList" />
        <byte label="SoundExists">0</byte>
        <sint32 label="ActionParam1">0</sint32>
        <sint32 label="ActionParam1b">0</sint32>
        <sint32 label="ActionParam2">0</sint32>
        <sint32 label="ActionParam2b">0</sint32>
        <sint32 label="ActionParam3">0</sint32>
        <sint32 label="ActionParam3b">0</sint32>
        <sint32 label="ActionParam4">0</sint32>
        <sint32 label="ActionParam4b">0</sint32>
        <sint32 label="ActionParam5">0</sint32>
        <sint32 label="ActionParam5b">0</sint32>
        <exostring label="ActionParamStrA" />
        <exostring label="ActionParamStrB" />
        <sint32 label="AlienRaceNode">0</sint32>
        <sint32 label="CamVidEffect">-1</sint32>
        <byte label="Changed">0</byte>
        <sint32 label="Emotion">4</sint32>
        <sint32 label="FacialAnim">0</sint32>
        <sint32 label="NodeID">0</sint32>
        <sint32 label="NodeUnskippable">0</sint32>
        <sint32 label="PostProcNode">0</sint32>
        <sint32 label="RecordNoOverri">0</sint32>
        <sint32 label="RecordVO">0</sint32>
        <resref label="Script2" />
        <sint32 label="VOTextChanged">0</sint32>
        <sint32 label="CameraID">-1</sint32>
        <sint32 label="RecordNoVOOverri">0</sint32>
        </struct>
      <struct id="2">
        <exostring label="Speaker" />
        <exostring label="Listener" />
        <list label="AnimList" />
        <locstring label="Text" strref="-1">
          <string language="0">I dun wanna talk no more.</string>
          </locstring>
        <resref label="VO_ResRef" />
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList" />
        <byte label="SoundExists">0</byte>
        <sint32 label="ActionParam1">0</sint32>
        <sint32 label="ActionParam1b">0</sint32>
        <sint32 label="ActionParam2">0</sint32>
        <sint32 label="ActionParam2b">0</sint32>
        <sint32 label="ActionParam3">0</sint32>
        <sint32 label="ActionParam3b">0</sint32>
        <sint32 label="ActionParam4">0</sint32>
        <sint32 label="ActionParam4b">0</sint32>
        <sint32 label="ActionParam5">0</sint32>
        <sint32 label="ActionParam5b">0</sint32>
        <exostring label="ActionParamStrA" />
        <exostring label="ActionParamStrB" />
        <sint32 label="AlienRaceNode">0</sint32>
        <sint32 label="CamVidEffect">-1</sint32>
        <byte label="Changed">0</byte>
        <sint32 label="Emotion">4</sint32>
        <sint32 label="FacialAnim">0</sint32>
        <sint32 label="NodeID">0</sint32>
        <sint32 label="NodeUnskippable">0</sint32>
        <sint32 label="PostProcNode">0</sint32>
        <sint32 label="RecordNoOverri">0</sint32>
        <sint32 label="RecordVO">0</sint32>
        <resref label="Script2" />
        <sint32 label="VOTextChanged">0</sint32>
        <sint32 label="CameraID">-1</sint32>
        <sint32 label="RecordNoVOOverri">0</sint32>
        </struct>
      </list>
    <byte label="OldHitCheck">1</byte>
    <list label="ReplyList">
      <struct id="0">
        <exostring label="Listener" />
        <list label="AnimList" />
        <locstring label="Text" strref="-1">
          <string language="0">Hello creature!</string>
          </locstring>
        <resref label="VO_ResRef" />
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList">
          <struct id="0">
            <uint32 label="Index">0</uint32>
            <resref label="Active" />
            <resref label="Active2" />
            <sint32 label="Param1">0</sint32>
            <sint32 label="Param1b">0</sint32>
            <sint32 label="Param2">0</sint32>
            <sint32 label="Param2b">0</sint32>
            <sint32 label="Param3">0</sint32>
            <sint32 label="Param3b">0</sint32>
            <sint32 label="Param4">0</sint32>
            <sint32 label="Param4b">0</sint32>
            <sint32 label="Param5">0</sint32>
            <sint32 label="Param5b">0</sint32>
            <exostring label="ParamStrA" />
            <exostring label="ParamStrB" />
            <byte label="Not">0</byte>
            <byte label="Not2">0</byte>
            <sint32 label="Logic">0</sint32>
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">0</byte>
        <sint32 label="ActionParam1">0</sint32>
        <sint32 label="ActionParam1b">0</sint32>
        <sint32 label="ActionParam2">0</sint32>
        <sint32 label="ActionParam2b">0</sint32>
        <sint32 label="ActionParam3">0</sint32>
        <sint32 label="ActionParam3b">0</sint32>
        <sint32 label="ActionParam4">0</sint32>
        <sint32 label="ActionParam4b">0</sint32>
        <sint32 label="ActionParam5">0</sint32>
        <sint32 label="ActionParam5b">0</sint32>
        <exostring label="ActionParamStrA" />
        <exostring label="ActionParamStrB" />
        <sint32 label="AlienRaceNode">0</sint32>
        <sint32 label="CamVidEffect">-1</sint32>
        <byte label="Changed">0</byte>
        <sint32 label="Emotion">4</sint32>
        <sint32 label="FacialAnim">0</sint32>
        <sint32 label="NodeID">0</sint32>
        <sint32 label="NodeUnskippable">0</sint32>
        <sint32 label="PostProcNode">0</sint32>
        <sint32 label="RecordNoOverri">0</sint32>
        <sint32 label="RecordVO">0</sint32>
        <resref label="Script" />
        <resref label="Script2" />
        <resref label="Sound" />
        <byte label="SoundExists">0</byte>
        <locstring label="Text" strref="-1">
          <string language="0">Goodbye.</string>
          </locstring>
        <sint32 label="VOTextChanged">0</sint32>
        <resref label="VO_ResRef" />
        <uint32 label="WaitFlags">0</uint32>
        </struct>
      <struct id="1">
        <sint32 label="ActionParam1">0</sint32>
        <sint32 label="ActionParam1b">0</sint32>
        <sint32 label="ActionParam2">0</sint32>
        <sint32 label="ActionParam2b">0</sint32>
        <sint32 label="ActionParam3">0</sint32>
        <sint32 label="ActionParam3b">0</sint32>
        <sint32 label="ActionParam4">0</sint32>
        <sint32 label="ActionParam4b">0</sint32>
        <sint32 label="ActionParam5">0</sint32>
        <sint32 label="ActionParam5b">0</sint32>
        <exostring label="ActionParamStrA" />
        <exostring label="ActionParamStrB" />
        <sint32 label="AlienRaceNode">0</sint32>
        <list label="AnimList">
          <struct id="0">
            <exostring label="Participant">aaa</exostring>
            <uint16 label="Animation">1200</uint16>
            </struct>
          <struct id="0">
            <exostring label="Participant">bbb</exostring>
            <uint16 label="Animation">2400</uint16>
            </struct>
          </list>
        <sint32 label="CamVidEffect">-1</sint32>
        <uint32 label="CameraAngle">0</uint32>
        <sint32 label="CameraID">-1</sint32>
        <byte label="Changed">0</byte>
        <exostring label="Comment" />
        <uint32 label="Delay">4294967295</uint32>
        <sint32 label="Emotion">4</sint32>
        <list label="EntriesList">
          <struct id="0">
            <uint32 label="Index">1</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            <resref label="Active2" />
            <sint32 label="Param1">0</sint32>
            <sint32 label="Param1b">0</sint32>
            <sint32 label="Param2">0</sint32>
            <sint32 label="Param2b">0</sint32>
            <sint32 label="Param3">0</sint32>
            <sint32 label="Param3b">0</sint32>
            <sint32 label="Param4">0</sint32>
            <sint32 label="Param4b">0</sint32>
            <sint32 label="Param5">0</sint32>
            <sint32 label="Param5b">0</sint32>
            <exostring label="ParamStrA" />
            <exostring label="ParamStrB" />
            <byte label="Not">0</byte>
            <byte label="Not2">0</byte>
            <sint32 label="Logic">0</sint32>
            </struct>
          </list>
        <sint32 label="FacialAnim">0</sint32>
        <byte label="FadeType">0</byte>
        <exostring label="Listener" />
        <sint32 label="NodeID">0</sint32>
        <sint32 label="NodeUnskippable">0</sint32>
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <sint32 label="PostProcNode">0</sint32>
        <exostring label="Quest" />
        <sint32 label="RecordNoOverri">0</sint32>
        <sint32 label="RecordNoVOOverri">0</sint32>
        <sint32 label="RecordVO">0</sint32>
        <resref label="Script" />
        <resref label="Script2" />
        <resref label="Sound" />
        <byte label="SoundExists">0</byte>
        <locstring label="Text" strref="-1">
          <string language="0">Goodbye.</string>
          </locstring>
        <sint32 label="VOTextChanged">0</sint32>
        <resref label="VO_ResRef" />
        <uint32 label="WaitFlags">0</uint32>
        </struct>
      </list>
    <list label="StartingList">
      <struct id="0">
        <uint32 label="Index">0</uint32>
        <resref label="Active" />
        <resref label="Active2" />
        <sint32 label="Param1">0</sint32>
        <sint32 label="Param1b">0</sint32>
        <sint32 label="Param2">0</sint32>
        <sint32 label="Param2b">0</sint32>
        <sint32 label="Param3">0</sint32>
        <sint32 label="Param3b">0</sint32>
        <sint32 label="Param4">0</sint32>
        <sint32 label="Param4b">0</sint32>
        <sint32 label="Param5">0</sint32>
        <sint32 label="Param5b">0</sint32>
        <exostring label="ParamStrA" />
        <exostring label="ParamStrB" />
        <byte label="Not">0</byte>
        <byte label="Not2">0</byte>
        <sint32 label="Logic">0</sint32>
        </struct>
      <struct id="1">
        <uint32 label="Index">2</uint32>
        <resref label="Active" />
        <resref label="Active2" />
        <sint32 label="Param1">0</sint32>
        <sint32 label="Param1b">0</sint32>
        <sint32 label="Param2">0</sint32>
        <sint32 label="Param2b">0</sint32>
        <sint32 label="Param3">0</sint32>
        <sint32 label="Param3b">0</sint32>
        <sint32 label="Param4">0</sint32>
        <sint32 label="Param4b">0</sint32>
        <sint32 label="Param5">0</sint32>
        <sint32 label="Param5b">0</sint32>
        <exostring label="ParamStrA" />
        <exostring label="ParamStrB" />
        <byte label="Not">0</byte>
        <byte label="Not2">0</byte>
        <sint32 label="Logic">0</sint32>
        </struct>
      </list>
    <byte label="UnequipHItem">1</byte>
    <byte label="UnequipItems">1</byte>
    <list label="StuntList">
      <struct id="0">
        <exostring label="Participant">aaa</exostring>
        <resref label="StuntModel">m01aa_c04_char01</resref>
        </struct>
      <struct id="0">
        <exostring label="Participant">bbb</exostring>
        <resref label="StuntModel">m01aa_c04_char01</resref>
        </struct>
      </list>
    <exostring label="VO_ID">echo</exostring>
    <sint32 label="AlienRaceOwner">123</sint32>
    <sint32 label="PostProcOwner">12</sint32>
    <sint32 label="RecordNoVO">3</sint32>
    <exostring label="EditorInfo">v2.3.2 Apr 30, 2008 LastEdit: 11-Jan-22 18:14:34</exostring>
    </struct>
  </gff3>
"""

TEST_K1_DLG_XML = """<gff3>
  <struct id="-1">
    <uint32 label="DelayEntry">0</uint32>
    <uint32 label="DelayReply">0</uint32>
    <uint32 label="NumWords">74</uint32>
    <resref label="EndConversation" />
    <resref label="EndConverAbort" />
    <byte label="Skippable">1</byte>
    <list label="StuntList" />
    <resref label="CameraModel" />
    <exostring label="VO_ID">woma08</exostring>
    <list label="EntryList">
      <struct id="0">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5448" />
        <resref label="VO_ResRef">nm02aawoma08008_</resref>
        <resref label="Script">k_ptar_rndtlkres</resref>
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">0</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      <struct id="1">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5449" />
        <resref label="VO_ResRef">nm02aawoma08006_</resref>
        <resref label="Script">k_ptar_rndtlkinc</resref>
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">1</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      <struct id="2">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5450" />
        <resref label="VO_ResRef">nm02aawoma08004_</resref>
        <resref label="Script">k_ptar_rndtlkinc</resref>
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment">outside apartment</exostring>
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">2</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      <struct id="3">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5451" />
        <resref label="VO_ResRef">nm02aawoma08002_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment">inside apartment</exostring>
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">3</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      <struct id="4">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5452" />
        <resref label="VO_ResRef">nm02aawoma08000_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">4</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      </list>
    <list label="ReplyList">
      <struct id="0">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08009_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      <struct id="1">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08007_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      <struct id="2">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08005_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      <struct id="3">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08003_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      <struct id="4">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08001_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      </list>
    <list label="StartingList">
      <struct id="0">
        <uint32 label="Index">4</uint32>
        <resref label="Active">k_ptar_sithdis</resref>
        </struct>
      <struct id="1">
        <uint32 label="Index">3</uint32>
        <resref label="Active">k_ptar_genhome</resref>
        </struct>
      <struct id="2">
        <uint32 label="Index">2</uint32>
        <resref label="Active">k_ptar_rndtalk0</resref>
        </struct>
      <struct id="3">
        <uint32 label="Index">1</uint32>
        <resref label="Active">k_ptar_rndtalk1</resref>
        </struct>
      <struct id="4">
        <uint32 label="Index">0</uint32>
        <resref label="Active" />
        </struct>
      </list>
    </struct>
  </gff3>
"""

class TestDLG(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, *args):
        self.log_messages.extend(args)

    def test_k1_reconstruct(self):
        gff: GFF = read_gff(TEST_K1_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K1)
        result = gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True)
        output = os.linesep.join(self.log_messages)
        assert result, output

    def test_k1_reconstruct_from_reconstruct(self):
        gff: GFF = read_gff(TEST_K1_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K1)
        re_reconstructed_gff: GFF = dismantle_dlg(construct_dlg(reconstructed_gff), Game.K1)
        result: bool = reconstructed_gff.compare(re_reconstructed_gff, self.log_func)
        output: str = os.linesep.join(self.log_messages)
        assert result, output

    def test_k1_serialization(self):
        gff: GFF = read_gff(TEST_K1_DLG_XML.encode())
        dlg: DLG = construct_dlg(gff)
        for node in dlg.all_entries():
            assert node == DLGNode.from_dict(node.to_dict())

    def test_k2_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K2)
        print(reconstructed_gff.root.get_list("EntryList").at(0).get_int32("RecordNoOverri"))
        reconstructed_gff.root.get_list("EntryList").at(0).set_int32("RecordNoOverri", 1)
        assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

    def test_k2_reconstruct_from_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_dlg(construct_dlg(gff), Game.K2)
        re_reconstructed_gff: GFF = dismantle_dlg(construct_dlg(reconstructed_gff), Game.K2)
        result = reconstructed_gff.compare(re_reconstructed_gff, self.log_func)
        output = os.linesep.join(self.log_messages)
        assert result, output

    def test_io_construct(self):
        gff = read_gff(TEST_DLG_XML.encode())
        dlg = construct_dlg(gff)
        self.validate_io(dlg)

    def validate_io(self, dlg: DLG):
        all_entries: list[DLGEntry] = dlg.all_entries()
        all_replies: list[DLGReply] = dlg.all_replies()

        entry0 = all_entries[0]
        entry1 = all_entries[1]
        entry2 = all_entries[2]

        reply0 = all_replies[0]
        reply1 = all_replies[1]

        assert len(all_entries) == 3
        assert len(all_replies) == 2
        assert len(dlg.starters) == 2
        assert len(dlg.stunts) == 2

        assert entry0 in [link.node for link in dlg.starters]
        assert entry2 in [link.node for link in dlg.starters]

        assert len(entry0.links) == 2
        assert reply0 in [link.node for link in entry0.links]
        assert reply1 in [link.node for link in entry0.links]

        assert len(reply0.links) == 1
        assert entry0 in [link.node for link in reply0.links]

        assert len(reply1.links) == 1
        assert entry1 in [link.node for link in reply1.links]

        assert len(entry2.links) == 0

        assert dlg.delay_entry == 13
        assert dlg.delay_reply == 14
        assert dlg.word_count == 1337
        assert dlg.on_abort == "abort"
        assert dlg.on_end == "end"
        assert dlg.skippable == 1
        assert dlg.ambient_track == "track"
        assert dlg.animated_cut == 123
        assert dlg.camera_model == "camm"
        assert dlg.computer_type.value == 1
        assert dlg.conversation_type.value == 1
        assert dlg.old_hit_check == 1
        assert dlg.unequip_hands == 1
        assert dlg.unequip_items == 1
        assert dlg.vo_id == "echo"
        assert dlg.alien_race_owner == 123
        assert dlg.post_proc_owner == 12
        assert dlg.record_no_vo == 3

        assert entry0.listener == "yoohoo"
        assert entry0.text.stringref == -1
        assert entry0.vo_resref == "gand"
        assert entry0.script1 == "num1"
        assert entry0.delay == -1
        assert entry0.comment == "commentto"
        assert entry0.sound == "gonk"
        assert entry0.quest == "quest"
        assert entry0.plot_index == -1
        assert entry0.plot_xp_percentage == 1.0
        assert entry0.wait_flags == 1
        assert entry0.camera_angle == 14
        assert entry0.fade_type == 1
        assert entry0.sound_exists == 1
        assert entry0.alien_race_node == 1
        assert entry0.vo_text_changed == 1
        assert entry0.emotion_id == 4
        assert entry0.facial_id == 2
        assert entry0.node_id == 1
        assert entry0.unskippable == 1
        assert entry0.post_proc_node == 3
        assert entry0.record_vo == 1
        assert entry0.script2 == "num2"
        assert entry0.vo_text_changed == 1
        assert entry0.record_no_vo_override == 1
        assert entry0.camera_id == 32
        assert entry0.speaker == "bark"
        assert entry0.camera_effect == -1
        assert entry0.record_no_vo_override == 1

        assert dlg.stunts[1].participant == "bbb"
        assert dlg.stunts[1].stunt_model == "m01aa_c04_char01"


class TestDLGEntrySerialization(unittest.TestCase):
    def test_dlg_entry_serialization_basic(self):
        entry = DLGEntry()
        entry.comment = "Test Comment"
        entry.camera_angle = 45

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry.comment == deserialized.comment
        assert entry.camera_angle == deserialized.camera_angle

    def test_dlg_entry_serialization_with_links(self):
        entry = DLGEntry()
        entry.comment = "Entry with links"
        link = DLGLink(entry, 1)
        entry.links.append(link)

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry.comment == deserialized.comment
        assert len(deserialized.links) == 1
        assert deserialized.links[0].list_index == 1

    def test_dlg_entry_serialization_all_attributes(self):
        entry = DLGEntry()
        entry.comment = "All attributes"
        entry.camera_angle = 30
        entry.listener = "Listener"
        entry.quest = "Quest"
        entry.script1 = ResRef("script1")

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry.comment == deserialized.comment
        assert entry.camera_angle == deserialized.camera_angle
        assert entry.listener == deserialized.listener
        assert entry.quest == deserialized.quest
        assert entry.script1 == deserialized.script1

    def test_dlg_entry_serialization_with_multilanguage_text(self):
        entry = DLGEntry()
        entry.comment = "Localized"
        entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello")
        entry.text.set_data(Language.FRENCH, Gender.FEMALE, "Bonjour")
        entry.text.set_data(Language.GERMAN, Gender.MALE, "Guten Tag")

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert deserialized.comment == "Localized"
        assert deserialized.text.get(Language.ENGLISH, Gender.MALE) == "Hello"
        assert deserialized.text.get(Language.FRENCH, Gender.FEMALE) == "Bonjour"
        assert deserialized.text.get(Language.GERMAN, Gender.MALE) == "Guten Tag"

    def test_dlg_entry_with_nested_replies(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))

        entry1.links.append(DLGLink(node=reply1))
        reply1.links.extend([DLGLink(node=entry2), DLGLink(node=reply2)])
        reply2.links.append(DLGLink(node=entry1))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249

        serialized = entry1.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry1.comment == deserialized.comment
        assert len(deserialized.links) == 1
        assert deserialized.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R222"
        assert len(deserialized.links[0].node.links) == 2
        assert deserialized.links[0].node.links[0].node.comment == "E221"
        assert deserialized.links[0].node.links[1].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert deserialized.links[0].node.links[1].node.links[0].node.comment == "E248"

    def test_dlg_entry_with_circular_reference(self):
        # Create DLGEntry and DLGReply objects
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R249"))

        # Establish links between entries and replies to create circular reference
        entry1.links.append(DLGLink(node=reply1))
        reply1.links.append(DLGLink(node=entry2))
        entry2.links.append(DLGLink(node=reply2))
        reply2.links.append(DLGLink(node=entry1))  # Circular reference

        # Serialize the entry1
        serialized = entry1.to_dict()
        # Deserialize back to object
        deserialized = DLGEntry.from_dict(serialized)

        # Assert top-level comment
        assert entry1.comment == deserialized.comment
        
        # Assert first level link
        assert len(deserialized.links) == 1
        deserialized_reply1 = deserialized.links[0].node
        assert deserialized_reply1.text.get(Language.ENGLISH, Gender.MALE) == "R222"

        # Assert second level link
        assert len(deserialized_reply1.links) == 1
        deserialized_entry2 = deserialized_reply1.links[0].node
        assert deserialized_entry2.comment == "E221"

        # Assert third level link
        assert len(deserialized_entry2.links) == 1
        deserialized_reply2 = deserialized_entry2.links[0].node
        assert deserialized_reply2.text.get(Language.ENGLISH, Gender.MALE) == "R249"

        # Assert circular reference back to the original entry1
        assert len(deserialized_reply2.links) == 1
        deserialized_entry1_circular = deserialized_reply2.links[0].node
        assert deserialized_entry1_circular.comment == "E248"

    def test_dlg_entry_with_multiple_levels(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")
        entry3 = DLGEntry(comment="E250")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))
        reply4 = DLGReply(text=LocalizedString.from_english("R225"))
        reply5 = DLGReply(text=LocalizedString.from_english("R224"))

        entry1.links.append(DLGLink(node=reply1))
        reply1.links.extend([DLGLink(node=entry2), DLGLink(node=reply2)])
        reply2.links.append(DLGLink(node=entry3))
        entry3.links.append(DLGLink(node=reply4))
        reply4.links.append(DLGLink(node=reply5))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249

        serialized = entry1.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        assert entry1.comment == deserialized.comment
        assert len(deserialized.links) == 1
        assert deserialized.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R222"
        assert len(deserialized.links[0].node.links) == 2
        assert deserialized.links[0].node.links[0].node.comment == "E221"
        assert deserialized.links[0].node.links[1].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert len(deserialized.links[0].node.links[1].node.links) == 1
        assert deserialized.links[0].node.links[1].node.links[0].node.comment == "E250"
        assert len(deserialized.links[0].node.links[1].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[1].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R225"
        assert len(deserialized.links[0].node.links[1].node.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[1].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R224"


class TestDLGReplySerialization(unittest.TestCase):
    def test_dlg_reply_serialization_basic(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Hello")
        reply.unskippable = True

        serialized = reply.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply.text == deserialized.text
        assert reply.unskippable == deserialized.unskippable

    def test_dlg_reply_serialization_with_links(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Reply with links")
        link = DLGLink(node=reply, list_index=2)
        reply.links.append(link)

        serialized = reply.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply.text == deserialized.text
        assert len(deserialized.links) == 1
        assert deserialized.links[0].list_index == 2

    def test_dlg_reply_serialization_all_attributes(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Reply with all attributes")
        reply.vo_resref = ResRef("vo_resref")
        reply.wait_flags = 5

        serialized = reply.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply.text == deserialized.text
        assert reply.vo_resref == deserialized.vo_resref
        assert reply.wait_flags == deserialized.wait_flags

    def test_dlg_reply_with_nested_entries(self):
        # Create replies with localized text
        reply1 = DLGReply()
        reply1.text.set_data(Language.ENGLISH, Gender.MALE, "R222")
        reply2 = DLGReply()
        reply2.text.set_data(Language.ENGLISH, Gender.MALE, "R223")
        reply3 = DLGReply()
        reply3.text.set_data(Language.ENGLISH, Gender.MALE, "R249")

        # Create entries with comments
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        # Link entries and replies together
        reply1.links.append(DLGLink(node=entry1))
        entry1.links.append(DLGLink(node=reply2))
        reply2.links.append(DLGLink(node=entry2))  # Missing link: reply2 -> entry2
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249

        # Serialize and deserialize reply1
        serialized = reply1.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        # Debug prints
        print("Serialized reply1:", serialized)
        print("Deserialized reply1:", deserialized)

        # Assertions
        # Check the text of the first reply
        original_text = reply1.text.get(Language.ENGLISH, Gender.MALE)
        deserialized_text = deserialized.text.get(Language.ENGLISH, Gender.MALE)
        assert original_text == deserialized_text

        # Check the first link in the deserialized reply
        deserialized_entry1 = deserialized.links[0].node
        assert len(deserialized.links) == 1
        assert deserialized_entry1.comment == "E248"

        # Check the first link in the deserialized entry1
        deserialized_reply2 = deserialized_entry1.links[0].node
        assert len(deserialized_entry1.links) == 1
        assert deserialized_reply2.text.get(Language.ENGLISH, Gender.MALE) == "R223"

        # Check the first link in the deserialized reply2
        deserialized_entry2 = deserialized_reply2.links[0].node
        assert deserialized_entry2.comment == "E221"
        assert len(deserialized_entry2.links) == 1

        # Check the first link in the deserialized entry2
        deserialized_reply3 = deserialized_entry2.links[0].node
        assert deserialized_reply3.text.get(Language.ENGLISH, Gender.MALE) == "R249"

    def test_dlg_reply_with_circular_reference(self):
        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R249"))

        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1.links.append(DLGLink(node=entry1))
        entry1.links.append(DLGLink(node=reply2))
        reply2.links.append(DLGLink(node=entry2))
        entry2.links.append(DLGLink(node=reply1))  # Circular reference

        serialized = reply1.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply1.text == deserialized.text
        assert len(deserialized.links) == 1
        assert deserialized.links[0].node.comment == "E248"
        assert len(deserialized.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R249"
        assert len(deserialized.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.comment == "E221"
        assert len(deserialized.links[0].node.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R222"

    def test_dlg_reply_with_multiple_levels(self):
        def _describe_chain(start_node: DLGReply | DLGEntry) -> str:
            """Return a compact string description of the first few nodes along the primary link chain."""
            parts: list[str] = []
            node = start_node
            steps = 0
            # Walk a single-link chain (the test structure uses one link at each depth)
            while node is not None and steps < 8:
                if isinstance(node, DLGEntry):
                    parts.append(f"Entry(comment={node.comment!r}, text={node.text.get(Language.ENGLISH, Gender.MALE)!r})")
                    node = node.links[0].node if node.links else None
                else:
                    parts.append(f"Reply(text={node.text.get(Language.ENGLISH, Gender.MALE)!r})")
                    node = node.links[0].node if node.links else None
                steps += 1
            return " -> ".join(parts)

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))
        reply4 = DLGReply(text=LocalizedString.from_english("R225"))

        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")
        entry3 = DLGEntry(comment="E250")
        entry4 = DLGEntry(comment="E224")

        reply1.links.append(DLGLink(node=entry1))
        reply2.links.append(DLGLink(node=entry2))
        entry1.links.append(DLGLink(node=reply2))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249
        reply3.links.append(DLGLink(node=entry3))
        entry3.links.append(DLGLink(node=reply4))
        reply4.links.append(DLGLink(node=entry4))

        serialized = reply1.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        assert reply1.text == deserialized.text
        assert len(deserialized.links) == 1
        assert deserialized.links[0].node.comment == "E248"
        assert len(deserialized.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert len(deserialized.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.comment == "E221"
        assert len(deserialized.links[0].node.links[0].node.links[0].node.links) == 1
        assert deserialized.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R249"
        assert len(deserialized.links[0].node.links[0].node.links) == 1

        # Traverse the deserialized graph to ensure all expected nodes survived.
        entry_comments: set[str] = set()
        reply_texts: set[str] = set()
        stack: list[DLGEntry | DLGReply] = [deserialized]
        while stack:
            node = stack.pop()
            if isinstance(node, DLGEntry):
                entry_comments.add(node.comment)
            else:
                reply_texts.add(node.text.get(Language.ENGLISH, Gender.MALE))
            for child_link in node.links:
                stack.append(child_link.node)

        entry3_chain = _describe_chain(deserialized)
        assert {"E248", "E221", "E250", "E224"}.issubset(entry_comments), entry3_chain
        assert {"R222", "R223", "R249", "R225"}.issubset(reply_texts), entry3_chain


class TestDLGLinkSerialization(unittest.TestCase):
    def test_dlg_link_serialization_basic(self):
        link = DLGLink(DLGEntry())
        link.list_index = 3

        serialized = link.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link.list_index == deserialized.list_index

    def test_dlg_link_serialization_with_node(self):
        entry = DLGEntry()
        entry.comment = "Linked entry"
        link = DLGLink(entry)

        serialized = link.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link.node.comment == deserialized.node.comment

    def test_dlg_link_serialization_all_attributes(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Linked reply")
        link = DLGLink(reply, 5)
        link.node = reply

        serialized = link.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link.list_index == deserialized.list_index
        assert link.node.text == deserialized.node.text

    def test_dlg_link_with_nested_entries_and_replies(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))

        link1 = DLGLink(node=reply1)
        link2 = DLGLink(node=entry2)
        link3 = DLGLink(node=reply2)
        link4 = DLGLink(node=reply3)

        entry1.links.append(link1)
        reply1.links.extend([link2, link3])
        entry2.links.append(link4)  # Reuse R249
        reply2.links.append(DLGLink(node=entry1))  # Circular reference: reply2 -> entry1

        serialized = link1.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link1.node.text == deserialized.node.text
        assert len(deserialized.node.links) == 2
        assert deserialized.node.links[0].node.comment == "E221"
        assert deserialized.node.links[1].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert len(deserialized.node.links[1].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.comment == "E248"

    def test_dlg_link_with_circular_references(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R249"))

        link1 = DLGLink(node=reply1)
        link2 = DLGLink(node=entry2)
        link3 = DLGLink(node=reply2)
        link4 = DLGLink(node=entry1)  # Circular reference

        entry1.links.append(link1)
        reply1.links.append(link2)
        entry2.links.append(link3)  # Reuse R249
        reply2.links.append(link4)

        serialized = link1.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link1.node.text == deserialized.node.text
        assert len(deserialized.node.links) == 1
        assert deserialized.node.links[0].node.comment == "E221"
        assert len(deserialized.node.links[0].node.links) == 1
        assert deserialized.node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R249"
        assert len(deserialized.node.links[0].node.links[0].node.links) == 1
        assert deserialized.node.links[0].node.links[0].node.links[0].node.comment == "E248"

    def test_dlg_link_with_multiple_levels(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")
        entry3 = DLGEntry(comment="E250")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))
        reply4 = DLGReply(text=LocalizedString.from_english("R225"))
        reply5 = DLGReply(text=LocalizedString.from_english("R224"))

        link1 = DLGLink(node=reply1)
        link2 = DLGLink(node=entry2)
        link3 = DLGLink(node=reply2)
        link4 = DLGLink(node=reply3)
        link5 = DLGLink(node=entry3)
        link6 = DLGLink(node=reply4)
        link7 = DLGLink(node=reply5)

        entry1.links.append(link1)
        reply1.links.append(link3)
        reply1.links.append(link2)
        entry2.links.append(link4)  # Reuse R249
        reply3.links.append(link5)
        entry3.links.append(link6)
        reply4.links.append(link7)

        serialized = link1.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        assert link1.node.text == deserialized.node.text
        assert len(deserialized.node.links) == 2
        assert deserialized.node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R223"
        assert deserialized.node.links[1].node.comment == "E221"
        assert len(deserialized.node.links[1].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R249"
        assert len(deserialized.node.links[1].node.links[0].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.links[0].node.comment == "E250"
        assert len(deserialized.node.links[1].node.links[0].node.links[0].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R225"
        assert len(deserialized.node.links[1].node.links[0].node.links[0].node.links[0].node.links) == 1
        assert deserialized.node.links[1].node.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE) == "R224"

    def test_dlg_link_serialization_preserves_shared_nodes(self):
        shared_reply = DLGReply(text=LocalizedString.from_english("Shared Reply"))

        link_a = DLGLink(node=shared_reply, list_index=0)
        link_b = DLGLink(node=shared_reply, list_index=1)

        node_map: dict[str | int, object] = {}
        link_a_dict = link_a.to_dict(node_map)
        link_b_dict = link_b.to_dict(node_map)

        restore_map: dict[str | int, object] = {}
        restored_a = DLGLink.from_dict(link_a_dict, restore_map)
        restored_b = DLGLink.from_dict(link_b_dict, restore_map)

        assert restored_a.node is restored_b.node
        assert restored_a.node.text.get(Language.ENGLISH, Gender.MALE) == "Shared Reply"
        assert {restored_a.list_index, restored_b.list_index} == {0, 1}

    def test_dlg_link_iteration_traverses_all_descendants(self):
        root_entry = DLGEntry(comment="root")
        reply_one = DLGReply(text=LocalizedString.from_english("r1"))
        reply_two = DLGReply(text=LocalizedString.from_english("r2"))
        entry_leaf = DLGEntry(comment="leaf")

        link_root = DLGLink(node=reply_one, list_index=0)
        link_secondary = DLGLink(node=reply_two, list_index=1)
        link_leaf = DLGLink(node=entry_leaf, list_index=2)

        root_entry.links.append(link_root)
        reply_one.links.append(link_leaf)
        reply_one.links.append(link_secondary)

        visited_nodes = {
            link.node.comment if isinstance(link.node, DLGEntry) else link.node.text.get(Language.ENGLISH, Gender.MALE)
            for link in link_root
        }
        assert visited_nodes == {"r1", "r2", "leaf"}

class TestDLGAnimationSerialization(unittest.TestCase):
    def test_dlg_animation_serialization_basic(self):
        animation = DLGAnimation()
        animation.animation_id = 1200
        animation.participant = "Player"

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        assert animation.animation_id == deserialized.animation_id
        assert animation.participant == deserialized.participant

    def test_dlg_animation_serialization_default(self):
        animation = DLGAnimation()

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        assert animation.animation_id == deserialized.animation_id
        assert animation.participant == deserialized.participant

    def test_dlg_animation_serialization_with_custom_values(self):
        animation = DLGAnimation()
        animation.animation_id = 2400
        animation.participant = "NPC"

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        assert animation.animation_id == deserialized.animation_id
        assert animation.participant == deserialized.participant


class TestDLGStuntSerialization(unittest.TestCase):
    def test_dlg_stunt_serialization_basic(self):
        stunt = DLGStunt()
        stunt.participant = "Player"
        stunt.stunt_model = ResRef("model")

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        assert stunt.participant == deserialized.participant
        assert stunt.stunt_model == deserialized.stunt_model

    def test_dlg_stunt_serialization_default(self):
        stunt = DLGStunt()

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        assert stunt.participant == deserialized.participant
        assert stunt.stunt_model == deserialized.stunt_model

    def test_dlg_stunt_serialization_with_custom_values(self):
        stunt = DLGStunt()
        stunt.participant = "NPC"
        stunt.stunt_model = ResRef("npc_model")

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        assert stunt.participant == deserialized.participant
        assert stunt.stunt_model == deserialized.stunt_model


class TestDLGGraphUtilities(unittest.TestCase):
    def _build_simple_graph(self) -> tuple[DLG, DLGEntry, DLGReply, DLGEntry, DLGLink, DLGLink, DLGLink, DLGLink]:
        dlg = DLG()

        entry0 = DLGEntry(comment="start")
        entry0.list_index = 0
        entry1 = DLGEntry(comment="leaf")
        entry1.list_index = 1

        reply0 = DLGReply(text=LocalizedString.from_english("middle"))
        reply0.list_index = 0

        start_link0 = DLGLink(node=entry0, list_index=0)
        start_link1 = DLGLink(node=entry1, list_index=1)

        link_entry0_reply = DLGLink(node=reply0, list_index=0)
        link_reply0_entry1 = DLGLink(node=entry1, list_index=0)

        entry0.links.append(link_entry0_reply)
        reply0.links.append(link_reply0_entry1)
        dlg.starters.extend([start_link0, start_link1])
        return dlg, entry0, reply0, entry1, start_link0, start_link1, link_entry0_reply, link_reply0_entry1

    def test_find_paths_for_nodes_and_links(self):
        dlg, entry0, reply0, entry1, start_link0, start_link1, link_entry0_reply, link_reply0_entry1 = self._build_simple_graph()

        paths_entry = dlg.find_paths(entry1)
        paths_reply = dlg.find_paths(reply0)
        paths_start_link = dlg.find_paths(start_link0)
        paths_child_link = dlg.find_paths(link_reply0_entry1)

        assert PureWindowsPath("EntryList", "1") in paths_entry
        assert PureWindowsPath("ReplyList", "0") in paths_reply
        assert PureWindowsPath("StartingList", "0") in paths_start_link
        assert PureWindowsPath("ReplyList", "0", "EntriesList", "0") in paths_child_link

    def test_get_link_parent_and_partial_path(self):
        dlg, entry0, reply0, entry1, start_link0, start_link1, link_entry0_reply, link_reply0_entry1 = self._build_simple_graph()

        assert dlg.get_link_parent(start_link0) is dlg
        assert dlg.get_link_parent(link_entry0_reply) is entry0
        assert dlg.get_link_parent(link_reply0_entry1) is reply0
        assert start_link0.partial_path(is_starter=True) == "StartingList\\0"
        assert link_entry0_reply.partial_path(is_starter=False) == "RepliesList\\0"

    def test_all_entries_and_replies_sorted_and_unique(self):
        dlg, entry0, reply0, entry1, start_link0, start_link1, link_entry0_reply, link_reply0_entry1 = self._build_simple_graph()
        entry2 = DLGEntry(comment="late")
        entry2.list_index = -1
        reply1 = DLGReply(text=LocalizedString.from_english("shared"))
        reply1.list_index = 5

        # Create additional shared references to ensure deduplication
        reply1.links.append(DLGLink(node=entry2, list_index=0))
        entry1.links.append(DLGLink(node=reply1, list_index=1))
        reply1.links.append(DLGLink(node=entry0, list_index=1))

        entries_unsorted = dlg.all_entries()
        replies_unsorted = dlg.all_replies()
        entries_sorted = dlg.all_entries(as_sorted=True)
        replies_sorted = dlg.all_replies(as_sorted=True)

        assert len(entries_unsorted) == 3
        assert len(replies_unsorted) == 2
        assert entries_sorted[0].list_index == 0
        assert entries_sorted[1].list_index == 1
        assert entries_sorted[-1].list_index == -1
        assert replies_sorted[0].list_index == 0
        assert replies_sorted[1].list_index == 5

    def test_calculate_links_and_nodes_counts_cycles_included(self):
        dlg, entry0, reply0, entry1, start_link0, start_link1, link_entry0_reply, link_reply0_entry1 = self._build_simple_graph()
        # Introduce an explicit cycle entry1 -> entry0
        entry1.links.append(DLGLink(node=entry0, list_index=2))

        num_links, num_nodes = entry0.calculate_links_and_nodes()
        # entry0 -> reply0, reply0 -> entry1, entry1 -> entry0 (cycle) => 3 links, 3 nodes
        assert num_links == 3
        assert num_nodes == 3

    def test_shift_item_and_bounds(self):
        dlg, entry0, reply0, entry1, start_link0, start_link1, link_entry0_reply, link_reply0_entry1 = self._build_simple_graph()
        entry0.shift_item(entry0.links, 0, 0)  # no-op allowed
        entry0.shift_item(entry0.links, 0, 0)  # idempotent
        # Add second link for ordering
        entry0.links.append(DLGLink(node=entry1, list_index=1))
        entry0.shift_item(entry0.links, 1, 0)
        assert entry0.links[0].node is entry1
        assert entry0.links[1].node is reply0
        with pytest.raises(IndexError):
            entry0.shift_item(entry0.links, 0, 5)

    def test_node_dict_roundtrip_preserves_metadata(self):
        entry = DLGEntry()
        entry.comment = "deep node"
        entry.speaker = "Carth"
        entry.camera_angle = 33
        entry.camera_anim = 77
        entry.camera_id = 9
        entry.camera_effect = -3
        entry.camera_fov = 90.5
        entry.camera_height = 1.25
        entry.target_height = 0.5
        entry.fade_type = 2
        entry.fade_color = Color(0.1, 0.2, 0.3, 1.0)
        entry.fade_delay = 0.25
        entry.fade_length = 1.5
        entry.quest = "quest_flag"
        entry.quest_entry = 4
        entry.script1 = ResRef("script_a")
        entry.script2 = ResRef("script_b")
        entry.script1_param1 = 11
        entry.script2_param6 = "str"
        entry.wait_flags = 3
        entry.sound_exists = 1
        entry.vo_resref = ResRef("vo")
        entry.sound = ResRef("snd")
        entry.emotion_id = 12
        entry.facial_id = 7
        entry.node_id = 42
        entry.post_proc_node = 17
        entry.record_no_vo_override = True
        entry.record_vo = True
        entry.vo_text_changed = True
        entry.unskippable = True
        entry.text.set_data(Language.ENGLISH, Gender.MALE, "Line")
        entry.text.set_data(Language.FRENCH, Gender.FEMALE, "Ligne")
        animation = DLGAnimation()
        animation.participant = "p1"
        animation.animation_id = 123
        entry.animations.append(animation)

        reply = DLGReply(text=LocalizedString.from_english("reply"))
        reply.camera_anim = 55
        reply.fade_type = 9

        entry.links.append(DLGLink(node=reply, list_index=0))
        reply.links.append(DLGLink(node=entry, list_index=0))

        serialized = entry.to_dict()
        restored = DLGEntry.from_dict(serialized)

        assert restored.camera_angle == 33
        assert restored.camera_anim == 77
        assert restored.camera_id == 9
        assert restored.camera_effect == -3
        assert restored.camera_fov == 90.5
        assert restored.camera_height == 1.25
        assert restored.target_height == 0.5
        assert restored.fade_type == 2
        assert restored.fade_color is not None
        assert restored.fade_color.r == pytest.approx(0.1, abs=0.005)
        assert restored.fade_color.g == pytest.approx(0.2, abs=0.005)
        assert restored.fade_color.b == pytest.approx(0.3, abs=0.005)
        assert restored.fade_color.a == pytest.approx(1.0, abs=0.005)
        assert restored.fade_delay == 0.25
        assert restored.fade_length == 1.5
        assert restored.quest == "quest_flag"
        assert restored.quest_entry == 4
        assert restored.script1 == ResRef("script_a")
        assert restored.script2 == ResRef("script_b")
        assert restored.script1_param1 == 11
        assert restored.script2_param6 == "str"
        assert restored.wait_flags == 3
        assert restored.sound_exists == 1
        assert restored.vo_resref == ResRef("vo")
        assert restored.sound == ResRef("snd")
        assert restored.emotion_id == 12
        assert restored.facial_id == 7
        assert restored.node_id == 42
        assert restored.post_proc_node == 17
        assert restored.record_no_vo_override is True
        assert restored.record_vo is True
        assert restored.vo_text_changed is True
        assert restored.unskippable is True
        assert restored.text.get(Language.FRENCH, Gender.FEMALE) == "Ligne"
        assert restored.animations[0].animation_id == 123
        assert restored.links[0].node.links[0].node.comment == "deep node"

    def test_find_paths_respects_multiple_starters_and_link_parenting(self):
        dlg = DLG()
        dlg.conversation_type = DLGConversationType.Computer
        dlg.computer_type = DLGComputerType.Ancient

        entry_a = DLGEntry(comment="A")
        entry_a.list_index = 2
        entry_b = DLGEntry(comment="B")
        entry_b.list_index = 3
        reply_a = DLGReply(text=LocalizedString.from_english("R"))
        reply_a.list_index = 4

        starter_a = DLGLink(node=entry_a, list_index=0)
        starter_b = DLGLink(node=entry_b, list_index=1)
        dlg.starters.extend([starter_a, starter_b])

        entry_a.links.append(DLGLink(node=reply_a, list_index=0))
        reply_a.links.append(DLGLink(node=entry_b, list_index=0))

        paths_reply_a = dlg.find_paths(reply_a)
        paths_entry_b = dlg.find_paths(entry_b)
        parent_for_reply_link = dlg.get_link_parent(entry_a.links[0])

        assert PureWindowsPath("ReplyList", "4") in paths_reply_a
        assert PureWindowsPath("EntryList", "3") in paths_entry_b
        assert parent_for_reply_link is entry_a


def _build_nested_chain() -> DLGEntry:
    entry1 = DLGEntry(comment="E248")
    entry2 = DLGEntry(comment="E221")
    entry3 = DLGEntry(comment="E250")

    reply1 = DLGReply(text=LocalizedString.from_english("R222"))
    reply2 = DLGReply(text=LocalizedString.from_english("R223"))
    reply3 = DLGReply(text=LocalizedString.from_english("R249"))
    reply4 = DLGReply(text=LocalizedString.from_english("R225"))
    reply5 = DLGReply(text=LocalizedString.from_english("R224"))

    entry1.links.append(DLGLink(node=reply1))
    reply1.links.extend([DLGLink(node=entry2), DLGLink(node=reply2)])  # type: ignore[arg-type]
    reply2.links.append(DLGLink(node=entry3))
    entry3.links.append(DLGLink(node=reply4))
    reply4.links.append(DLGLink(node=reply5))  # type: ignore[arg-type]
    entry2.links.append(DLGLink(node=reply3))
    return entry1


def test_serialization_roundtrip_preserves_deep_chain():
    """Ensure nested entry/reply chains survive to_dict/from_dict roundtrips."""
    root = _build_nested_chain()
    serialized = root.to_dict()
    deserialized = DLGEntry.from_dict(serialized)

    reply1 = deserialized.links[0].node
    reply2 = deserialized.links[0].node.links[1].node
    entry3 = reply2.links[0].node
    reply4 = entry3.links[0].node
    reply5 = reply4.links[0].node

    assert reply1.text.get(Language.ENGLISH, Gender.MALE) == "R222"
    assert reply2.text.get(Language.ENGLISH, Gender.MALE) == "R223"
    assert entry3.comment == "E250"
    assert reply4.text.get(Language.ENGLISH, Gender.MALE) == "R225"
    assert reply5.text.get(Language.ENGLISH, Gender.MALE) == "R224"


def test_shared_node_identity_survives_link_roundtrip():
    """Ensure shared nodes are restored as the same object when deserialized."""
    shared_reply = DLGReply(text=LocalizedString.from_english("Shared Reply"))
    link_a = DLGLink(node=shared_reply, list_index=0)
    link_b = DLGLink(node=shared_reply, list_index=1)

    node_map: dict[str | int, object] = {}
    link_a_dict = link_a.to_dict(node_map)
    link_b_dict = link_b.to_dict(node_map)

    restore_map: dict[str | int, object] = {}
    restored_a = DLGLink.from_dict(link_a_dict, restore_map)
    restored_b = DLGLink.from_dict(link_b_dict, restore_map)

    assert restored_a.node is restored_b.node
    assert restored_a.node.text.get(Language.ENGLISH, Gender.MALE) == "Shared Reply"
    assert {restored_a.list_index, restored_b.list_index} == {0, 1}


if __name__ == "__main__":
    unittest.main()
