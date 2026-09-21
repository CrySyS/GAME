import logging
import logging.config
import random
from pathlib import Path
import pickle
import pandas as pd
import json

from config import *
from genetic.ga import GeneticAlgorithm
from model.simbiota_ml import SimbiotaML
from model.simbiota import Simbiota

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


def select_files_to_test(num_files) -> list[Path]:
    """Select a random malware files for the experiment batch."""
    all_files = list(MALWARE_DIR.iterdir())
    random.seed(42)
    return random.sample(all_files, num_files)
    
    
def train_and_save_models() -> list[Path]:
    model_paths = []
    # Check if the SimbiotaML model exists, if not, train and save it
    for model_type in ["LR", "RF"]:
        detector = SimbiotaML(model_type)
        if not (OUTPUT_DIR / f"{detector}.pkl").exists():
            data_file = pd.read_csv(DATA_DIR / f"{ARCH}_medium_tlsh.csv")
            X = data_file["tlsh"].values.tolist()
            y = data_file["label"]
            
            detector.fit(X, y)
            with open(OUTPUT_DIR / f"{detector}.pkl", "wb") as f:
                pickle.dump(detector, f)
                
        model_paths.append(OUTPUT_DIR / f"{detector}.pkl")
            
    # Check if the Simbiota model exists, if not, train and save it
    detector = Simbiota(40)
    if not (OUTPUT_DIR / f"{detector}.pkl").exists():
        data_file = pd.read_csv(DATA_DIR / f"{ARCH}_medium_tlsh.csv")
        X = data_file.loc[data_file["label"] == 1, "tlsh"].values.tolist()
        
        detector.fit(X)
        with open(OUTPUT_DIR / f"{detector}.pkl", "wb") as f:
            pickle.dump(detector, f)
    model_paths.append(OUTPUT_DIR / f"{detector}.pkl")
    
    return model_paths


def generate_experiment_configs(files_to_test: list[Path], model_paths: list[Path]) -> list[dict]:
    experiments = []
    for input_file_path in files_to_test:
        for model_path in model_paths:
            experiments.append(
                {
                    "input_file_path": input_file_path,
                    "model_path": model_path,
                }
            )
    return experiments


def run_experiment(experiment: dict) -> None:
    input_file = experiment["input_file_path"].read_bytes()
    model_path = experiment["model_path"]
    with open(model_path, "rb") as f:
        detector = pickle.load(f)
    
    # check if experiment has already been run
    strategy_path = OUTPUT_DIR / str(detector) / f"{experiment['input_file_path'].name}.json" 
    if strategy_path.exists():
        logger.info(f"Experiment for {experiment['input_file_path'].name} has already been run.")
        return

    ga = GeneticAlgorithm(input_file=input_file, model=detector, config=BASE_CONFIG)
    best_strategy = ga.run()
    
    # Save best strategy to JSON
    strategy_path = OUTPUT_DIR / str(ga.model) / f"{experiment["input_file_path"].name}.json"
    strategy_path.parent.mkdir(parents=True, exist_ok=True)
    strategy_json = best_strategy.to_dict()
    strategy_json['detector'] = detector.to_dict()
    with open(strategy_path, 'w') as f:
        json.dump(strategy_json, f, indent=2)
        
    logger.info(f"Best strategy saved to {strategy_path}")
    



def main() -> None:
    files_to_run_on = select_files_to_test(num_files=600)
    model_paths = train_and_save_models()
    experiment_configurations = generate_experiment_configs(files_to_run_on, model_paths)

    total_generations = sum(
        BASE_CONFIG["NUM_GENERATIONS"] for experiment in experiment_configurations
    )
    logger.info(
        f"Generated {len(experiment_configurations)} experiments. ({total_generations} generations in total)"
    )
    logger.info("This will run a separate Genetic Algorithm for each configuration.")

    for index, experiment in enumerate(experiment_configurations, start=1):
        logger.info(f"--- Running Experiment {index}/{len(experiment_configurations)} ---")
        run_experiment(experiment)

    logger.info("All experiments completed.")


if __name__ == "__main__":
    main()
