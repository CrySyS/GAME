import numpy as np
import tlsh
import networkx as nx
import logging
logger = logging.getLogger(__name__)


class Simbiota():

    def __init__(self, threshold: int):
        self.similarity_threshold = threshold
        
        
    def fit(self, X, y=None):
        self.model = self._get_dominating_set_greedy(X)
        logger.info("Size of dominating set: %d", len(self.model))
        
        
    def predict(self, X):
        predictions = []
        for x_tlsh in X:
            predictions.append(self.predict_single(x_tlsh))
        return np.array(predictions)


    def _get_dominating_set_greedy(self, hashes) -> np.ndarray:
        logger.info('W/ greedy global dominating set algo')
        G = nx.Graph()
        for hash in hashes:
            G.add_node(hash)
            for node in G.nodes:
                if tlsh.diff(hash, node) <= self.similarity_threshold:
                    G.add_edge(hash, node) # G includes self-edges for span calculation

        D = set()
        uncovered_nodes = set(G.nodes)
        span_dict = {node: len(G.adj[node]) for node in G.nodes}

        while uncovered_nodes:
            next_node = max(span_dict, key=span_dict.get)
            D.add(next_node)
            span_dict.pop(next_node)
            
            for node in G.adj[next_node]:
                if node in span_dict:
                    span_dict[node] -= 1
                if node != next_node and node in uncovered_nodes:
                    for neighbour in G.adj[node]:
                        if neighbour in span_dict:
                            span_dict[neighbour] -= 1
                uncovered_nodes.discard(node)

        assert nx.is_dominating_set(G, D) == True
        return np.array(list(D))
    
    
    def predict_single(self, x_tlsh: str) -> int:
        for ds_tlsh in self.model:
            if tlsh.diff(x_tlsh, ds_tlsh) <= self.similarity_threshold:
                return 1
        return 0
    
    
    def to_dict(self) -> dict:
        return {
            "detector_type": "Simbiota",
            "similarity_threshold": self.similarity_threshold,
            "dominating_set_size": len(self.model)
        }
    
    
    def __str__(self):
        return f"Simbiota_{self.similarity_threshold}"
    
    
if __name__ == "__main__":
    from config import DATA_DIR, ARCH, MALWARE_DIR, BENIGN_DIR
    import pandas as pd
    from sklearn.metrics import confusion_matrix
    
    
    detector = Simbiota(40)
    data_file = pd.read_csv(DATA_DIR / f"{ARCH}_medium_tlsh.csv")
    X = data_file.loc[data_file["label"] == 1, "tlsh"].values.tolist()
    detector.fit(X)
    print(f"Size of dominating set: {len(detector.model)}")
    
    mw_hashes = [tlsh.hash(open(file_path, 'rb').read()) for file_path in MALWARE_DIR.iterdir()]
    bn_hashes = [tlsh.hash(open(file_path, 'rb').read()) for file_path in BENIGN_DIR.iterdir()]
    
    predictions = detector.predict(mw_hashes + bn_hashes)
    true_labels = [1] * len(mw_hashes) + [0] * len(bn_hashes)
    cm = confusion_matrix(true_labels, predictions)
    tn, fp, fn, tp = cm.ravel().tolist()
    print(f"Simbiota: True Negatives: {tn}, False Positives: {fp}, False Negatives: {fn}, True Positives: {tp}")
    
    # 759e87ae50268c27acd60a2365109bed8ca5f29eb178b939eb70d57a85fd7fca is FP