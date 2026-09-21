import json
import random
import os
import argparse
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from copy import deepcopy
import tlsh

from genetic.strategy import Strategy

from utils import *
from config import LOGGING_CONFIG

import logging
logger = logging.getLogger(__name__)


_WORKER_CONTEXT = {
    "original_file": None,
    "original_tlsh": None,
    "original_file_size": None,
    "original_entropy": None,
    "model": None,
    "fitness_weights": None,
    "anomaly_weights": None,
    "detected_penalty": None,
    "repetition": None
}

def _initialize_fitness_worker(
    original_file: bytes,
    original_tlsh: str,
    original_file_size: int,
    original_entropy: float,
    model,
    fitness_weights: dict,
    anomaly_weights: dict,
    detected_penalty: float,
    repetition: int
):
    # Pool workers are separate processes on macOS; configure logging per worker.
    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)

    _WORKER_CONTEXT["original_file"] = original_file
    _WORKER_CONTEXT["original_tlsh"] = original_tlsh
    _WORKER_CONTEXT["original_file_size"] = original_file_size
    _WORKER_CONTEXT["original_entropy"] = original_entropy
    _WORKER_CONTEXT["model"] = model
    _WORKER_CONTEXT["fitness_weights"] = fitness_weights
    _WORKER_CONTEXT["anomaly_weights"] = anomaly_weights
    _WORKER_CONTEXT["detected_penalty"] = detected_penalty
    _WORKER_CONTEXT["repetition"] = repetition



def _evaluate_strategy_worker(strategy):
    weighted_fitness_sum = 0.0
    for _ in range(_WORKER_CONTEXT["repetition"] - 1):
        modified_file = strategy.execute(_WORKER_CONTEXT["original_file"])
        modified_tlsh = tlsh.hash(modified_file)
        modified_size = len(modified_file)
        modified_entropy = file_entropy(modified_file)

        tlsh_diff = tlsh.diff(modified_tlsh, _WORKER_CONTEXT["original_tlsh"])
        size_increase_ratio = (modified_size - _WORKER_CONTEXT["original_file_size"]) / _WORKER_CONTEXT["original_file_size"]
        entropy_diff = abs(modified_entropy - _WORKER_CONTEXT["original_entropy"])
        norm_tlsh_diff = sigmoid_norm_tlsh_diff(tlsh_diff)
        norm_size_increase = sigmoid_norm_size_increase(size_increase_ratio)
        norm_entropy_diff = sigmoid_norm_entropy_diff(entropy_diff)

        weighted_fitness = (
            norm_tlsh_diff * _WORKER_CONTEXT["fitness_weights"]['tlsh_diff']
            + norm_size_increase * _WORKER_CONTEXT["fitness_weights"]['size_increase']
            + norm_entropy_diff * _WORKER_CONTEXT["fitness_weights"]['entropy_diff'])
        
        weighted_fitness *= _WORKER_CONTEXT["anomaly_weights"].get(strategy.elf_modifier_names()[0])

        if _WORKER_CONTEXT["model"].predict([modified_tlsh])[0] == 1:  # if detected as malware
            weighted_fitness *= _WORKER_CONTEXT['detected_penalty']
            
        weighted_fitness_sum += weighted_fitness

    strategy.fitness = weighted_fitness_sum / _WORKER_CONTEXT['repetition'] * 100
    return strategy


