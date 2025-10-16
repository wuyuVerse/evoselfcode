from __future__ import annotations

import asyncio
from pathlib import Path

import typer

app = typer.Typer(add_completion=False, help="Data generation commands")


@app.command("generate-names")
def generate_names(
    mode: str = typer.Option(..., "--mode", help="Generation mode: 'fim' or 'l2r'"),
    config: Path = typer.Option(None, "--config", help="Custom config path (default: configs/datagen/{mode}.yaml)"),
    num_samples: int = typer.Option(None, "--num-samples", help="Number of samples to generate (overrides config)"),
):
    """Generate function names using FIM or L2R mode"""
    import json
    from ..services.datagen_service import DataGenService
    from ..utils.logger import setup_task_logger, LoggerManager
    from ..constants import PROJECT_ROOT
    
    # Determine config path
    if config is None:
        config = PROJECT_ROOT / f"configs/datagen/{mode}.yaml"
    
    if not config.exists():
        typer.echo(f"Error: Config file not found: {config}", err=True)
        raise typer.Exit(1)
    
    # Setup logging
    log_dir = PROJECT_ROOT / "logs"
    LoggerManager.setup_base_dir(log_dir)
    logger = setup_task_logger("datagen", mode)
    
    mode_upper = "FIM" if mode == "fim" else "L2R"
    logger.info(f"Starting {mode_upper} function name generation")
    logger.info(f"Config: {config}")
    
    # Run generation
    async def run():
        service = DataGenService.from_config_path(config, task=mode, logger=logger)
        results = await service.generate_function_names(mode=mode_upper, num_samples=num_samples)
        
        # Save results
        out_dir = PROJECT_ROOT / f"data/generated/names/{mode}"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / f"{mode}_results.jsonl"
        
        with open(output_file, "w", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        
        logger.info(f"Saved {len(results)} results to: {output_file}")
        return len(results)
    
    try:
        total = asyncio.run(run())
        logger.info(f"✓ Generation completed: {total} function names")
    except Exception as e:
        logger.exception(f"Generation failed: {e}")
        raise typer.Exit(1)
    finally:
        LoggerManager.close_all()


@app.command("generate-code")
def generate_code(
    config: Path = typer.Option("configs/datagen.yaml", "--config", help="Datagen config path"),
    names_file: Path = typer.Option(..., "--names", help="Input function names JSONL file"),
):
    """Generate code completions for given function names"""
    typer.echo(f"Generating code for names from: {names_file}")
    typer.echo("(Not yet implemented)")
    # TODO: Implement code generation


@app.command("score")
def score_candidates(
    config: Path = typer.Option("configs/datagen.yaml", "--config", help="Datagen config path"),
    input_file: Path = typer.Option(..., "--input", help="Input JSONL file to score"),
    output_file: Path = typer.Option(None, "--output", help="Output scored JSONL file"),
):
    """Score generated candidates using perplexity"""
    typer.echo(f"Scoring candidates from: {input_file}")
    typer.echo("(Not yet implemented)")
    # TODO: Implement scoring


@app.command("filter")
def filter_candidates(
    config: Path = typer.Option("configs/datagen.yaml", "--config", help="Datagen config path"),
    input_file: Path = typer.Option(..., "--input", help="Input JSONL file to filter"),
    output_file: Path = typer.Option(..., "--output", help="Output filtered JSONL file"),
):
    """Filter candidates by quality metrics"""
    typer.echo(f"Filtering candidates from: {input_file}")
    typer.echo("(Not yet implemented)")
    # TODO: Implement filtering

