from __future__ import annotations

import inspect as ___inspect___
import sys as ___sys___


def assert_with_variable_trace(___condition___: bool, ___message___: str = "Assertion Failed"):
    if ___condition___:
        return
    # Capture the current stack trace
    ___frames___: list[___inspect___.FrameInfo] = ___inspect___.getouterframes(___inspect___.currentframe())

    # Get the line of code calling assert_with_variable_trace
    ___calling_frame_record___ = ___frames___[1]
    (
        ___unused_frame_type___,
        ___filename_errorhandler___,
        ___line_no___,
        ___unused_str_thing___,
        ___code_context___,
        ___unused_frame_type___,
    ) = ___calling_frame_record___
    ___line_of_code___ = ___code_context___[0].strip() if ___code_context___ else "Unknown condition"

    # Get default module attributes to filter out built-ins
    ___default_attrs___: set[str] = set(dir(___sys___.modules["builtins"]))

    # Construct a detailed message with variables from all stack frames
    ___detailed_message___: list[str] = [
        f"{___message___}: Expected condition '{___line_of_code___}' failed at {___filename_errorhandler___}:{___line_no___}.",
        "Stack Trace Variables:",
    ]
    for ___frame_info___ in ___frames___:
        (
            ___frame___,
            ___filename_errorhandler___,
            ___line_no___,
            ___function___,
            ___code_context___,
            ___unused_index___,
        ) = ___frame_info___
        ___detailed_message___.append(f"\nFunction '{___function___}' at {___filename_errorhandler___}:{___line_no___}:")

        # Filter out built-in and imported names
        ___detailed_message___.extend(
            f"  {var} = {val}"
            for var, val in ___frame___.f_locals.items()
            if var not in ___default_attrs___
            and var
            not in [
                "___detailed_message___",
                "___default_attrs___",
                "___line_of_code___",
                "___calling_frame_record___",
                "___code_context___",
                "___frames___",
                "___filename_errorhandler___",
                "___line_no___",
                "___function___",
                "___frame_info___",
                "__builtins__",
                "___inspect___",
                "___sys___",
                "assert_with_variable_trace",
                "___condition___",
                "___frame___",
                "___message___",
                "___value___",
                "___unused_str_thing___",
                "___unused_index___",
                "___unused_frame_type___",
            ]
        )
    full_message: str = "\n".join(___detailed_message___)

    # Raise an exception with the detailed message
    raise AssertionError(full_message)
