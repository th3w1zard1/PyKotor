"""Generate ScriptDefs.cs from NSS files using the actual NCS lexer/parser.

This script uses PyKotor's native NSS lexer to tokenize and then parses
tokens according to the grammar rules to extract constants and functions
from k1_nwscript.nss and k2_nwscript.nss (k2 is the same as tsl), ensuring 100% accuracy.
Outputs C# ScriptDefs.cs instead of Python scriptdefs.py.
"""

from __future__ import annotations

import re
import sys

from pathlib import Path
from typing import TYPE_CHECKING, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "Libraries" / "PyKotor" / "src"))

if TYPE_CHECKING:
    from ply.lex import LexToken

    from pykotor.common.script import (  # type: ignore[import-not-found]  # pyright: ignore[reportUnusedImport]  # noqa: F401
        DataType,
        ScriptConstant,
        ScriptFunction,
        ScriptParam,
    )

try:
    # Import from PyKotor - scriptdefs.py should be a minimal stub before generation
    # Import lexer and classes directly to avoid importing scriptdefs.py
    # We need to temporarily suppress scriptdefs import errors
    import types

    # Suppress scriptdefs import errors by monkey-patching sys.modules
    # This allows us to import the compiler modules even if scriptdefs.py is broken
    scriptdefs_module = types.ModuleType("pykotor.common.scriptdefs")
    scriptdefs_module.KOTOR_CONSTANTS = []  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
    scriptdefs_module.KOTOR_FUNCTIONS = []  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
    scriptdefs_module.TSL_CONSTANTS = []  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
    scriptdefs_module.TSL_FUNCTIONS = []  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
    sys.modules["pykotor.common.scriptdefs"] = scriptdefs_module

    from pykotor.common.misc import Game  # type: ignore[import-not-found, note]
    from pykotor.resource.formats.ncs.compiler.classes import (  # type: ignore[import-not-found, note]
        FloatExpression,  # pyright: ignore[reportUnusedImport]  # noqa: F401
        Identifier,  # pyright: ignore[reportUnusedImport]  # noqa: F401
        IntExpression,  # pyright: ignore[reportUnusedImport]  # noqa: F401
        StringExpression,  # pyright: ignore[reportUnusedImport]  # noqa: F401
        VectorExpression,  # pyright: ignore[reportUnusedImport]  # noqa: F401
    )
    from pykotor.resource.formats.ncs.compiler.lexer import NssLexer  # type: ignore[import-not-found, note]
