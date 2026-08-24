import pytest
from typer.testing import CliRunner
from archaeologist.cli import app

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "The Codebase Archaeologist" in result.output

def test_cli_ask_without_ingest():
    result = runner.invoke(app, ["ask", "What is the architecture?"])
    # Should exit cleanly or report no chunks found
    assert result.exit_code in [0, 1]
