"""
Script to compare modified ELF files at byte level.
Useful for checking if multiple runs of the same strategy produce identical results.
"""

import os
import hashlib
from pathlib import Path
from typing import List, Tuple, Dict


def get_file_hash(file_path: str) -> str:
    """
    Calculates SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hex string of SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compare_files(file1: str, file2: str) -> Tuple[bool, Dict]:
    """
    Compares two files at byte level.
    
    Args:
        file1: Path to first file
        file2: Path to second file
    
    Returns:
        Tuple of (are_identical: bool, details: dict with metadata)
    """
    file1 = Path(file1)
    file2 = Path(file2)
    
    if not file1.exists():
        raise FileNotFoundError(f"File not found: {file1}")
    if not file2.exists():
        raise FileNotFoundError(f"File not found: {file2}")
    
    size1 = file1.stat().st_size
    size2 = file2.stat().st_size
    
    details = {
        "file1": str(file1),
        "file2": str(file2),
        "size1": size1,
        "size2": size2,
        "size_match": size1 == size2,
    }
    
    # Quick size check
    if size1 != size2:
        details["identical"] = False
        details["difference"] = f"File sizes differ: {size1} vs {size2} bytes"
        return False, details
    
    # Hash comparison
    hash1 = get_file_hash(str(file1))
    hash2 = get_file_hash(str(file2))
    details["hash1"] = hash1
    details["hash2"] = hash2
    
    if hash1 != hash2:
        details["identical"] = False
        details["difference"] = "File hashes differ (byte-level differences exist)"
        return False, details
    
    details["identical"] = True
    return True, details


def compare_multiple_files(folder: str) -> Dict:
    """
    Compares multiple files and reports which ones are identical.
    
    Args:
        folder: Path to folder containing files to compare
    
    Returns:
        Dictionary with comparison results
    """
    folder = Path(folder)
    if not folder.exists() or not folder.is_dir():
        raise ValueError("Provided path is not a valid directory")

    file_paths = [f for f in folder.iterdir() if f.is_file()]
    if len(file_paths) < 2:
        raise ValueError("Need at least 2 files to compare")
    
    file_paths = [Path(p) for p in file_paths]
    for p in file_paths:
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")
    
    # Get hashes for all files
    hashes = {}
    for file_path in file_paths:
        hashes[str(file_path)] = get_file_hash(str(file_path))
    
    # Group files by hash
    hash_to_files = {}
    for file_path, file_hash in hashes.items():
        if file_hash not in hash_to_files:
            hash_to_files[file_hash] = []
        hash_to_files[file_hash].append(file_path)
    
    # Report results
    results = {
        "total_files": len(file_paths),
        "unique_hashes": len(hash_to_files),
        "groups": hash_to_files,
    }
    
    if len(hash_to_files) == 1:
        results["summary"] = "All files are identical at byte level"
    else:
        results["summary"] = f"Files have {len(hash_to_files)} different versions"
    
    return results


def print_comparison_result(identical: bool, details: Dict):
    """Pretty prints comparison results."""
    print(f"\n{'='*60}")
    print(f"File Comparison Results")
    print(f"{'='*60}")
    print(f"File 1: {details['file1']}")
    print(f"File 2: {details['file2']}")
    print(f"Size 1: {details['size1']} bytes")
    print(f"Size 2: {details['size2']} bytes")
    print(f"Size Match: {details['size_match']}")
    
    if "hash1" in details:
        print(f"\nHash 1: {details['hash1']}")
        print(f"Hash 2: {details['hash2']}")
    
    print(f"\nIdentical: {identical}")
    if not identical and "difference" in details:
        print(f"Difference: {details['difference']}")
    print(f"{'='*60}\n")


def print_multiple_comparison(results: Dict):
    """Pretty prints multiple file comparison results."""
    print(f"\n{'='*60}")
    print(f"Multiple File Comparison Results")
    print(f"{'='*60}")
    print(f"Total Files: {results['total_files']}")
    print(f"Unique Versions: {results['unique_hashes']}")
    print(f"Summary: {results['summary']}")
    
    print(f"\nGrouped by Hash:")
    for idx, (file_hash, files) in enumerate(results['groups'].items(), 1):
        print(f"\n  Version {idx} (Hash: {file_hash[:16]}...):")
        for file_path in files:
            print(f"    - {file_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python elf_compare.py <file1> <file2>")
        print("   or: python elf_compare.py <folder>")
        sys.exit(1)
        
    if len(sys.argv) == 2:
        folder = sys.argv[1]
        try:
            results = compare_multiple_files(folder)
            print_multiple_comparison(results)
        except Exception as e:
            print(f"Error: {e}")
    elif len(sys.argv) == 3:
        file1 = sys.argv[1]
        file2 = sys.argv[2]
        try:
            identical, details = compare_files(file1, file2)
            print_comparison_result(identical, details)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Invalid arguments. Provide either 2 file paths or a single folder path.")
        sys.exit(1)
