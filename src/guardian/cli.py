import sys
from pathlib import Path

import click

from guardian.object_scanner import read_loose, read_packfile


@click.group()
def cli():
    """Repo-Guardian: Herramienta para auditar repositorios Git"""
    pass

@cli.command()
@click.argument("repo_path")
def scan(repo_path):
    """Escanea un repositorio Git en busca de objetos corruptos."""
    repo_path = Path(repo_path)
    git_dir = repo_path / ".git" if (repo_path / ".git").exists() else repo_path

    if not git_dir.exists():
        click.echo(f"Error: El directorio {git_dir} no existe", err=True)
        return 1

    objects_dir = git_dir / "objects"
    if not objects_dir.exists():
        click.echo(f"Error: No se encontraron objetos en {git_dir}", err=True)
        return 1

    error_count = 0

    # Escanear objetos sueltos
    for obj_file in objects_dir.glob("??/*"):
        try:
            read_loose(obj_file)
        except ValueError as e:
            click.echo(f"✗ Error en {obj_file}: {str(e)}", err=True)
            error_count += 1

    # Escanear packfiles
    pack_dir = objects_dir / "pack"
    if pack_dir.exists():
        for pack_file in pack_dir.glob("*.pack"):
            try:
                read_packfile(pack_file)
            except ValueError as e:
                click.echo(f"✗ Error en {pack_file}: {str(e)}", err=True)
                error_count += 1

    if error_count > 0:
        click.echo(f"\nSe encontraron {error_count} errores", err=True)
        sys.exit(2)  # Salir explícitamente con código 2

    click.echo("No se encontraron errores en los objetos Git")
    return 0

if __name__ == "__main__":
    cli()
