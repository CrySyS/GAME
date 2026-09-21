import logging
from data_generator import AbstractDataGenerator
from elf_modifier import AbstractELFModifier
from insertion_ratio_sampler import AbstractInsertionRatioSampler
logger = logging.getLogger(__name__)

class Appender(AbstractELFModifier):
    
    
    def modify(self, input_file: bytes, ratio_sampler: AbstractInsertionRatioSampler, data_generator: AbstractDataGenerator) -> bytes:
        
        ratio = ratio_sampler.sample()
        file_size = len(input_file)
        nr_of_bytes = int(file_size * ratio)
        logger.debug(f"Appending {nr_of_bytes} bytes using {data_generator.__class__.__name__}")
        
        data_to_append = data_generator.generate_data(nr_of_bytes)
        modified_file = input_file + data_to_append
        logger.debug(f"Appended {data_to_append} bytes to file")
        logger.debug(f"New file size: {len(modified_file)} bytes (original {file_size} bytes)")
        return modified_file
        

    
if __name__ == "__main__":
    from config import LOGGING_CONFIG, DATA_DIR, OUTPUT_DIR
    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)
    FILE_NAME = "usr-bin-ls"
    ORIGINAL_FILE = DATA_DIR / FILE_NAME
    from data_generator import SequentialByteGenerator
    from insertion_ratio_sampler import UniformInsertionRatioSampler
    appender = Appender()
    input_bytes = open(ORIGINAL_FILE, "rb").read()
    advex_bytes = appender.modify(input_bytes, UniformInsertionRatioSampler(), SequentialByteGenerator())
    with open(OUTPUT_DIR / f"{FILE_NAME}.app", "wb") as f:
        f.write(advex_bytes) 
