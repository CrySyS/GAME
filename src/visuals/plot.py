import random
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

from utils import *
from config import MALWARE_DIR, BENIGN_DIR, OUTPUT_DIR
from data_generator import *
from genetic import AVAILABLE_ELF_MODIFIERS

import logging
logger = logging.getLogger(__name__)

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman"]

def plot_history(ga, input_file_name:str):
    cmap = dict(zip(
        (modifier.__name__ for modifier in AVAILABLE_ELF_MODIFIERS),
        sns.color_palette(("green", "blue", "red")),
    ))
    # Keep strategy types visually separated with a small fixed offset and jitter.
    x_offsets = {
        "Appender": -0.22,
        "PaddingOverwriter": 0.0,
        "SegmentInjector": 0.22,
    }
    jitter_scale = 0.1
    plt.figure(figsize=(15, 5))
    for gen_num, (strat,fitness_scores) in enumerate(ga.history):
        base_generation = gen_num + 1
        generation_axis = np.array([
            base_generation + x_offsets[s] + random.uniform(-jitter_scale, jitter_scale)
            for s in strat
        ])
        
        colors = [cmap[s] for s in strat]

        plt.scatter(
            generation_axis,
            fitness_scores,
            c=colors,
            s=10,
            alpha=0.5,
            edgecolor='none'
        )

    generations = range(1, len(ga.history) + 1)
    
    plt.plot(generations, [np.mean(fitnesses) for _, fitnesses in ga.history], color = 'gray', ls = '--' , marker = 's',label='Average Fitness', linewidth=2,alpha=0.8,)

    plt.plot(generations,[10]*len(ga.history)) # detection line

    plt.title('Population Fitness Over Generations', fontsize=16)
    plt.xlabel('Generation', fontsize=14)
    plt.ylabel('Fitness Score', fontsize=14)
    plt.xticks(generations, fontsize=12)
    plt.yticks(fontsize=12)
    ax = plt.gca()
    ax.set_xlim(0.5, len(ga.history)+0.5)
    if len(ga.history) > 1:
        midpoints = np.arange(1.5, len(ga.history) + 0.5, 1.0)
        ax.set_xticks(midpoints, minor=True)
    plt.legend()
    ax.grid(True, axis='y', linestyle='--', alpha=0.6)
    ax.grid(True, which='minor', axis='x', linestyle='--', alpha=0.4)
    
    handles = [plt.Line2D([], [], color=color, marker='o', linestyle='', label=name)
            for name, color in cmap.items()]
    handles.append(plt.Line2D([], [], color='gray', linestyle='--', label='Avg Fitness'))
    handles.append(plt.Line2D([], [], color='blue', linestyle='-', label='Detection Threshold'))
    plt.legend(handles=handles, loc='best', fontsize=12)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{input_file_name}.png", dpi=300)
    logger.info(f"Fitness distribution plot saved to {OUTPUT_DIR / f'{input_file_name}.png'}")


