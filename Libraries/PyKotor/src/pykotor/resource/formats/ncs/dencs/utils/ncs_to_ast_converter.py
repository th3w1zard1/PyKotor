"""NCS to AST Converter - Comprehensive instruction conversion.

This module provides comprehensive conversion of NCS (NWScript Compiled Script) bytecode
instructions directly to DeNCS AST (Abstract Syntax Tree) format, bypassing the traditional
Decoder -> Lexer -> Parser chain for improved performance and accuracy.

The converter handles all NCS instruction types comprehensively:
- Constants: CONSTI, CONSTF, CONSTS, CONSTO
- Control flow: JMP, JSR, JZ, JNZ, RETN
- Stack operations: CPDOWNSP, CPTOPSP, CPDOWNBP, CPTOPBP, MOVSP, INCxSP, DECxSP, INCxBP, DECxBP
- RSADD variants: RSADDI, RSADDF, RSADDS, RSADDO, RSADDEFF, RSADDEVT, RSADDLOC, RSADDTAL
- Function calls: ACTION
- Stack management: SAVEBP, RESTOREBP, STORE_STATE, DESTRUCT
- Arithmetic: ADDxx, SUBxx, MULxx, DIVxx, MODxx, NEGx
- Comparison: EQUALxx, NEQUALxx, GTxx, GEQxx, LTxx, LEQxx
- Logical: LOGANDxx, LOGORxx, NOTx
- Bitwise: BOOLANDxx, INCORxx, EXCORxx, SHLEFTxx, SHRIGHTxx, USHRIGHTxx, COMPx
- No-ops: NOP, NOP2, RESERVED (typically skipped during conversion)

References:
----------
    vendor/reone/src/libs/script/format/ncsreader.cpp - NCS instruction reading
    vendor/xoreos/src/aurora/nwscript/ncsfile.cpp - NCS instruction execution
    DeNCS - Original NCS decompiler implementation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.start import Start  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCS, NCSInstruction

def convert_ncs_to_ast(ncs: NCS) -> Start:
    """Convert NCSInstruction[] to DeNCS AST format.

    This replaces the Decoder -> Lexer -> Parser chain by directly
    converting NCSInstruction objects to AST nodes.
    """
    from pykotor.resource.formats.ncs.dencs.node.a_program import AProgram  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.eof import EOF  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.start import Start  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]
    
    program = AProgram()

    instructions = ncs.instructions
    if not instructions:
        return Start(program, EOF())

    # Find subroutines (JSR targets)
    subroutine_starts = set()
    for i, inst in enumerate(instructions):
        if inst.ins_type == NCSInstructionType.JSR and inst.jump is not None:
            try:
                jump_idx = ncs.get_instruction_index(inst.jump)
                if jump_idx >= 0:
                    subroutine_starts.add(jump_idx)
            except (ValueError, AttributeError):
                pass

    # The main program starts at instruction 0
    # Create main subroutine (all code until first JSR target or end)
    main_end = len(instructions)
    if subroutine_starts:
        main_end = min(subroutine_starts)

    main_sub = _convert_instruction_range_to_subroutine(instructions, 0, main_end, 0)
    if main_sub:
        program.add_subroutine(main_sub)

    # Convert each subroutine
    for sub_start in sorted(subroutine_starts):
        # Find end of this subroutine (next subroutine or RETN)
        sub_end = len(instructions)
        for i in range(sub_start + 1, len(instructions)):
            if i in subroutine_starts:
                sub_end = i
                break
            if instructions[i].ins_type == NCSInstructionType.RETN:
                sub_end = i + 1
                break

        sub = _convert_instruction_range_to_subroutine(instructions, sub_start, sub_end, len(program.get_subroutine()))
        if sub:
            program.add_subroutine(sub)

    from pykotor.resource.formats.ncs.dencs.node.eof import EOF  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.start import Start  # pyright: ignore[reportMissingImports]
    return Start(program, EOF())

def _convert_instruction_range_to_subroutine(
    instructions: list[NCSInstruction],
    start_idx: int,
    end_idx: int,
    sub_id: int
):
    """Convert a range of instructions to an ASubroutine."""
    from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]

    if start_idx >= end_idx or start_idx >= len(instructions):
        return None

    sub = ASubroutine()
    sub.set_id(sub_id)

    cmd_block = ACommandBlock()

    for i in range(start_idx, min(end_idx, len(instructions))):
        inst = instructions[i]
        cmd = _convert_instruction_to_cmd(inst, i, instructions)
        if cmd:
            cmd_block.add_cmd(cmd)

    sub.set_command_block(cmd_block)

    # Find return
    for i in range(start_idx, min(end_idx, len(instructions))):
        if instructions[i].ins_type == NCSInstructionType.RETN:
            ret = _convert_retn(instructions[i], i)
            if ret:
                sub.set_return(ret)
            break

    return sub

def _convert_instruction_to_cmd(inst: NCSInstruction, pos: int, instructions: list[NCSInstruction] | None = None):
    """Convert a single NCSInstruction to an AST command node.
    
    Handles all NCS instruction types comprehensively:
    - Constants: CONSTI, CONSTF, CONSTS, CONSTO
    - Control flow: JMP, JSR, JZ, JNZ, RETN
    - Stack operations: CPDOWNSP, CPTOPSP, CPDOWNBP, CPTOPBP, MOVSP, INCxSP, DECxSP, INCxBP, DECxBP
    - RSADD variants: RSADDI, RSADDF, RSADDS, RSADDO, RSADDEFF, RSADDEVT, RSADDLOC, RSADDTAL
    - Function calls: ACTION
    - Stack management: SAVEBP, RESTOREBP, STORE_STATE, DESTRUCT
    - Arithmetic: ADDxx, SUBxx, MULxx, DIVxx, MODxx, NEGx
    - Comparison: EQUALxx, NEQUALxx, GTxx, GEQxx, LTxx, LEQxx
    - Logical: LOGANDxx, LOGORxx, NOTx
    - Bitwise: BOOLANDxx, INCORxx, EXCORxx, SHLEFTxx, SHRIGHTxx, USHRIGHTxx, COMPx
    - No-ops: NOP, NOP2, RESERVED
    """
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type

    # Constants
    if ins_type in {NCSInstructionType.CONSTI, NCSInstructionType.CONSTF, NCSInstructionType.CONSTS, NCSInstructionType.CONSTO}:
        return _convert_const_cmd(inst, pos)
    
    # Function calls
    elif ins_type == NCSInstructionType.ACTION:
        return _convert_action_cmd(inst, pos)
    
    # Control flow - unconditional jumps
    elif ins_type in {NCSInstructionType.JMP, NCSInstructionType.JSR}:
        return _convert_jump_cmd(inst, pos, instructions)
    
    # Control flow - conditional jumps
    elif ins_type in {NCSInstructionType.JZ, NCSInstructionType.JNZ}:
        return _convert_conditional_jump_cmd(inst, pos, instructions)
    
    # Control flow - return
    elif ins_type == NCSInstructionType.RETN:
        return _convert_retn_cmd(inst, pos)
    
    # Stack copy operations - stack pointer
    elif ins_type in {NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP}:
        return _convert_copy_sp_cmd(inst, pos)
    
    # Stack copy operations - base pointer
    elif ins_type in {NCSInstructionType.CPDOWNBP, NCSInstructionType.CPTOPBP}:
        return _convert_copy_bp_cmd(inst, pos)
    
    # Stack move operations
    elif ins_type == NCSInstructionType.MOVSP:
        return _convert_movesp_cmd(inst, pos)
    
    # Stack increment/decrement operations
    elif ins_type in {NCSInstructionType.INCxSP, NCSInstructionType.DECxSP, NCSInstructionType.INCxBP, NCSInstructionType.DECxBP}:
        return _convert_stack_op_cmd(inst, pos)
    
    # RSADD variants (all types)
    elif ins_type in {
        NCSInstructionType.RSADDI, NCSInstructionType.RSADDF, NCSInstructionType.RSADDS, NCSInstructionType.RSADDO,
        NCSInstructionType.RSADDEFF, NCSInstructionType.RSADDEVT, NCSInstructionType.RSADDLOC, NCSInstructionType.RSADDTAL
    }:
        return _convert_rsadd_cmd(inst, pos)
    
    # Stack management
    elif ins_type == NCSInstructionType.DESTRUCT:
        return _convert_destruct_cmd(inst, pos)
    elif ins_type in {NCSInstructionType.SAVEBP, NCSInstructionType.RESTOREBP}:
        return _convert_bp_cmd(inst, pos)
    elif ins_type == NCSInstructionType.STORE_STATE:
        return _convert_store_state_cmd(inst, pos)
    
    # No-operation instructions (NOP, NOP2, RESERVED)
    elif ins_type in {NCSInstructionType.NOP, NCSInstructionType.NOP2, NCSInstructionType.RESERVED, NCSInstructionType.RESERVED_01}:
        # NOP instructions are typically removed during optimization, but we convert them for completeness
        # They don't produce any meaningful AST nodes, so we return None (they'll be skipped)
        return None
    
    # Unary operations (NEG, NOT, COMP)
    elif inst.ins_type in {NCSInstructionType.NEGI, NCSInstructionType.NEGF, NCSInstructionType.NOTI, NCSInstructionType.COMPI}:
        return _convert_unary_cmd(inst, pos)
    
    # Binary operations (arithmetic, comparison, bitwise)
    elif inst.is_arithmetic() or inst.is_comparison() or inst.is_bitwise():
        return _convert_binary_cmd(inst, pos)
    
    # Logical operations (LOGANDII, LOGORII, and bitwise logical ops)
    elif inst.is_logical() or inst.ins_type in {
        NCSInstructionType.BOOLANDII, NCSInstructionType.INCORII, NCSInstructionType.EXCORII
    }:
        return _convert_logii_cmd(inst, pos)
    
    # Unknown instruction type - log warning but don't crash
    # This allows the converter to continue processing other instructions
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Unknown instruction type at position {pos}: {ins_type.name} (value: {ins_type.value if hasattr(ins_type, 'value') else 'N/A'})")
    return None

def _convert_const_cmd(inst: NCSInstruction, pos: int):
    """Convert CONST instruction to AConstCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_const_cmd import AConstCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_const_command import AConstCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_float_constant import AFloatConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_int_constant import AIntConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_string_constant import AStringConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_const import TConst  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_float_constant import TFloatConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_string_literal import TStringLiteral  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    const_cmd = AConstCmd()
    const_command = AConstCommand()

    const_command.set_const(TConst(pos, 0))
    const_command.set_pos(TIntegerConstant(str(pos), pos, 0))

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    const_command.set_type(TIntegerConstant(str(type_val), pos, 0))

    if inst.args:
        if ins_type == NCSInstructionType.CONSTI:
            int_val = inst.args[0] if len(inst.args) > 0 else 0
            const_constant = AIntConstant()
            const_constant.set_integer_constant(TIntegerConstant(str(int_val), pos, 0))
            const_command.set_constant(const_constant)
        elif ins_type == NCSInstructionType.CONSTF:
            float_val = inst.args[0] if len(inst.args) > 0 else 0.0
            const_constant = AFloatConstant()
            const_constant.set_float_constant(TFloatConstant(str(float_val), pos, 0))
            const_command.set_constant(const_constant)
        elif ins_type == NCSInstructionType.CONSTS:
            str_val = inst.args[0] if len(inst.args) > 0 else ""
            const_constant = AStringConstant()
            const_constant.set_string_literal(TStringLiteral(f'"{str_val}"', pos, 0))
            const_command.set_constant(const_constant)
        elif ins_type == NCSInstructionType.CONSTO:
            obj_val = inst.args[0] if len(inst.args) > 0 else 0
            const_constant = AIntConstant()
            const_constant.set_integer_constant(TIntegerConstant(str(obj_val), pos, 0))
            const_command.set_constant(const_constant)

    const_command.set_semi(TSemi(pos, 0))
    const_cmd.set_const_command(const_command)

    return const_cmd

