# Ghidra Script: Force Analysis of KOTOR .text Section
# 
# This script attempts to force Ghidra to analyze the .text section
# even if it appears to be encrypted/packed.
#
# For Steam KOTOR: The .text section is encrypted by DRM. This script
# will NOT work on the encrypted binary. You must first dump the 
# unpacked executable from memory while the game is running.
#
# For GOG KOTOR or unpacked dumps: This script will help ensure
# complete analysis.
#
# @category KOTOR
# @author PyKotor Project

from ghidra.app.cmd.disassemble import DisassembleCommand
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.program.model.address import AddressSet
from ghidra.app.services import ConsoleService
from ghidra.util.task import TaskMonitor

def get_text_section():
    """Find the .text section."""
    memory = currentProgram.getMemory()
    for block in memory.getBlocks():
        if block.getName() == ".text":
            return block
    return None

def analyze_text_section():
    """Force analysis of the .text section."""
    text_block = get_text_section()
    
    if text_block is None:
        print("ERROR: Could not find .text section!")
        return
        
    start = text_block.getStart()
    end = text_block.getEnd()
    
    print("Found .text section: {} - {}".format(start, end))
    print("Size: {} bytes".format(text_block.getSize()))
    
    # Check if the section looks encrypted
    # Encrypted sections typically have high entropy / random-looking bytes
    sample_bytes = []
    addr = start
    for i in range(min(100, text_block.getSize())):
        try:
            b = getByte(addr)
            sample_bytes.append(b & 0xFF)
            addr = addr.add(1)
        except:
            break
            
    # Check for common x86 prologue patterns
    # push ebp = 0x55
    # mov ebp, esp = 0x8B 0xEC or 0x89 0xE5
    prologue_count = 0
    for i in range(len(sample_bytes) - 2):
        if sample_bytes[i] == 0x55:  # push ebp
            if i + 2 < len(sample_bytes):
                if (sample_bytes[i+1] == 0x8B and sample_bytes[i+2] == 0xEC) or \
                   (sample_bytes[i+1] == 0x89 and sample_bytes[i+2] == 0xE5):
                    prologue_count += 1
                    
    if prologue_count == 0:
        print("\nWARNING: No function prologues found in first 100 bytes!")
        print("The .text section may be encrypted/packed.")
        print("You need to dump the unpacked executable from memory.")
        print("See: scripts/STEAM_KOTOR_UNPACKING_GUIDE.md")
        return
        
    print("\nFound {} potential function prologues - section appears unpacked!".format(prologue_count))
    
    # Create address set for the entire .text section
    addr_set = AddressSet(start, end)
    
    # Disassemble the entire section
    print("\nDisassembling .text section...")
    disasm_cmd = DisassembleCommand(addr_set, None, True)
    disasm_cmd.applyTo(currentProgram, TaskMonitor.DUMMY)
    
    print("Disassembly complete!")
    
    # Now try to create functions at known entry points
    # We'll look for common function patterns
    print("\nSearching for function entry points...")
    
    func_count = 0
    addr = start
    while addr.compareTo(end) < 0:
        try:
            b = getByte(addr)
            # Look for push ebp (0x55)
            if (b & 0xFF) == 0x55:
                next_addr = addr.add(1)
                next_b = getByte(next_addr)
                # Check for mov ebp, esp
                if (next_b & 0xFF) == 0x8B:
                    third_addr = addr.add(2)
                    third_b = getByte(third_addr)
                    if (third_b & 0xFF) == 0xEC:
                        # This looks like a function prologue
                        existing_func = getFunctionAt(addr)
                        if existing_func is None:
                            cmd = CreateFunctionCmd(addr)
                            if cmd.applyTo(currentProgram):
                                func_count += 1
                                if func_count % 100 == 0:
                                    print("Created {} functions...".format(func_count))
        except:
            pass
        addr = addr.add(1)
        
    print("\nCreated {} new functions".format(func_count))
    
    # Count total functions
    func_manager = currentProgram.getFunctionManager()
    total_funcs = func_manager.getFunctionCount()
    print("Total functions in program: {}".format(total_funcs))

if __name__ == "__main__":
    analyze_text_section()

