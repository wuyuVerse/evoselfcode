# Scripts

Utility scripts for running various pipeline tasks.

## Directory Structure

```
scripts/
├── datagen/              # Data generation pipeline scripts
│   ├── generate_funcnames.py        # Generate algorithm problem descriptions
│   ├── generate_funcnames.sh        # Wrapper script
│   ├── generate_funcnames_fim.sh    # FIM mode (background)
│   ├── generate_funcnames_l2r.sh    # L2R mode (background)
│   ├── generate_skeletons.py        # Generate function skeletons
│   ├── generate_skeletons_fim.sh    # FIM skeleton generation (background)
│   ├── generate_skeletons_l2r.sh    # L2R skeleton generation (background)
│   ├── generate_code.py             # Generate function implementations
│   ├── generate_code_fim.sh         # FIM code generation (background)
│   └── generate_code_l2r.sh         # L2R code generation (background)
└── test_client.py        # API client testing utility
```

## Data Generation Scripts

### Problem Description Generation

Generate algorithm problem descriptions using FIM or L2R mode.

**Direct usage:**
```bash
# Generate using FIM mode
python scripts/datagen/generate_funcnames.py --mode fim

# Generate using L2R mode
python scripts/datagen/generate_funcnames.py --mode l2r

# Limit number of samples
python scripts/datagen/generate_funcnames.py --mode fim --num-samples 100
```

**Background execution:**
```bash
# FIM mode (runs in background with logging)
bash scripts/datagen/generate_funcnames_fim.sh

# L2R mode (runs in background with logging)
bash scripts/datagen/generate_funcnames_l2r.sh

# Monitor progress
tail -f logs/datagen/problems_fim/generation_*.log
tail -f logs/datagen/problems_l2r/generation_*.log
```

**Configurations:**
- FIM mode: `configs/datagen/fim.yaml`
- L2R mode: `configs/datagen/l2r.yaml`

**Output:**
- FIM mode: `data/generated/problems_desc/fim/fim_results.jsonl`
- L2R mode: `data/generated/problems_desc/l2r/l2r_results.jsonl`

### Function Skeleton Generation

Generate Python function skeletons from problem descriptions.

**Direct usage:**
```bash
# Generate from FIM problems
python scripts/datagen/generate_skeletons.py --source fim

# Generate from L2R problems
python scripts/datagen/generate_skeletons.py --source l2r

# Limit number of samples
python scripts/datagen/generate_skeletons.py --source fim --num-samples 50
```

**Background execution:**
```bash
# FIM mode
bash scripts/datagen/generate_skeletons_fim.sh

# L2R mode
bash scripts/datagen/generate_skeletons_l2r.sh

# Monitor progress
tail -f logs/datagen/skeleton_fim/generation_*.log
tail -f logs/datagen/skeleton_l2r/generation_*.log
```

**Configuration:**
- `configs/datagen/skeleton.yaml`

**Output:**
- FIM mode: `data/generated/func_skeletons/fim/skeletons.jsonl`
- L2R mode: `data/generated/func_skeletons/l2r/skeletons.jsonl`

### Function Implementation Generation

Generate complete Python function implementations from skeletons.

**Direct usage:**
```bash
# Generate from FIM skeletons
python scripts/datagen/generate_code.py --source fim

# Generate from L2R skeletons
python scripts/datagen/generate_code.py --source l2r

# Limit number of samples
python scripts/datagen/generate_code.py --source fim --num-samples 50
```

**Background execution:**
```bash
# FIM mode
bash scripts/datagen/generate_code_fim.sh

# L2R mode
bash scripts/datagen/generate_code_l2r.sh

# Monitor progress
tail -f logs/datagen/codegen_fim/generation_*.log
tail -f logs/datagen/codegen_l2r/generation_*.log
```

**Configuration:**
- `configs/datagen/codegen.yaml`

**Output:**
- FIM mode: `data/generated/func_implementations/fim/implementations.jsonl`
- L2R mode: `data/generated/func_implementations/l2r/implementations.jsonl`

## Pipeline Overview

The complete data generation pipeline consists of three stages:

1. **Problem Description Generation** → `data/generated/problems_desc/{fim|l2r}/`
2. **Function Skeleton Generation** → `data/generated/func_skeletons/{fim|l2r}/`
3. **Function Implementation Generation** → `data/generated/func_implementations/{fim|l2r}/`

Each stage can be run independently or as part of the full pipeline.

## Testing

Test API client connectivity:
```bash
python scripts/test_client.py
```

