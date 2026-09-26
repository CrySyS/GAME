"""Plot the distribution of strategy fitness."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

from config import ARCH, OUTPUT_DIR
from genetic import (
	AVAILABLE_DATA_GENERATORS,
	AVAILABLE_ELF_MODIFIERS,
	AVAILABLE_INSERTION_RATIO_SAMPLERS,
)


plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman"]

GENE_TYPES = {
	"elf_modifier": AVAILABLE_ELF_MODIFIERS,
	"ratio_sampler": AVAILABLE_INSERTION_RATIO_SAMPLERS,
	"data_generator": AVAILABLE_DATA_GENERATORS,
}

PALETTES = {
	"elf_modifier": sns.color_palette(["green", "blue", "red"]),
	"ratio_sampler": sns.color_palette("Set2", n_colors=len(AVAILABLE_INSERTION_RATIO_SAMPLERS)),
	"data_generator": sns.color_palette("Set3", n_colors=len(AVAILABLE_DATA_GENERATORS)),
}
INTERVALS = [f"{start}-{start + 9}" for start in range(1, 100, 10)]
MODELS = (
	("Simbiota_40", "SIMBIoTA-40"),
	("Simbiota_ML_LR", "SIMBIoTA-ML-LR"),
	("Simbiota_ML_RF", "SIMBIoTA-ML-RF"),
)
BAR_WIDTH = 0.25


def _fitness_interval(fitness: float) -> str:
	# Keep the displayed bins aligned with the 1-10, ..., 91-100 axis labels.
	first_interval = int((fitness - 1) // 10) * 10 + 1
	start = min(max(first_interval, 1), 91)
	return f"{start}-{start + 9}"


def average_fitness_by_malware(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Average the fitness values of the repeated runs for each malware."""
	# Each malware has one selected strategy, so its repeated runs must
	# become one observation before strategies are counted in the plot.
	averaged = (
		dataframe.groupby("mw", as_index=False)
		.agg(
			fitness=("fitness", "mean"),
			elf_modifier=("elf_modifier", "first"),
			ratio_sampler=("ratio_sampler", "first"),
			data_generator=("data_generator", "first"),
		)
	)
	averaged["fitness_interval"] = averaged["fitness"].map(_fitness_interval)
	return averaged


def _distribution(dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
	# Count each gene type within every averaged fitness interval. Reindexing
	# keeps empty intervals and gene types visible as zero-height bars.
	return {
		gene: pd.crosstab(dataframe["fitness_interval"], dataframe[gene]).reindex(
			index=INTERVALS,
			columns=[gene_type.__name__ for gene_type in gene_types],
			fill_value=0,
		)
		for gene, gene_types in GENE_TYPES.items()
	}


def _evasion_percentages(
    dataframe: pd.DataFrame, averaged: pd.DataFrame
) -> pd.Series:
	# Use the same malware-level intervals as the bars, while counting the number of detections in each interval.
    interval_rows = dataframe.drop(
        columns="fitness_interval", errors="ignore"
    ).merge(
        averaged[["mw", "fitness_interval"]],
        on="mw",
        how="inner",
    )

    return (
        interval_rows["detected"].eq("NO") # Becomes True for undetected samples, False for detected samples
        .groupby(interval_rows["fitness_interval"])
        .mean() # Calculate the percentage of undetected samples in each interval
        .mul(100)
        .reindex(INTERVALS)
    )

def _legend_handles() -> list[Patch]:
	return [
		Patch(facecolor=color, label=gene_type.__name__, edgecolor="black")
		for gene, gene_types in GENE_TYPES.items()
		for gene_type, color in zip(gene_types, PALETTES[gene])
	]


def _plot_distribution(
	averaged: pd.DataFrame, model_name: str, evasion_percentages: pd.Series
) -> None:
	title = f"Distribution of best strategies against {model_name} ({ARCH.upper()})"
	distributions = _distribution(averaged)
	figure, axis = plt.subplots(figsize=(8, 6))
	positions = range(len(INTERVALS))
	gene_offsets = (-BAR_WIDTH, 0, BAR_WIDTH)

	# Draw one stacked bar for each gene family, offset slightly so the three
	# families can be compared within each fitness interval.
	for (gene, gene_types), offset in zip(GENE_TYPES.items(), gene_offsets):
		bottom = pd.Series(0.0, index=INTERVALS)
		gene_distribution = distributions[gene]
		for gene_type, color in zip(gene_types, PALETTES[gene]):
			name = gene_type.__name__
			values = gene_distribution[name]
			axis.bar(
				[position + offset for position in positions],
				values,
				bottom=bottom,
				facecolor=color,
				edgecolor="black",
				width=BAR_WIDTH,
			)
			bottom += values

	for position, interval in enumerate(INTERVALS):
		bar_height = distributions["elf_modifier"].loc[interval].sum()
		if bar_height == 0:
			# There is no strategy in this interval, so a percentage would be
			# misleading even though the interval remains on the x-axis.
			continue

		axis.text(
			position,
			bar_height,
			f"{evasion_percentages[interval]:.1f}%",
			ha="center",
			va="bottom",
			fontsize=14,
			fontweight="bold"
		)

	axis.set_title(title, fontsize=18)
	axis.set_xlabel("Fitness of strategies", fontsize=16)
	axis.set_ylabel("Number of strategies", fontsize=16)
	axis.set_xticks(list(positions))
	axis.set_xticklabels(INTERVALS, fontsize=12)
	axis.tick_params(axis="y", labelsize=12)
	axis.grid(axis="y", alpha=0.25)
	axis.set_axisbelow(True)
	axis.legend(
		handles=_legend_handles(),
		loc="upper left",
		frameon=True,
		ncol=1,
	)
	figure.tight_layout()
	plt.savefig(OUTPUT_DIR / f"strategy_distribution_{model_name}_{ARCH}.png", dpi=300, bbox_inches="tight")


def plot_all_distributions() -> None:
	"""Display one stacked histogram for each architecture/model pair."""
	for model, model_name in MODELS:
		print(f"{ARCH.upper()} - {model}")
		input_path = OUTPUT_DIR / f"samples_{ARCH}_{model}.csv"
		dataframe = pd.read_csv(input_path)
		averaged = average_fitness_by_malware(dataframe)
		evasion_percentages = _evasion_percentages(dataframe, averaged)
		_plot_distribution(averaged, model_name, evasion_percentages)


if __name__ == "__main__":
	plot_all_distributions()
