import math
from collections import Counter
import logging
import hashlib
logger = logging.getLogger(__name__)

# mathematically stable sigmoid function to avoid overflow errors
def _stable_sigmoid(value):
    if value >= 0:
        exponent = math.exp(-value)
        return 1 / (1 + exponent)

    exponent = math.exp(value)
    return exponent / (1 + exponent)


def file_entropy(data: bytes):
    counter = Counter(data)
    length = len(data)
    return -sum((count / length) * math.log2(count / length) for count in counter.values())


def sigmoid_norm_tlsh_diff(tlsh_diff):
    k = 0.05  # Steepness of the curve; adjust to control how quickly it saturates
    x0 = 125  # Midpoint of the sigmoid; adjust to control where the curve centers
    return _stable_sigmoid(k * (tlsh_diff - x0))


def sigmoid_norm_size_increase(size_increase_ratio):
    k = 10.0  # Steepness of the curve; adjust to control how quickly it saturates
    x0 = 0.5  # Midpoint of the sigmoid; adjust to control where the curve centers
    return _stable_sigmoid(-k * (size_increase_ratio - x0))


def sigmoid_norm_entropy_diff(entropy_diff):
    k = 8.0  # Steepness of the curve; adjust to control how quickly it saturates
    x0 = 0.75  # Midpoint of the sigmoid; adjust to control where the curve centers
    return _stable_sigmoid(-k * (entropy_diff - x0))


def sha256_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

