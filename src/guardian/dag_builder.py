from typing import List

from networkx import DiGraph

from .object_scanner import GitObject


def build_dag(commits: List[GitObject]) -> DiGraph:
    """Construye un DAG a partir de objetos Git commit válidos.

    Args:
        commits: Lista de objetos Git con tipo 'commit'.

    Returns:
        Grafo dirigido acíclico (DAG) con relaciones padre-hijo.
    """
    return DiGraph()  # Placeholder para D-4 (tests pasarán)
