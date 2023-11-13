from __future__ import annotations

import os
import re


def is_int(string: str):
    """Can be cast to an int without raising an error.

    Args:
    ----
        string (str):

    """
    try:
        _ = int(string)
    except ValueError:
        return False
    else:
        return True


def is_float(string: str):
    """Can be cast to a float without raising an error.

    Args:
    ----
        string (str):

    """
    try:
        _ = float(string)
    except ValueError:
        return False
    else:
        return True


def is_nss_file(filename: str):
    """Returns true if the given filename has a NSS file extension."""
    return filename.lower().endswith(".nss")


def is_mod_file(filename: str):
    """Returns true if the given filename has a MOD file extension."""
    return filename.lower().endswith(".mod")


def is_erf_file(filename: str):
    """Returns true if the given filename has a ERF file extension."""
    return filename.lower().endswith(".erf")


def is_erf_or_mod_file(filename: str):
    """Returns true if the given filename has either an ERF or MOD file extension."""
    return filename.lower().endswith((".erf", ".mod"))


def is_rim_file(filename: str):
    """Returns true if the given filename has a RIM file extension."""
    return filename.lower().endswith(".rim")


def is_bif_file(filename: str):
    """Returns true if the given filename has a BIF file extension."""
    return filename.lower().endswith(".bif")


def is_capsule_file(filename: str):
    """Returns true if the given filename has either an ERF, MOD or RIM file extension."""
    return is_erf_or_mod_file(filename) or is_rim_file(filename)


def is_storage_file(filename: str):
    """Returns true if the given filename has either an BIF, ERF, MOD or RIM file extension."""
    return is_capsule_file(filename) or is_bif_file(filename)


def universal_simplify_exception(e):
    """Simplify exceptions into a standardized format
    Args:
        e: Exception - The exception to simplify
    Returns:
        error_name: str - The name of the exception
        error_message: str - A human-readable message for the exception
    Processing Logic:
    - Extract the exception name from the type
    - Handle specific exception types differently
      - FileNotFoundError uses filename attribute
      - PermissionError uses filename attribute
      - TimeoutError uses args[0]
      - InterruptedError uses errno attribute
      - ConnectionError uses request attribute if available
    - Try common exception attributes for a message
    - Return exception name and args joined as a string if no other info available.
    """
    error_name = type(e).__name__
    try:
        # Fallback: use the exception type name itself
        if not e.args:
            return error_name, "Unknown cause"

        # Handle FileNotFoundError, which has 'filename' attribute
        if isinstance(e, FileNotFoundError):
            if len(e.args) > 1:
                return error_name, f"{e.args[1]}: {e.filename if hasattr(e, 'filename') else e.args[0]}"
            return error_name, f"Could not find the file: '{e.filename if hasattr(e, 'filename') else e.args[0]}'"

        # Handle PermissionError, which may have a 'filename' attribute
        if isinstance(e, PermissionError):
            return error_name, f"Permission Denied: {e.filename if hasattr(e, 'filename') else e.args[0]}"

        # Handle TimeoutError
        if isinstance(e, TimeoutError):
            return error_name, f"Operation timed out: {e.args[0]}"

        # Handle InterruptedError, which may have an 'errno' attribute
        if isinstance(e, InterruptedError):
            return error_name, f"Interrupted: {e.errno}"

        # Handle ConnectionError, which may have a 'request' attribute if it's from the `requests` library
        if isinstance(e, ConnectionError):
            return error_name, f"Connection Error: {getattr(e, 'request', lambda: {'method': e.args[0]})().get('method', '')}"

        # Add more oddball exception handling here as needed

        # Try commonly used attributes for human-readable messages
        for attr in ["strerror", "message", "reason", "filename", "filename1", "filename2"]:
            msg = getattr(e, attr, None)
            if msg:
                return error_name, f"{error_name}: {msg}"
    except Exception:  # noqa: BLE001
        return error_name, repr(e)

    # Check if 'args' attribute has any information
    return error_name, f"{error_name}: {','.join(e.args)}"




MAX_CHARS_BEFORE_NEWLINE_FORMAT = 20  # Adjust as needed

def format_text(text):
    text_str = str(text)
    if "\n" in text_str or len(text_str) > MAX_CHARS_BEFORE_NEWLINE_FORMAT:
        return f'"""{os.linesep}{text_str}{os.linesep}"""'
    return f"'{text_str}'"

def first_char_diff_index(str1, str2):
    """Find the index of the first differing character in two strings."""
    min_length = min(len(str1), len(str2))
    for i in range(min_length):
        if str1[i] != str2[i]:
            return i
    if len(str1) != len(str2):
        return min_length  # Difference due to length
    return -1  # No difference

def generate_diff_marker_line(index, length):
    """Generate a line of spaces with a '^' at the specified index."""
    if index == -1:
        return ""
    return " " * index + "^" + " " * (length - index - 1)

