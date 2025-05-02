import sys
from unittest.mock import MagicMock, patch

import click  # Añadido para el tipo de excepción
import pytest
from click.testing import CliRunner
from guardian.cli import _get_git_dir, _scan_repository, cli


@pytest.fixture
def runner():
    return CliRunner()


def test_get_git_dir_valid(tmp_path):
    """Prueba detección de directorio .git válido."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "objects").mkdir()
    assert _get_git_dir(tmp_path) == tmp_path / ".git"


def test_get_git_dir_invalid(tmp_path):
    """Prueba detección de directorio inválido."""
    with pytest.raises(click.BadParameter):
        _get_git_dir(tmp_path / "nonexistent")


def test_scan_repository_no_errors(tmp_path, mocker):
    """Prueba escaneo sin errores."""
    objects_dir = tmp_path / "objects"
    objects_dir.mkdir()
    (objects_dir / "ab").mkdir()
    (objects_dir / "ab" / "cdef123").touch()

    mocker.patch("guardian.cli.read_loose", return_value=MagicMock())
    mocker.patch("guardian.cli.read_packfile", return_value=[])

    assert _scan_repository(tmp_path) == 0


def test_scan_repository_with_errors(tmp_path, mocker):
    """Prueba escaneo con errores."""
    objects_dir = tmp_path / "objects"
    objects_dir.mkdir()
    (objects_dir / "ab").mkdir()
    (objects_dir / "ab" / "cdef123").touch()

    mocker.patch("guardian.cli.read_loose", side_effect=ValueError("Error simulado"))
    assert _scan_repository(tmp_path) == 1


def test_cli_scan_valid_repo(runner, tmp_path, mocker):
    """Prueba CLI con repositorio válido."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "objects").mkdir()

    mocker.patch("guardian.cli._scan_repository", return_value=0)
    result = runner.invoke(cli, ["scan", str(tmp_path)])
    assert result.exit_code == 0
    assert "No se encontraron errores" in result.output


def test_cli_scan_invalid_repo(runner, tmp_path):
    """Prueba CLI con repositorio inválido."""
    result = runner.invoke(cli, ["scan", str(tmp_path / "nonexistent")])
    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_main_execution(mocker):
    """Prueba ejecución como script."""
    mock_cli = mocker.patch("guardian.cli.cli")
    with patch.object(sys, 'argv', ['cli.py']):
        if __name__ == "__main__":
            sys.modules["__main__"].__dict__.clear()
            exec(open("src/guardian/cli.py").read())
            mock_cli.assert_called_once()
