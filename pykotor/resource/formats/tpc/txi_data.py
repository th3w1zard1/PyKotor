# From https://nwn.wiki/display/NWN1/TXI#TXI-TextureRelatedFields
# From DarthParametric and Drazgar in the DeadlyStream Discord.
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.common.geometry import Vector2


class TXIBaseInformation:
    def __init__(self) -> None:
        #  Mipmap and Filter settings (0/1) can apply different graphical "softening" on the fonts (not affecting spacing etc.). Don't use it though, in most case it would hurt your eyes.
        #  The engine has broken mip use implementation. It incorrectly mixes mip levels, even on objects filling the screen.
        self.mipmap: int = 0  # The mipmap 0 setting shouldn't be changed. That tells the engine to use mip 0, i.e. the highest resolution of the image
        self.filter: int = 0
        self.downsamplemin: int = 0  # unused in KOTOR
        self.downsamplemax: int = 0  # unused in KOTOR


class TXIMaterialInformation(TXIBaseInformation):
    def __init__(self) -> None:
        self.bumpmaptexture: int
        self.bumpyshinytexture: int
        self.envmaptexture: int
        self.bumpreplacementtexture: int
        self.blending: int
        self.decal: int


class TXITextureInformation(TXIBaseInformation):
    def __init__(self) -> None:
        super().__init__()
        self.proceduretype: int
        self.filerange: int
        self.defaultwidth: int
        self.defaultheight: int
        self.filter: int
        self.maptexelstopixels: int
        self.gamma: int
        self.isbumpmap: int
        self.clamp: int
        self.alphamean: int
        self.isdiffusebumpmap: int
        self.isspecularbumpmap: int
        self.bumpmapscaling: int
        self.specularcolor: int
        self.numx: int
        self.numy: int
        self.cube: int
        self.bumpintensity: int
        self.temporary: int
        self.useglobalalpha: int
        self.isenvironmentmapped: int
        self.pltreplacement: int


class TXIFontInformation(TXIBaseInformation):
    def __init__(self) -> None:
        super().__init__()
        # don't touch these defaults for any reason
        self.numchars: int = 256
        self.upperleftcoords: int = 256
        self.lowerrightcoords: int = 0
        self.spacingB: float = 0  # Float between 0 and 1. spacingB should be left alone.

        self.fontheight: float  # Float between 0 and 1.
        self.baselineheight: float  # presumably sets where the text sits. Probably to account for stuff like French that has those accents that hang underneath characters.
        self.texturewidth: float  # Float between 0 and 1. Actual displayed width of the texture, allows stretching/compressing along the X axis.
        self.fontwidth: float  # Float between 0 and 1. Actually stretches down somehow. Heavily distorts the text when modified. Perhaps this is the Y axis and texturewidth is the X axis?
        self.spacingR: float  # Float between 0 and 1. Do NOT exceed the maximum of 0.002600
        self.caretindent: float  # Float between 0 and 1.
        self.isdoublebyte: int  # unused?
        # self.dbmapping:  # unused in KOTOR
        self.cols: list[Vector2]
        self.rows: list[Vector2]