def plot_target_bytes_distribution(samples: int = 1000):
    from insertion_ratio_sampler import BetaInsertionRatioSampler, LogNormalInsertionRatioSampler, UniformInsertionRatioSampler
    sampler = BetaInsertionRatioSampler()
    distribution = [sampler.sample() for _ in range(samples)]
    print(f"Mean ratio: {np.mean(distribution)}, Median ratio: {np.median(distribution)}, Min ratio: {np.min(distribution)}, Max ratio: {np.max(distribution)}")
    
    plt.hist(distribution, bins=100)
    plt.title("Distribution of Insertion Ratios", fontsize=16)
    plt.xlabel("Ratio", fontsize=14)
    plt.ylabel("Frequency", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.show()
    
    
def plot_sigmoid_norm_tlsh_diff():
    print(f"In 0-40 range, sigmoid_norm_tlsh_diff(0)={sigmoid_norm_tlsh_diff(0)}, sigmoid_norm_tlsh_diff(40)={sigmoid_norm_tlsh_diff(40)}")
    xs = np.linspace(0, 250, 100) 
    ys = np.vectorize(sigmoid_norm_tlsh_diff)(xs)
    plt.figure(figsize=(6,4))
    plt.plot(xs, ys, label='sigmoid_norm_tlsh_diff', linewidth=2)
    plt.axvline(40, color='gray', linestyle='--', alpha=0.6)
    plt.axvline(86, color='gray', linestyle='--', alpha=0.6)
    plt.axvline(144, color='gray', linestyle='--', alpha=0.6)
    plt.xlabel('TLSH Difference', fontsize=14)
    plt.ylabel('Normalized Value', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.title('TLSH Difference Normalization', fontsize=16)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "tlsh_diff_normalization.png", dpi=300)
    

def plot_sigmoid_norm_size_increase():
    xs = np.linspace(0, 1.0, 100) 
    ys = np.vectorize(sigmoid_norm_size_increase)(xs)
    plt.figure(figsize=(6,4))
    plt.plot(xs, ys, label='sigmoid_norm_size_increase')
    plt.xlabel('Size Increase Ratio', fontsize=14)
    plt.ylabel('Normalized Value', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.title('Size Increase Normalization', fontsize=16)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "size_increase_normalization.png", dpi=300)
    
    
def plot_sigmoid_norm_entropy_diff():
    xs = np.linspace(0, 2, 100) 
    ys = np.vectorize(sigmoid_norm_entropy_diff)(xs)
    plt.figure(figsize=(6,4))
    plt.plot(xs, ys, label='sigmoid_norm_entropy_diff')
    plt.xlabel('Entropy Difference', fontsize=14)
    plt.ylabel('Normalized Value', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.title('Entropy Difference Normalization', fontsize=16)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "entropy_diff_normalization.png", dpi=300)


def plot_entropy():
    mw_entropies = []
    for file in MALWARE_DIR.iterdir():
        with file.open('rb') as f:
            mw_entropies.append(file_entropy(f.read()))
    bn_entropies = []
    for file in BENIGN_DIR.iterdir():
        with file.open('rb') as f:
            bn_entropies.append(file_entropy(f.read()))
    
    plt.figure(figsize=(12,8))
    plt.hist(mw_entropies, bins=30, alpha=0.5, label='Malware')
    plt.hist(bn_entropies, bins=30, alpha=0.5, label='Benign')
    plt.xlabel('Entropy')
    plt.ylabel('Frequency')
    plt.title('Entropy Distribution of Malware and Benign Samples')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()
    

def plot_gamma_dist_bytes():
    num_bytes_to_generate = 10000
    shape = 0.1
    scale = 1
    gamma_gen = GammaDistByteGenerator(shape=shape, scale=scale)
    gamma_bytes = gamma_gen.generate_data(num_bytes_to_generate)
    gamma_bytes = list(gamma_bytes)
    print(f"Actual Mean: {np.mean(gamma_bytes):.2f}")
    print(f"Actual Variance: {np.var(gamma_bytes):.2f}")
    plt.hist(gamma_bytes, bins=range(256), alpha=0.7, color='blue')
    plt.xlabel("Byte value", fontsize=20)
    plt.ylabel("Frequency", fontsize=20)
    plt.title("Histogram of Generated Bytes", fontsize=22)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.tight_layout()
    plt.show()
    
    
def plot_normal_dist_bytes():
    num_bytes_to_generate = 10000
    mean = 170
    variance = 1000
    normal_gen = NormalDistByteGenerator(mean=mean, variance=variance)
    normal_bytes = normal_gen.generate_data(num_bytes_to_generate)
    normal_bytes = list(normal_bytes)
    print(f"Base Mean: {mean}, Actual Mean: {np.mean(normal_bytes):.2f}")
    print(f"Base Variance: {variance}, Actual Variance: {np.var(normal_bytes):.2f}")
    plt.hist(normal_bytes, bins=range(256), alpha=0.7, color='blue')
    plt.xlabel("Byte value", fontsize=14)
    plt.ylabel("Frequency", fontsize=14)
    plt.title("Histogram of Generated Bytes", fontsize=16)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.show()
    
def plot_weibull_dist_bytes():
    num_bytes_to_generate = 10000
    weibull_gen = WeibullDistByteGenerator(shape=1.5, scale=100)
    weibull_bytes = weibull_gen.generate_data(num_bytes_to_generate)
    weibull_bytes = list(weibull_bytes)
    print(f"Actual Mean: {np.mean(weibull_bytes):.2f}")
    print(f"Actual Variance: {np.var(weibull_bytes):.2f}")
    plt.hist(weibull_bytes, bins=range(256), alpha=0.7, color='blue')
    plt.xlabel("Byte value", fontsize=20)
    plt.ylabel("Frequency", fontsize=20)
    plt.title("Histogram of Generated Bytes", fontsize=22)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.tight_layout()
    plt.show()
    
    
if __name__ == "__main__":
    
    # plot_target_bytes_distribution()
    plot_sigmoid_norm_tlsh_diff()
    plot_sigmoid_norm_size_increase()
    plot_sigmoid_norm_entropy_diff()
    # plot_entropy()
    # plot_gamma_dist_bytes()
    # plot_weibull_dist_bytes()
    # plot_normal_dist_bytes()