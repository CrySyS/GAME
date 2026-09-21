import random
from genetic import AVAILABLE_ELF_MODIFIERS, AVAILABLE_INSERTION_RATIO_SAMPLERS, AVAILABLE_DATA_GENERATORS
from typing import Tuple
from data_generator import AbstractDataGenerator
from elf_modifier import AbstractELFModifier
from insertion_ratio_sampler import AbstractInsertionRatioSampler
from copy import deepcopy


class Gene:
    """
    Represents a single step in a modification strategy.
    """
    
    def __init__(self, elf_modifier: AbstractELFModifier, ratio_sampler: AbstractInsertionRatioSampler, data_generator: AbstractDataGenerator, ):
        self.elf_modifier: AbstractELFModifier = elf_modifier
        self.ratio_sampler: AbstractInsertionRatioSampler = ratio_sampler
        self.data_generator: AbstractDataGenerator = data_generator
        
        
    def execute(self, input_file: bytes) -> Tuple[bytes, int]:
        return self.elf_modifier.modify(input_file, self.ratio_sampler, self.data_generator)


    @classmethod
    def create_random(cls):
        ELFModifierClass = random.choice(AVAILABLE_ELF_MODIFIERS)
        InsertionRatioSamplerClass = random.choice(AVAILABLE_INSERTION_RATIO_SAMPLERS)
        DataGeneratorClass = random.choice(AVAILABLE_DATA_GENERATORS)
        elf_modifier = ELFModifierClass()
        ratio_sampler = InsertionRatioSamplerClass.create_random()
        data_generator = DataGeneratorClass.create_random()
        return cls(elf_modifier, ratio_sampler, data_generator)
    
    
    def _crossover(self, parent1: 'Gene', parent2: 'Gene', weights: list) -> 'Gene':
        
        # Select the ELF modifier based on weighted random choice
        em = deepcopy(parent1.elf_modifier) if random.choices([0, 1], weights=weights, k=1)[0] == 0 else deepcopy(parent2.elf_modifier) 
        
        rs = parent1.ratio_sampler.crossover(parent2.ratio_sampler, weights=weights)
        dg = parent1.data_generator.crossover(parent2.data_generator, weights=weights)
        
        return Gene(elf_modifier=em, ratio_sampler=rs, data_generator=dg)
    
    
    def crossover(self, other_gene: 'Gene', weights: list) -> 'Gene':
        return self._crossover(self, other_gene, weights)
        

    def mutate(self, mutation_chances : dict) -> bool:
        rand_val = random.random()
        mutated = False
        
        if rand_val < mutation_chances["ratio_sampler"]:
            self.ratio_sampler.mutate()
            mutated = True
            
        if rand_val < mutation_chances["data_generator"]:
            self.data_generator.mutate()
            mutated = True
        
        return mutated


    def __str__(self):
        return (
            f"({self.elf_modifier.__class__.__name__}, "
            f"{self.ratio_sampler.__class__.__name__}, "
            f"{self.data_generator.__class__.__name__})"
        )


    def to_dict(self):
        return {
            "elf_modifier": self.elf_modifier.to_dict(),
            "ratio_sampler": self.ratio_sampler.to_dict(),
            "data_generator": self.data_generator.to_dict(),
        }


    @classmethod
    def from_dict(cls, saved_obj):
        def resolve_class(classes, class_name):
            return next(klass for klass in classes if klass.__name__ == class_name)

        modifier_payload = saved_obj["elf_modifier"]
        ratio_sampler_payload = saved_obj["ratio_sampler"]
        generator_payload = saved_obj["data_generator"]

        elf_modifier = resolve_class(AVAILABLE_ELF_MODIFIERS, modifier_payload["type"]).from_dict(modifier_payload)
        ratio_sampler = resolve_class(AVAILABLE_INSERTION_RATIO_SAMPLERS, ratio_sampler_payload["type"]).from_dict(ratio_sampler_payload)
        data_generator = resolve_class(AVAILABLE_DATA_GENERATORS, generator_payload["type"]).from_dict(generator_payload)

        return cls(elf_modifier, ratio_sampler, data_generator)