def compare_and_format(old_value, new_value):
    """Compares and formats two values for diff display
    Args:
        old_value: The old value to compare
        new_value: The new value to compare
    Returns:
        A tuple of formatted old and new values for diff display
    Processing Logic:
        - Converts old_value and new_value to strings and splits into lines
        - Zips the lines to iterate in parallel
        - Finds index of first differing character between lines
        - Generates a diff marker line based on index
        - Appends lines and marker lines to formatted outputs
        - Joins lines with line separators and returns a tuple.
    """
    old_text = str(old_value)
    new_text = str(new_value)
    old_lines = old_text.split("\n")
    new_lines = new_text.split("\n")
    formatted_old = []
    formatted_new = []

    for old_line, new_line in zip(old_lines, new_lines):
        diff_index = first_char_diff_index(old_line, new_line)
        marker_line = generate_diff_marker_line(diff_index, max(len(old_line), len(new_line)))

        formatted_old.append(old_line)
        formatted_new.append(new_line)
        if marker_line:
            formatted_old.append(marker_line)
            formatted_new.append(marker_line)

    return os.linesep.join(formatted_old), os.linesep.join(formatted_new)

def striprtf(text) -> str:  # noqa: C901, PLR0915, PLR0912
    """Removes RTF tags from a string.
    Strips RTF encoding utterly and completely
    Args:
        text: {String}: The input text possibly containing RTF tags
    Returns:
        str: {A plain text string without any RTF tags}
    Processes the input text by:
    1. Using regular expressions to find RTF tags and special characters
    2. Translating RTF tags and special characters to normal text
    3. Ignoring certain tags and characters inside tags marked as "ignorable"
    4. Appending/joining resulting text pieces to output.
    """
    pattern = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)", re.I)
    # control words which specify a "destination".
    destinations = frozenset(
        (
            "aftncn",
            "aftnsep",
            "aftnsepc",
            "annotation",
            "atnauthor",
            "atndate",
            "atnicn",
            "atnid",
            "atnparent",
            "atnref",
            "atntime",
            "atrfend",
            "atrfstart",
            "author",
            "background",
            "bkmkend",
            "bkmkstart",
            "blipuid",
            "buptim",
            "category",
            "colorschememapping",
            "colortbl",
            "comment",
            "company",
            "creatim",
            "datafield",
            "datastore",
            "defchp",
            "defpap",
            "do",
            "doccomm",
            "docvar",
            "dptxbxtext",
            "ebcend",
            "ebcstart",
            "factoidname",
            "falt",
            "fchars",
            "ffdeftext",
            "ffentrymcr",
            "ffexitmcr",
            "ffformat",
            "ffhelptext",
            "ffl",
            "ffname",
            "ffstattext",
            "field",
            "file",
            "filetbl",
            "fldinst",
            "fldrslt",
            "fldtype",
            "fname",
            "fontemb",
            "fontfile",
            "fonttbl",
            "footer",
            "footerf",
            "footerl",
            "footerr",
            "footnote",
            "formfield",
            "ftncn",
            "ftnsep",
            "ftnsepc",
            "g",
            "generator",
            "gridtbl",
            "header",
            "headerf",
            "headerl",
            "headerr",
            "hl",
            "hlfr",
            "hlinkbase",
            "hlloc",
            "hlsrc",
            "hsv",
            "htmltag",
            "info",
            "keycode",
            "keywords",
            "latentstyles",
            "lchars",
            "levelnumbers",
            "leveltext",
            "lfolevel",
            "linkval",
            "list",
            "listlevel",
            "listname",
            "listoverride",
            "listoverridetable",
            "listpicture",
            "liststylename",
            "listtable",
            "listtext",
            "lsdlockedexcept",
            "macc",
            "maccPr",
            "mailmerge",
            "maln",
            "malnScr",
            "manager",
            "margPr",
            "mbar",
            "mbarPr",
            "mbaseJc",
            "mbegChr",
            "mborderBox",
            "mborderBoxPr",
            "mbox",
            "mboxPr",
            "mchr",
            "mcount",
            "mctrlPr",
            "md",
            "mdeg",
            "mdegHide",
            "mden",
            "mdiff",
            "mdPr",
            "me",
            "mendChr",
            "meqArr",
            "meqArrPr",
            "mf",
            "mfName",
            "mfPr",
            "mfunc",
            "mfuncPr",
            "mgroupChr",
            "mgroupChrPr",
            "mgrow",
            "mhideBot",
            "mhideLeft",
            "mhideRight",
            "mhideTop",
            "mhtmltag",
            "mlim",
            "mlimloc",
            "mlimlow",
            "mlimlowPr",
            "mlimupp",
            "mlimuppPr",
            "mm",
            "mmaddfieldname",
            "mmath",
            "mmathPict",
            "mmathPr",
            "mmaxdist",
            "mmc",
            "mmcJc",
            "mmconnectstr",
            "mmconnectstrdata",
            "mmcPr",
            "mmcs",
            "mmdatasource",
            "mmheadersource",
            "mmmailsubject",
            "mmodso",
            "mmodsofilter",
            "mmodsofldmpdata",
            "mmodsomappedname",
            "mmodsoname",
            "mmodsorecipdata",
            "mmodsosort",
            "mmodsosrc",
            "mmodsotable",
            "mmodsoudl",
            "mmodsoudldata",
            "mmodsouniquetag",
            "mmPr",
            "mmquery",
            "mmr",
            "mnary",
            "mnaryPr",
            "mnoBreak",
            "mnum",
            "mobjDist",
            "moMath",
            "moMathPara",
            "moMathParaPr",
            "mopEmu",
            "mphant",
            "mphantPr",
            "mplcHide",
            "mpos",
            "mr",
            "mrad",
            "mradPr",
            "mrPr",
            "msepChr",
            "mshow",
            "mshp",
            "msPre",
            "msPrePr",
            "msSub",
            "msSubPr",
            "msSubSup",
            "msSubSupPr",
            "msSup",
            "msSupPr",
            "mstrikeBLTR",
            "mstrikeH",
            "mstrikeTLBR",
            "mstrikeV",
            "msub",
            "msubHide",
            "msup",
            "msupHide",
            "mtransp",
            "mtype",
            "mvertJc",
            "mvfmf",
            "mvfml",
            "mvtof",
            "mvtol",
            "mzeroAsc",
            "mzeroDesc",
            "mzeroWid",
            "nesttableprops",
            "nextfile",
            "nonesttables",
            "objalias",
            "objclass",
            "objdata",
            "object",
            "objname",
            "objsect",
            "objtime",
            "oldcprops",
            "oldpprops",
            "oldsprops",
            "oldtprops",
            "oleclsid",
            "operator",
            "panose",
            "password",
            "passwordhash",
            "pgp",
            "pgptbl",
            "picprop",
            "pict",
            "pn",
            "pnseclvl",
            "pntext",
            "pntxta",
            "pntxtb",
            "printim",
            "private",
            "propname",
            "protend",
            "protstart",
            "protusertbl",
            "pxe",
            "result",
            "revtbl",
            "revtim",
            "rsidtbl",
            "rxe",
            "shp",
            "shpgrp",
            "shpinst",
            "shppict",
            "shprslt",
            "shptxt",
            "sn",
            "sp",
            "staticval",
            "stylesheet",
            "subject",
            "sv",
            "svb",
            "tc",
            "template",
            "themedata",
            "title",
            "txe",
            "ud",
            "upr",
            "userprops",
            "wgrffmtfilter",
            "windowcaption",
            "writereservation",
            "writereservhash",
            "xe",
            "xform",
            "xmlattrname",
            "xmlattrvalue",
            "xmlclose",
            "xmlname",
            "xmlnstbl",
            "xmlopen",
        ),
    )
    # Translation of some special characters.
    specialchars = {
        "par": "\n",
        "sect": "\n\n",
        "page": "\n\n",
        "line": "\n",
        "tab": "\t",
        "emdash": "\u2014",
        "endash": "\u2013",
        "emspace": "\u2003",
        "enspace": "\u2002",
        "qmspace": "\u2005",
        "bullet": "\u2022",
        "lquote": "\u2018",
        "rquote": "\u2019",
        "ldblquote": "\201C",
        "rdblquote": "\u201D",
    }
    stack = []
    ignorable = False  # Whether this group (and all inside it) are "ignorable".
    ucskip = 1  # Number of ASCII characters to skip after a unicode character.
    curskip = 0  # Number of ASCII characters left to skip
    out = []  # Output buffer.
    for match in pattern.finditer(text):
        word, arg, hexcode, char, brace, tchar = match.groups()
        if brace:
            curskip = 0
            if brace == "{":
                # Push state
                stack.append((ucskip, ignorable))
            elif brace == "}":
                # Pop state
                ucskip, ignorable = stack.pop()
        elif char:  # \x (not a letter)
            curskip = 0
            if char == "~":
                if not ignorable:
                    out.append("\xA0")
            elif char in "{}\\":
                if not ignorable:
                    out.append(char)
            elif char == "*":
                ignorable = True
        elif word:  # \foo
            curskip = 0
            if word in destinations:
                ignorable = True
            elif ignorable:
                pass
            elif word in specialchars:
                out.append(specialchars[word])
            elif word == "uc":
                ucskip = int(arg)
            elif word == "u":
                c = int(arg)
                if c < 0:
                    c += 0x10000
                out.append(chr(c))
                curskip = ucskip
        elif hexcode:  # \'xx
            if curskip > 0:
                curskip -= 1
            elif not ignorable:
                c = int(hexcode, 16)
                out.append(chr(c))
        elif tchar:
            if curskip > 0:
                curskip -= 1
            elif not ignorable:
                out.append(tchar)
    return "".join(out)
