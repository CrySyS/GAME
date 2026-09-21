from genetic.gene import Gene
import logging
logger = logging.getLogger(__name__)


class Strategy:
    """
    Represents a full chromosome: a chain of Genes to be executed in sequence.
    Currently, a Strategy consists of a single Gene, but this can be extended to multiple Genes in the future.
    """
    
    def __init__(self, genes: list[Gene]):
        self.genes : list[Gene] = genes
        self.fitness = None


    def __str__(self):
        return f"{self.genes[0]}, fitness={self.fitness:.2f})"


    def execute(self, input_file: bytes) -> bytes:
        """Executes the strategy's chain of genes on a file."""
        for gene in self.genes:
            input_file = gene.execute(input_file)
        return input_file


    @classmethod
    def create_random(cls):
        return cls([Gene.create_random()])
    
    
    def crossover(self, other_strategy: 'Strategy') -> 'Strategy':
        child_genes = []
        for gene_self, gene_other in zip(self.genes, other_strategy.genes):
            child_gene = gene_self.crossover(gene_other, weights=[self.fitness, other_strategy.fitness])
            child_genes.append(child_gene)
        return Strategy(child_genes)


    def mutate(self, mutation_chances):
        mutated = False
        for gene in self.genes:
                mutated |= gene.mutate(mutation_chances)
        if mutated:
            self.fitness = None  # Reset fitness since the strategy has changed


    def elf_modifier_names(self):
        return [gene.elf_modifier.__class__.__name__ for gene in self.genes]
    
    
    def to_dict(self):
        return {
            "genes": [gene.to_dict() for gene in self.genes],
            "fitness": self.fitness
        }


    @classmethod
    def from_dict(cls, saved_obj):
        genes = [Gene.from_dict(gene_data) for gene_data in saved_obj["genes"]]
        strategy = cls(genes)
        strategy.fitness = saved_obj["fitness"]
        return strategy