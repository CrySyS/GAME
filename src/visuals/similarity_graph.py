"""Build TLSH similarity graphs for the generated adversarial samples.

Each input CSV produces one GEXF graph. The graph nodes are one selected
adversarial sample and its original malware sample per malware. Edges connect
samples with TLSH distance at most 40.
"""
import networkx as nx
import pandas as pd
import seaborn as sns
import tlsh
from config import OUTPUT_DIR, ARCH
from genetic import AVAILABLE_ELF_MODIFIERS

MODELS = ("Simbiota_40", "Simbiota_ML_LR", "Simbiota_ML_RF")
ELF_MODIFIER_PALETTE = sns.color_palette(("green", "blue", "red"))
ELF_MODIFIER_COLORS = dict(
	zip(
		(modifier.__name__ for modifier in AVAILABLE_ELF_MODIFIERS),
		ELF_MODIFIER_PALETTE,
	)
)


def _node_color(row: pd.Series) -> dict[str, int]:
	color = ELF_MODIFIER_COLORS[row["elf_modifier"]]
	return {
		"r": round(color[0] * 255),
		"g": round(color[1] * 255),
		"b": round(color[2] * 255),
	}


def _select_samples(dataframe: pd.DataFrame) -> pd.DataFrame:
	selected_rows = []
	for malware_id, group in dataframe.groupby("mw", sort=True):
		selected_rows.append(group.iloc[0])  # select the first row for each malware
	return pd.DataFrame(selected_rows).reset_index(drop=True)


def build_similarity_graph(dataframe: pd.DataFrame) -> nx.Graph:
	"""Build a graph containing original and deterministic adversarial samples."""
	selected = _select_samples(dataframe)
	graph = nx.Graph()
	graph.graph["tlsh_threshold"] = 40
	graph.graph["malware_count"] = len(selected)
	graph.graph["sample_count"] = len(selected) * 2

	for node_id, row in selected.iterrows():
		color = _node_color(row)
		graph.add_node(
			str(node_id),
			mw=str(row["mw"]),
			tlsh=str(row["adv_tlsh"]),
			elf_modifier=str(row["elf_modifier"]),
			ratio_sampler=str(row["ratio_sampler"]),
			data_generator=str(row["data_generator"]),
			sample_type="advex",
			viz={"color": color})
  
		grey = {"r": 128, "g": 128, "b": 128, "a": 0.5}
		graph.add_node(
			str(row['mw']),
			tlsh=str(row["tlsh"]),
			sample_type="malware",
			viz={"color": grey},
		)

	nodes = list(graph.nodes(data=True))
	for left_index, (left_id, left_data) in enumerate(nodes):
		for right_id, right_data in nodes[left_index + 1 :]:
			distance = tlsh.diff(left_data["tlsh"], right_data["tlsh"])
			if distance <= 40:
				graph.add_edge(left_id, right_id, weight=41-distance)  # edge weight for Gephi, where higher weight = closer distance

	return graph


def build_graphs() -> None:
	"""Build graphs under ``OUTPUT_DIR``."""
	for model in MODELS:
		input_path = OUTPUT_DIR / f"samples_{ARCH}_{model}.csv"
		df = pd.read_csv(input_path)
		graph = build_similarity_graph(df)
		nx.write_gexf(graph, OUTPUT_DIR / f"similarity_{ARCH}_{model}.gexf")
		print(f"{model}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")


if __name__ == "__main__":
	build_graphs()
