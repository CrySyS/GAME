"""Plot the cost of successful, undetected adversarial attacks."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

from config import ARCH, OUTPUT_DIR
from genetic import AVAILABLE_ELF_MODIFIERS

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman"]


def _strategy_definitions() -> list[tuple[str, tuple[int, int, int]]]:
	palette = sns.color_palette(("green", "blue", "red"))
	return [(elf_modifier.__name__, color)
		for elf_modifier, color in zip(AVAILABLE_ELF_MODIFIERS, palette)]


def undetected_samples(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Return valid samples that the model did not detect as malware."""
	result = dataframe.loc[
		dataframe["detected"].astype(str).eq("NO")
	].copy()
	result["size_increase"] = pd.to_numeric(result["size_increase"])
	result["tlsh_diff"] = pd.to_numeric(result["tlsh_diff"])
	return result.dropna(subset=["size_increase", "tlsh_diff"])


def _plot_attack_cost(dataframe: pd.DataFrame, title: str) -> None:
	figure, axis = plt.subplots(figsize=(8, 6))
	strategy_definitions = _strategy_definitions()

	for strategy, color in strategy_definitions:
		strategy_rows = dataframe.loc[
			dataframe["elf_modifier"] == strategy
		]
		axis.scatter(
			strategy_rows["size_increase"],
			strategy_rows["tlsh_diff"],
			facecolors=color,
			edgecolors=None,
			alpha=0.5,
			linewidths=0.1,
			s=12,
			label=strategy,
		)

	axis.set_title(
		f"{title}\nCost of successful, undetected attacks", fontsize=16
	)
	axis.set_xlabel("Size increase", fontsize=14)
	axis.set_ylabel("TLSH diff", fontsize=14)
	axis.tick_params(axis="both", labelsize=12)
	axis.grid(alpha=0.25)
	axis.set_axisbelow(True)
	handles = [plt.Line2D([], [], color=color, marker='o', linestyle='', label=name)
			 for name, color in strategy_definitions]
	axis.legend(
		handles=handles,
		loc="lower right",
		frameon=True,
		fontsize=12,
		
	)
	figure.tight_layout()


def plot_all_attack_costs() -> None:
	"""Display one scatter plot for each architecture/model pair."""
	MODELS = [("Simbiota_40", "SIMBIoTA-40"), ("Simbiota_ML_LR", "SIMBIoTA-ML with Logistic Regression"), ("Simbiota_ML_RF", "SIMBIoTA-ML with Random Forest")]
	for model,model_name in MODELS:
		print(f"{ARCH.upper()} - {model}")
		input_path = OUTPUT_DIR / f"samples_{ARCH}_{model}.csv"
		dataframe = undetected_samples(pd.read_csv(input_path))
		_plot_attack_cost(dataframe, f"{model_name} ({ARCH.upper()})")
		plt.savefig(OUTPUT_DIR / f"attack_cost_{model}_{ARCH}.png", dpi=300, bbox_inches="tight")
		plt.show()


if __name__ == "__main__":
	plot_all_attack_costs()
