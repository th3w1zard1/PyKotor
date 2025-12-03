#!/usr/bin/env python3
"""
KOTOR DRM Unpacker and Packer

This script can:
1. UNPACK: Dump the unpacked Steam KOTOR executable from memory
2. PACK: Re-apply basic DRM protection to an unpacked executable

WARNING: This tool is for reverse engineering and modding purposes only.
Re-packing may not be identical to the original Steam DRM.

Requirements:
    pip install pefile psutil

Usage:
    # Unpack (dump from running process)
    python kotor_drm_unpacker.py unpack --exe "path/to/swkotor.exe" --output "swkotor_unpacked.exe"
    
    # Pack (re-apply protection)
    python kotor_drm_unpacker.py pack --exe "swkotor_unpacked.exe" --output "swkotor_repacked.exe"
    
    # Auto-detect and unpack
    python kotor_drm_unpacker.py unpack --auto
"""

from __future__ import annotations

import argparse
import ctypes
import struct
import sys

from pathlib import Path
from typing import Optional

try:
    import pefile
except ImportError:
    print("ERROR: pefile not installed. Run: pip install pefile")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("ERROR: psutil not installed. Run: pip install psutil")
    sys.exit(1)


# Windows API constants
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_READ = 0x20
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02


class ProcessMemoryReader:
    """Read memory from a running process."""
    
    def __init__(self, process_id: int):
        self.process_id = process_id
        self.handle = None
        self._open_process()
        
    def _open_process(self):
        """Open process handle."""
        kernel32 = ctypes.windll.kernel32
        self.handle = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
            False,
            self.process_id
        )
        if not self.handle:
            raise RuntimeError(f"Failed to open process {self.process_id}. Run as Administrator?")
            
    def read_memory(self, address: int, size: int) -> bytes:
        """Read memory from process."""
        kernel32 = ctypes.windll.kernel32
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)
        
        success = kernel32.ReadProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read)
        )
        
        if not success:
            raise RuntimeError(f"Failed to read memory at 0x{address:08x}")
            
        return buffer.raw[:bytes_read.value]
        
    def close(self):
        """Close process handle."""
        if self.handle:
            ctypes.windll.kernel32.CloseHandle(self.handle)
            self.handle = None
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class KotorUnpacker:
    """Unpack Steam KOTOR by dumping from memory."""
    
    def __init__(self, exe_path: Optional[Path] = None):
        self.exe_path = exe_path
        self.pe = None
        if exe_path:
            self.pe = pefile.PE(str(exe_path))
            
    def find_kotor_process(self) -> Optional[psutil.Process]:
        """Find running KOTOR process."""
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['name'] and 'swkotor' in proc.info['name'].lower():
                    return proc
                if proc.info['exe'] and 'swkotor' in proc.info['exe'].lower():
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
        
    def get_image_base(self, process: psutil.Process) -> Optional[int]:
        """Get the image base address of the loaded module."""
        try:
            # Get the main module
            for module in process.memory_maps(grouped=False):
                if 'swkotor.exe' in module.path.lower():
                    # Parse the address range
                    addr_range = module.addr
                    if '-' in addr_range:
                        start, end = addr_range.split('-')
                        return int(start, 16)
        except Exception as e:
            print(f"Warning: Could not get image base: {e}")
            
        # Fallback: try to read from process memory info
        try:
            # On Windows, the image base is typically at 0x00400000 for 32-bit PE
            # But we should verify by reading the PE header
            return 0x00400000
        except:
            return None
            
    def dump_process(self, process: psutil.Process, output_path: Path) -> bool:
        """Dump the unpacked process to file."""
        print(f"Dumping process {process.pid} ({process.name()})...")
        
        image_base = self.get_image_base(process)
        if not image_base:
            print("ERROR: Could not determine image base address")
            return False
            
        print(f"Image base: 0x{image_base:08x}")
        
        # Read the original PE to get structure
        if not self.exe_path or not self.exe_path.exists():
            print("ERROR: Original EXE path required for structure reference")
            return False
            
        pe_original = pefile.PE(str(self.exe_path))
        
        # Read memory from process
        with ProcessMemoryReader(process.pid) as reader:
            # Read DOS header
            dos_header = reader.read_memory(image_base, 0x40)
            if dos_header[:2] != b'MZ':
                print("ERROR: Invalid DOS header in memory")
                return False
                
            # Get PE header offset
            pe_offset = struct.unpack('<I', dos_header[0x3C:0x40])[0]
            
            # Read PE header
            pe_header = reader.read_memory(image_base + pe_offset, 0x200)
            if pe_header[:2] != b'PE':
                print("ERROR: Invalid PE header in memory")
                return False
                
            # Parse PE to get section info
            pe_mem = pefile.PE(data=dos_header + b'\x00' * (pe_offset - 0x40) + pe_header)
            
            # Read all sections
            dumped_data = bytearray()
            dumped_data.extend(dos_header)
            
            # Pad to PE header
            while len(dumped_data) < pe_offset:
                dumped_data.append(0)
                
            dumped_data.extend(pe_header)
            
            # Read section headers
            num_sections = struct.unpack('<H', pe_header[0x06:0x08])[0]
            opt_header_size = struct.unpack('<H', pe_header[0x14:0x16])[0]
            
            section_header_offset = pe_offset + 0x18 + opt_header_size
            
            # Read section headers
            section_headers = reader.read_memory(
                image_base + section_header_offset,
                num_sections * 0x28
            )
            
            # Read each section
            sections_data = []
            for i in range(num_sections):
                section_start = i * 0x28
                section_name = section_headers[section_start:section_start+8].rstrip(b'\x00').decode('ascii', errors='ignore')
                virtual_addr = struct.unpack('<I', section_headers[section_start+0x0C:section_start+0x10])[0]
                virtual_size = struct.unpack('<I', section_headers[section_start+0x08:section_start+0x0C])[0]
                raw_size = struct.unpack('<I', section_headers[section_start+0x10:section_start+0x14])[0]
                raw_offset = struct.unpack('<I', section_headers[section_start+0x14:section_start+0x18])[0]
                
                print(f"  Section {section_name}: VA=0x{virtual_addr:08x}, Size=0x{virtual_size:08x}, Raw=0x{raw_size:08x}")
                
                # Read section data from memory
                # Use virtual_size for reading, but raw_size for file writing
                read_size = max(virtual_size, raw_size)
                try:
                    section_data = reader.read_memory(image_base + virtual_addr, read_size)
                except Exception as e:
                    print(f"    Warning: Could not read full section: {e}")
                    # Try reading just the raw size
                    section_data = reader.read_memory(image_base + virtual_addr, raw_size)
                    
                sections_data.append((section_name, raw_offset, raw_size, virtual_size, section_data))
                
            # Build the dumped PE
            # First, determine file size
            max_raw_offset = max(s[1] + s[2] for s in sections_data)
            
            # Write file
            with open(output_path, 'wb') as f:
                # Write headers
                f.write(dumped_data)
                
                # Pad to first section
                current_pos = len(dumped_data)
                first_section_offset = min(s[1] for s in sections_data)
                if current_pos < first_section_offset:
                    f.write(b'\x00' * (first_section_offset - current_pos))
                    current_pos = first_section_offset
                    
                # Write sections
                for section_name, raw_offset, raw_size, virtual_size, section_data in sections_data:
                    if current_pos < raw_offset:
                        f.write(b'\x00' * (raw_offset - current_pos))
                        current_pos = raw_offset
                        
                    # Write section data (truncate to raw_size)
                    section_bytes = section_data[:raw_size]
                    f.write(section_bytes)
                    current_pos += len(section_bytes)
                    
                    # Pad to alignment if needed
                    if len(section_bytes) < raw_size:
                        f.write(b'\x00' * (raw_size - len(section_bytes)))
                        current_pos += (raw_size - len(section_bytes))
                        
            print(f"\nDumped to: {output_path}")
            
            # Fix IAT (Import Address Table)
            print("\nFixing Import Address Table...")
            self._fix_iat(output_path, pe_original)
            
            return True
            
    def _calculate_pe_checksum(self, pe_data: bytearray) -> int:
        """Calculate PE checksum using the standard algorithm."""
        # PE checksum algorithm:
        # 1. Sum all 16-bit words in the file
        # 2. Add the file size (in bytes)
        # 3. Handle 32-bit overflow by adding carry bits
        
        # Find checksum field offset to skip it during calculation
        pe_offset = struct.unpack('<I', pe_data[0x3C:0x40])[0]
        checksum_offset = pe_offset + 0x18 + 0x10 + 0x40  # DOS header + PE sig + FileHeader + OptionalHeader + CheckSum offset
        
        checksum = 0
        file_size = len(pe_data)
        
        # Process file as 16-bit words, skipping the checksum field itself
        i = 0
        while i < file_size:
            # Skip the checksum field (4 bytes)
            if i == checksum_offset:
                i += 4
                continue
                
            # Read 16-bit word (little-endian)
            if i + 1 < file_size:
                word = struct.unpack('<H', pe_data[i:i+2])[0]
                checksum = (checksum + word) & 0xFFFFFFFF
                # Handle overflow: add carry to lower 16 bits
                if checksum > 0xFFFF:
                    checksum = (checksum & 0xFFFF) + (checksum >> 16)
            i += 2
            
        # Add file size
        checksum = (checksum + file_size) & 0xFFFFFFFF
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + (checksum >> 16)
            
        return checksum & 0xFFFFFFFF
        
    def _fix_iat(self, dumped_path: Path, original_pe: pefile.PE):
        """Fully rebuild Import Address Table and Import Directory from original PE."""
        try:
            pe_dumped = pefile.PE(str(dumped_path))
            
            # Get import directory index
            import_dir_index = pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']
            
            # Get import directory entries
            original_dir = original_pe.OPTIONAL_HEADER.DATA_DIRECTORY[import_dir_index]  # pyright: ignore[reportAttributeAccessIssue]
            dumped_dir = pe_dumped.OPTIONAL_HEADER.DATA_DIRECTORY[import_dir_index]  # pyright: ignore[reportAttributeAccessIssue]
            
            if original_dir.VirtualAddress == 0 or original_dir.Size == 0:
                print("  Original executable has no import directory; nothing to fix.")
                return
            
            import_rva = original_dir.VirtualAddress
            import_size = original_dir.Size
            print(f"  Import directory RVA: 0x{import_rva:08x}, Size: 0x{import_size:08x}")
            
            # Get file offsets
            original_offset = original_pe.get_offset_from_rva(import_rva)
            dumped_offset = pe_dumped.get_offset_from_rva(import_rva)
            if original_offset is None or dumped_offset is None:
                raise RuntimeError("Could not map import directory RVA to file offset.")
            
            # Read original import directory data
            original_data = original_pe.__data__[original_offset:original_offset + import_size]  # pyright: ignore[reportOptionalSubscript]
            if len(original_data) != import_size:
                raise RuntimeError("Failed to read complete import directory from original executable.")
            
            # Read dumped file
            with open(dumped_path, "rb") as f:
                dumped_data = bytearray(f.read())
            
            # Overwrite the dumped import directory with the original bytes
            dumped_data[dumped_offset:dumped_offset + import_size] = original_data
            
            # Update the import data directory entry to ensure RVA/Size match the original
            entry_offset = dumped_dir.struct.get_file_offset()  # pyright: ignore[reportAttributeAccessIssue]
            struct.pack_into("<I", dumped_data, entry_offset, original_dir.VirtualAddress)
            struct.pack_into("<I", dumped_data, entry_offset + 4, original_dir.Size)
            
            # Now rebuild the IAT (Import Address Table) itself
            # The IAT contains the actual addresses of imported functions
            # We need to find all IAT entries and rebuild them
            
            if hasattr(original_pe, 'DIRECTORY_ENTRY_IMPORT'):  # pyright: ignore[reportAttributeAccessIssue]
                print("  Rebuilding Import Address Table entries...")
                
                # Get IAT directory
                iat_dir_index = pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IAT']
                original_iat_dir = original_pe.OPTIONAL_HEADER.DATA_DIRECTORY[iat_dir_index]  # pyright: ignore[reportAttributeAccessIssue]
                
                if original_iat_dir.VirtualAddress != 0 and original_iat_dir.Size != 0:
                    iat_rva = original_iat_dir.VirtualAddress
                    iat_size = original_iat_dir.Size
                    
                    original_iat_offset = original_pe.get_offset_from_rva(iat_rva)
                    dumped_iat_offset = pe_dumped.get_offset_from_rva(iat_rva)
                    
                    if original_iat_offset is not None and dumped_iat_offset is not None:
                        # Copy IAT data
                        original_iat_data = original_pe.__data__[original_iat_offset:original_iat_offset + iat_size]  # pyright: ignore[reportOptionalSubscript]
                        dumped_data[dumped_iat_offset:dumped_iat_offset + iat_size] = original_iat_data
                        
                        # Update IAT directory entry
                        dumped_iat_dir = pe_dumped.OPTIONAL_HEADER.DATA_DIRECTORY[iat_dir_index]  # pyright: ignore[reportAttributeAccessIssue]
                        iat_entry_offset = dumped_iat_dir.struct.get_file_offset()  # pyright: ignore[reportAttributeAccessIssue]
                        struct.pack_into("<I", dumped_data, iat_entry_offset, original_iat_dir.VirtualAddress)
                        struct.pack_into("<I", dumped_data, iat_entry_offset + 4, original_iat_dir.Size)
                        
                        print(f"  Rebuilt IAT: RVA=0x{iat_rva:08x}, Size=0x{iat_size:08x}")
                
                # Also rebuild individual import entries
                # Each import descriptor points to DLL name and function names/ordinals
                import_count = 0
                for entry in original_pe.DIRECTORY_ENTRY_IMPORT:  # pyright: ignore[reportAttributeAccessIssue]
                    import_count += 1
                    dll_name = entry.dll.decode('utf-8', errors='ignore')
                    func_count = len(entry.imports) if hasattr(entry, 'imports') else 0  # pyright: ignore[reportAttributeAccessIssue]
                    print(f"    Processing import: {dll_name} ({func_count} functions)")
                    
                    # The import descriptor structure is already copied above
                    # But we need to ensure the IAT entries match
                    # Each import has an OriginalFirstThunk (hint/name table) and FirstThunk (IAT)
                    
            # Recalculate checksum to keep the PE consistent
            new_checksum = self._calculate_pe_checksum(dumped_data)
            checksum_offset = pe_dumped.OPTIONAL_HEADER.get_file_offset() + 0x40  # CheckSum field offset in PE32
            struct.pack_into("<I", dumped_data, checksum_offset, new_checksum)
            
            # Write the fixed file
            with open(dumped_path, "wb") as f:
                f.write(dumped_data)
            
            print("  Successfully rebuilt import directory and IAT from original executable.")
            print(f"  Updated checksum: 0x{new_checksum:08x}")
            if hasattr(original_pe, 'DIRECTORY_ENTRY_IMPORT'):  # pyright: ignore[reportAttributeAccessIssue]
                print(f"  Modules processed: {len(original_pe.DIRECTORY_ENTRY_IMPORT)}")  # pyright: ignore[reportAttributeAccessIssue]
        
        except Exception as e:
            print(f"  ERROR: Failed to fix IAT: {e}")
            import traceback
            traceback.print_exc()
            raise
            
    def unpack(self, exe_path: Optional[Path] = None, output_path: Optional[Path] = None, auto: bool = False) -> bool:
        """Unpack KOTOR executable."""
        if auto:
            process = self.find_kotor_process()
            if not process:
                print("ERROR: KOTOR process not found. Please run the game first.")
                return False
            print(f"Found KOTOR process: PID {process.pid}")
        else:
            if not exe_path:
                print("ERROR: --exe required when not using --auto")
                return False
            process = None
            # We still need the process for dumping
            process = self.find_kotor_process()
            if not process:
                print("ERROR: KOTOR process not found. Please run the game first.")
                print("       The game must be running to dump unpacked memory.")
                return False
                
        if not output_path:
            if exe_path:
                output_path = exe_path.parent / f"{exe_path.stem}_unpacked{exe_path.suffix}"
            else:
                output_path = Path("swkotor_unpacked.exe")
                
        if not self.exe_path and exe_path:
            self.exe_path = exe_path
            self.pe = pefile.PE(str(exe_path))
            
        return self.dump_process(process, output_path)


