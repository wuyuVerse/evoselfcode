from __future__ import annotations

import logging
from pathlib import Path

import typer

app = typer.Typer(add_completion=False, help="EvoSelfCode CLI")


@app.callback(invoke_without_command=True)
def main(
    log_level: str = typer.Option("INFO", help="Logging level"),
):
    """EvoSelfCode - Iterative Self-Training and Dual Learning for Python Code Generation"""
    # Setup basic logging (task-specific loggers will be created by each command)
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(message)s")


# Import subcommands
from . import datagen_commands, eval_commands, pipeline_commands

# Register subcommands
app.add_typer(datagen_commands.app, name="datagen", help="Data generation commands")
app.add_typer(pipeline_commands.app, name="pipeline", help="Training pipeline commands")
app.add_typer(eval_commands.app, name="eval", help="Evaluation commands")


if __name__ == "__main__":
    app()

