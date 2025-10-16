# Scripts

Utility scripts for running various pipeline tasks.

## Data Generation Scripts

### generate_funcnames.py (Unified Script)

Generate function names using FIM or L2R mode.

**Usage:**
```bash
# Generate using FIM mode
python scripts/generate_funcnames.py --mode fim

# Generate using L2R mode
python scripts/generate_funcnames.py --mode l2r

# Use custom config
python scripts/generate_funcnames.py --mode fim --config my_config.yaml
```

**Configurations:**
- FIM mode: `configs/datagen/fim.yaml`
- L2R mode: `configs/datagen/l2r.yaml`

**Output:**
- FIM mode: `data/generated/names/fim/*.jsonl`
- L2R mode: `data/generated/names/l2r/*.jsonl`

### generate_funcnames_fim.sh / generate_funcnames_l2r.sh

Shell script wrappers for convenience.

**Usage:**
```bash
# FIM mode
bash scripts/generate_funcnames_fim.sh

# L2R mode
bash scripts/generate_funcnames_l2r.sh
```

## CLI Usage

The new CLI is organized into subcommands:

### Data Generation
```bash
# Generate function names - FIM mode
python -m evoselfcode.cli datagen generate-names --config configs/datagen/fim.yaml

# Generate function names - L2R mode
python -m evoselfcode.cli datagen generate-names --config configs/datagen/l2r.yaml

# Or use the unified script
python scripts/generate_funcnames.py --mode fim
python scripts/generate_funcnames.py --mode l2r

# Generate code (TODO)
python -m evoselfcode.cli datagen generate-code --names data/generated/names/filtered.jsonl

# Score candidates (TODO)
python -m evoselfcode.cli datagen score --input data/generated/code/raw.jsonl

# Filter candidates (TODO)
python -m evoselfcode.cli datagen filter --input data/generated/code/scored.jsonl --output data/generated/code/filtered.jsonl
```

### Training Pipeline
```bash
# Generate samples
python -m evoselfcode.cli pipeline generate --config configs/generation.yaml

# Score samples
python -m evoselfcode.cli pipeline score --config configs/generation.yaml

# Filter samples
python -m evoselfcode.cli pipeline filter --config configs/generation.yaml

# Train D2C model
python -m evoselfcode.cli pipeline train-d2c --config configs/train_d2c.yaml

# Train C2D model
python -m evoselfcode.cli pipeline train-c2d --config configs/train_c2d.yaml

# Run iterative training
python -m evoselfcode.cli pipeline iterate --config configs/iterate.yaml
```

### Evaluation
```bash
# Evaluate on specific benchmark
python -m evoselfcode.cli eval humaneval --ckpt checkpoints/model_v1
python -m evoselfcode.cli eval mbpp --ckpt checkpoints/model_v1
python -m evoselfcode.cli eval lcb --ckpt checkpoints/model_v1
python -m evoselfcode.cli eval bigcodebench --ckpt checkpoints/model_v1

# Evaluate on all benchmarks
python -m evoselfcode.cli eval all --ckpt checkpoints/model_v1
```

## Help

Get help for any command:
```bash
python -m evoselfcode.cli --help
python -m evoselfcode.cli datagen --help
python -m evoselfcode.cli pipeline --help
python -m evoselfcode.cli eval --help
```

