import pandas as pd
from genetic import AVAILABLE_ELF_MODIFIERS


def print_summary_statistics(dataframe: pd.DataFrame) -> None:
	"""Print summary statistics about the dataset."""
	total_samples = len(dataframe)
	total_malware = dataframe["mw"].nunique()
	print(f"\nTotal malware: {total_malware}")
	print(f"Total advex samples: {total_samples}")
	print(f"Total detected advex samples: {len(dataframe.loc[dataframe['detected'].eq('YES')])}")
	print(f"Evasion rate: {len(dataframe.loc[dataframe['detected'].eq('NO')]) / total_samples * 100:.2f} %")
	print(f"Average tlsh difference: {dataframe['tlsh_diff'].mean():.2f}")
	print(f"Average size increase: {dataframe['size_increase'].mean() * 100:.2f} %")
	print(f"Average entropy difference: {dataframe['entropy_diff'].mean():.2f}")
	print(f"Number of malware without any undetected samples: {dataframe.groupby('mw')['detected'].apply(lambda x: (x == 'NO').sum() == 0).sum()}")
	print(f"Name of malware without any undetected samples: {dataframe.groupby('mw')['detected'].apply(lambda x: (x == 'NO').sum() == 0).loc[lambda x: x].index.tolist()}")
	print(f"Name of malware with lowest average fitness: {dataframe.groupby('mw')['fitness'].mean().idxmin()}")


def print_undetected_size_increase(dataframe: pd.DataFrame) -> None:
	for elf_modifier in [modifier.__name__ for modifier in AVAILABLE_ELF_MODIFIERS]:
		modifier_rows = dataframe.loc[dataframe["elf_modifier"].eq(elf_modifier)]
		print(f"Number {elf_modifier} of strategies: {int(modifier_rows['mw'].nunique())}")
		print(f"{elf_modifier}:  Average size increase for undetected samples: {modifier_rows.loc[modifier_rows['detected'].eq('NO'), 'size_increase'].mean()*100:.2f} %")
  
  
def print_uniqueness(dataframe: pd.DataFrame) -> None:
	"""Print uniqueness statistics about the dataset."""
	total_samples = len(dataframe)
	total_malware = dataframe["mw"].nunique()
	print(f"\nTotal malware: {total_malware}")
	print(f"Total unique malware samples: {dataframe['mw'].nunique()}")
	print(f"Total unique malware tlsh: {dataframe['tlsh'].nunique()}")
	print(f"Total advex samples: {total_samples}")
	print(f"Total unique advex samples: {dataframe['adv_sha256'].nunique()}")
	print(f"Total unique advex tlsh: {dataframe['adv_tlsh'].nunique()}")


if __name__ == "__main__":
	from config import ARCH, OUTPUT_DIR

	MODELS = [("Simbiota_40", "SIMBIoTA-40"), ("Simbiota_ML_RF", "SIMBIoTA-ML (RF)"), ("Simbiota_ML_LR", "SIMBIoTA-ML (LR)")]
	for model, model_name in MODELS:
		print(f"\n### Statistics for {model_name} - {ARCH}:")
		input_path = OUTPUT_DIR / f"samples_{ARCH}_{model}.csv"
		dataframe = pd.read_csv(input_path)
		print_summary_statistics(dataframe)
		print_undetected_size_increase(dataframe)
		print_uniqueness(dataframe)