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
            data=(
                b"parent \n"
                b"tree abc\n"
                b"author Test <test@example.com> 1234567890 +0000\n"
                b"committer Test <test@example.com> 1234567890 +0000\n"
                b"\n"
                b"Commit message 1"
            ),
            sha="commit_a"
        ),
        GitObject(
            type="commit",
            data=(
                b"parent commit_a\n"
                b"tree def\n"
                b"author Test <test@example.com> 1234567890 +0000\n"
                b"committer Test <test@example.com> 1234567890 +0000\n"
                b"\n"
                b"Commit message 2"
            ),
            sha="commit_b"
        ),
        GitObject(
            type="commit",
            data=(
                b"parent commit_b\n"
                b"tree ghi\n"
                b"author Test <test@example.com> 1234567890 +0000\n"
                b"committer Test <test@example.com> 1234567890 +0000\n"
                b"\n"
                b"Commit message 3"
            ),
            sha="commit_c"
        ),
    ]

def test_build_dag_empty():
    """Prueba que un DAG vacío retorna un grafo sin nodos."""
    dag = build_dag([])
    assert isinstance(dag, DiGraph)
    assert dag.number_of_nodes() == 0
    assert dag.number_of_edges() == 0

def test_build_dag_structure(sample_commits):
    """Prueba que el DAG construye correctamente la estructura commit-padre."""
    dag = build_dag(sample_commits)

    assert isinstance(dag, DiGraph)
    assert dag.number_of_nodes() == 3
    assert dag.number_of_edges() == 2

    # Verificar nodos
    assert set(dag.nodes) == {"commit_a", "commit_b", "commit_c"}

    # Verificar aristas
    assert ("commit_a", "commit_b") in dag.edges
    assert ("commit_b", "commit_c") in dag.edges

    # Verificar metadatos
    assert dag.nodes["commit_a"]["author"] == "Test <test@example.com> 1234567890 +0000"
    assert dag.nodes["commit_c"]["message"] == "Commit message 3"

def test_build_dag_invalid_objects():
    """Prueba que el DAG ignora objetos no commit."""
    invalid_objects = [
        GitObject(type="blob", data=b"blob data", sha="123abc"),
        GitObject(type="tree", data=b"tree data", sha="456def"),
    ]
    dag = build_dag(invalid_objects)
    assert dag.number_of_nodes() == 0
    assert dag.number_of_edges() == 0
