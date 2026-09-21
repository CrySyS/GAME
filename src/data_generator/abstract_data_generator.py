from abc import ABC, abstractmethod
import random
from copy import deepcopy

class AbstractDataGenerator(ABC):
    
    @abstractmethod
    def generate_data(self, size: int) -> bytes:
        raise NotImplementedError("Subclasses must implement this method")
    
    
    def mutate(self):
        pass
    
    
    def crossover(self, other_generator: 'AbstractDataGenerator', weights: list) -> 'AbstractDataGenerator':
        """
        Combines two parent generators to create a child generator.
        The default implementation randomly selects one of the parents based on their weights.
        Subclasses can override this method to implement more complex crossover logic.
        """
        ds = self if random.choices([0, 1], weights=weights, k=1)[0] == 0 else other_generator
        return deepcopy(ds)


    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "parameters": self._parameters_to_dict()
        }
        
        
    @classmethod
    def create_random(cls) -> 'AbstractDataGenerator':
        return cls()
        
        
    def _parameters_to_dict(self) -> dict:
        return {}


    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'AbstractDataGenerator':
        return cls()

    

    
