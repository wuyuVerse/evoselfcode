from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(add_completion=False, help="Evaluation commands")


@app.command("humaneval")
def humaneval(
    ckpt: Path = typer.Option(..., "--ckpt", help="Checkpoint path"),
    config: Path = typer.Option(None, "--config", help="Eval config"),
):
    """Evaluate on HumanEval benchmark"""
    from ..evaluation.humaneval import cmd_eval
    cmd_eval(ckpt, config)


@app.command("mbpp")
def mbpp(
    ckpt: Path = typer.Option(..., "--ckpt", help="Checkpoint path"),
    config: Path = typer.Option(None, "--config", help="Eval config"),
):
    """Evaluate on MBPP benchmark"""
    from ..evaluation.mbpp import cmd_eval
    cmd_eval(ckpt, config)


@app.command("lcb")
def lcb(
    ckpt: Path = typer.Option(..., "--ckpt", help="Checkpoint path"),
    config: Path = typer.Option(None, "--config", help="Eval config"),
):
    """Evaluate on LiveCodeBench"""
    from ..evaluation.lcb import cmd_eval
    cmd_eval(ckpt, config)


@app.command("bigcodebench")
def bigcodebench(
    ckpt: Path = typer.Option(..., "--ckpt", help="Checkpoint path"),
    config: Path = typer.Option(None, "--config", help="Eval config"),
):
    """Evaluate on BigCodeBench"""
    from ..evaluation.bigcodebench import cmd_eval
    cmd_eval(ckpt, config)


@app.command("all")
def all_benchmarks(
    ckpt: Path = typer.Option(..., "--ckpt", help="Checkpoint path"),
    config: Path = typer.Option(None, "--config", help="Eval config"),
):
    """Evaluate on all benchmarks"""
    typer.echo("Running all benchmarks...")
    
    typer.echo("\n[1/4] HumanEval")
    from ..evaluation.humaneval import cmd_eval as humaneval_eval
    humaneval_eval(ckpt, config)
    
    typer.echo("\n[2/4] MBPP")
    from ..evaluation.mbpp import cmd_eval as mbpp_eval
    mbpp_eval(ckpt, config)
    
    typer.echo("\n[3/4] LiveCodeBench")
    from ..evaluation.lcb import cmd_eval as lcb_eval
    lcb_eval(ckpt, config)
    
    typer.echo("\n[4/4] BigCodeBench")
    from ..evaluation.bigcodebench import cmd_eval as bigcodebench_eval
    bigcodebench_eval(ckpt, config)
    
    typer.echo("\n✓ All benchmarks completed")

