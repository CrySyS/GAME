from abc import ABC, abstractmethod
import random
from copy import deepcopy

class AbstractInsertionRatioSampler(ABC):

    @abstractmethod
    def sample(self) -> float:
        raise NotImplementedError("Subclasses must implement this method")
    
    
    def mutate(self):
        pass
    
    
    def crossover(self, other_sampler: 'AbstractInsertionRatioSampler', weights: list) -> 'AbstractInsertionRatioSampler':
        """
        Combines two parent samplers to create a child sampler.
        The default implementation randomly selects one of the parents based on their weights.
        Subclasses can override this method to implement more complex crossover logic.
        """
        rs = self if random.choices([0, 1], weights=weights, k=1)[0] == 0 else other_sampler
        return deepcopy(rs)


    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "parameters": self._parameters_to_dict()
        }
        
        
    def _parameters_to_dict(self) -> dict:
        return {}
        
        
    @classmethod
    def create_random(cls) -> 'AbstractInsertionRatioSampler':
        return cls()


    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'AbstractInsertionRatioSampler':
        return cls()