def _convert_action_cmd(inst: NCSInstruction, pos: int):
    """Convert ACTION instruction to AActionCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_action_cmd import AActionCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_action import TAction  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

    action_cmd = AActionCmd()
    action_command = AActionCommand()

    action_command.set_action(TAction(pos, 0))
    action_command.set_pos(TIntegerConstant(str(pos), pos, 0))

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    action_command.set_type(TIntegerConstant(str(type_val), pos, 0))

    # ACTION args: [routine_id (uint16), arg_count (uint8)]
    id_val = 0
    arg_count_val = 0
    if inst.args and len(inst.args) >= 1:
        id_val = inst.args[0] if len(inst.args) > 0 else 0
        arg_count_val = inst.args[1] if len(inst.args) > 1 else 0

    action_command.set_id(TIntegerConstant(str(id_val), pos, 0))
    action_command.set_arg_count(TIntegerConstant(str(arg_count_val), pos, 0))
    action_command.set_semi(TSemi(pos, 0))

    action_cmd.set_action_command(action_command)

    return action_cmd

def _convert_jump_cmd(inst: NCSInstruction, pos: int, instructions: list[NCSInstruction] | None = None):
    """Convert JMP/JSR/JZ/JNZ instruction to appropriate cmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_jump_cmd import AJumpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_sub_cmd import AJumpSubCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_jmp import TJmp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_jsr import TJsr  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0

    offset = 0
    if inst.jump is not None and instructions is not None:
        try:
            jump_idx = instructions.index(inst.jump)
            offset = jump_idx - pos
        except ValueError:
            offset = 0

    if ins_type == NCSInstructionType.JSR:
        jsr_cmd = AJumpSubCmd()
        jsr_to_sub = AJumpToSubroutine()

        jsr_to_sub.set_jsr(TJsr(pos, 0))
        jsr_to_sub.set_pos(TIntegerConstant(str(pos), pos, 0))
        jsr_to_sub.set_type(TIntegerConstant(str(type_val), pos, 0))
        jsr_to_sub.set_offset(TIntegerConstant(str(offset), pos, 0))
        jsr_to_sub.set_semi(TSemi(pos, 0))

        jsr_cmd.set_jump_to_subroutine(jsr_to_sub)
        return jsr_cmd
    else:
        jump_cmd = AJumpCmd()
        jump_command = AJumpCommand()

        jump_command.set_jmp(TJmp(pos, 0))
        jump_command.set_pos(TIntegerConstant(str(pos), pos, 0))
        jump_command.set_type(TIntegerConstant(str(type_val), pos, 0))
        jump_command.set_offset(TIntegerConstant(str(offset), pos, 0))
        jump_command.set_semi(TSemi(pos, 0))

        jump_cmd.set_jump_command(jump_command)
        return jump_cmd

