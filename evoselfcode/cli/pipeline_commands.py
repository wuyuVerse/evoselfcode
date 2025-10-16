from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(add_completion=False, help="Training pipeline commands")


@app.command("generate")
def generate(config: Path = typer.Option(None, help="Generation config")):
    """Generate candidate samples"""
    from ..pipeline.sampling import cmd_generate
    cmd_generate(config)


@app.command("score")
def score(config: Path = typer.Option(None, help="Scoring config")):
    """Score generated candidates"""
    from ..pipeline.scoring import cmd_score
    cmd_score(config)


@app.command("filter")
def filter(config: Path = typer.Option(None, help="Filtering config")):
    """Filter candidates by quality"""
    from ..pipeline.filtering import cmd_filter
    cmd_filter(config)


@app.command("train-d2c")
def train_d2c(config: Path = typer.Option(None, help="Train D2C config")):
    """Train description-to-code model"""
    from ..pipeline.train_sft import cmd_train_d2c
    cmd_train_d2c(config)


@app.command("train-c2d")
def train_c2d(config: Path = typer.Option(None, help="Train C2D config")):
    """Train code-to-description model"""
    from ..pipeline.dual_model import cmd_train_c2d
    cmd_train_c2d(config)


@app.command("iterate")
def iterate(config: Path = typer.Option(None, help="Iteration config")):
    """Run iterative self-training loop"""
    from ..pipeline.iteration import cmd_iterate
    cmd_iterate(config)

