from elf_modifier import *
from insertion_ratio_sampler import *
from data_generator import *


AVAILABLE_ELF_MODIFIERS = [
    Appender, 
    PaddingOverwriter,
    SegmentInjector,
]

AVAILABLE_INSERTION_RATIO_SAMPLERS = [
    UniformInsertionRatioSampler,
    LogNormalInsertionRatioSampler,
    BetaInsertionRatioSampler
]

AVAILABLE_DATA_GENERATORS = [
    UniformByteGenerator,
    SequentialByteGenerator,
    NormalDistByteGenerator,
    GammaDistByteGenerator,
    WeibullDistByteGenerator,
    SequentialFileDataGenerator,
    RandomBlockFileDataGenerator
]


            
            