class GeneticAlgorithm:
    def __init__(self, input_file: bytes, model, config: dict):
        self.original_file = input_file
        self.original_tlsh = tlsh.hash(self.original_file)
        self.original_file_size = len(self.original_file)
        self.original_entropy = file_entropy(self.original_file)
        self.model = model
        self.config = config 
        self.population = []
        self.history = []
        self._pool = None


    def _pool_process_count(self):
        return os.cpu_count() - 1 if os.cpu_count() > 1 else 1


    def _ensure_pool(self):    
        self._pool = Pool(
            processes=self._pool_process_count(),
            initializer=_initialize_fitness_worker,
            initargs=(
                self.original_file,
                self.original_tlsh,
                self.original_file_size,
                self.original_entropy,
                self.model,
                self.config['FITNESS_WEIGHTS'],
                self.config['ANOMALY_WEIGHTS'],
                self.config['DETECTED_PENALTY'],
                self.config['REPETITION']
            ),
        )


    def _shutdown_pool(self):    
        self._pool.close()
        self._pool.join()
        self._pool = None


    def _initialize_population(self):
        """Creates the very first generation of random strategies."""
        logger.info("Initializing population...")
        self.population = [Strategy.create_random() for _ in range(self.config['POPULATION_SIZE'])]


    def _evaluate_population(self):
        """
        Splits the population across worker processes, evaluates chunk fitnesses,
        then sorts by fitness in descending order.
        """
        self.population = self._pool.map(_evaluate_strategy_worker, self.population)
        self.population.sort(key=lambda s: s.fitness, reverse=True)


    def _selection(self) -> Strategy:
        """
        Selects a single parent from the population using Tournament Selection.
        """
        p = self.config['tournament_selection_p']
        tournament_entrants = random.sample(self.population, self.config['TOURNAMENT_SIZE'])
        tournament_entrants.sort(key=lambda s: s.fitness, reverse=True)
        for i in range(len(tournament_entrants)):
            if random.random() < p * ((1 - p) ** i):
                return tournament_entrants[i]
        return tournament_entrants[0]


    def _create_new_generation(self):
        # Creates a new generation of strategies by keeping the top N (elitism), adding some fresh random strategies.
        new_population = [deepcopy(strategy) for strategy in self.population[:self.config['ELITISM_COUNT']]] 
        new_population.extend([Strategy.create_random() for _ in range(self.config['FRESH_COUNT'])])

        # Filling the rest with children from crossover.
        while len(new_population) < self.config['POPULATION_SIZE']:
            parent1 = self._selection()
            parent2 = self._selection()
            child = parent1.crossover(parent2)
            child.mutate(self.config['MUTATION_CHANCES'])
            new_population.append(child)
                
        self.population = new_population


    def run(self, early_stopping_threshold=99):
        logger.info(f"Starting GAME ...")
        self._initialize_population()
        self._ensure_pool()

        try:
            for gen in range(self.config['NUM_GENERATIONS']):
                self._evaluate_population()
                best_strategy = self.population[0]
                strategies = [s.elf_modifier_names()[0] for s in self.population]
                fitness_scores = [s.fitness for s in self.population]
                avg_fitness = np.mean(fitness_scores)
                below_threshold_count = sum(1 for s in self.population if s.fitness < 10)
                unique_strategies_count = len(set(json.dumps(strategy.to_dict()["genes"][0]) for strategy in self.population))
                self.history.append((strategies, fitness_scores))

                logger.info(f"{gen+1:03d} | avg fitness:{avg_fitness:.2f} | below threshold:{below_threshold_count} | unique strategies:{unique_strategies_count} | best:{best_strategy}")

                if avg_fitness > early_stopping_threshold: # early stopping if we have a very good strategy, to save time and avoid overfitting
                    logger.info(f"Early stopping at generation {gen+1} due to high average fitness.")
                    break

                if gen < self.config['NUM_GENERATIONS'] - 1:
                    self._create_new_generation()
        finally:
            self._shutdown_pool()

        logger.info(f"GAME finished.")
        return best_strategy
  

#------------------------------------------------------------------------------


if __name__ == "__main__":
    
    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)
    from evaluation.strategy_eval import StrategyEvaluator
    from visuals.plot import plot_history
    from config import OUTPUT_DIR, MALWARE_DIR, BASE_CONFIG
    import pickle


    parser = argparse.ArgumentParser(description="Run GAME with a trained detector and a malware sample.")
    parser.add_argument(
        "--model-path",
        type=Path,
        required=True,
        help="Path to the trained detector pickle file.",
    )
    parser.add_argument(
        "--malware-id",
        help="Malware sample id to use.",
    )
    args = parser.parse_args()


    model_path = args.model_path.expanduser()

    with open(model_path, "rb") as f:
        detector = pickle.load(f)
    logger.debug(f"Loaded model from {model_path}.")


    if args.malware_id:
        mw_id = args.malware_id
        mw_path = MALWARE_DIR / mw_id
        
    mw_file = mw_path.read_bytes()
    
    logger.info(f"Selected malware sample: {mw_id} for GAME execution.")
    ga = GeneticAlgorithm(mw_file, model=detector, config=BASE_CONFIG)
    best_strategy = ga.run()

    # Save best strategy to JSON
    # strategy_path = OUTPUT_DIR / str(ga.model) / f"{mw_id}.json"
    # strategy_path.parent.mkdir(parents=True, exist_ok=True)
    # strategy_json = best_strategy.to_dict()
    # strategy_json['detector'] = detector.to_dict()
    # with open(strategy_path, 'w') as f:
    #     json.dump(strategy_json, f, indent=2)
    # logger.info(f"Best strategy saved to {strategy_path}")
    
    plot_history(ga, mw_id) 
    evaluator = StrategyEvaluator(input_file=mw_file, model=detector, strategy=best_strategy)
    evaluator.evaluate_multiple_runs(num_runs=12)
        
        