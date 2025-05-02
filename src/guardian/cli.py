import sys
from pathlib import Path

import click

from guardian.object_scanner import read_loose, read_packfile


@click.group()
def cli():
    """Repo-Guardian: Herramienta para auditar repositorios Git"""
    pass


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True, path_type=Path))
def scan(repo_path: Path):
    """Escanea un repositorio Git en busca de objetos corruptos."""
    try:
        git_dir = _get_git_dir(repo_path)
        error_count = _scan_repository(git_dir)

        if error_count > 0:
            click.echo(f"\nSe encontraron {error_count} errores", err=True)
            sys.exit(2)

        click.echo("✅ No se encontraron errores en los objetos Git")
        sys.exit(0)

    except click.BadParameter as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


def _get_git_dir(repo_path: Path) -> Path:
    """Obtiene la ruta del directorio .git válido."""
    git_dir = repo_path / ".git" if (repo_path / ".git").exists() else repo_path

    if not git_dir.exists():
        raise click.BadParameter(f"El directorio {git_dir} no existe")

    objects_dir = git_dir / "objects"
    if not objects_dir.exists():
        raise click.BadParameter(f"No se encontraron objetos en {git_dir}")

    return git_dir


def _scan_repository(git_dir: Path) -> int:
    """Realiza el escaneo de objetos Git."""
    error_count = 0
    objects_dir = git_dir / "objects"

    # Escanear objetos sueltos
    for obj_file in objects_dir.glob("??/*"):
        try:
            read_loose(obj_file)
            click.echo(f"✓ {obj_file} es válido", err=True)
        except ValueError as e:
            click.echo(f"✗ Error en {obj_file}: {str(e)}", err=True)
            error_count += 1

    # Escanear packfiles
    pack_dir = objects_dir / "pack"
    if pack_dir.exists():
        for pack_file in pack_dir.glob("*.pack"):
            try:
                read_packfile(pack_file)
                click.echo(f"✓ {pack_file} es válido", err=True)
            except ValueError as e:
                click.echo(f"✗ Error en {pack_file}: {str(e)}", err=True)
                error_count += 1

    return error_count


def main():
    cli()


if __name__ == "__main__":
    main()
