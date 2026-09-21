import lief
import io
import contextlib
import logging
from data_generator import AbstractDataGenerator
from elf_modifier import AbstractELFModifier
from insertion_ratio_sampler import AbstractInsertionRatioSampler
logger = logging.getLogger(__name__)


class SegmentInjector(AbstractELFModifier):
    

    def modify(self, input_file: bytes, ratio_sampler: AbstractInsertionRatioSampler, data_generator: AbstractDataGenerator) -> bytes:
        
        ratio = ratio_sampler.sample()
        nr_of_bytes = int(len(input_file) * ratio)
       
        logger.debug(f"Attempting to inject segment with target size {nr_of_bytes} bytes")
        
        try:
            stderr_buffer = io.StringIO()
            with contextlib.redirect_stderr(stderr_buffer): # LIEF can be noisy, we capture its stderr output for debugging
                lief_adv: lief.ELF.Binary = lief.ELF.parse(input_file)
                logger.debug(f"LIEF parsing ... {stderr_buffer.getvalue().strip()}")
                    
            if not lief_adv:
                logger.error("Error: Could not parse ELF file with LIEF. Returning original file.")
                return input_file
                
            # Generate content for the new segment
            segment_content_bytes = data_generator.generate_data(nr_of_bytes)

            # Create a new segment
            new_segment = lief.ELF.Segment()
            new_segment.type = lief.ELF.Segment.TYPE.LOAD
            new_segment.flags = lief.ELF.Segment.FLAGS.R | lief.ELF.Segment.FLAGS.W | lief.ELF.Segment.FLAGS.X
            new_segment.content = list(segment_content_bytes)
            added_segment_obj: lief.ELF.Segment = lief_adv.add(new_segment)

            if not added_segment_obj:
                logger.error("Error: LIEF failed to add segment. Returning original file.")
                return input_file

            builder = lief.ELF.Builder(lief_adv)
            builder.build()
            advex_bytes = bytes(builder.get_build())

            if not advex_bytes:
                logger.error("Error: LIEF returned empty build output. Returning original file.")
                return input_file
             
            # Accessing added segment content can fail on some binaries/LIEF versions.
            logger.debug(f"Injected new segment with target size {nr_of_bytes} bytes")
            return advex_bytes

        except Exception as e:
            logger.error(f"Generic error in elf_primitive_inject_segment: {e}. Returning original file.")
            return input_file


if __name__ == "__main__":
    from config import LOGGING_CONFIG, DATA_DIR, OUTPUT_DIR
    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)
    FILE_NAME = "usr-bin-ls"
    ORIGINAL_FILE = DATA_DIR / FILE_NAME
    
    from data_generator import SequentialByteGenerator
    from insertion_ratio_sampler import UniformInsertionRatioSampler
    segment_injector = SegmentInjector()
    input_bytes = open(ORIGINAL_FILE, "rb").read()
    advex_bytes = segment_injector.modify(input_bytes, UniformInsertionRatioSampler(), SequentialByteGenerator())
    with open(OUTPUT_DIR / f"{FILE_NAME}.seg", "wb") as f:
        f.write(advex_bytes)
    