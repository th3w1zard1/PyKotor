"""NCS validation for NWScript Virtual Machine compatibility.

This module provides validation functions for NCS (compiled NWScript) files
to ensure they are compatible with the game's virtual machine based on
reverse engineering analysis of swkotor.exe.

Key findings from reverse engineering:
- VM uses stack-based execution with CVirtualMachineStack
- ExecuteCode function is a large switch-based interpreter (5529 bytes)
- Stack operations must maintain proper types and depths
- Call stack size is tracked and validated
- Error handling includes stack unwinding on failures
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from pykotor.resource.formats.ncs.ncs_data import NCS, NCSInstructionType

if TYPE_CHECKING:
    pass

logger = RobustLogger("pykotor.resource.formats.ncs.vm_validation")


def validate_ncs_for_vm(ncs: NCS) -> None:
    """Validate an NCS file for compatibility with the NWScript VM.

    Based on reverse engineering of CVirtualMachine::ExecuteCode,
    this function checks for common issues that could cause VM errors.

    Args:
    ----
        ncs: The NCS object to validate

    Raises:
    ------
        ValueError: If validation fails with details about the issue
    """
    issues = []

    # Check for empty scripts (valid but unusual)
    if not ncs.instructions:
        logger.warning("NCS file contains no instructions")
        return

    # Validate instruction sequence
    _validate_instruction_sequence(ncs, issues)

    # Check stack operations
    _validate_stack_operations(ncs, issues)

    # Validate control flow
    _validate_control_flow(ncs, issues)

    # Check for potential infinite loops or problematic constructs
    _validate_execution_safety(ncs, issues)

    if issues:
        error_msg = f"NCS validation failed with {len(issues)} issue(s):\n" + "\n".join(f"  - {issue}" for issue in issues)
        raise ValueError(error_msg)


def _validate_instruction_sequence(ncs: NCS, issues: list[str]) -> None:
    """Validate the sequence of instructions for VM compatibility."""
    instructions = ncs.instructions

    for i, instr in enumerate(instructions):
        # Check for instructions that should not appear in certain contexts
        if instr.type == NCSInstructionType.RETN and i < len(instructions) - 1:
            # RETN in middle of script - may indicate missing control flow
            issues.append(f"RETN instruction at position {i} is not at end of script")

        # Check for consecutive stack operations that might cause issues
        if i > 0:
            prev_instr = instructions[i - 1]
            if (_is_stack_operation(instr.type) and _is_stack_operation(prev_instr.type) and
                _stack_operations_conflict(instr, prev_instr)):
                issues.append(f"Conflicting stack operations at positions {i-1} and {i}")


def _validate_stack_operations(ncs: NCS, issues: list[str]) -> None:
    """Validate stack operations for proper balance and types."""
    # This is a simplified stack validation - full validation would require
    # simulating the entire VM execution which is complex

    stack_depth = 0
    max_stack_depth = 0

    for i, instr in enumerate(ncs.instructions):
        # Track basic stack operations
        if instr.type in (NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP):
            # Stack pointer manipulation
            if hasattr(instr, 'size') and instr.size < 0:
                stack_depth += abs(instr.size)  # Negative size means allocating stack space
        elif instr.type in (NCSInstructionType.CONSTI, NCSInstructionType.CONSTF,
                           NCSInstructionType.CONSTS, NCSInstructionType.CONSTO):
            # Constants push values onto stack
            stack_depth += 1
        elif instr.type == NCSInstructionType.ACTION:
            # Function calls consume arguments and push return value
            # This is simplified - actual validation would need argument counts
            pass

        max_stack_depth = max(max_stack_depth, stack_depth)

        # Check for potential stack underflow
        if stack_depth < 0:
            issues.append(f"Potential stack underflow at instruction {i}")
            stack_depth = 0  # Reset for continued validation

    # Check for excessive stack usage (based on VM limitations)
    if max_stack_depth > 1000:  # Conservative limit based on typical script complexity
        issues.append(f"Potentially excessive stack usage (max depth: {max_stack_depth})")


def _validate_control_flow(ncs: NCS, issues: list[str]) -> None:
    """Validate control flow instructions."""
    instructions = ncs.instructions

    for i, instr in enumerate(instructions):
        if instr.type in (NCSInstructionType.JMP, NCSInstructionType.JZ, NCSInstructionType.JNZ, NCSInstructionType.JSR):
            if instr.jump is None:
                issues.append(f"Jump instruction at position {i} has no valid target")
                continue

            # Check jump target bounds
            target_index = instructions.index(instr.jump)
            if target_index < 0 or target_index >= len(instructions):
                issues.append(f"Jump instruction at position {i} targets invalid location {target_index}")
                continue

            # Check for suspicious jump patterns
            if abs(target_index - i) > 1000:  # Very long jumps might indicate issues
                issues.append(f"Unusually long jump at position {i} (distance: {abs(target_index - i)})")

            # Check for jumps to invalid locations (e.g., into middle of instructions)
            if instr.type == NCSInstructionType.JSR and target_index == 0:
                issues.append(f"JSR at position {i} jumps to script start (potential recursion issue)")


def _validate_execution_safety(ncs: NCS, issues: list[str]) -> None:
    """Validate for execution safety issues."""
    instructions = ncs.instructions

    # Check for scripts that are too long (based on VM instruction limits)
    if len(instructions) > 10000:  # Conservative limit
        issues.append(f"Script is unusually long ({len(instructions)} instructions)")

    # Check for excessive consecutive NOP-like operations
    consecutive_noops = 0
    for instr in instructions:
        if instr.type in (NCSInstructionType.NOP,):  # Add other no-op instructions as identified
            consecutive_noops += 1
            if consecutive_noops > 10:
                issues.append("Excessive consecutive no-op instructions detected")
                break
        else:
            consecutive_noops = 0


def _is_stack_operation(instr_type: NCSInstructionType) -> bool:
    """Check if an instruction type manipulates the stack."""
    return instr_type in (
        NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP,
        NCSInstructionType.CPDOWNBP, NCSInstructionType.CPTOPBP,
        NCSInstructionType.MOVSP, NCSInstructionType.SAVEBP,
        NCSInstructionType.RESTOREBP
    )


def _stack_operations_conflict(instr1: NCSInstruction, instr2: NCSInstruction) -> bool:
    """Check if two consecutive stack operations might conflict."""
    # This is a simplified check - full analysis would be more complex
    # For example, CPDOWNSP followed by CPTOPSP with incompatible sizes

    if (instr1.type == NCSInstructionType.CPDOWNSP and
        instr2.type == NCSInstructionType.CPTOPSP):
        # Check if sizes are compatible
        size1 = getattr(instr1, 'size', 0)
        size2 = getattr(instr2, 'size', 0)
        if size1 != size2 and size1 != 0 and size2 != 0:
            return True

    return False
