import json
import logging
import logging.config
import pickle
from pathlib import Path

import pandas as pd
import tlsh

from config import ARCH, LOGGING_CONFIG, MALWARE_DIR, OUTPUT_DIR
from genetic.strategy import Strategy
from evaluation.strategy_eval import StrategyEvaluator
from utils import file_entropy


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "mw",
    "tlsh",
    "size",
    "entropy",
    "elf_modifier",
    "ratio_sampler",
    "data_generator",
    "run_id",
    "adv_sha256",
    "adv_tlsh",
    "tlsh_diff",
    "size_increase",
    "entropy_diff",
    "detected",
    "fitness",
]


def _load_strategy(path: Path) -> Strategy:
    with path.open("r") as f:
        return Strategy.from_dict(json.load(f))


def _load_model(model_name: str):
    model_path = OUTPUT_DIR / f"{model_name}.pkl"
    with model_path.open("rb") as f:
        return pickle.load(f)


def _strategy_signature(strategy: Strategy) -> tuple[str, str, str]:
    gene = strategy.genes[0]
    return (
        gene.elf_modifier.__class__.__name__,
        gene.ratio_sampler.__class__.__name__,
        gene.data_generator.__class__.__name__,
    )


def _keep_unique_adv_sha256(run_metrics: list[dict]) -> list[dict]:
    """Keep the first run for each unique generated sample hash."""
    seen_hashes = set()
    unique_runs = []

    for metrics in run_metrics:
        adv_sha256 = metrics["adv_sha256"]
        if adv_sha256 in seen_hashes:
            continue
        seen_hashes.add(adv_sha256)
        unique_runs.append(metrics)

    duplicate_count = len(run_metrics) - len(unique_runs)
    if duplicate_count:
        logger.info("Removed %d duplicate run(s) based on adv_sha256.", duplicate_count)

    return unique_runs


def _build_sample_rows_for_strategy(model_name: str, strategy_path: Path) -> list[dict]:
    mw_id = strategy_path.stem
    mw_path = MALWARE_DIR / mw_id

    strategy = _load_strategy(strategy_path)
    original_bytes = mw_path.read_bytes()
    original_tlsh = tlsh.hash(original_bytes)
    original_size = len(original_bytes)
    original_entropy = file_entropy(original_bytes)
    elf_modifier, ratio_sampler, data_generator = _strategy_signature(strategy)

    model = _load_model(model_name)
    evaluator = StrategyEvaluator(input_file=original_bytes, model=model, strategy=strategy)
    
    assert evaluator.original_sha256 == mw_id  # sanity check
    
    run_metrics = _keep_unique_adv_sha256(
        evaluator.evaluate_multiple_runs(num_runs=12)
    )
    rows = []
    for run_id, metrics in enumerate(run_metrics, start=1):

        rows.append(
            {
                "mw": mw_id,
                "tlsh": original_tlsh,
                "size": original_size,
                "entropy": original_entropy,
                "elf_modifier": elf_modifier,
                "ratio_sampler": ratio_sampler,
                "data_generator": data_generator,
                "run_id": run_id,
                "adv_sha256": metrics["adv_sha256"],
                "adv_tlsh": metrics["adv_tlsh"],
                "tlsh_diff": metrics["tlsh_diff"],
                "size_increase": metrics["size_increase"],
                "entropy_diff": metrics["entropy_diff"],
                "detected": metrics["detected"],
                "fitness": metrics["fitness"],
            }
        )

    return rows


def build_dataframe_for_model(model_name: str) -> pd.DataFrame:
    model_dir = OUTPUT_DIR / model_name

    rows = []
    strategy_files = list(model_dir.glob("*.json"))
    for i, strategy_path in enumerate(strategy_files):
        rows.extend(_build_sample_rows_for_strategy(model_name, strategy_path))
        logger.info(f"Processed strategy {i+1}/{len(strategy_files)}")

    dataframe = pd.DataFrame(rows, columns=EXPECTED_COLUMNS)
    logger.info("Built dataframe for %s with %d rows.", model_name, len(dataframe))
    return dataframe


def main() -> None:

    model_names = ['Simbiota_40', 'Simbiota_ML_RF', 'Simbiota_ML_LR']

    for model_name in model_names:
        dataframe = build_dataframe_for_model(model_name)
        output_path = OUTPUT_DIR / f"samples_{ARCH}_{model_name}.csv"
        dataframe.to_csv(output_path, index=False)
        logger.info("Saved %s", output_path)


if __name__ == "__main__":
    main()
