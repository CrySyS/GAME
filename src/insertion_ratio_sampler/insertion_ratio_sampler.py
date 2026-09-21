from insertion_ratio_sampler import AbstractInsertionRatioSampler
import numpy as np
import random

MAX_INSERTION_RATIO = 1.0

class UniformInsertionRatioSampler(AbstractInsertionRatioSampler):
    
    def __init__(self, min_ratio: float = 0.0, max_ratio: float = 1.0):
        """
        Initializes the UniformInsertionRatioSampler with specified minimum and maximum ratios.
        """
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio
        self._rng = np.random.default_rng()
    
    
    def sample(self) -> float:
        """Sample a ratio uniformly between min_ratio and max_ratio."""
        return min(self._rng.uniform(self.min_ratio, self.max_ratio), MAX_INSERTION_RATIO)  # Ensure the ratio does not exceed the maximum allowed value
    
    
    def mutate(self):
        """Mutate the min_ratio and max_ratio slightly."""
        self.min_ratio += self._rng.uniform(-0.05, 0.05)
        self.max_ratio += self._rng.uniform(-0.05, 0.05)
        
        # Ensure min_ratio is less than max_ratio and both are >= 0
        self.min_ratio = max(0.0, min(self.min_ratio, self.max_ratio - 0.01))
        self.max_ratio = max(self.min_ratio + 0.01, self.max_ratio)
        
        
    def crossover(self, other_sampler: 'UniformInsertionRatioSampler', weights: list) -> 'UniformInsertionRatioSampler':
        """
        Averages the min_ratio and max_ratio of two parent samplers to create a child sampler.
        """
        if not isinstance(other_sampler, UniformInsertionRatioSampler):
            return super().crossover(other_sampler, weights)
        
        min_ratio = np.average([self.min_ratio, other_sampler.min_ratio], weights=weights)
        max_ratio = np.average([self.max_ratio, other_sampler.max_ratio], weights=weights)
        return UniformInsertionRatioSampler(min_ratio=min_ratio, max_ratio=max_ratio)
    
        
    def _parameters_to_dict(self) -> dict:
        return {
            "min_ratio": self.min_ratio,
            "max_ratio": self.max_ratio,
        }
        
        
    @classmethod
    def create_random(cls) -> 'UniformInsertionRatioSampler':
        r1 = random.uniform(0.0, 1.0)
        r2 = random.uniform(0.0, 1.0)
        min_ratio = min(r1, r2)
        max_ratio = max(r1, r2)
        return cls(min_ratio=min_ratio, max_ratio=max_ratio)
    
    
    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'UniformInsertionRatioSampler':
        parameters = saved_obj["parameters"]
        sampler = cls(min_ratio=parameters["min_ratio"], max_ratio=parameters["max_ratio"])
        return sampler
    
    
    
class LogNormalInsertionRatioSampler(AbstractInsertionRatioSampler):
    def __init__(self, mean: float = -1.8, sigma: float = 0.5):
        """
        Initializes the LogNormalInsertionRatioSampler with specified mean and sigma.
        """
        self.mean = mean
        self.sigma = sigma
        self._rng = np.random.default_rng()
        
    
    def sample(self) -> float:
        """Sample a ratio from a log-normal distribution."""
        ratio =  self._rng.lognormal(mean=self.mean, sigma=self.sigma)
        return min(ratio, MAX_INSERTION_RATIO)  # Ensure the ratio does not exceed the maximum allowed value


    def mutate(self):
        """Mutate the mean and sigma slightly."""
        self.mean += self._rng.uniform(-0.05, 0.05)
        self.sigma += self._rng.uniform(-0.05, 0.05)
        
        # Ensure sigma stay positive
        self.sigma = max(0.01, self.sigma)
        
        
    def crossover(self, other_sampler: 'LogNormalInsertionRatioSampler', weights: list) -> 'LogNormalInsertionRatioSampler':
        """
        Averages the mean and sigma of two parent samplers to create a child sampler.
        """
        if not isinstance(other_sampler, LogNormalInsertionRatioSampler):
            return super().crossover(other_sampler, weights)
        
        mean = np.average([self.mean, other_sampler.mean], weights=weights)
        sigma = np.average([self.sigma, other_sampler.sigma], weights=weights)
        return LogNormalInsertionRatioSampler(mean=mean, sigma=sigma)


    def _parameters_to_dict(self) -> dict:
        return {
            "mean": self.mean,
            "sigma": self.sigma,
        }
        
        
    @classmethod
    def create_random(cls) -> 'LogNormalInsertionRatioSampler':
        mean = random.uniform(-3.0, -1.2)
        sigma = random.uniform(0.1, 0.9)
        return cls(mean=mean, sigma=sigma)
    
    
    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'LogNormalInsertionRatioSampler':
        parameters = saved_obj["parameters"]
        sampler = cls(mean=parameters["mean"], sigma=parameters["sigma"])
        return sampler


class BetaInsertionRatioSampler(AbstractInsertionRatioSampler):
    def __init__(self, alpha: float = 2.0, beta: float = 8.0):
        """
        Initializes the BetaInsertionRatioSampler with specified alpha and beta.
        """
        self.alpha = alpha
        self.beta = beta
        self._rng = np.random.default_rng()


    def sample(self) -> float:
        """Sample a ratio from a beta distribution."""
        return self._rng.beta(self.alpha, self.beta) # always returns a value in [0, 1], so no need to clamp to MAX_INSERTION_RATIO


    def mutate(self):
        """Mutate the alpha and beta parameters slightly."""
        self.alpha += self._rng.uniform(-0.25, 0.25)
        self.beta += self._rng.uniform(-0.25, 0.25)

        # Ensure alpha and beta stay positive
        self.alpha = max(0.01, self.alpha)
        self.beta = max(0.01, self.beta)


    def crossover(self, other_sampler: 'BetaInsertionRatioSampler', weights: list) -> 'BetaInsertionRatioSampler':
        """
        Averages the alpha and beta parameters of two parent samplers to create a child sampler.
        """
        if not isinstance(other_sampler, BetaInsertionRatioSampler):
            return super().crossover(other_sampler, weights)

        alpha = np.average([self.alpha, other_sampler.alpha], weights=weights)
        beta = np.average([self.beta, other_sampler.beta], weights=weights)
        return BetaInsertionRatioSampler(alpha=alpha, beta=beta)
    
    
    def _parameters_to_dict(self) -> dict:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
        }


    @classmethod
    def create_random(cls) -> 'BetaInsertionRatioSampler':
        alpha = random.uniform(0.5, 4.0)
        beta = random.uniform(2.0, 12.0)
        return cls(alpha=alpha, beta=beta)


    @classmethod
    def from_dict(cls, saved_obj: dict) -> 'BetaInsertionRatioSampler':
        parameters = saved_obj["parameters"]
        sampler = cls(alpha=parameters["alpha"], beta=parameters["beta"])
        return sampler
    

    