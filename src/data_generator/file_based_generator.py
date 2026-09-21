import os
import random
import logging
import numpy as np
from pathlib import Path
from data_generator import AbstractDataGenerator

from config import BENIGN_DIR
logger = logging.getLogger(__name__)

_benign_files = [str(f) for f in BENIGN_DIR.iterdir()]


class SequentialFileDataGenerator(AbstractDataGenerator):
    def __init__(self, source_file: str , offset: int):
        self.source_file = source_file
        self.offset = offset
        # Do not load the entire source file into memory. Read on-demand in generate_data().
        self.source_file_size = os.path.getsize(self.source_file)


    def generate_data(self, size: int) -> bytes:
        # Read the requested slice from disk to avoid keeping large buffers in memory
        with open(self.source_file, "rb") as f:
            f.seek(self.offset)
            return f.read(size)
        
        
    def mutate(self):
        self.source_file = random.choice(_benign_files)
        self.source_file_size = os.path.getsize(self.source_file)
        self.offset = random.randint(0, max(0, self.source_file_size - 1))


    def _parameters_to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "offset": self.offset
        }

    @classmethod
    def create_random(cls) -> 'SequentialFileDataGenerator':
        source_file = random.choice(_benign_files)
        offset = random.randint(0, max(0, os.path.getsize(source_file) - 1))
        return cls(source_file=source_file, offset=offset)


    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'SequentialFileDataGenerator':
        parameters = saved_obj["parameters"]
        source_file = BENIGN_DIR / Path(parameters["source_file"]).name
        return cls(
            source_file=str(source_file),
            offset=parameters["offset"]
        )

    

class RandomBlockFileDataGenerator(AbstractDataGenerator):
    def __init__(self, source_file: str, num_blocks: int):
        self._rng = np.random.default_rng()
        self.source_file = source_file
        self.num_blocks = max(1, num_blocks)
        # Do not preload the source file into memory; keep its path and size and read blocks on demand.
        self.source_file_size = os.path.getsize(self.source_file)


    def generate_data(self, size: int) -> bytes:
        block_size = max(1, size // self.num_blocks)

        data_chunks = []
        bytes_generated = 0

        while bytes_generated < size:
            remaining_bytes = size - bytes_generated
            block_size = min(remaining_bytes, block_size)

            if self.source_file_size <= block_size:
                random_offset = 0
            else:
                random_offset = int(self._rng.integers(0, self.source_file_size - block_size))
            # Read chunk from disk
            with open(self.source_file, "rb") as f:
                f.seek(random_offset)
                chunk = f.read(block_size)
            data_chunks.append(chunk)
            bytes_generated += len(chunk)

        return b''.join(data_chunks)

        
    def mutate(self):
        self.source_file = self._rng.choice(_benign_files)
        self.source_file_size = os.path.getsize(self.source_file)
        self.num_blocks += self._rng.integers(-2, 3, dtype=int)  # Randomly increase or decrease the number of blocks
        self.num_blocks = max(1, self.num_blocks)  # Ensure at least one
        

    def _parameters_to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "num_blocks": self.num_blocks,
        }

    @classmethod
    def create_random(cls) -> 'RandomBlockFileDataGenerator':
        source_file = random.choice(_benign_files)
        num_blocks = random.randint(10, 50)
        return cls(source_file=source_file, num_blocks=num_blocks)

    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'RandomBlockFileDataGenerator':
        parameters = saved_obj["parameters"]
        source_file = BENIGN_DIR / Path(parameters["source_file"]).name
        return cls(
            source_file=str(source_file),
            num_blocks=parameters["num_blocks"],
        )


if __name__ == '__main__':
    from config import OUTPUT_DIR
    
    # --- Example of how to use these classes ---
    dummy_file_path = OUTPUT_DIR / "dummy_source.bin"
    
    # 1. Create a dummy file to act as our data source
    print(dummy_file_path)
    with open(dummy_file_path, "wb") as f:
        f.write(b"HEADER_DATA" + os.urandom(200) + b"FOOTER_DATA")
    
    print(f"Created a dummy source file: '{dummy_file_path}'")
    print("-" * 40)

    # 2. Test the sequential read class
    print("--- Testing Sequential Read ---")
    # Read 11 bytes from the very beginning (offset 0)
    seq_gen = SequentialFileDataGenerator(source_file=dummy_file_path, offset=0)
    header_data = seq_gen.generate_data(size=11)
    print(f"Read from offset 0: {header_data.decode()}")

    # Read 11 bytes from the end of the file
    file_len = os.path.getsize(dummy_file_path)
    seq_gen_end = SequentialFileDataGenerator(source_file=dummy_file_path, offset=file_len - 11)
    footer_data = seq_gen_end.generate_data(size=11)
    print(f"Read from offset {file_len - 11}: {footer_data.decode()}")
    print("-" * 40)


    # 3. Test the random block read class
    print("--- Testing Random Block Read ---")
    random_gen = RandomBlockFileDataGenerator(source_file=dummy_file_path, num_blocks=8)
    random_block_data = random_gen.generate_data(size=50)
    print(f"Generated 50 bytes from 8 random blocks.")
    print(f"Generated data (first 30 bytes): {random_block_data[:30]}")
    print(f"Total length of generated data: {len(random_block_data)}")
    print("-" * 40)
