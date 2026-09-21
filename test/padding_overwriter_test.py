#!/usr/bin/env python3
"""
Used for comparing the output of padding_overwriter.py, which uses LIEF library, with the output given by this script.

Find file intervals not covered by:
  • the ELF header
  • the program header table
  • any PT_LOAD (loadable) segment
"""

import struct
import sys


# ---------------------------------------------------------------------------
# ELF constants
# ---------------------------------------------------------------------------
ELFMAG = b'\x7fELF'

EI_CLASS   = 4   # 1 = 32-bit, 2 = 64-bit
EI_DATA    = 5   # 1 = little-endian, 2 = big-endian
PT_LOAD    = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_at(f, offset, size):
    f.seek(offset)
    data = f.read(size)
    if len(data) != size:
        raise ValueError(f"Short read at offset 0x{offset:x}: wanted {size}, got {len(data)}")
    return data


def gaps(covered: list[tuple[int, int]], file_size: int) -> list[tuple[int, int]]:
    """
    Given a list of (start, end) intervals (end is exclusive),
    return the intervals in [0, file_size) not covered by any of them.
    """
    merged = []
    for start, end in sorted(covered):
        start = max(0, start)
        end   = min(end, file_size)
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append([start, end])

    result = []
    prev = 0
    for start, end in merged:
        if prev < start:
            result.append((prev, start))
        prev = end
    if prev < file_size:
        result.append((prev, file_size))
    return result


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
def parse_elf(path: str):
    with open(path, 'rb') as f:
        # ── e_ident (16 bytes) ──────────────────────────────────────────────
        e_ident = read_at(f, 0, 16)
        if e_ident[:4] != ELFMAG:
            raise ValueError("Not an ELF file (bad magic bytes)")

        ei_class = e_ident[EI_CLASS]
        ei_data  = e_ident[EI_DATA]

        if ei_class == 1:
            bits = 32
        elif ei_class == 2:
            bits = 64
        else:
            raise ValueError(f"Unknown EI_CLASS: {ei_class}")

        if ei_data == 1:
            endian = '<'
        elif ei_data == 2:
            endian = '>'
        else:
            raise ValueError(f"Unknown EI_DATA: {ei_data}")

        # ── ELF header ──────────────────────────────────────────────────────
        if bits == 32:
            # Elf32_Ehdr  (52 bytes total)
            hdr_fmt  = endian + '2H5I6H'
            hdr_size = struct.calcsize(hdr_fmt)          # 36 bytes after e_ident
            raw = read_at(f, 16, hdr_size)
            (e_type, e_machine, e_version,
             e_entry, e_phoff, e_shoff, e_flags,
             e_ehsize, e_phentsize, e_phnum,
             e_shentsize, e_shnum, e_shstrndx) = struct.unpack(hdr_fmt, raw)
        else:
            # Elf64_Ehdr  (64 bytes total)
            hdr_fmt  = endian + '2HI3QI6H'
            hdr_size = struct.calcsize(hdr_fmt)          # 48 bytes after e_ident
            raw = read_at(f, 16, hdr_size)
            (e_type, e_machine, e_version,
             e_entry, e_phoff, e_shoff, e_flags,
             e_ehsize, e_phentsize, e_phnum,
             e_shentsize, e_shnum, e_shstrndx) = struct.unpack(hdr_fmt, raw)

        elf_header_end = e_ehsize          # == 52 (32-bit) or 64 (64-bit)

        # ── Program header table ────────────────────────────────────────────
        if e_phoff == 0 or e_phnum == 0:
            raise ValueError("No program header table found in this ELF file")

        pht_start = e_phoff
        pht_end   = e_phoff + e_phnum * e_phentsize

        # ── Parse each program header entry ─────────────────────────────────
        load_segments = []

        if bits == 32:
            ph_fmt  = endian + '8I'   # p_type, p_offset, p_vaddr, p_paddr,
                                      # p_filesz, p_memsz, p_flags, p_align
            ph_size = struct.calcsize(ph_fmt)
        else:
            ph_fmt  = endian + '2I6Q' # p_type, p_flags, p_offset, p_vaddr,
                                      # p_paddr, p_filesz, p_memsz, p_align
            ph_size = struct.calcsize(ph_fmt)

        for i in range(e_phnum):
            ph_raw = read_at(f, e_phoff + i * e_phentsize, ph_size)
            if bits == 32:
                (p_type, p_offset, p_vaddr, p_paddr,
                 p_filesz, p_memsz, p_flags, p_align) = struct.unpack(ph_fmt, ph_raw)
            else:
                (p_type, p_flags, p_offset, p_vaddr,
                 p_paddr, p_filesz, p_memsz, p_align) = struct.unpack(ph_fmt, ph_raw)

            if p_type == PT_LOAD and p_filesz > 0:
                load_segments.append((p_offset, p_offset + p_filesz))

        # ── File size ────────────────────────────────────────────────────────
        f.seek(0, 2)
        file_size = f.tell()

    # ── Collect covered intervals ────────────────────────────────────────────
    covered = []
    covered.append((0, elf_header_end))                   # ELF header
    covered.append((pht_start, pht_end))                  # Program header table
    for seg in load_segments:
        covered.append(seg)                               # Each PT_LOAD segment

    gap_list = gaps(covered, file_size)

    # ── Report ───────────────────────────────────────────────────────────────
    print(f"ELF file : {path}")
    print(f"Class    : ELF{bits}")
    print(f"Endian   : {'little' if endian == '<' else 'big'}")
    print(f"File size: {file_size} bytes  (0x{file_size:x})")
    print()

    print("── Covered regions ─────────────────────────────────────────────")
    print(f"  ELF header          : [0x{0:08x}, 0x{elf_header_end:08x})  ({elf_header_end} bytes)")
    print(f"  Program header table: [0x{pht_start:08x}, 0x{pht_end:08x})  ({pht_end - pht_start} bytes)")
    for idx, (s, e) in enumerate(load_segments):
       print(f"  PT_LOAD segment {idx:<3d} : [0x{s:08x}, 0x{e:08x})  ({e - s} bytes)")
    print()

    #print("── Gap intervals (not covered by any of the above) ─────────────")
    if not gap_list:
        print("  (none — the file is fully covered)")
        pass
    else:
        total_gap = 0
        for s, e in gap_list:
            size = e - s
            total_gap += size
            print(f"  [0x{s:08x}, 0x{e:08x}]  ({size} bytes)")
        print(f"\n  Total gap: {total_gap} bytes  (0x{total_gap:x})")

    return gap_list, file_size


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <elf-file>")
        sys.exit(1)
    try:
        parse_elf(sys.argv[1])
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
