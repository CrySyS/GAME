import lief
import io
import contextlib
from data_generator import AbstractDataGenerator
from elf_modifier import AbstractELFModifier
from insertion_ratio_sampler import AbstractInsertionRatioSampler
import logging
logger = logging.getLogger(__name__)


class PaddingOverwriter(AbstractELFModifier):
    

    def modify(self, input_file: bytes, ratio_sampler: AbstractInsertionRatioSampler, data_generator: AbstractDataGenerator) -> bytes:
        ratio = ratio_sampler.sample()
        file_size = len(input_file)
        nr_of_bytes = int(file_size * ratio)
        
        logger.debug(f"Targeting ~{nr_of_bytes} bytes using {data_generator.__class__.__name__}") 
        
        try:
            stderr_buffer = io.StringIO()
            with contextlib.redirect_stderr(stderr_buffer): # LIEF can be noisy, we capture its stderr output for debugging
                lief_adv: lief.ELF.Binary = lief.ELF.parse(input_file)
                logger.debug(f"LIEF parsing ... {stderr_buffer.getvalue().strip()}")
                    
                if not lief_adv:
                    logger.error("Error: Could not parse ELF file with LIEF. Returning original file.")
                    return input_file

                # Protect bytes that are mapped into memory by the loader.
                # Writing outside these ranges preserves runtime functionality.
                protected_ranges = []
                for seg in lief_adv.segments:
                    # Only PT_LOAD data participates in runtime memory image.
                    if seg.type == lief.ELF.Segment.TYPE.LOAD:
                        start = max(0, int(seg.file_offset))
                        end = min(file_size, int(seg.file_offset + seg.physical_size))
                        if end > start:
                            protected_ranges.append((start, end))
                logger.debug(f"Processing segments ... {stderr_buffer.getvalue().strip()}")

            protected_ranges.sort(key=lambda item: item[0])
            
            merged_protected = []
            for start, end in protected_ranges:
                if not merged_protected or start > merged_protected[-1][1]:
                    merged_protected.append([start, end])
                else:
                    merged_protected[-1][1] = max(merged_protected[-1][1], end)

            # Candidate overwrite ranges are bytes not loaded into memory.
            candidate_ranges = []
            cursor = 0
            for start, end in merged_protected:
                if cursor < start:
                    candidate_ranges.append((cursor, start))
                cursor = max(cursor, end)
            if cursor < file_size:
                candidate_ranges.append((cursor, file_size))

            total_capacity = sum(end - start for start, end in candidate_ranges)
            logger.debug(f"Found {len(candidate_ranges)} safe ranges totaling {total_capacity} bytes")

            remaining_bytes = int(nr_of_bytes)
            if total_capacity < remaining_bytes:
                logger.debug(
                    f"Requested {remaining_bytes} bytes but only {total_capacity} are safe to overwrite"
                )

            modified_data = bytearray(input_file)
            for start, end in candidate_ranges:
                if remaining_bytes <= 0:
                    break
                
                logger.debug(f"Overwriting range 0x{start:08x}-0x{end:08x} ({end - start} bytes)")

                region_size = end - start
                if region_size <= 0:
                    continue

                bytes_for_region = min(region_size, remaining_bytes)
                generated = data_generator.generate_data(bytes_for_region)
                inserted_bytes = min(len(generated), bytes_for_region)
                if inserted_bytes <= 0:
                    continue

                modified_data[start:start + inserted_bytes] = generated[:inserted_bytes]
                remaining_bytes -= inserted_bytes

            if remaining_bytes > 0:
                logger.debug(f"Skipped {remaining_bytes} requested bytes due to limited safe space")

            return bytes(modified_data)

            
        except Exception as e:
            logger.error(f"Generic error in modify: {e}. Returning original file.")
            return input_file
            

# TODO create statistics on the size of the gaps form malware files
if __name__ == "__main__":
    from config import LOGGING_CONFIG, DATA_DIR, OUTPUT_DIR, MALWARE_DIR
    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)
    FILE_NAME = "usr-bin-ls"
    ORIGINAL_FILE = DATA_DIR / FILE_NAME
    
    # FILE_NAME = "8b70c2ee00133a6aa0868ce46cd56331ac3a07b588c598863cf9f58f1f198697"
    # FILE_NAME = "fc02a9b9993525a448b392f7d3b0388c8ef8d30e6ceda8d6c91027aafb4a90e6"
    # ORIGINAL_FILE = MALWARE_DIR / FILE_NAME
    
    from data_generator import SequentialByteGenerator
    from insertion_ratio_sampler import UniformInsertionRatioSampler
    padding_overwriter = PaddingOverwriter()
    input_bytes = open(ORIGINAL_FILE, "rb").read()
    advex_bytes = padding_overwriter.modify(input_bytes, UniformInsertionRatioSampler(), SequentialByteGenerator())
    
    with open(OUTPUT_DIR / f"{FILE_NAME}.pad", "wb") as f:
        f.write(advex_bytes) 
    