except ImportError as e:
    print(f"Error importing PyKotor modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)


def token_type_to_datatype(token_type: str) -> str | None:
    """Convert lexer token type to NSS datatype string."""
    type_map = {
        "INT_TYPE": "int",
        "FLOAT_TYPE": "float",
        "STRING_TYPE": "string",
        "VOID_TYPE": "void",
        "OBJECT_TYPE": "object",
        "VECTOR_TYPE": "vector",
        "LOCATION_TYPE": "location",
        "EFFECT_TYPE": "effect",
        "EVENT_TYPE": "event",
        "TALENT_TYPE": "talent",
        "ACTION_TYPE": "action",
    }
    return type_map.get(token_type)


def parse_constant_from_tokens(tokens: list, start_idx: int, lines: list[str]) -> tuple[dict, int] | None:
    """Parse a constant declaration from tokens.

    Grammar: global_variable_initialization : data_type IDENTIFIER '=' expression ';'
    Note: TRUE and FALSE are tokenized as TRUE_VALUE/FALSE_VALUE, not IDENTIFIER
    Note: Negative numbers are tokenized as MINUS followed by INT_VALUE
    """
    if start_idx + 4 >= len(tokens):
        return None

    # Check pattern: TYPE IDENTIFIER = VALUE ;
    # Also handle: TYPE TRUE_VALUE = VALUE ; or TYPE FALSE_VALUE = VALUE ;
    # Also handle: TYPE IDENTIFIER = MINUS VALUE ; (negative numbers)
    name_token_type = tokens[start_idx + 1].type
    is_valid_name = (name_token_type == "IDENTIFIER" or
                     name_token_type in ["TRUE_VALUE", "FALSE_VALUE", "OBJECTSELF_VALUE", "OBJECTINVALID_VALUE"])

    # Check for negative number pattern first (TYPE IDENTIFIER = MINUS VALUE ;)
    if (start_idx + 5 < len(tokens) and
        tokens[start_idx].type in ["INT_TYPE", "FLOAT_TYPE"] and
        is_valid_name and
        tokens[start_idx + 2].type == "=" and
        tokens[start_idx + 3].type == "MINUS" and
        tokens[start_idx + 5].type == ";"):

        datatype = token_type_to_datatype(tokens[start_idx].type)
        if not datatype:
            return None

        # Extract name
        name_token = tokens[start_idx + 1]
        if name_token.type == "TRUE_VALUE":
            name = "TRUE"
        elif name_token.type == "FALSE_VALUE":
            name = "FALSE"
        elif name_token.type == "OBJECTSELF_VALUE":
            name = "OBJECT_SELF"
        elif name_token.type == "OBJECTINVALID_VALUE":
            name = "OBJECT_INVALID"
        elif hasattr(name_token.value, "name"):
            name = name_token.value.name
        else:
            name = str(name_token.value)

        value_token = tokens[start_idx + 4]

        # Extract value (it's negative)
        if datatype == "int" and value_token.type == "INT_VALUE":
            expr = value_token.value
            raw_value = str(expr.value) if hasattr(expr, "value") else str(expr)
            value = f"-{raw_value}"
        elif datatype == "float" and value_token.type == "FLOAT_VALUE":
            expr = value_token.value
            if hasattr(expr, "value"):
                raw_value = str(expr.value).rstrip("f")
            else:
                raw_value = str(expr).rstrip("f")
            value = f"-{raw_value}"
        else:
            return None

        return ({
            "datatype": datatype,
            "name": name,
            "value": value
        }, start_idx + 6)

    # Standard pattern: TYPE IDENTIFIER = VALUE ;
    if (tokens[start_idx].type in ["INT_TYPE", "FLOAT_TYPE", "STRING_TYPE"] and
        is_valid_name and
        tokens[start_idx + 2].type == "=" and
        tokens[start_idx + 4].type == ";"):

        datatype = token_type_to_datatype(tokens[start_idx].type)
        if not datatype:
            return None

        # Extract name - handle special tokens
        name_token = tokens[start_idx + 1]
        if name_token.type == "TRUE_VALUE":
            name = "TRUE"
        elif name_token.type == "FALSE_VALUE":
            name = "FALSE"
        elif name_token.type == "OBJECTSELF_VALUE":
            name = "OBJECT_SELF"
        elif name_token.type == "OBJECTINVALID_VALUE":
            name = "OBJECT_INVALID"
        elif hasattr(name_token.value, "name"):
            name = name_token.value.name
        else:
            name = str(name_token.value)
        value_token = tokens[start_idx + 3]

        # Extract value based on type
        # Note: lexer converts tokens to expression objects (StringExpression, IntExpression, FloatExpression)
        if datatype == "string":
            if value_token.type == "STRING_VALUE":
                # StringExpression.value is the string without quotes
                expr = value_token.value
                if hasattr(expr, "value"):
                    value = expr.value  # RAW VALUE - Do not add quotes here
                else:
                    value = str(expr)   # RAW VALUE - Do not add quotes here
            else:
                return None
        elif datatype == "int":
            if value_token.type == "INT_VALUE":
                # IntExpression.value is the int
                expr = value_token.value
                value = str(expr.value) if hasattr(expr, "value") else str(expr)
            elif value_token.type == "INT_HEX_VALUE":
                # Convert hex to decimal
                hex_str = value_token.value
                if isinstance(hex_str, str):
                    value = str(int(hex_str, 16))
                else:
                    value = str(hex_str)
            elif value_token.type == "TRUE_VALUE":
                value = "1"
            elif value_token.type == "FALSE_VALUE":
                value = "0"
            else:
                return None
        elif datatype == "float":
            if value_token.type == "FLOAT_VALUE":
                # FloatExpression.value is the float
                expr = value_token.value
                if hasattr(expr, "value"):
                    value = str(expr.value).rstrip("f")
                else:
                    value = str(expr).rstrip("f")
            else:
                return None
        else:
            return None

        return ({
            "datatype": datatype,
            "name": name,
            "value": value
        }, start_idx + 5)

    return None


def parse_function_from_tokens(tokens: list, start_idx: int, lines: list[str], line_numbers: dict) -> tuple[dict, int] | None:
    """Parse a function forward declaration from tokens.

    Grammar: function_forward_declaration : data_type IDENTIFIER '(' function_definition_params ')' ';'
    """
    # Find the function signature in tokens
    # Pattern: TYPE IDENTIFIER ( ... ) ;

    if start_idx + 5 >= len(tokens):
        return None

    # Check if this looks like a function declaration
    if (tokens[start_idx].type.endswith("_TYPE") or tokens[start_idx].type == "VOID_TYPE") and \
       tokens[start_idx + 1].type == "IDENTIFIER" and \
       tokens[start_idx + 2].type == "(":

        return_type_token = tokens[start_idx]
        name_token = tokens[start_idx + 1]

        return_type = token_type_to_datatype(return_type_token.type) or "void"
        # Extract name - could be Identifier object or string
        if hasattr(name_token.value, "name"):
            name = name_token.value.name
        else:
            name = str(name_token.value)

        # Find matching closing paren and semicolon
        paren_count = 1
        i = start_idx + 3
        param_tokens = []

        while i < len(tokens) and paren_count > 0:
            if tokens[i].type == "(":
                paren_count += 1
            elif tokens[i].type == ")":
                paren_count -= 1
                if paren_count == 0:
                    break
            else:
                param_tokens.append(tokens[i])
            i += 1

        if paren_count != 0:
            return None

        # Check for semicolon after closing paren
        if i + 1 >= len(tokens) or tokens[i + 1].type != ";":
            return None

        # Parse parameters
        params = parse_function_params(param_tokens)

        # Get function documentation from original lines
        func_line_num = line_numbers.get(id(tokens[start_idx]), 0)
        func_doc = extract_function_documentation_from_line(lines, func_line_num, name)

        return ({
            "return_type": return_type,
            "name": name,
            "params": params,
            "description": func_doc["description"],
            "raw": func_doc["raw"],
        }, i + 2)

    return None


def parse_function_params(param_tokens: list) -> list[dict]:
    """Parse function parameters from tokens.

    Grammar: function_definition_param : data_type IDENTIFIER ['=' expression]
    """
    params: list[dict[str, Any]] = []

    if not param_tokens:
        return params

    # Split by commas (but handle nested structures)
    param_groups: list[list[LexToken]] = []
    current_group: list[LexToken] = []
    paren_depth = 0
    bracket_depth = 0

    for token in param_tokens:
        if token.type == "(":
            paren_depth += 1
            current_group.append(token)
        elif token.type == ")":
            paren_depth -= 1
            current_group.append(token)
        elif token.type == "[":
            bracket_depth += 1
            current_group.append(token)
        elif token.type == "]":
            bracket_depth -= 1
            current_group.append(token)
        elif token.type == "," and paren_depth == 0 and bracket_depth == 0:
            if current_group:
                param_groups.append(current_group)
            current_group = []
        else:
            current_group.append(token)

    if current_group:
        param_groups.append(current_group)

    # Parse each parameter group
    for group in param_groups:
        if len(group) < 2:
            continue

        # Pattern: TYPE IDENTIFIER [= VALUE]
        if group[0].type.endswith("_TYPE") and group[1].type == "IDENTIFIER":
            param_type = token_type_to_datatype(group[0].type) or "int"
            # Extract parameter name - could be Identifier object or string
            name_token = group[1]
            if hasattr(name_token.value, "name"):
                param_name = name_token.value.name
            else:
                param_name = str(name_token.value)
            default_value = None

            # Check for default value
            if len(group) >= 4 and group[2].type == "=":
                default_token = group[3]
                # Special handling: negative number defaults like -1 or -1.0
                # Pattern: = MINUS INT_VALUE or = MINUS FLOAT_VALUE
                if (len(group) >= 5 and
                    default_token.type == "MINUS" and
                    group[4].type in ["INT_VALUE", "FLOAT_VALUE"]):
                    value_token = group[4]
                    if value_token.type == "INT_VALUE":
                        expr = value_token.value
                        raw_value = str(expr.value) if hasattr(expr, "value") else str(expr)
                        default_value = f"-{raw_value}"
                    elif value_token.type == "FLOAT_VALUE":
                        expr = value_token.value
                        if hasattr(expr, "value"):
                            raw_value = str(expr.value).rstrip("f")
                        else:
                            raw_value = str(expr).rstrip("f")
                        default_value = f"-{raw_value}"
                # Special handling: vector defaults like [0.0,0.0,0.0]
                # Pattern: [ FLOAT_VALUE , FLOAT_VALUE , FLOAT_VALUE ]
                elif param_type == "vector" and default_token.type == "[":
                    # Try to parse vector literal: [ FLOAT_VALUE , FLOAT_VALUE , FLOAT_VALUE ]
                    if (len(group) >= 10 and
                        group[3].type == "[" and
                        group[4].type == "FLOAT_VALUE" and
                        group[5].type == "," and
                        group[6].type == "FLOAT_VALUE" and
                        group[7].type == "," and
                        group[8].type == "FLOAT_VALUE" and
                        group[9].type == "]"):
                        # Extract the three float values
                        x_expr = group[4].value
                        y_expr = group[6].value
                        z_expr = group[8].value
                        x = x_expr.value if hasattr(x_expr, "value") else float(str(x_expr).rstrip("f"))
                        y = y_expr.value if hasattr(y_expr, "value") else float(str(y_expr).rstrip("f"))
                        z = z_expr.value if hasattr(z_expr, "value") else float(str(z_expr).rstrip("f"))
                        # Generate C# Vector3 representation
                        default_value = f"new Vector3({x}f, {y}f, {z}f)"
                    else:
                        # Vector literal not in expected format, set to None as fallback
                        default_value = None
                elif default_token.type == "OBJECTINVALID_VALUE":
                    # OBJECT_INVALID is a special constant - keep as identifier name, not value
                    default_value = "OBJECT_INVALID"
                elif default_token.type == "OBJECTSELF_VALUE":
                    # OBJECT_SELF is a special constant - keep as identifier name, not value
                    default_value = "OBJECT_SELF"
                elif default_token.type == "TRUE_VALUE":
                    default_value = "1"
                elif default_token.type == "FALSE_VALUE":
                    default_value = "0"
                elif default_token.type == "IDENTIFIER":
                    # Could be a constant like OBJECT_SELF, OBJECT_INVALID, TALKVOLUME_TALK, OBJECT_TYPE_INVALID, etc.
                    # For object/effect/event/etc types, keep as constant names (don't resolve to values)
                    # For int/float types with constant defaults, also keep names for readability
                    if hasattr(default_token.value, "name"):
                        constant_name = default_token.value.name
                    else:
                        constant_name = str(default_token.value)

                    # Always keep constant names - don't resolve to numeric values
                    # The C# compiler will handle constant resolution at runtime
                    default_value = constant_name
                elif default_token.type == "INT_VALUE":
                    # Extract value from IntExpression - this is a literal number
                    expr = default_token.value
                    if hasattr(expr, "value"):
                        default_value = str(expr.value)
                    else:
                        default_value = str(expr)
                elif default_token.type == "FLOAT_VALUE":
                    # Extract value from FloatExpression - this is a literal number
                    expr = default_token.value
                    if hasattr(expr, "value"):
                        default_value = f"{str(expr.value).rstrip('f')}f"
                    else:
                        default_value = f"{str(expr).rstrip('f')}f"
                elif default_token.type == "STRING_VALUE":
                    # Extract value from StringExpression - this is a literal string
                    expr = default_token.value
                    if hasattr(expr, "value"):
                        # expr.value is the actual string (without quotes)
                        # For C#, escape properly
                        str_value = expr.value
                        default_value = repr(str_value).replace("'", '"')  # Use double quotes for C#
                    else:
                        # Not an expression object, treat as string
                        str_val = str(expr)
                        default_value = repr(str_val).replace("'", '"')
                elif default_token.type == "INT_HEX_VALUE":
                    # Hex value - this is a literal hex number
                    hex_str = default_token.value
                    if isinstance(hex_str, str):
                        default_value = str(int(hex_str, 16))
                    else:
                        default_value = str(hex_str)
                elif default_token.type == "[":
                    # Vector or array default - should have been handled above for vector type
                    # This is a fallback for non-vector types with [ token
                    default_value = None
                # Try to extract value from expression object (fallback path)
                # Never use str() or repr() on expression objects - always extract .value
                elif hasattr(default_token, "value"):
                    expr = default_token.value
                    # Check if it's an expression object with a .value attribute
                    if hasattr(expr, "value"):
                        # It's an expression object - extract the actual value
                        try:
                            if isinstance(expr, StringExpression):
                                # For strings, wrap in quotes
                                default_value = f'"{expr.value}"'
                            elif isinstance(expr, IntExpression):
                                # For integers, convert to string
                                default_value = str(expr.value)
                            elif isinstance(expr, FloatExpression):
                                # For floats, convert to string with f suffix
                                default_value = f"{expr.value}f"
                            elif isinstance(expr, VectorExpression):
                                # For vectors, generate C# Vector3 representation
                                default_value = f"new Vector3({expr.x}f, {expr.y}f, {expr.z}f)"
                            else:
                                # Unknown expression type, try to get value
                                default_value = str(expr.value) if hasattr(expr, "value") else None
                        except Exception:
                            # Fallback if isinstance fails - still extract .value
                            default_value = str(expr.value) if hasattr(expr, "value") else None
                    # Not an expression object, but might be a primitive value
                    # Try to use it directly if it's a simple type
                    elif isinstance(expr, (int, float, str)):
                        if isinstance(expr, str):
                            default_value = f'"{expr}"'
                        elif isinstance(expr, float):
                            default_value = f"{expr}f"
                        else:
                            default_value = str(expr)
                    else:
                        # Unknown type, skip it
                        default_value = None
                else:
                    # No value attribute, can't extract default
                    default_value = None

            params.append({
                "type": param_type,
                "name": param_name,
                "default": default_value,
            })

    return params


def extract_function_documentation_from_line(lines: list[str], line_num: int, func_name: str) -> dict:
    """Extract function documentation by finding the function in the original lines."""
    # Find the function line
    func_line_idx = None
    for i, line in enumerate(lines):
        if re.search(rf"\b{re.escape(func_name)}\s*\(", line):
            func_line_idx = i
            break

    if func_line_idx is None:
        return {"description": "", "raw": ""}

    # Collect comment lines before function
    comments: list[str] = []
    i = func_line_idx - 1
    while i >= 0 and i >= func_line_idx - 50:
        line = lines[i].strip()
        if line.startswith("//"):
            comments.insert(0, lines[i].rstrip())
        elif line == "":
            pass
        else:
            break
        i -= 1

    # Get function signature line
    sig_line = lines[func_line_idx].strip()
    all_lines = comments + [sig_line]
    description = "\r\n".join(all_lines)
    raw = description

    return {"description": description, "raw": raw}


def preprocess_nss(content: str) -> str:
    """Preprocess NSS content to handle preprocessor directives and prepare for lexing."""
    lines = content.split("\n")
    processed_lines: list[str] = []

    for line in lines:
        # Skip preprocessor directives (they're not needed for constant/function extraction)
        if line.strip().startswith("#"):
            continue
        # Keep everything else as-is
        processed_lines.append(line)

    return "\n".join(processed_lines)


def parse_nss_file(nss_path: Path, game: Game) -> tuple[list[dict], list[dict]]:
    """Parse an NSS file using the NCS lexer and return (constants, functions)."""
    content = nss_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Preprocess to remove preprocessor directives
    processed_content = preprocess_nss(content)

    # Use lexer to tokenize
    lexer = NssLexer()
    lexer.lexer.input(processed_content)
    tokens: list[LexToken] = list(lexer.lexer)

    # Create line number mapping for tokens
    line_numbers: dict[int, int] = {}
    for token in tokens:
        if hasattr(token, "lineno"):
            line_numbers[id(token)] = token.lineno - 1  # Convert to 0-based index

    constants: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []

    # Parse constants and functions from tokens
    i = 0
    while i < len(tokens):
        # Try to parse as constant
        const_result = parse_constant_from_tokens(tokens, i, lines)
        if const_result:
            const_dict, next_idx = const_result
            constants.append(const_dict)
            i = next_idx
            continue

        # Try to parse as function
        func_result = parse_function_from_tokens(tokens, i, lines, line_numbers)
        if func_result:
            func_dict, next_idx = func_result
            functions.append(func_dict)
            i = next_idx
            continue

        i += 1

    return constants, functions


def csharp_type_from_nss(datatype: str) -> str:
    """Convert NSS type to C# DataType enum value."""
    type_map = {
        "int": "DataType.Int",
        "float": "DataType.Float",
        "string": "DataType.String",
        "void": "DataType.Void",
        "object": "DataType.Object",
        "vector": "DataType.Vector",
        "location": "DataType.Location",
        "effect": "DataType.Effect",
        "event": "DataType.Event",
        "talent": "DataType.Talent",
        "action": "DataType.Action",
    }
    return type_map.get(datatype.lower(), f"DataType.{datatype.capitalize()}")


def generate_constant_csharp(constant: dict) -> str:
    """Generate C# code for a constant."""
    datatype_cs = csharp_type_from_nss(constant["datatype"])
    name = constant["name"]
    value = constant["value"]

    if constant["datatype"] == "string":
        # Value is the raw string content
        # Use repr() to generate a proper C# string literal (with quotes)
        value_cs = repr(value).replace("'", '"')
    elif constant["datatype"] == "float":
        # Ensure float values have 'f' suffix
        try:
            float_val = float(value)
            value_cs = f"{float_val}f"
        except (ValueError, TypeError):
            value_cs = value
    else:
        value_cs = value

    return f'        new ScriptConstant({datatype_cs}, "{name}", {value_cs}),'


def resolve_constant_value(constant_name: str, constants: list[dict]) -> str | None:
    """Resolve a constant name to its value by looking it up in constants list."""
    for const in constants:
        if const["name"] == constant_name:
            # Return the actual value, handling negative numbers properly
            value = const["value"]
            # Ensure negative numbers are handled (they might be strings like "-1")
            return value
    # Special cases for built-in constants
    if constant_name == "OBJECT_SELF":
        return "OBJECT_SELF"
    if constant_name == "OBJECT_INVALID":
        return "OBJECT_INVALID"
    if constant_name == "OBJECT_TYPE_INVALID":
        return "OBJECT_TYPE_INVALID"
    return None


def generate_function_csharp(func: dict, constants: list[dict]) -> str:
    """Generate C# code for a function."""
    return_type_cs = csharp_type_from_nss(func["return_type"])
    name = func["name"]

    params_cs = []
    for param in func["params"]:
        param_type_cs = csharp_type_from_nss(param["type"])
        param_name = param["name"]

        if param["default"] is not None:
            default = param["default"]
            # Default values from parse_function_params are already correctly formatted
            # Just need to ensure proper quoting/formatting for C# output

            # If default is None after processing, use null
            if default is None:
                params_cs.append(f'new ScriptParam({param_type_cs}, "{param_name}", null)')
            else:
                # Format default value for C# code
                # If default is a string, check if it should be a string literal or C# code
                if isinstance(default, str):
                    # Check if it's a numeric value (integer or float)
                    # These should NOT be quoted in C# - they're code values
                    try:
                        # Try parsing as int first (including negative)
                        int(default)
                        # It's a valid integer literal, use without quotes
                        default_formatted = default
                    except ValueError:
                        try:
                            # Try parsing as float (including negative)
                            float(default.rstrip('f'))
                            # It's a valid float literal, use without quotes
                            default_formatted = default
                        except ValueError:
                            # Not a numeric value, check other cases
                            # Check if it's already a formatted string literal (starts/ends with quotes)
                            if (default.startswith('"') and default.endswith('"')) or (default.startswith("'") and default.endswith("'")):
                                # Already formatted, use as-is (convert single to double quotes)
                                if default.startswith("'") and default.endswith("'"):
                                    default_formatted = default.replace("'", '"')
                                else:
                                    default_formatted = default
                            # Check if it looks like C# code (function calls, constructors, etc.)
                            elif default.startswith("new Vector3("):
                                # It's C# code (Vector3 constructor), use as-is (don't quote it)
                                default_formatted = default
                            # Check if it's a constant name (identifiers, not literals)
                            # These should remain unquoted as C# constant references
                            else:
                                # It's a constant name or identifier - use without quotes
                                default_formatted = default
                else:
                    # Not a string, use directly
                    default_formatted = str(default)
                # Use the default value directly in C# code
                params_cs.append(f'new ScriptParam({param_type_cs}, "{param_name}", {default_formatted})')
        else:
            params_cs.append(f'new ScriptParam({param_type_cs}, "{param_name}", null)')

    params_str = ", ".join(params_cs) if params_cs else ""
    params_list = f"new List<ScriptParam>() {{ {params_str} }}" if params_str else "new List<ScriptParam>()"

    description = func["description"].replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
    raw = func["raw"].replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")

    return f"""        new ScriptFunction(
            {return_type_cs},
            "{name}",
            {params_list},
            "{description}",
            "{raw}",
        ),"""


def generate_scriptdefs_csharp(k1_constants: list[dict], k1_functions: list[dict],
                              k2_constants: list[dict], k2_functions: list[dict]) -> str:
    """Generate the complete ScriptDefs.cs file content."""
    header = """using System.Collections.Generic;
using CSharpKOTOR.Common;
using CSharpKOTOR.Common.Script;

namespace CSharpKOTOR.Common.Script
{

    /// <summary>
    /// NWScript constant and function definitions for KOTOR and TSL.
    /// Generated from k1_nwscript.nss and k2_nwscript.nss (k2 is the same as tsl) using generate_scriptdefs_csharp.py.
    /// Matching PyKotor implementation at Libraries/PyKotor/src/pykotor/common/scriptdefs.py
    /// </summary>
    public static class ScriptDefs
    {
        // Built-in object constants (not defined in NSS files but used as defaults)
        public const int OBJECT_SELF = 0;
        public const int OBJECT_INVALID = 1;

        /// <summary>
        /// KOTOR (Knights of the Old Republic) script constants.
        /// </summary>
        public static readonly List<ScriptConstant> KOTOR_CONSTANTS = new List<ScriptConstant>()
        {
"""

    kotor_constants_cs = ""
    for const in k1_constants:
        kotor_constants_cs += generate_constant_csharp(const) + "\n"
    kotor_constants_cs += "        }\n\n"

    tsl_constants_cs = """        /// <summary>
        /// TSL (The Sith Lords, also known as K2) script constants.
        /// </summary>
        public static readonly List<ScriptConstant> TSL_CONSTANTS = new List<ScriptConstant>()
        {
"""
    for const in k2_constants:
        tsl_constants_cs += generate_constant_csharp(const) + "\n"
    tsl_constants_cs += "        }\n\n"

    kotor_functions_cs = """        /// <summary>
        /// KOTOR (Knights of the Old Republic) script functions.
        /// </summary>
        public static readonly List<ScriptFunction> KOTOR_FUNCTIONS = new List<ScriptFunction>()
        {
"""
    for func in k1_functions:
        kotor_functions_cs += generate_function_csharp(func, k1_constants) + "\n"
    kotor_functions_cs += "        }\n\n"

    tsl_functions_cs = """        /// <summary>
        /// TSL (The Sith Lords, also known as K2) script functions.
        /// </summary>
        public static readonly List<ScriptFunction> TSL_FUNCTIONS = new List<ScriptFunction>()
        {
"""
    for func in k2_functions:
        tsl_functions_cs += generate_function_csharp(func, k2_constants) + "\n"
    tsl_functions_cs += "        }\n    }\n}"

    return header + kotor_constants_cs + tsl_constants_cs + kotor_functions_cs + tsl_functions_cs


def main():
    """Main entry point."""
    # Script is at vendor/PyKotor/scripts/, so parent.parent is vendor/PyKotor
    pykotor_root = Path(__file__).parent.parent
    k1_nss = pykotor_root / "vendor" / "NorthernLights" / "Scripts" / "k1_nwscript.nss"
    k2_nss = pykotor_root / "vendor" / "NorthernLights" / "Scripts" / "k2_nwscript.nss"

    # Output to HoloPatcher.NET root (parent of vendor)
    holopatcher_root = pykotor_root.parent.parent
    output_file = holopatcher_root / "src" / "CSharpKOTOR" / "Common" / "Script" / "ScriptDefs.cs"

    print(f"Parsing {k1_nss}...")
    k1_constants, k1_functions = parse_nss_file(k1_nss, Game.K1)
    print(f"  Found {len(k1_constants)} constants and {len(k1_functions)} functions")

    print(f"Parsing {k2_nss}...")
    k2_constants, k2_functions = parse_nss_file(k2_nss, Game.K2)
    print(f"  Found {len(k2_constants)} constants and {len(k2_functions)} functions")

    print(f"Generating {output_file}...")
    content = generate_scriptdefs_csharp(k1_constants, k1_functions, k2_constants, k2_functions)

    output_file.write_text(content, encoding="utf-8")
    print(f"Done! Generated {output_file}")


if __name__ == "__main__":
    main()

