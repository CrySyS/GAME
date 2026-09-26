import pandas as pd
import tlsh
from genetic.strategy import Strategy
from config import LOGGING_CONFIG, MALWARE_DIR, OUTPUT_DIR, BASE_CONFIG
from utils import *

import logging
logger = logging.getLogger(__name__)


class StrategyEvaluator:
    """Evaluates a saved strategy multiple times and logs detailed statistics."""
    
    def __init__(self, input_file, model, strategy: Strategy):
        self.input_file = input_file
        self.model = model
        self.strategy = strategy
        
        self.original_tlsh = tlsh.hash(self.input_file)
        self.original_size = len(self.input_file)
        self.original_entropy = file_entropy(self.input_file)
        self.original_sha256 = sha256_hash(self.input_file)

    def get_strategy_metrics(self) -> dict:
        modified_file = self.strategy.execute(self.input_file)
        modified_tlsh = tlsh.hash(modified_file)
        metrics = {}
        metrics['adv_sha256'] = sha256_hash(modified_file)
        metrics['adv_tlsh'] = modified_tlsh
        metrics['tlsh_diff'] = tlsh.diff(self.original_tlsh, modified_tlsh)
        metrics['size_increase'] = (len(modified_file) - self.original_size) / self.original_size
        metrics['entropy_diff'] = abs(file_entropy(modified_file) - self.original_entropy)
        metrics['detected'] = "YES" if self.model.predict([modified_tlsh])[0] else "NO"
        
        norm_tlsh_diff = sigmoid_norm_tlsh_diff(metrics['tlsh_diff'])
        norm_size_increase = sigmoid_norm_size_increase(metrics['size_increase'])
        norm_entropy_diff = sigmoid_norm_entropy_diff(metrics['entropy_diff'])
        
        weighted_fitness = (
            norm_tlsh_diff * BASE_CONFIG["FITNESS_WEIGHTS"]['tlsh_diff']
            + norm_size_increase * BASE_CONFIG["FITNESS_WEIGHTS"]['size_increase']
            + norm_entropy_diff * BASE_CONFIG["FITNESS_WEIGHTS"]['entropy_diff'])
                
        weighted_fitness *= BASE_CONFIG["TYPE_PENALTIES"].get(self.strategy.elf_modifier_names()[0])
        
        if metrics['detected'] == "YES":  # if detected as malware
            weighted_fitness *= BASE_CONFIG['DETECTED_PENALTY']
            
        metrics['fitness'] = weighted_fitness * 100
            
        return metrics
    
        
    def evaluate_multiple_runs(self, num_runs: int) -> list:
        """
        Runs the strategy multiple times and extracts metrics for each run.
        
        Args:
            num_runs: Number of times to execute the strategy
        
        Returns:
            List of metric dictionaries, one per run
        """
        results = []
        
        for run_idx in range(num_runs):
            # Execute strategy on input bytes
            metrics = self.get_strategy_metrics()
            results.append(metrics)
            logger.debug(f"Run {run_idx+1}/{num_runs} - TLSH Diff: {metrics['tlsh_diff']:.2f}, "
                        f"Size Increase: {metrics['size_increase']:.2f}, "
                        f"Entropy Diff: {metrics['entropy_diff']:.2f}, "
                        f"Detected: {metrics['detected']}")
        
        return results
    
    
    def save_results_to_csv(self, results: list, csv_path):
        """
        Saves evaluation results to a CSV file, overwriting if it exists.
        Each row represents one run.
        
        Args:
            results: List of metric dictionaries from evaluate_multiple_runs
            csv_path: Path to save CSV results
        """
        
        # Create rows for new results
        rows = []
        for run_idx, metrics in enumerate(results):
            row = {
                'run_id': run_idx + 1,
                'adv_sha256': metrics['adv_sha256'],
                'tlsh_diff': metrics['tlsh_diff'],
                'size_increase': metrics['size_increase'],
                'entropy_diff': metrics['entropy_diff'],
                'detected': metrics['detected'],
            }
            rows.append(row)
        
        
        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False)
        logger.info(f"Results saved to {csv_path}")


if __name__ == "__main__":
    import argparse
    import logging.config
    import pickle
    import json

    logging.config.dictConfig(LOGGING_CONFIG)

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file_id", help="Malware sha256 hash, e.g. 80d2...")
    parser.add_argument("--runs", type=int, default=12, help="Number of runs to evaluate the strategy")
    parser.add_argument("--model_path", type=str, required=True, help="Path to the trained model pickle file.")
    args = parser.parse_args()
    
    with open(args.model_path, "rb") as f:
        detector = pickle.load(f)
    input_file_id = args.input_file_id
    strategy_path = OUTPUT_DIR / str(detector) / f"{input_file_id}.json"
    with open(strategy_path, 'r') as f:
        strategy = Strategy.from_dict(json.load(f))

    input_file_path = MALWARE_DIR / input_file_id
    input_file = input_file_path.read_bytes()
    evaluator = StrategyEvaluator(input_file=input_file, model=detector, strategy=strategy)

    results = evaluator.evaluate_multiple_runs(args.runs)

    csv_output = OUTPUT_DIR / f"strategy_evaluation_results_{input_file_id}.csv"
    evaluator.save_results_to_csv(results, csv_output)

    logger.info(f"Evaluation complete. Results saved to {csv_output}")
