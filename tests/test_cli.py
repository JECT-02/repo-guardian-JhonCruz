import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner
from guardian.cli import _get_commits_from_repo, _get_git_dir, _scan_repository, cli
from guardian.object_scanner import GitObject


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_git_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        # Crear estructura de repositorio con objetos y packfiles simulados
        objects_dir = repo_path / ".git" / "objects" / "ab"
        objects_dir.mkdir(parents=True)
        (objects_dir / "cdef123").touch()  # Objeto suelto simulado
        pack_dir = repo_path / ".git" / "objects" / "pack"
        pack_dir.mkdir(parents=True)
        (pack_dir / "test.pack").touch()  # Packfile simulado
        yield repo_path


def test_get_git_dir_valid(temp_git_repo):
    assert _get_git_dir(temp_git_repo) == temp_git_repo / ".git"


def test_get_git_dir_invalid():
    with pytest.raises(click.BadParameter):
        _get_git_dir(Path("/nonexistent"))


def test_get_git_dir_no_objects():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        git_dir = repo_path / ".git"
        git_dir.mkdir()
        with pytest.raises(click.BadParameter):
            _get_git_dir(repo_path)


def test_scan_repository_no_errors(temp_git_repo, mocker):
    mocker.patch(
        "guardian.cli.read_loose",
        return_value=GitObject("blob", b"data", "sha")
    )
    mocker.patch("guardian.cli.read_packfile", return_value=[])
    assert _scan_repository(temp_git_repo / ".git") == 0


def test_scan_repository_with_errors(temp_git_repo, mocker):
    mocker.patch(
        "guardian.cli.read_loose",
        side_effect=ValueError("Invalid object")
    )
    mocker.patch(
        "guardian.cli.read_packfile",
        side_effect=ValueError("Invalid packfile signature")
    )
    assert _scan_repository(temp_git_repo / ".git") == 2  # 1 objeto suelto + 1 packfile


def test_get_commits_from_repo(temp_git_repo, mocker):
    mock_commit = GitObject("commit", b"tree abc\nparent 123", "sha1")
    mocker.patch("guardian.cli.read_loose", return_value=mock_commit)
    mocker.patch("guardian.cli.read_packfile", return_value=[mock_commit])
    commits = _get_commits_from_repo(temp_git_repo / ".git")
    assert len(commits) == 2  # 1 de objeto suelto + 1 de packfile
    assert commits[0].sha == "sha1"


def test_get_commits_from_repo_no_objects(temp_git_repo, mocker):
    # Simular que no hay objetos válidos
    mocker.patch(
        "guardian.cli.read_loose",
        side_effect=ValueError("Invalid object")
    )
    mocker.patch(
        "guardian.cli.read_packfile",
        side_effect=ValueError("Invalid packfile")
    )
    commits = _get_commits_from_repo(temp_git_repo / ".git")
    assert len(commits) == 0


def test_cli_scan_valid_repo(runner, temp_git_repo, mocker):
    mocker.patch("guardian.cli._scan_repository", return_value=0)
    result = runner.invoke(cli, ["scan", str(temp_git_repo)])
    assert result.exit_code == 0
    assert "No se encontraron errores" in result.output


'''def test_cli_scan_invalid_repo(runner):
    result = runner.invoke(cli, ["scan", "/nonexistent"])
    assert result.exit_code == 1  # _get_git_dir lanza BadParameter
    assert "El directorio /nonexistent no existe" in result.output, \
        f"Unexpected output: {result.output}"'''


def test_cli_scan_with_errors(runner, temp_git_repo, mocker):
    mocker.patch("guardian.cli._scan_repository", return_value=2)
    result = runner.invoke(cli, ["scan", str(temp_git_repo)])
    assert result.exit_code == 2
    assert "Se encontraron 2 errores" in result.output


def test_cli_export_graph(runner, temp_git_repo, mocker):
    mocker.patch(
        "guardian.cli._get_commits_from_repo",
        return_value=[GitObject("commit", b"tree abc", "sha1")]
    )
    mocker.patch("networkx.write_graphml")
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["export-graph", str(temp_git_repo), "-o", "test.graphml"]
        )
        assert result.exit_code == 0
        assert "DAG exported to test.graphml" in result.output


def test_cli_export_graph_error(runner, temp_git_repo, mocker):
    mocker.patch(
        "guardian.cli._get_commits_from_repo",
        side_effect=Exception("Graph error")
    )
    result = runner.invoke(cli, ["export-graph", str(temp_git_repo)])
    assert result.exit_code == 1
    assert "Error: Graph error" in result.output


def test_main_execution(mocker):
    mock_cli = mocker.patch("guardian.cli.cli")
    with patch.object(sys, "__name__", "__main__"):
        from guardian.cli import main
        main()
        mock_cli.assert_called_once()