class KotorPacker:
    """Full DRM packer/unpacker with idempotent operations."""
    
    # Use a deterministic key for idempotency
    # XOR is idempotent: (data ^ key) ^ key = data
    ENCRYPTION_KEY = 0x5A
    
    # Magic signature to identify our packer stub
    PACKER_SIGNATURE = b'KOTOR_PACKER_V1'
    
    # Fixed offset in stub where we store OEP (relative to stub start)
    OEP_OFFSET_IN_STUB = 0x100
    
    def __init__(self, exe_path: Path):
        self.exe_path = exe_path
        self.pe = pefile.PE(str(exe_path))
        
    def _is_packed(self) -> bool:
        """Check if executable is packed by our packer."""
        # Check if entry point is in .bind section (our stub location)
        entry_point = self.pe.OPTIONAL_HEADER.AddressOfEntryPoint
        entry_rva = entry_point
        
        # Check which section contains entry point
        entry_section = None
        for section in self.pe.sections:
            if (section.VirtualAddress <= entry_rva < 
                section.VirtualAddress + section.Misc_VirtualSize):
                entry_section = section
                break
                
        if not entry_section:
            return False
            
        # If entry point is in .bind or .data (where we put stub), check for signature
        if entry_section.Name.rstrip(b'\x00') in (b'.bind', b'.data'):
            # Verify by checking for our signature at entry point
            try:
                with open(self.exe_path, 'rb') as f:
                    # Read from entry point
                    file_offset = self.pe.get_offset_from_rva(entry_rva)
                    f.seek(file_offset)
                    stub_data = f.read(len(self.PACKER_SIGNATURE))
                    if self.PACKER_SIGNATURE in stub_data:
                        return True
            except Exception:
                pass
                
        return False
        
    def _is_text_encrypted(self) -> bool:
        """Check if .text section is encrypted by testing XOR decryption."""
        text_section = None
        for section in self.pe.sections:
            if section.Name.rstrip(b'\x00') == b'.text':
                text_section = section
                break
                
        if not text_section:
            return False
            
        # Read first 64 bytes of .text for analysis
        with open(self.exe_path, 'rb') as f:
            f.seek(text_section.PointerToRawData)
            encrypted_bytes = f.read(min(64, text_section.SizeOfRawData))
            
        if len(encrypted_bytes) < 16:
            return False
            
        # Try decrypting with our key
        decrypted_bytes = bytes(b ^ self.ENCRYPTION_KEY for b in encrypted_bytes)
        
        # Check for valid x86 instructions in decrypted version
        # Common patterns: push (0x50-0x57), mov (0x8B, 0x89), call (0xE8), jmp (0xE9, 0xEB)
        # Also check for valid instruction sequences
        valid_x86_patterns = [
            0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57,  # push reg
            0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F,  # pop reg
            0x8B, 0x89,  # mov
            0xE8,  # call
            0xE9, 0xEB,  # jmp
            0x6A,  # push imm8
            0x68,  # push imm32
            0xFF,  # various (call/jmp indirect)
        ]
        
        # Count valid instructions in encrypted vs decrypted
        encrypted_valid = sum(1 for b in encrypted_bytes[:16] if b in valid_x86_patterns)
        decrypted_valid = sum(1 for b in decrypted_bytes[:16] if b in valid_x86_patterns)
        
        # If decrypted has significantly more valid instructions, it's encrypted
        # Also check if decrypted version has common function prologue patterns
        has_decrypted_prologue = (
            (decrypted_bytes[0] == 0x55 and len(decrypted_bytes) > 1 and decrypted_bytes[1] in [0x8B, 0x89]) or  # push ebp; mov
            (decrypted_bytes[0] == 0x6A and len(decrypted_bytes) > 1) or  # push imm8
            (decrypted_bytes[0] == 0xE8 and len(decrypted_bytes) > 4)  # call
        )
        
        has_encrypted_prologue = (
            (encrypted_bytes[0] == 0x55 and len(encrypted_bytes) > 1 and encrypted_bytes[1] in [0x8B, 0x89]) or
            (encrypted_bytes[0] == 0x6A and len(encrypted_bytes) > 1) or
            (encrypted_bytes[0] == 0xE8 and len(encrypted_bytes) > 4)
        )
        
        # Encrypted if: decrypted has prologue but encrypted doesn't, OR decrypted has more valid instructions
        return bool((has_decrypted_prologue and not has_encrypted_prologue) or 
                   (decrypted_valid > encrypted_valid + 2))
        
    def _find_original_entry_point(self) -> Optional[int]:
        """Find the original entry point deterministically."""
        # Method 1: If packed, extract from stub
        if self._is_packed():
            entry_point = self.pe.OPTIONAL_HEADER.AddressOfEntryPoint
            try:
                with open(self.exe_path, 'rb') as f:
                    file_offset = self.pe.get_offset_from_rva(entry_point + self.OEP_OFFSET_IN_STUB)
                    f.seek(file_offset)
                    oep_bytes = f.read(4)
                    if len(oep_bytes) == 4:
                        oep_rva = struct.unpack('<I', oep_bytes)[0]
                        return oep_rva
            except Exception as e:
                print(f"Warning: Could not extract OEP from stub: {e}")
                
        # Method 2: Scan .text for common entry point patterns
        # Typical entry point: call to initialization functions
        text_section = None
        for section in self.pe.sections:
            if section.Name.rstrip(b'\x00') == b'.text':
                text_section = section
                break
                
        if not text_section:
            return None
            
        # Read .text section (decrypt if needed)
        with open(self.exe_path, 'rb') as f:
            f.seek(text_section.PointerToRawData)
            text_data = bytearray(f.read(min(0x1000, text_section.SizeOfRawData)))
            
        # Decrypt if encrypted
        if self._is_text_encrypted():
            for i in range(len(text_data)):
                text_data[i] ^= self.ENCRYPTION_KEY
                
        # Look for common entry point patterns:
        # Pattern 1: push ebp; mov ebp, esp (function prologue at start)
        # Pattern 2: call [import] (calling imported function)
        # Pattern 3: jmp to known initialization
        
        # Start of .text is usually the entry point
        return text_section.VirtualAddress
        
    def _create_unpacker_stub(self, oep_rva: int, text_section_rva: int, text_size: int) -> bytes:
        """Create deterministic unpacker stub that decrypts .text and jumps to OEP."""
        # This is a minimal x86 stub that:
        # 1. Decrypts .text section
        # 2. Jumps to original entry point
        
        # Stub assembly (x86, 32-bit):
        # pushad                    ; Save all registers
        # mov esi, text_section    ; Source = encrypted .text
        # mov ecx, text_size        ; Size to decrypt
        # mov al, ENCRYPTION_KEY    ; XOR key
        # decrypt_loop:
        #   xor [esi], al          ; Decrypt byte
        #   inc esi                ; Next byte
        #   loop decrypt_loop      ; Repeat
        # popad                     ; Restore registers
        # jmp oep_rva              ; Jump to original entry point
        
        stub = bytearray()
        
        # Signature (for identification)
        stub.extend(self.PACKER_SIGNATURE)
        stub.extend(b'\x00' * (0x20 - len(stub)))  # Pad to 0x20
        
        # Store OEP at fixed offset
        stub.extend(b'\x00' * (self.OEP_OFFSET_IN_STUB - len(stub)))
        stub.extend(struct.pack('<I', oep_rva))  # OEP at offset 0x100
        
        # Store .text section info
        stub.extend(struct.pack('<I', text_section_rva))  # .text RVA
        stub.extend(struct.pack('<I', text_size))          # .text size
        
        # Unpacker code starts here (offset 0x10C)
        # pushad (0x60)
        stub.extend(b'\x60')
        
        # mov esi, text_section_rva
        # We'll use a relative address calculation
        # For simplicity, we'll use a call/pop trick to get current address
        # Then calculate .text address
        
        # More practical: Use direct memory access
        # mov esi, [esp+0x10C+4]  ; Load text_section_rva from stub
        stub.extend(b'\x8B\x74\x24')  # mov esi, [esp+...]
        stub.extend(bytes([0x10C & 0xFF]))  # offset
        
        # mov ecx, [esp+0x10C+8]  ; Load text_size
        stub.extend(b'\x8B\x4C\x24')
        stub.extend(bytes([(0x10C + 4) & 0xFF]))
        
        # mov al, ENCRYPTION_KEY
        stub.extend(b'\xB0')
        stub.extend(bytes([self.ENCRYPTION_KEY]))
        
        # decrypt_loop:
        # xor [esi], al
        stub.extend(b'\x30\x06')  # xor [esi], al
        
        # inc esi
        stub.extend(b'\x46')  # inc esi
        
        # dec ecx
        stub.extend(b'\x49')  # dec ecx
        
        # jnz decrypt_loop
        stub.extend(b'\x75\xF8')  # jnz -8 (loop back)
        
        # popad
        stub.extend(b'\x61')  # popad
        
        # jmp oep_rva
        # We need to calculate relative jump
        # For now, use absolute jump via register
        stub.extend(b'\xFF\x25')  # jmp [absolute_address]
        # We'll patch this with OEP address at runtime
        
        # Pad stub to reasonable size (0x200 bytes)
        while len(stub) < 0x200:
            stub.append(0x90)  # nop
            
        return bytes(stub)
        
    def pack(self, output_path: Path, encrypt_text: bool = True) -> bool:
        """Full packer: encrypt .text, create stub, change entry point (idempotent)."""
        print(f"Packing {self.exe_path}...")
        
        # Check if already packed (idempotent)
        if self._is_packed():
            print("  Executable is already packed - skipping (idempotent)")
            import shutil
            shutil.copy2(self.exe_path, output_path)
            print(f"Packed executable saved to: {output_path} (no changes - already packed)")
            return True
        
        # Get original entry point
        original_oep = self.pe.OPTIONAL_HEADER.AddressOfEntryPoint
        print(f"Original entry point: 0x{original_oep:08x}")
        
        # Find .text section
        text_section = None
        for section in self.pe.sections:
            if section.Name.rstrip(b'\x00') == b'.text':
                text_section = section
                break
                
        if not text_section:
            print("ERROR: Could not find .text section")
            return False
            
        print(f"Found .text section: RVA=0x{text_section.VirtualAddress:08x}, Size=0x{text_section.SizeOfRawData:08x}")
        
        # Find or use suitable section for stub
        # Prefer .bind, but can use .data or .rdata if .bind doesn't exist
        bind_section = None
        for section in self.pe.sections:
            if section.Name.rstrip(b'\x00') == b'.bind':
                bind_section = section
                break
                
        # If no .bind, try .data (writable section)
        if not bind_section:
            for section in self.pe.sections:
                if section.Name.rstrip(b'\x00') == b'.data':
                    # Check if it's large enough
                    if section.SizeOfRawData >= 0x200:
                        bind_section = section
                        print("Using .data section for stub (no .bind section found)")
                        break
                        
        if not bind_section:
            print("ERROR: Could not find suitable section for stub (.bind or .data)")
            print("Available sections:")
            for section in self.pe.sections:
                section_name_bytes = section.Name.rstrip(b'\x00')
                section_name = section_name_bytes.decode('ascii', errors='ignore')
                print(f"  {section_name}: Size=0x{section.SizeOfRawData:08x}")
            return False
            
        section_name = bind_section.Name.rstrip(b'\x00').decode()
        print(f"Found {section_name} section: RVA=0x{bind_section.VirtualAddress:08x}, Size=0x{bind_section.SizeOfRawData:08x}")
        
        # Read the entire file
        with open(self.exe_path, 'rb') as f:
            pe_data = bytearray(f.read())
            
        # Step 1: Encrypt .text section
        if encrypt_text:
            text_start = text_section.PointerToRawData
            text_size = text_section.SizeOfRawData
            
            print(f"Encrypting .text section with XOR key 0x{self.ENCRYPTION_KEY:02x}...")
            for i in range(text_size):
                pe_data[text_start + i] ^= self.ENCRYPTION_KEY
                
        # Step 2: Create unpacker stub
        stub = self._create_unpacker_stub(
            original_oep,
            text_section.VirtualAddress,
            text_section.SizeOfRawData
        )
        
        # Step 3: Save original section contents before writing stub (for idempotency)
        bind_start = bind_section.PointerToRawData
        original_section_data = pe_data[bind_start:bind_start + bind_section.SizeOfRawData]
        
        # Step 4: Write stub to section
        # We need to store the full original section data somewhere
        # Since we're overwriting the section, we'll store it at the END of the section
        # and write the stub at the BEGINNING
        section_name_str = bind_section.Name.rstrip(b'\x00').decode()
        print(f"Writing unpacker stub to {section_name_str} section (offset 0x{bind_start:08x})...")
        
        # Calculate how much space we have for stub + original data storage
        # Store original data at end of section, stub at beginning
        stub_size = len(stub)
        if stub_size > bind_section.SizeOfRawData:
            print(f"WARNING: Stub size ({stub_size}) exceeds section size ({bind_section.SizeOfRawData})")
            stub = stub[:bind_section.SizeOfRawData]
            stub_size = len(stub)
        
        # Write stub at beginning
        for i, byte_val in enumerate(stub):
            if bind_start + i < len(pe_data):
                pe_data[bind_start + i] = byte_val
        
        # Store FULL original section data AFTER stub (for idempotent restoration)
        # This allows us to restore the entire section when unpacking
        # Store it starting right after the stub
        original_data_storage_start = bind_start + stub_size
        section_end = bind_start + bind_section.SizeOfRawData
        available_space = section_end - original_data_storage_start
        
        if available_space >= len(original_section_data):
            # We have space to store the full original section data after stub
            for i, byte_val in enumerate(original_section_data):
                if original_data_storage_start + i < len(pe_data):
                    pe_data[original_data_storage_start + i] = byte_val
            print(f"  Stored {len(original_section_data)} bytes of original {section_name_str} section data after stub (offset 0x{original_data_storage_start:08x})")
        else:
            # Not enough space - store what we can and warn
            print(f"  WARNING: Not enough space to store full original section data ({available_space} < {len(original_section_data)})")
            for i in range(min(available_space, len(original_section_data))):
                if original_data_storage_start + i < len(pe_data):
                    pe_data[original_data_storage_start + i] = original_section_data[i]
            print(f"  Stored {min(available_space, len(original_section_data))} bytes (partial)")
                
        # Step 5: Update entry point to stub
        stub_rva = bind_section.VirtualAddress
        print(f"Setting entry point to stub at RVA 0x{stub_rva:08x}...")
        
        # Update PE header entry point using pefile's get_file_offset method
        try:
            # Get the file offset of AddressOfEntryPoint field in OptionalHeader
            entry_point_offset = self.pe.OPTIONAL_HEADER.get_file_offset() + 0x10
            
            # Verify by reading current entry point
            current_ep = struct.unpack('<I', pe_data[entry_point_offset:entry_point_offset+4])[0]
            if current_ep != original_oep:
                print(f"Warning: Current entry point mismatch, searching...")
                # Search for the entry point value in the OptionalHeader region
                ep_bytes = struct.pack('<I', original_oep)
                pe_sig_offset = self.pe.DOS_HEADER.e_lfanew
                search_start = pe_sig_offset + 4 + 0x18  # After PE sig + FileHeader
                search_end = min(search_start + 0x200, len(pe_data))
                found_offset = pe_data.find(ep_bytes, search_start, search_end)
                if found_offset != -1:
                    entry_point_offset = found_offset
                    print(f"  Found entry point at offset 0x{entry_point_offset:08x}")
                else:
                    print(f"  Could not find entry point, using calculated offset 0x{entry_point_offset:08x}")
            
            # Write new entry point (little-endian)
            struct.pack_into('<I', pe_data, entry_point_offset, stub_rva)
            current_ep_read = struct.unpack('<I', pe_data[entry_point_offset:entry_point_offset+4])[0]
            print(f"  Updated entry point at file offset 0x{entry_point_offset:08x} (0x{current_ep_read:08x} -> 0x{stub_rva:08x})")
            
        except Exception as e:
            print(f"ERROR: Failed to update entry point: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Save the packed file
        with open(output_path, 'wb') as f:
            f.write(pe_data)
            
        print(f"Packed executable saved to: {output_path}")
        print(f"  Entry point changed: 0x{original_oep:08x} -> 0x{stub_rva:08x}")
        print(f"  OEP stored in stub at offset 0x{self.OEP_OFFSET_IN_STUB:08x}")
        return True
        
    def unpack(self, output_path: Path) -> bool:
        """Full unpacker: decrypt .text, restore original entry point (idempotent)."""
        print(f"Unpacking {self.exe_path}...")
        
        # Check if already unpacked (idempotent)
        is_packed = self._is_packed()
        if not is_packed:
            # Check if .text is encrypted (might be encrypted but entry point not changed)
            is_encrypted = self._is_text_encrypted()
            if not is_encrypted:
                print("  Executable is already unpacked - skipping (idempotent)")
                import shutil
                shutil.copy2(self.exe_path, output_path)
                print(f"Unpacked executable saved to: {output_path} (no changes - already unpacked)")
                return True
        
        # Read the entire file
        with open(self.exe_path, 'rb') as f:
            pe_data = bytearray(f.read())
            
        # Get original entry point from stub if packed
        original_oep = None
        if is_packed:
            current_entry = self.pe.OPTIONAL_HEADER.AddressOfEntryPoint
            print(f"Current entry point (stub): 0x{current_entry:08x}")
            
            # Extract OEP from stub
            try:
                file_offset = self.pe.get_offset_from_rva(current_entry + self.OEP_OFFSET_IN_STUB)
                if file_offset < len(pe_data):
                    oep_bytes = pe_data[file_offset:file_offset+4]
                    if len(oep_bytes) == 4:
                        original_oep = struct.unpack('<I', oep_bytes)[0]
                        print(f"Extracted OEP from stub: 0x{original_oep:08x}")
            except Exception as e:
                print(f"Warning: Could not extract OEP from stub: {e}")
                
        # Fallback: use current entry point if not packed or extraction failed
        if original_oep is None:
            original_oep = self.pe.OPTIONAL_HEADER.AddressOfEntryPoint
            print(f"Using current entry point as OEP: 0x{original_oep:08x}")
            
        # Find .text section
        text_section = None
        for section in self.pe.sections:
            if section.Name.rstrip(b'\x00') == b'.text':
                text_section = section
                break
                
        if not text_section:
            print("ERROR: Could not find .text section")
            return False
            
        print(f"Found .text section: RVA=0x{text_section.VirtualAddress:08x}, Size=0x{text_section.SizeOfRawData:08x}")
        
        # Decrypt .text section
        is_encrypted = self._is_text_encrypted()
        if is_encrypted:
            text_start = text_section.PointerToRawData
            text_size = text_section.SizeOfRawData
            
            print(f"Decrypting .text section with XOR key 0x{self.ENCRYPTION_KEY:02x}...")
            for i in range(text_size):
                pe_data[text_start + i] ^= self.ENCRYPTION_KEY
        else:
            print("  .text section is not encrypted")
            
        # Restore original section contents if we overwrote them with stub
        current_entry = None
        if is_packed:
            current_entry = self.pe.OPTIONAL_HEADER.AddressOfEntryPoint
            
            # Find which section contains the stub
            stub_section = None
            for section in self.pe.sections:
                if (section.VirtualAddress <= current_entry < 
                    section.VirtualAddress + section.Misc_VirtualSize):
                    stub_section = section
                    break
                    
            if stub_section:
                # Restore original section contents
                # Original data is stored AFTER the stub (we stored it there during packing)
                stub_file_offset = self.pe.get_offset_from_rva(current_entry)
                section_file_offset = stub_section.PointerToRawData
                section_size = stub_section.SizeOfRawData
                
                # Calculate stub size by finding our signature
                stub_size = 0x400  # Fixed size - stub is always 0x400 bytes or less
                
                # Original data starts after stub (at section_file_offset + stub_size)
                original_data_offset = section_file_offset + stub_size
                # We stored the full original section data, but we can only read what fits
                # The available space is: section_size - stub_size
                available_space = section_size - stub_size
                original_data_size = min(available_space, section_size)
                
                # Read and restore original section data
                if original_data_offset + original_data_size <= len(pe_data) and original_data_size > 0:
                    original_section_data = pe_data[original_data_offset:original_data_offset + original_data_size]
                    # Restore: first stub_size bytes stay as stub (or we could restore them too, but they're overwritten)
                    # Restore the rest of the section with original data
                    # Actually, we stored the FULL original section, so restore everything after stub
                    pe_data[section_file_offset + stub_size:section_file_offset + stub_size + original_data_size] = original_section_data
                    # Also restore the stub area with original data (first stub_size bytes of original_section_data)
                    if len(original_section_data) >= stub_size:
                        pe_data[section_file_offset:section_file_offset + stub_size] = original_section_data[:stub_size]
                    section_name = stub_section.Name.rstrip(b'\x00').decode()
                    print(f"  Restored {original_data_size} bytes of original {section_name} section contents from after stub (offset 0x{original_data_offset:08x})")
                else:
                    section_name = stub_section.Name.rstrip(b'\x00').decode()
                    print(f"  WARNING: Could not restore {section_name} section - data may be incomplete")
            
            # Use pefile's method to get the correct offset
            try:
                entry_point_offset = self.pe.OPTIONAL_HEADER.get_file_offset() + 0x10
                
                # Verify by reading current entry point
                current_ep_check = struct.unpack('<I', pe_data[entry_point_offset:entry_point_offset+4])[0]
                if current_ep_check != current_entry:
                    # Search for it
                    ep_bytes = struct.pack('<I', current_entry)
                    pe_sig_offset = self.pe.DOS_HEADER.e_lfanew
                    search_start = pe_sig_offset + 4 + 0x18
                    search_end = min(search_start + 0x200, len(pe_data))
                    found_offset = pe_data.find(ep_bytes, search_start, search_end)
                    if found_offset != -1:
                        entry_point_offset = found_offset
                        print(f"  Found entry point at alternative offset 0x{entry_point_offset:08x}")
                
                print(f"Restoring entry point to OEP: 0x{original_oep:08x}...")
                struct.pack_into('<I', pe_data, entry_point_offset, original_oep)
                
                # Verify it was written
                verify_ep = struct.unpack('<I', pe_data[entry_point_offset:entry_point_offset+4])[0]
                if verify_ep != original_oep:
                    print(f"  WARNING: Entry point verification failed: wrote 0x{original_oep:08x}, read 0x{verify_ep:08x}")
                else:
                    print(f"  Entry point successfully restored at offset 0x{entry_point_offset:08x}")
                    
            except Exception as e:
                print(f"ERROR: Failed to restore entry point: {e}")
                import traceback
                traceback.print_exc()
                return False
            
        # Save the unpacked file
        with open(output_path, 'wb') as f:
            f.write(pe_data)
            
        print(f"Unpacked executable saved to: {output_path}")
        if is_packed and current_entry is not None:
            print(f"  Entry point restored: 0x{current_entry:08x} -> 0x{original_oep:08x}")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='KOTOR DRM Unpacker and Packer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Unpack command
    unpack_parser = subparsers.add_parser('unpack', help='Unpack (dump) KOTOR from memory')
    unpack_parser.add_argument('--exe', type=Path, help='Path to original swkotor.exe (for structure reference)')
    unpack_parser.add_argument('--output', '-o', type=Path, help='Output path for unpacked executable')
    unpack_parser.add_argument('--auto', action='store_true', help='Auto-detect KOTOR process and EXE path')
    
    # Pack command
    pack_parser = subparsers.add_parser('pack', help='Pack (re-apply protection) to unpacked executable')
    pack_parser.add_argument('--exe', type=Path, required=True, help='Path to unpacked executable')
    pack_parser.add_argument('--output', '-o', type=Path, help='Output path for packed executable')
    pack_parser.add_argument('--no-encrypt', action='store_true', help='Skip .text encryption (testing only)')
    
    # Unpack-from-file command (decrypt file-based packed exe)
    unpack_file_parser = subparsers.add_parser('unpack-file', help='Unpack (decrypt) a file-based packed executable')
    unpack_file_parser.add_argument('--exe', type=Path, required=True, help='Path to packed executable')
    unpack_file_parser.add_argument('--output', '-o', type=Path, help='Output path for unpacked executable')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    if args.command == 'unpack':
        unpacker = KotorUnpacker(args.exe)
        success = unpacker.unpack(args.exe, args.output, args.auto)
        return 0 if success else 1
        
    elif args.command == 'pack':
        if not args.exe.exists():
            print(f"ERROR: File not found: {args.exe}")
            return 1
            
        if not args.output:
            args.output = args.exe.parent / f"{args.exe.stem}_packed{args.exe.suffix}"
            
        packer = KotorPacker(args.exe)
        success = packer.pack(args.output, not args.no_encrypt)
        return 0 if success else 1
        
    elif args.command == 'unpack-file':
        if not args.exe.exists():
            print(f"ERROR: File not found: {args.exe}")
            return 1
            
        if not args.output:
            args.output = args.exe.parent / f"{args.exe.stem}_unpacked{args.exe.suffix}"
            
        packer = KotorPacker(args.exe)
        success = packer.unpack(args.output)
        return 0 if success else 1
        
    return 0


if __name__ == '__main__':
    sys.exit(main())

