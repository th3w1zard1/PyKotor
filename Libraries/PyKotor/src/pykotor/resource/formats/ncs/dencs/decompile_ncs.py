"""NCS decompilation functionality."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import io

    from pykotor.resource.formats.ncs.dencs.actions_data import ActionsData
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData
    from pykotor.resource.formats.ncs.dencs.utils.file_script_data import FileScriptData
    from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine

logger = logging.getLogger(__name__)


@dataclass
class DecompilationContext:
    """Context for NCS decompilation containing all analysis data."""

    file_data: FileScriptData
    node_data: NodeAnalysisData
    subroutine_data: SubroutineAnalysisData
    actions: ActionsData


class DecompilationError(Exception):
    """Base exception for NCS decompilation errors."""


class SubroutinePrototypingError(DecompilationError):
    """Raised when subroutine prototyping fails."""


@contextmanager
def _managed_decompilation_context(actions: ActionsData):
    """Context manager for decompilation resources."""
    # Import here to avoid circular imports
    from pykotor.resource.formats.ncs.dencs.utils.file_script_data import FileScriptData
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData

    file_data = FileScriptData()
    node_data = NodeAnalysisData()
    subroutine_data = SubroutineAnalysisData(node_data)

    context = DecompilationContext(
        file_data=file_data,
        node_data=node_data,
        subroutine_data=subroutine_data,
        actions=actions
    )

    try:
        yield context
    finally:
        # Clean up resources
        if context.node_data is not None:
            context.node_data.close()
        if context.subroutine_data is not None:
            context.subroutine_data.parse_done()


def decompile_ncs(file_path: str | io.BufferedIOBase, actions: ActionsData) -> str | None:
    """
    Decompile an NCS (compiled script) file to NSS (source script) format.

    This function orchestrates the complete decompilation process including:
    - Reading and parsing the NCS file
    - Converting to AST representation
    - Analyzing control flow and subroutines
    - Type inference and prototyping
    - Code generation

    Args:
        file_path: Path to the NCS file or a file-like object
        actions: Action data containing type information and configuration

    Returns:
        The decompiled NSS source code as a string, or None if decompilation fails

    Raises:
        DecompilationError: If decompilation fails due to structural issues
        Exception: For unexpected errors during processing
    """
    if actions is None:
        logger.error("Actions data is required for decompilation")
        return None

    try:
        with _managed_decompilation_context(actions) as context:
            ncs_data = _read_ncs_file(file_path)
            ast = _convert_to_ast(ncs_data)

            _initialize_analysis(context, ast)
            _flatten_subroutines(context)
            _process_global_variables(context)
            _perform_initial_prototyping(context)
            _perform_final_prototyping(context)
            _generate_code(context)

            return context.file_data.get_code()

    except DecompilationError:
        raise
    except Exception as e:
        logger.exception("Unexpected error during NCS decompilation")
        raise DecompilationError(f"Decompilation failed: {e}") from e


def _read_ncs_file(file_path: str | io.BufferedIOBase):
    """Read and parse the NCS file."""
    from pykotor.resource.formats.ncs.ncs_auto import read_ncs

    logger.debug("Reading NCS file: %s", file_path)
    return read_ncs(file_path)


def _convert_to_ast(ncs_data):
    """Convert NCS instructions to AST representation."""
    from pykotor.resource.formats.ncs.dencs.utils.ncs_to_ast_converter import convert_ncs_to_ast

    logger.debug("Converting NCS to AST")
    return convert_ncs_to_ast(ncs_data)


def _initialize_analysis(context: DecompilationContext, ast):
    """Initialize analysis data structures and perform initial AST processing."""
    from pykotor.resource.formats.ncs.dencs.utils.set_positions import SetPositions
    from pykotor.resource.formats.ncs.dencs.utils.set_destinations import SetDestinations
    from pykotor.resource.formats.ncs.dencs.utils.set_dead_code import SetDeadCode

    logger.debug("Initializing analysis data structures")

    # Set node positions
    ast.apply(SetPositions(context.node_data))

    # Set destinations and analyze control flow
    destinations = SetDestinations(ast, context.node_data, context.subroutine_data)
    ast.apply(destinations)

    # Mark dead code
    ast.apply(SetDeadCode(context.node_data, context.subroutine_data, destinations.get_origins()))
    destinations.done()

    # Split subroutines from main AST
    context.subroutine_data.split_off_subroutines(ast)


def _flatten_subroutines(context: DecompilationContext):
    """Flatten subroutine structures for analysis."""
    from pykotor.resource.formats.ncs.dencs.utils.flatten_sub import FlattenSub

    logger.debug("Flattening subroutine structures")

    main_sub = context.subroutine_data.get_main_sub()
    if main_sub is None:
        raise DecompilationError("Main subroutine not found")

    flattener = FlattenSub(main_sub, context.node_data)
    main_sub.apply(flattener)

    # Process all subroutines
    subroutines = context.subroutine_data.get_subroutines()
    while subroutines.has_next():
        sub: ASubroutine = subroutines.next()
        flattener.set_sub(sub)
        sub.apply(flattener)

    flattener.done()


def _process_global_variables(context: DecompilationContext):
    """Process global variable declarations and initialization."""
    from pykotor.resource.formats.ncs.dencs.do_global_vars import DoGlobalVars
    from pykotor.resource.formats.ncs.dencs.scriptutils.cleanup_pass import CleanupPass

    logger.debug("Processing global variables")

    globals_sub = context.subroutine_data.get_globals_sub()
    if globals_sub is None:
        return

    global_vars = DoGlobalVars(context.node_data, context.subroutine_data)
    globals_sub.apply(global_vars)

    cleanup = CleanupPass(
        global_vars.get_script_root(),
        context.node_data,
        context.subroutine_data,
        global_vars.get_state()
    )
    cleanup.apply()

    context.subroutine_data.set_global_stack(global_vars.get_stack())
    context.subroutine_data.global_state(global_vars.get_state())

    cleanup.done()


def _perform_initial_prototyping(context: DecompilationContext):
    """Perform initial subroutine prototyping passes."""
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_path_finder import SubroutinePathFinder
    from pykotor.resource.formats.ncs.dencs.do_types import DoTypes

    logger.debug("Performing initial subroutine prototyping")

    for pass_num in range(1, 6):
        all_done = True
        one_done = False

        subroutines = context.subroutine_data.get_subroutines()
        while subroutines.has_next():
            sub = subroutines.next()

            if context.subroutine_data.is_prototyped(context.node_data.get_pos(sub), True):
                continue

            path_finder = SubroutinePathFinder(
                context.subroutine_data.get_state(sub),
                context.node_data,
                context.subroutine_data,
                pass_num
            )
            sub.apply(path_finder)

            if context.subroutine_data.is_being_prototyped(context.node_data.get_pos(sub)):
                typer = DoTypes(
                    context.subroutine_data.get_state(sub),
                    context.node_data,
                    context.subroutine_data,
                    context.actions,
                    True
                )
                sub.apply(typer)
                typer.done()
                one_done = True
            else:
                all_done = False

        if all_done:
            break
        if not one_done and pass_num >= 5:
            break

    if not all_done:
        context.subroutine_data.print_states()
        raise SubroutinePrototypingError("Unable to complete initial prototyping of all subroutines")


def _perform_final_prototyping(context: DecompilationContext):
    """Perform final subroutine prototyping and type inference."""
    from pykotor.resource.formats.ncs.dencs.do_types import DoTypes

    logger.debug("Performing final subroutine prototyping")

    main_sub = context.subroutine_data.get_main_sub()
    if main_sub is None:
        raise DecompilationError("Main subroutine not found during final prototyping")

    # Initial main subroutine typing
    main_state = context.subroutine_data.get_state(main_sub)
    if main_state is None:
        raise DecompilationError("Main subroutine state not found")

    typer = DoTypes(
        main_state,
        context.node_data,
        context.subroutine_data,
        context.actions,
        False
    )
    main_sub.apply(typer)
    typer.assert_stack()
    typer.done()

    # Iterative refinement passes
    max_iterations = 1000
    for iteration in range(max_iterations):
        all_done = context.subroutine_data.count_subs_done() == context.subroutine_data.num_subs()

        if all_done:
            break

        # Type all subroutines
        subroutines = context.subroutine_data.get_subroutines()
        while subroutines.has_next():
            sub = subroutines.next()
            sub_state = context.subroutine_data.get_state(sub)
            if sub_state is None:
                continue  # Skip subroutines without state

            typer = DoTypes(
                sub_state,
                context.node_data,
                context.subroutine_data,
                context.actions,
                False
            )
            sub.apply(typer)
            typer.done()

        # Type main subroutine
        typer = DoTypes(
            main_state,
            context.node_data,
            context.subroutine_data,
            context.actions,
            False
        )
        main_sub.apply(typer)
        typer.done()

    if not all_done:
        logger.error("Unable to complete final prototyping of all subroutines")
        return

    context.node_data.clear_proto_data()


def _generate_code(context: DecompilationContext):
    """Generate the final decompiled code."""
    from pykotor.resource.formats.ncs.dencs.main_pass import MainPass
    from pykotor.resource.formats.ncs.dencs.scriptutils.cleanup_pass import CleanupPass
    from pykotor.resource.formats.ncs.dencs.utils.destroy_parse_tree import DestroyParseTree

    logger.debug("Generating final decompiled code")

    # Process all subroutines
    subroutines = context.subroutine_data.get_subroutines()
    while subroutines.has_next():
        sub = subroutines.next()
        sub_state = context.subroutine_data.get_state(sub)
        if sub_state is None:
            continue  # Skip subroutines without state

        main_pass = MainPass(
            sub_state,
            context.node_data,
            context.subroutine_data,
            context.actions
        )
        sub.apply(main_pass)

        cleanup = CleanupPass(
            main_pass.get_script_root(),
            context.node_data,
            context.subroutine_data,
            main_pass.get_state()
        )
        cleanup.apply()

        context.file_data.add_sub(main_pass.get_state())
        main_pass.done()
        cleanup.done()

    # Process main subroutine
    main_sub = context.subroutine_data.get_main_sub()
    if main_sub is None:
        raise DecompilationError("Main subroutine not found during code generation")

    main_state = context.subroutine_data.get_state(main_sub)
    if main_state is None:
        raise DecompilationError("Main subroutine state not found during code generation")

    main_pass = MainPass(
        main_state,
        context.node_data,
        context.subroutine_data,
        context.actions
    )
    main_sub.apply(main_pass)
    main_pass.assert_stack()

    cleanup = CleanupPass(
        main_pass.get_script_root(),
        context.node_data,
        context.subroutine_data,
        main_pass.get_state()
    )
    cleanup.apply()

    main_pass.get_state().is_main(True)
    context.file_data.add_sub(main_pass.get_state())
    main_pass.done()
    cleanup.done()

    # Set subroutine data
    context.file_data.subdata(context.subroutine_data)

    # Process global variables if present
    # Note: Global variable processing is handled during the main pass
    # and cleanup pass, so no additional processing needed here

    # Clean up parse trees
    destroyer = DestroyParseTree()
    subroutines = context.subroutine_data.get_subroutines()
    while subroutines.has_next():
        subroutines.next().apply(destroyer)
    main_sub.apply(destroyer)

    # Generate final code
    context.file_data.generate_code()
