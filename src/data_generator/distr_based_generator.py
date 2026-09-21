import random, math
import numpy as np
from data_generator import AbstractDataGenerator


class UniformByteGenerator(AbstractDataGenerator):
    def __init__(self):
        self._rng = np.random.default_rng()

    def generate_data(self, size: int) -> bytes:
        """Generates a block of random bytes uniformly distributed between 0 and 255."""
        return self._rng.integers(0, 256, size=size, dtype=np.uint8).tobytes()

    
class SequentialByteGenerator(AbstractDataGenerator):
    def generate_data(self, size: int) -> bytes:
        """Generates a block of sequential bytes (e.g., 0, 1, 2...)."""
        return bytes(i % 256 for i in range(size))


class NormalDistByteGenerator(AbstractDataGenerator):
    """
        Generates random bytes with a bounded discrete distribution based on a discretized normal distribution.

        Parameters:
            mean: Initial value for the mean.
            variance: Initial value for the variance.
        """
    def __init__(self, mean=128, variance=1024):
        self.mean = mean 
        self.variance = variance
        self._rng = np.random.default_rng()
        
        
    def generate_data(self, size: int) -> bytes:
        """
        Generates a block of random bytes with a normal distribution.

        Args:
            size: Number of random bytes to generate.

        Returns:
            A list of integers in range 0-255 representing random bytes.
        """
        samples = self._rng.normal(loc=self.mean, scale=math.sqrt(self.variance), size=size)
        clipped_samples = np.clip(samples, 0, 255).astype(np.uint8) # Clip to byte range and convert to integers
        return bytes(clipped_samples.tolist())
    
    
    def mutate(self):
        self.mean += self._rng.uniform(-10, 10)
        self.mean = max(0.1, self.mean)  # Ensure mean stays positive
        self.variance += self._rng.uniform(-20, 20)
        self.variance = max(0.1, self.variance)  # Ensure variance stays positive
        
        
    def crossover(self, other_generator: 'NormalDistByteGenerator', weights: list) -> 'NormalDistByteGenerator':
        """
        Averages the parameters of two parent generators to create a child generator.
        """
        if not isinstance(other_generator, NormalDistByteGenerator):
            return super().crossover(other_generator, weights)

        mean = np.average([self.mean, other_generator.mean], weights=weights)
        variance = np.average([self.variance, other_generator.variance], weights=weights)
        return NormalDistByteGenerator(mean=mean, variance=variance)


    def _parameters_to_dict(self) -> dict:
        return {
            "mean": self.mean,
            "variance": self.variance,
        }
        
        
    @classmethod
    def create_random(cls) -> 'NormalDistByteGenerator':
        mean = random.uniform(0, 255)
        variance = random.uniform(1, 10000)
        return cls(mean=mean, variance=variance)


    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'NormalDistByteGenerator':
        parameters = saved_obj["parameters"]
        generator = cls(mean=parameters["mean"], variance=parameters["variance"])
        return generator
    

class GammaDistByteGenerator(AbstractDataGenerator):
    """
    Generates random bytes with a bounded discrete distribution based on a
    discretized gamma distribution.

    Parameters:
        shape: Initial value for the shape parameter.
        scale: Initial value for the scale parameter.
        
    """
    def __init__(self, shape=2.0, scale=20.0):
        self.shape = shape
        self.scale = scale
        self._rng = np.random.default_rng()


    def generate_data(self, size: int) -> bytes:
        """
        Generates a block of random bytes with a gamma distribution.

        Args:
            size: Number of random bytes to generate.

        Returns:
            A bytes object of random bytes with gamma distribution.
        """
        
        samples = self._rng.gamma(shape=self.shape, scale=self.scale, size=size)
        clipped_samples = np.clip(samples, 0, 255).astype(np.uint8) # Clip to byte range and convert to integers
        return bytes(clipped_samples.tolist())
    
    
    def mutate(self):
        self.shape += self._rng.uniform(-0.5, 0.5)
        self.shape = max(0.1, self.shape)  # Ensure shape stays positive
        self.scale += self._rng.uniform(-5, 5)
        self.scale = max(0.1, self.scale)  # Ensure scale stays positive
        
        
    def crossover(self, other_generator: 'GammaDistByteGenerator', weights: list) -> 'GammaDistByteGenerator':
        """
        Averages the parameters of two parent generators to create a child generator.
        """
        if not isinstance(other_generator, GammaDistByteGenerator):
            return super().crossover(other_generator, weights)

        shape = np.average([self.shape, other_generator.shape], weights=weights)
        scale = np.average([self.scale, other_generator.scale], weights=weights)
        return GammaDistByteGenerator(shape=shape, scale=scale)
        
        
    def _parameters_to_dict(self) -> dict:
        return {
            "shape": self.shape,
            "scale": self.scale,
        }
        
        
    @classmethod
    def create_random(cls) -> 'GammaDistByteGenerator':
        shape = random.uniform(0.1, 10.0)
        scale = random.uniform(1.0, 100.0)
        return cls(shape=shape, scale=scale)


    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'GammaDistByteGenerator':
        parameters = saved_obj["parameters"]
        generator = cls(shape=parameters["shape"], scale=parameters["scale"])
        return generator


class WeibullDistByteGenerator(AbstractDataGenerator):
    """
    Generates random bytes with a bounded discrete distribution
    based on a discretized Weibull distribution.

    Parameters:
        shape: Initial value for the shape parameter.
        scale: Initial value for the scale parameter.
    """
    def __init__(self, shape=1.5, scale=10.0):
        self.shape = shape
        self.scale = scale
        self._rng = np.random.default_rng()


    def generate_data(self, size: int) -> bytes:
        """
        Generates a block of random bytes with a Weibull distribution.

        Args:
            size: Number of random bytes to generate.

        Returns:
            A bytes object of random bytes with Weibull distribution.
        """
        samples = self._rng.weibull(a=self.shape, size=size) * self.scale
        clipped_samples = np.clip(samples, 0, 255).astype(np.uint8) # Clip to byte range and convert to integers
        return bytes(clipped_samples.tolist())
    
    
    def mutate(self):
        self.shape += self._rng.uniform(-0.5, 0.5)
        self.shape = max(0.1, self.shape)  # Ensure shape stays positive
        self.scale += self._rng.uniform(-5, 5)
        self.scale = max(0.1, self.scale)  # Ensure scale stays positive
        
        
    def crossover(self, other_generator: 'WeibullDistByteGenerator', weights: list) -> 'WeibullDistByteGenerator':
        """
        Averages the parameters of two parent generators to create a child generator.
        """
        if not isinstance(other_generator, WeibullDistByteGenerator):
            return super().crossover(other_generator, weights)

        shape = np.average([self.shape, other_generator.shape], weights=weights)
        scale = np.average([self.scale, other_generator.scale], weights=weights)
        return WeibullDistByteGenerator(shape=shape, scale=scale)
    

    def _parameters_to_dict(self) -> dict:
        return {
            "shape": self.shape,
            "scale": self.scale,
        }
        
        
    @classmethod
    def create_random(cls) -> 'WeibullDistByteGenerator':
        shape = random.uniform(0.1, 5.0)
        scale = random.uniform(1.0, 100.0)
        return cls(shape=shape, scale=scale)


    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'WeibullDistByteGenerator':
        parameters = saved_obj["parameters"]
        generator = cls(shape=parameters["shape"], scale=parameters["scale"])
        return generator

    