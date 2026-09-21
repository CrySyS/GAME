"""Plot the distribution of malware-level average strategy fitness."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman"]

from config import OUTPUT_DIR, ARCH
from genetic import (
	AVAILABLE_DATA_GENERATORS,
	AVAILABLE_ELF_MODIFIERS,
	AVAILABLE_INSERTION_RATIO_SAMPLERS,
)


COMPONENTS = {
	"elf_modifier": AVAILABLE_ELF_MODIFIERS,
	"ratio_sampler": AVAILABLE_INSERTION_RATIO_SAMPLERS,
	"data_generator": AVAILABLE_DATA_GENERATORS,
}

PALETTES = {
	"elf_modifier": sns.color_palette(("green", "blue", "red")),
	"ratio_sampler": sns.color_palette("Set2", n_colors=len(AVAILABLE_INSERTION_RATIO_SAMPLERS)),
	"data_generator": sns.color_palette("Set3", n_colors=len(AVAILABLE_DATA_GENERATORS)),
}
INTERVALS = [f"{start}-{start + 9}" for start in range(1, 100, 10)]


def _fitness_interval(fitness: float) -> str:
	start = min(max(int((fitness - 1) // 10) * 10 + 1, 1), 91)
	return f"{start}-{start + 9}"


def average_fitness_by_malware(dataframe: pd.DataFrame) -> pd.DataFrame:
	"""Average the twelve adversarial-run fitness values for each malware."""
	averaged = (
		dataframe.assign(fitness=pd.to_numeric(dataframe["fitness"], errors="coerce"))
		.dropna(subset=["fitness"])
		.groupby("mw", as_index=False)
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
	distributions = {}
	for component, classes in COMPONENTS.items():
		component_names = [component_type.__name__ for component_type in classes]
		distributions[component] = pd.crosstab(
			dataframe["fitness_interval"], dataframe[component]
		).reindex(index=INTERVALS, columns=component_names, fill_value=0)
	return distributions


def _evasion_percentages(
	dataframe: pd.DataFrame, averaged: pd.DataFrame
) -> pd.Series:
	intervals_by_malware = averaged[["mw", "fitness_interval"]]
	interval_rows = dataframe.drop(
		columns="fitness_interval", errors="ignore"
	).merge(intervals_by_malware, on="mw", how="inner")
	return (
		interval_rows.assign(
			undetected=interval_rows["detected"].astype(str).str.upper().eq("NO")
		)
		.groupby("fitness_interval")["undetected"]
		.mean()
		.mul(100)
		.reindex(INTERVALS, fill_value=0)
	)


def _plot_distribution(
	dataframe: pd.DataFrame, title: str, evasion_percentages: pd.Series
) -> None:
	distributions = _distribution(dataframe)
	figure, axis = plt.subplots(figsize=(8, 6))
	positions = range(len(INTERVALS))
	bar_width = 0.25
	component_offsets = (-bar_width, 0, bar_width)

	for (component, classes), offset in zip(COMPONENTS.items(), component_offsets):
		bottom = pd.Series(0.0, index=INTERVALS)
		component_distribution = distributions[component]
		for component_type, color in zip(classes, PALETTES[component]):
			name = component_type.__name__
			values = component_distribution[name]
			axis.bar(
				[position + offset for position in positions],
				values,
				bottom=bottom,
				facecolor=color,
				edgecolor="black",
				width=bar_width,
			)
			bottom += values

	maximum_bar_height = max(
		distribution.loc[interval].sum()
		for distribution in distributions.values()
		for interval in INTERVALS
	)
	axis.set_ylim(0, maximum_bar_height * 1.1 if maximum_bar_height else 1)
	for position, interval in enumerate(INTERVALS):
		bar_height = distributions["elf_modifier"].loc[interval].sum()
		axis.text(
			position,
			bar_height,
			f"{evasion_percentages[interval]:.1f}%",
			ha="center",
			va="bottom",
			fontsize="large",
		)

	axis.set_title(title)
	axis.set_xlabel("Fitness of best strategies", fontsize=14)
	axis.set_ylabel("Number of strategies", fontsize=14)
	axis.set_xticks(list(positions))
	axis.set_xticklabels(INTERVALS, fontsize=12)
	axis.tick_params(axis="y", labelsize=12)
	axis.grid(axis="y", alpha=0.25)
	axis.set_axisbelow(True)
	axis.legend(
		handles=[
			Patch(facecolor=color, label=component_type.__name__, edgecolor="black")
			for component, classes in COMPONENTS.items()
			for component_type, color in zip(classes, PALETTES[component])
		],
		loc="upper left",
		frameon=True,
		ncol=1,
	)
	figure.tight_layout()


def plot_all_distributions() -> None:
	"""Display one stacked histogram for each architecture/model pair."""
	
	MODELS = [("Simbiota_40", "SIMBIoTA-40"), ("Simbiota_ML_LR", "SIMBIoTA-ML with Logistic Regression"), ("Simbiota_ML_RF", "SIMBIoTA-ML with Random Forest")]
	for model, model_name in MODELS:
		input_path = OUTPUT_DIR / f"samples_{ARCH}_{model}.csv"
		dataframe = pd.read_csv(input_path)
		result = average_fitness_by_malware(dataframe)
		evasion_percentages = _evasion_percentages(dataframe, result)
		_plot_distribution(result, f"{model_name} ({ARCH.upper()})", evasion_percentages)
  		# plt.show()
		plt.savefig(
			OUTPUT_DIR / f"strategy_distribution_{model}_{ARCH}.png", dpi=300, bbox_inches="tight"
		)
	


if __name__ == "__main__":
	plot_all_distributions()
