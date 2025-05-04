from typing import Any, Dict, List

from networkx import DiGraph

from .object_scanner import GitObject


def parse_commit(commit: GitObject) -> Dict[str, Any]:
    """Parsea los metadatos de un objeto commit Git."""
    if commit.type != "commit":
        raise ValueError(f"Expected commit object, got {commit.type}")

    try:
        content = commit.data.decode(errors='replace')
    except UnicodeDecodeError as e:
        raise ValueError(f"Invalid commit encoding: {str(e)}") from e

    parents: List[str] = []
    metadata: Dict[str, str] = {}

    # Separar header y message
    parts = content.split('\n\n', 1)
    header = parts[0]
    if len(parts) > 1 and parts[1].strip():
        metadata["message"] = parts[1].strip()

    # Procesar líneas del header
    for line in header.split('\n'):
        if line.startswith('parent '):
            parts = line.split()
            if len(parts) >= 2:
                parents.append(parts[1])
        elif ' ' in line:
            key, value = line.split(' ', 1)
            metadata[key] = value

    return {"parents": parents, "metadata": metadata}

def build_dag(commits: List[GitObject]) -> DiGraph:
    """Construye un DAG a partir de objetos Git commit válidos."""
    dag = DiGraph()
    commit_map: Dict[str, Dict[str, Any]] = {}

    for commit in commits:
        if commit.type != "commit":
            continue

        try:
            data = parse_commit(commit)
            commit_map[commit.sha] = data
            dag.add_node(commit.sha, **data["metadata"])

            for parent_sha in data["parents"]:
                if parent_sha in commit_map:
                    dag.add_edge(parent_sha, commit.sha)
        except ValueError:
            continue

    return dag
