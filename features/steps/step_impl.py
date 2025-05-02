import shlex
import subprocess
from pathlib import Path

from behave import given, then, when


@given('un repositorio con packfile corrupto "{repo_path}"')
def step_given_repo_with_corrupt_pack(context, repo_path):
    context.repo_path = Path(repo_path)
    assert (context.repo_path / "objects" / "pack").exists(), (
        f"No se encontró packfile en {repo_path}"
    )


@when('ejecuto el comando "{command}"')
def step_when_run_command(context, command):
    cmd = shlex.split(command)
    context.result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )


@then('el comando debe fallar con código de salida {code:d}')
def step_then_command_should_fail(context, code):
    assert context.result.returncode == code, (
        f"Expected exit code {code}, got {context.result.returncode}\n"
        f"Output: {context.result.stdout}\n"
        f"Error: {context.result.stderr}"
    )


@then('la salida debe contener "{text}"')
def step_then_output_should_contain(context, text):
    output = context.result.stdout + context.result.stderr
    assert text in output, (
        f"Expected '{text}' not found in output. Actual output:\n{output}"
    )