def _convert_conditional_jump_cmd(inst: NCSInstruction, pos: int, instructions: list[NCSInstruction] | None = None):
    """Convert JZ/JNZ instruction to ACondJumpCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_cond_jump_cmd import ACondJumpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_nonzero_jump_if import ANonzeroJumpIf  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_zero_jump_if import AZeroJumpIf  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_jnz import TJnz  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_jz import TJz  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0

    offset = 0
    if inst.jump is not None and instructions is not None:
        try:
            jump_idx = instructions.index(inst.jump)
            offset = jump_idx - pos
        except ValueError:
            offset = 0

    cond_jump_cmd = ACondJumpCmd()
    cond_jump_command = AConditionalJumpCommand()

    if ins_type == NCSInstructionType.JZ:
        zero_jump_if = AZeroJumpIf()
        zero_jump_if.set_jz(TJz(pos, 0))
        cond_jump_command.set_jump_if(zero_jump_if)
    else:  # JNZ
        nonzero_jump_if = ANonzeroJumpIf()
        nonzero_jump_if.set_jnz(TJnz(pos, 0))
        cond_jump_command.set_jump_if(nonzero_jump_if)

    cond_jump_command.set_pos(TIntegerConstant(str(pos), pos, 0))
    cond_jump_command.set_type(TIntegerConstant(str(type_val), pos, 0))
    cond_jump_command.set_offset(TIntegerConstant(str(offset), pos, 0))
    cond_jump_command.set_semi(TSemi(pos, 0))

    cond_jump_cmd.set_conditional_jump_command(cond_jump_command)

    return cond_jump_cmd

def _convert_retn(inst: NCSInstruction, pos: int):
    """Convert RETN instruction to AReturn (for subroutine return)."""
    from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_retn import TRetn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

    ret = AReturn()
    ret.set_retn(TRetn(pos, 0))
    ret.set_pos(TIntegerConstant(str(pos), pos, 0))

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    ret.set_type(TIntegerConstant(str(type_val), pos, 0))
    ret.set_semi(TSemi(pos, 0))

    return ret

def _convert_retn_cmd(inst: NCSInstruction, pos: int):
    """Convert RETN instruction to AReturnCmd (for command block)."""
    from pykotor.resource.formats.ncs.dencs.node.a_return_cmd import AReturnCmd  # pyright: ignore[reportMissingImports]

    retn_cmd = AReturnCmd()
    retn = _convert_retn(inst, pos)
    retn_cmd.set_return(retn)

    return retn_cmd

def _convert_copy_sp_cmd(inst: NCSInstruction, pos: int):
    """Convert CPDOWNSP/CPTOPSP instruction to appropriate cmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_copy_down_sp_command import ACopyDownSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copy_top_sp_command import ACopyTopSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copydownsp_cmd import ACopydownspCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copytopsp_cmd import ACopytopspCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_cpdownsp import TCpdownsp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_cptopsp import TCptopsp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    offset = inst.args[0] if inst.args and len(inst.args) > 0 else 0
    size = inst.args[1] if inst.args and len(inst.args) > 1 else 0

    if ins_type == NCSInstructionType.CPDOWNSP:
        cmd = ACopydownspCmd()
        command = ACopyDownSpCommand()
        command.set_cpdownsp(TCpdownsp(pos, 0))
        command.set_pos(TIntegerConstant(str(pos), pos, 0))
        command.set_type(TIntegerConstant(str(type_val), pos, 0))
        command.set_offset(TIntegerConstant(str(offset), pos, 0))
        command.set_size(TIntegerConstant(str(size), pos, 0))
        command.set_semi(TSemi(pos, 0))
        cmd.set_copy_down_sp_command(command)
        return cmd
    else:  # CPTOPSP
        cmd = ACopytopspCmd()
        command = ACopyTopSpCommand()
        command.set_cptopsp(TCptopsp(pos, 0))
        command.set_pos(TIntegerConstant(str(pos), pos, 0))
        command.set_type(TIntegerConstant(str(type_val), pos, 0))
        command.set_offset(TIntegerConstant(str(offset), pos, 0))
        command.set_size(TIntegerConstant(str(size), pos, 0))
        command.set_semi(TSemi(pos, 0))
        cmd.set_copy_top_sp_command(command)
        return cmd

