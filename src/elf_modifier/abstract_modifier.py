from data_generator import AbstractDataGenerator
from insertion_ratio_sampler import AbstractInsertionRatioSampler

class AbstractELFModifier:
    
    
    def modify(self, input_file: bytes, ratio_sampler: AbstractInsertionRatioSampler, data_generator: AbstractDataGenerator) -> bytes:
        raise NotImplementedError("Subclasses must implement this method")
    
    
    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__
        }

    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'AbstractELFModifier':
        modifier = cls()
        return modifier

