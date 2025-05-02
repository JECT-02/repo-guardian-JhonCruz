import pytest
from guardian.dag_builder import build_dag
from guardian.object_scanner import GitObject
from networkx import DiGraph


@pytest.fixture
def sample_commits() -> list[GitObject]:
    """Fixture con 3 commits simulados (padre → hijo)."""
    return [
        GitObject(
            type="commit",
            data=b"parent \0tree abc...",
            sha="commit_a"
        ),
        GitObject(
            type="commit",
            data=b"parent commit_a\0tree def...",
            sha="commit_b"
        ),
        GitObject(
            type="commit",
            data=b"parent commit_b\0tree ghi...",
            sha="commit_c"
        ),
    ]


def test_build_dag_empty():
    """Prueba que un DAG vacío retorna un grafo sin nodos."""
    dag = build_dag([])
    assert isinstance(dag, DiGraph)
    assert dag.number_of_nodes() == 0


def test_build_dag_structure(sample_commits):
    """Prueba que el DAG retorna un grafo (placeholder para D-4)."""
    dag = build_dag(sample_commits)
    assert isinstance(dag, DiGraph)  # Placeholder: retorna grafo vacío


def test_build_dag_invalid_objects():
    """Prueba que el DAG retorna grafo vacío con objetos no commit."""
    invalid_objects = [
        GitObject(type="blob", data=b"blob data", sha="123abc"),
        GitObject(type="tree", data=b"tree data", sha="456def"),
    ]
    dag = build_dag(invalid_objects)
    assert dag.number_of_nodes() == 0