def _convert_copy_bp_cmd(inst: NCSInstruction, pos: int):
    """Convert CPDOWNBP/CPTOPBP instruction to appropriate cmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_copy_down_bp_command import ACopyDownBpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copy_top_bp_command import ACopyTopBpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copydownbp_cmd import ACopydownbpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copytopbp_cmd import ACopytopbpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_cpdownbp import TCpdownbp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_cptopbp import TCptopbp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    offset = inst.args[0] if inst.args and len(inst.args) > 0 else 0
    size = inst.args[1] if inst.args and len(inst.args) > 1 else 0

    if ins_type == NCSInstructionType.CPDOWNBP:
        cmd = ACopydownbpCmd()
        command = ACopyDownBpCommand()
        command.set_cpdownbp(TCpdownbp(pos, 0))
        command.set_pos(TIntegerConstant(str(pos), pos, 0))
        command.set_type(TIntegerConstant(str(type_val), pos, 0))
        command.set_offset(TIntegerConstant(str(offset), pos, 0))
        command.set_size(TIntegerConstant(str(size), pos, 0))
        command.set_semi(TSemi(pos, 0))
        cmd.set_copy_down_bp_command(command)
        return cmd
    else:  # CPTOPBP
        cmd = ACopytopbpCmd()
        command = ACopyTopBpCommand()
        command.set_cptopbp(TCptopbp(pos, 0))
        command.set_pos(TIntegerConstant(str(pos), pos, 0))
        command.set_type(TIntegerConstant(str(type_val), pos, 0))
        command.set_offset(TIntegerConstant(str(offset), pos, 0))
        command.set_size(TIntegerConstant(str(size), pos, 0))
        command.set_semi(TSemi(pos, 0))
        cmd.set_copy_top_bp_command(command)
        return cmd

def _convert_movesp_cmd(inst: NCSInstruction, pos: int):
    """Convert MOVSP instruction to AMovespCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_movesp_cmd import AMovespCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_movsp import TMovsp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    offset = inst.args[0] if inst.args and len(inst.args) > 0 else 0

    cmd = AMovespCmd()
    command = AMoveSpCommand()
    command.set_movsp(TMovsp(pos, 0))
    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_type(TIntegerConstant(str(type_val), pos, 0))
    command.set_offset(TIntegerConstant(str(offset), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_move_sp_command(command)

    return cmd

def _convert_rsadd_cmd(inst: NCSInstruction, pos: int):
    """Convert RSADD instruction to ARsaddCmd.
    
    Handles all RSADD variants:
    - RSADDI, RSADDF, RSADDS, RSADDO (basic types)
    - RSADDEFF, RSADDEVT, RSADDLOC, RSADDTAL (complex types)
    """
    from pykotor.resource.formats.ncs.dencs.node.a_rsadd_cmd import ARsaddCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_rsadd_command import ARsaddCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_rsadd import TRsadd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0

    cmd = ARsaddCmd()
    command = ARsaddCommand()
    command.set_rsadd(TRsadd(pos, 0))
    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_type(TIntegerConstant(str(type_val), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_rsadd_command(command)

    return cmd

def _convert_stack_op_cmd(inst: NCSInstruction, pos: int):
    """Convert stack increment/decrement instructions (INCxSP, DECxSP, INCxBP, DECxBP) to AStackOpCmd.
    
    These instructions adjust the stack or base pointer by a specified offset.
    """
    from pykotor.resource.formats.ncs.dencs.node.a_decibp_stack_op import ADecibpStackOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_decisp_stack_op import ADecispStackOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_incibp_stack_op import AIncibpStackOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_incisp_stack_op import AIncispStackOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_stack_command import AStackCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_stack_op_cmd import AStackOpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_decibp import TDecibp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_decisp import TDecisp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_incibp import TIncibp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_incisp import TIncisp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    offset = inst.args[0] if inst.args and len(inst.args) > 0 else 0

    # Create appropriate stack operation node
    if ins_type == NCSInstructionType.INCxSP:
        stack_op = AIncispStackOp()
        stack_op.set_incisp(TIncisp(pos, 0))
    elif ins_type == NCSInstructionType.DECxSP:
        stack_op = ADecispStackOp()
        stack_op.set_decisp(TDecisp(pos, 0))
    elif ins_type == NCSInstructionType.INCxBP:
        stack_op = AIncibpStackOp()
        stack_op.set_incibp(TIncibp(pos, 0))
    elif ins_type == NCSInstructionType.DECxBP:
        stack_op = ADecibpStackOp()
        stack_op.set_decibp(TDecibp(pos, 0))
    else:
        # Should not reach here, but handle gracefully
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Unexpected instruction type in _convert_stack_op_cmd: {ins_type.name}")
        return None

    # Create stack command
    stack_command = AStackCommand()
    stack_command.set_stack_op(stack_op)
    stack_command.set_pos(TIntegerConstant(str(pos), pos, 0))
    stack_command.set_type(TIntegerConstant(str(type_val), pos, 0))
    stack_command.set_offset(TIntegerConstant(str(offset), pos, 0))
    stack_command.set_semi(TSemi(pos, 0))

    # Create and return command
    cmd = AStackOpCmd()
    cmd.set_stackCommand(stack_command)

    return cmd

def _convert_destruct_cmd(inst: NCSInstruction, pos: int):
    """Convert DESTRUCT instruction to ADestructCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_destruct_cmd import ADestructCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_destruct_command import ADestructCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_destruct import TDestruct  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0

    # DESTRUCT args: [sizeRem (uint16), offset (uint16), sizeSave (uint16)]
    size_rem = inst.args[0] if inst.args and len(inst.args) > 0 else 0
    offset = inst.args[1] if inst.args and len(inst.args) > 1 else 0
    size_save = inst.args[2] if inst.args and len(inst.args) > 2 else 0

    cmd = ADestructCmd()
    command = ADestructCommand()
    command.set_destruct(TDestruct(pos, 0))
    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_type(TIntegerConstant(str(type_val), pos, 0))
    command.set_size_rem(TIntegerConstant(str(size_rem), pos, 0))
    command.set_offset(TIntegerConstant(str(offset), pos, 0))
    command.set_size_save(TIntegerConstant(str(size_save), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_destruct_command(command)

    return cmd

def _convert_bp_cmd(inst: NCSInstruction, pos: int):
    """Convert SAVEBP/RESTOREBP instruction to ABpCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_bp_cmd import ABpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_bp_command import ABpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_restorebp_bp_op import ARestorebpBpOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_savebp_bp_op import ASavebpBpOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_restorebp import TRestorebp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_savebp import TSavebp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0

    cmd = ABpCmd()
    command = ABpCommand()

    if ins_type == NCSInstructionType.SAVEBP:
        bp_op = ASavebpBpOp()
        bp_op.set_savebp(TSavebp(pos, 0))
        command.set_bp_op(bp_op)
    else:  # RESTOREBP
        bp_op = ARestorebpBpOp()
        bp_op.set_restorebp(TRestorebp(pos, 0))
        command.set_bp_op(bp_op)

    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_type(TIntegerConstant(str(type_val), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_bp_command(command)

    return cmd

def _convert_store_state_cmd(inst: NCSInstruction, pos: int):
    """Convert STORE_STATE instruction to AStoreStateCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_store_state_cmd import AStoreStateCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_store_state_command import AStoreStateCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_storestate import TStorestate  # pyright: ignore[reportMissingImports]

    # STORE_STATE has 2 args according to ncs_data.py: [offset (uint16), sizeBp (uint8), sizeSp (uint8)]
    # The args are packed, so we need to extract them properly
    offset = inst.args[0] if inst.args and len(inst.args) > 0 else 0
    # The second arg contains both sizeBp and sizeSp packed together
    # Assuming args[1] is the packed value (sizeBp in low byte, sizeSp in high byte) or separate args
    size_bp = inst.args[1] if inst.args and len(inst.args) > 1 else 0
    size_sp = inst.args[2] if inst.args and len(inst.args) > 2 else 0

    cmd = AStoreStateCmd()
    command = AStoreStateCommand()
    command.set_storestate(TStorestate(pos, 0))
    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_offset(TIntegerConstant(str(offset), pos, 0))
    command.set_size_bp(TIntegerConstant(str(size_bp), pos, 0))
    command.set_size_sp(TIntegerConstant(str(size_sp), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_store_state_command(command)

    return cmd

def _convert_binary_cmd(inst: NCSInstruction, pos: int):
    """Convert binary operation instruction (ADD, SUB, MUL, DIV, MOD, comparisons, bitwise) to ABinaryCmd/ABinaryCommand."""
    from pykotor.resource.formats.ncs.dencs.node.a_binary_cmd import ABinaryCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    
    # Get type qualifier
    type_val = inst.ins_type.value.qualifier if hasattr(inst.ins_type, 'value') and hasattr(inst.ins_type.value, 'qualifier') else 0
    
    # Map instruction type to operator token and node
    # TODO: Create full operator classes (AAddBinaryOp, ASubBinaryOp, etc.)
    # For now, create a placeholder operator node
    binary_op = _create_binary_operator(inst.ins_type, pos)
    
    cmd = ABinaryCmd()
    command = ABinaryCommand()
    command.set_binary_op(binary_op)
    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_type(TIntegerConstant(str(type_val), pos, 0))
    
    # Calculate size based on result type
    result_size = 1  # Default to 1, will be refined when Type system is fully integrated
    command.set_size(TIntegerConstant(str(result_size), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_binary_command(command)
    
    return cmd

def _convert_unary_cmd(inst: NCSInstruction, pos: int):
    """Convert unary operation instruction (NEG, NOT, COMP) to AUnaryCmd/AUnaryCommand."""
    from pykotor.resource.formats.ncs.dencs.node.a_unary_cmd import AUnaryCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_unary_command import AUnaryCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    
    # Get type qualifier
    type_val = inst.ins_type.value.qualifier if hasattr(inst.ins_type, 'value') and hasattr(inst.ins_type.value, 'qualifier') else 0
    
    # Create unary operator
    unary_op = _create_unary_operator(inst.ins_type, pos)
    
    cmd = AUnaryCmd()
    command = AUnaryCommand()
    command.set_unary_op(unary_op)
    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_type(TIntegerConstant(str(type_val), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_unary_command(command)
    
    return cmd

def _convert_logii_cmd(inst: NCSInstruction, pos: int):
    """Convert logic operation instruction (LOGANDII, LOGORII) to ALogiiCmd/ALogiiCommand."""
    from pykotor.resource.formats.ncs.dencs.node.a_logii_cmd import ALogiiCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_logii_command import ALogiiCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    
    # Get type qualifier
    type_val = inst.ins_type.value.qualifier if hasattr(inst.ins_type, 'value') and hasattr(inst.ins_type.value, 'qualifier') else 0
    
    # Create logic operator
    logii_op = _create_logii_operator(inst.ins_type, pos)
    
    cmd = ALogiiCmd()
    command = ALogiiCommand()
    command.set_logii_op(logii_op)
    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_type(TIntegerConstant(str(type_val), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_logii_command(command)
    
    return cmd

def _create_binary_operator(ins_type: NCSInstructionType, pos: int):
    """Create a PBinaryOp node for the given instruction type.
    
    Handles all binary operations:
    - Arithmetic: ADDxx, SUBxx, MULxx, DIVxx, MODxx
    - Comparison: EQUALxx, NEQUALxx, GTxx, GEQxx, LTxx, LEQxx
    - Bitwise: SHLEFTxx, SHRIGHTxx, USHRIGHTxx
    """
    from pykotor.resource.formats.ncs.dencs.node.a_add_binary_op import AAddBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_div_binary_op import ADivBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_equal_binary_op import AEqualBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_geq_binary_op import AGeqBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_gt_binary_op import AGtBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_leq_binary_op import ALeqBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_lt_binary_op import ALtBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_mod_binary_op import AModBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_mul_binary_op import AMulBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_nequal_binary_op import ANequalBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_shleft_binary_op import AShleftBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_shright_binary_op import AShrightBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_sub_binary_op import ASubBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_unright_binary_op import AUnrightBinaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]
    
    # Map instruction type to operator class
    # Use exact matches for better type safety
    if ins_type == NCSInstructionType.USHRIGHTII:
        return AUnrightBinaryOp()
    
    ins_name = ins_type.name
    
    # Arithmetic operators
    if ins_name.startswith("ADD"):
        return AAddBinaryOp()
    elif ins_name.startswith("SUB"):
        return ASubBinaryOp()
    elif ins_name.startswith("MUL"):
        return AMulBinaryOp()
    elif ins_name.startswith("DIV"):
        return ADivBinaryOp()
    elif ins_name.startswith("MOD"):
        return AModBinaryOp()
    # Comparison operators
    elif ins_name.startswith("EQUAL"):
        return AEqualBinaryOp()
    elif ins_name.startswith("NEQUAL"):
        return ANequalBinaryOp()
    elif ins_name.startswith("GT"):
        return AGtBinaryOp()
    elif ins_name.startswith("LT"):
        return ALtBinaryOp()
    elif ins_name.startswith("GEQ"):
        return AGeqBinaryOp()
    elif ins_name.startswith("LEQ"):
        return ALeqBinaryOp()
    # Bitwise shift operators
    elif ins_name.startswith("SHLEFT"):
        return AShleftBinaryOp()
    elif ins_name.startswith("SHRIGHT"):
        return AShrightBinaryOp()
    elif ins_name.startswith("USHRIGHT"):
        return AUnrightBinaryOp()
    else:
        # Fallback: return a placeholder for unknown operators
        # This should rarely happen if all instruction types are properly handled
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Unknown binary operator: {ins_type.name}, creating placeholder")
        
        from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]
        class PlaceholderBinaryOp(PBinaryOp):
            def __init__(self):
                super().__init__()
                self._ins_type = ins_type
            
            def apply(self, sw):
                sw.case_node(self)
        
        return PlaceholderBinaryOp()

def _create_unary_operator(ins_type: NCSInstructionType, pos: int):
    """Create a PUnaryOp node for the given instruction type.
    
    Handles all unary operations:
    - Arithmetic: NEGI, NEGF (negation)
    - Logical: NOTI (logical not)
    - Bitwise: COMPI (bitwise complement)
    """
    from pykotor.resource.formats.ncs.dencs.node.a_comp_unary_op import ACompUnaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_neg_unary_op import ANegUnaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_not_unary_op import ANotUnaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]
    
    # Map instruction type to operator class
    # Use exact matches for better type safety
    if ins_type in {NCSInstructionType.NEGI, NCSInstructionType.NEGF}:
        return ANegUnaryOp()
    elif ins_type == NCSInstructionType.NOTI:
        return ANotUnaryOp()
    elif ins_type == NCSInstructionType.COMPI:
        return ACompUnaryOp()
    
    # Fallback to name-based matching for any variants
    ins_name = ins_type.name
    
    if ins_name.startswith("NEG"):
        return ANegUnaryOp()
    elif ins_name.startswith("NOT"):
        return ANotUnaryOp()
    elif ins_name.startswith("COMP"):
        return ACompUnaryOp()
    else:
        # Fallback: return a placeholder for unknown operators
        # This should rarely happen if all instruction types are properly handled
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Unknown unary operator: {ins_type.name}, creating placeholder")
        
        from pykotor.resource.formats.ncs.dencs.node.p_unary_op import PUnaryOp  # pyright: ignore[reportMissingImports]
        class PlaceholderUnaryOp(PUnaryOp):
            def __init__(self):
                super().__init__()
                self._ins_type = ins_type
            
            def apply(self, sw):
                sw.case_node(self)
        
        return PlaceholderUnaryOp()

def _create_logii_operator(ins_type: NCSInstructionType, pos: int):
    """Create a PLogiiOp node for the given instruction type.
    
    Handles all logical and bitwise logical operations:
    - Logical: LOGANDxx, LOGORxx
    - Bitwise logical: BOOLANDxx, INCORxx, EXCORxx
    """
    from pykotor.resource.formats.ncs.dencs.node.a_and_logii_op import AAndLogiiOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_bit_and_logii_op import ABitAndLogiiOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_excl_or_logii_op import AExclOrLogiiOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_incl_or_logii_op import AInclOrLogiiOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_or_logii_op import AOrLogiiOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]
    
    # Map instruction type to operator class
    # Use exact matches for better type safety where possible
    if ins_type == NCSInstructionType.LOGANDII:
        return AAndLogiiOp()
    elif ins_type == NCSInstructionType.LOGORII:
        return AOrLogiiOp()
    elif ins_type == NCSInstructionType.BOOLANDII:
        return ABitAndLogiiOp()
    elif ins_type == NCSInstructionType.EXCORII:
        return AExclOrLogiiOp()
    elif ins_type == NCSInstructionType.INCORII:
        return AInclOrLogiiOp()
    
    # Fallback to name-based matching for any variants
    ins_name = ins_type.name
    
    if ins_name.startswith("LOGAND"):
        return AAndLogiiOp()
    elif ins_name.startswith("LOGOR"):
        return AOrLogiiOp()
    elif ins_name.startswith("BOOLAND"):
        return ABitAndLogiiOp()
    elif ins_name.startswith("EXCOR"):
        return AExclOrLogiiOp()
    elif ins_name.startswith("INCOR"):
        return AInclOrLogiiOp()
    else:
        # Fallback: return a placeholder for unknown operators
        # This should rarely happen if all instruction types are properly handled
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Unknown logical operator: {ins_type.name}, creating placeholder")
        
        from pykotor.resource.formats.ncs.dencs.node.p_logii_op import PLogiiOp  # pyright: ignore[reportMissingImports]
        class PlaceholderLogiiOp(PLogiiOp):
            def __init__(self):
                super().__init__()
                self._ins_type = ins_type
            
            def apply(self, sw):
                sw.case_node(self)
        
        return PlaceholderLogiiOp()

