# Scripts

Utility scripts for running various pipeline tasks.

## Directory Structure

```
scripts/
├── datagen/              # Data generation pipeline scripts
│   ├── generate_problems.py         # Generate algorithm problem descriptions
│   ├── generate_problems.sh         # Wrapper script
│   ├── generate_problems_fim.sh     # FIM mode (background)
│   ├── generate_problems_l2r.sh     # L2R mode (background)
│   ├── generate_skeletons.py        # Generate function skeletons
│   ├── generate_skeletons_fim.sh    # FIM skeleton generation (background)
│   ├── generate_skeletons_l2r.sh    # L2R skeleton generation (background)
│   ├── generate_code.py             # Generate function implementations
│   ├── generate_code_fim.sh         # FIM code generation (background)
│   ├── generate_code_l2r.sh         # L2R code generation (background)
│   ├── generate_ratings.py          # Generate code quality ratings
│   ├── generate_ratings_fim.sh      # FIM rating generation (background)
│   ├── generate_ratings_l2r.sh      # L2R rating generation (background)
│   ├── analyze_ratings.py           # Analyze and visualize ratings
│   ├── convert_to_chatml.py         # Convert to ChatML format (multiprocessing)
│   ├── convert_to_chatml.sh         # Wrapper script for conversion
│   ├── convert_to_chatml_fim.sh     # FIM conversion (background)
│   ├── convert_to_chatml_l2r.sh     # L2R conversion (background)
│   ├── RATING_ANALYSIS.md           # Rating analysis documentation
│   └── README.md                    # This file
└── test_client.py        # API client testing utility
```

## Data Generation Scripts

### Problem Description Generation

Generate algorithm problem descriptions using FIM or L2R mode.

**Direct usage:**
```bash
# Generate using FIM mode
python scripts/datagen/generate_problems.py --mode fim

# Generate using L2R mode
python scripts/datagen/generate_problems.py --mode l2r

# Limit number of samples
python scripts/datagen/generate_problems.py --mode fim --num-samples 100
```

**Background execution:**
```bash
# FIM mode (runs in background with logging)
bash scripts/datagen/generate_problems_fim.sh

# L2R mode (runs in background with logging)
bash scripts/datagen/generate_problems_l2r.sh

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

### Code Quality Rating Generation

Generate 5-dimension quality ratings for function implementations.

**Direct usage:**
```bash
# Generate ratings for FIM implementations
python scripts/datagen/generate_ratings.py --source fim

# Generate ratings for L2R implementations
python scripts/datagen/generate_ratings.py --source l2r

# Limit number of samples
python scripts/datagen/generate_ratings.py --source fim --num-samples 100
```

**Background execution:**
```bash
# FIM mode
bash scripts/datagen/generate_ratings_fim.sh

# L2R mode
bash scripts/datagen/generate_ratings_l2r.sh

# Monitor progress
tail -f logs/datagen/rating_fim/*.log
tail -f logs/datagen/rating_l2r/*.log
```

**Configuration:**
- `configs/datagen/rating.yaml`

**Output:**
- FIM mode: `data/generated/func_ratings/fim/ratings.jsonl`
- L2R mode: `data/generated/func_ratings/l2r/ratings.jsonl`

**Rating Dimensions:**
1. Problem Design Quality (1-5)
2. Function Definition & Naming Quality (1-5)
3. Algorithmic Correctness (1-5)
4. Algorithmic Efficiency & Design Choice (1-5)
5. Code Readability & Structure (1-5)

### Rating Analysis and Visualization

Analyze and visualize code quality ratings from FIM and L2R modes.

**Usage:**
```bash
# Basic usage (uses default paths)
python scripts/datagen/analyze_ratings.py

# Custom paths
python scripts/datagen/analyze_ratings.py \
  --fim-path data/generated/func_ratings/fim/ratings.jsonl \
  --l2r-path data/generated/func_ratings/l2r/ratings.jsonl \
  --output-dir results/rating_analysis

# Debug mode
python scripts/datagen/analyze_ratings.py --log-level DEBUG
```

**Output:**
- `data/analysis/rating_comparison/radar_chart.png` - 5-dimension radar chart
- `data/analysis/rating_comparison/distribution_histograms.png` - Score distributions
- `data/analysis/rating_comparison/statistics_report.txt` - Detailed statistics

**See also:** `scripts/datagen/RATING_ANALYSIS.md` for detailed documentation.

### ChatML Format Conversion

Convert rated implementations to ChatML format for model fine-tuning. Uses multiprocessing for efficient conversion.

**Direct usage:**
```bash
# Convert FIM data (uses paths from config)
python scripts/datagen/convert_to_chatml.py --mode fim

# Convert L2R data
python scripts/datagen/convert_to_chatml.py --mode l2r

# Custom paths
python scripts/datagen/convert_to_chatml.py \
  --input data/custom/ratings.jsonl \
  --output data/custom/chatml.jsonl
```

**Background execution:**
```bash
# FIM mode (runs in background with logging)
bash scripts/datagen/convert_to_chatml_fim.sh

# L2R mode (runs in background with logging)
bash scripts/datagen/convert_to_chatml_l2r.sh

# Monitor progress
tail -f logs/datagen/convert_fim/*.log
tail -f logs/datagen/convert_l2r/*.log
```

**Configuration:**
- Input/output paths: `configs/datagen/convert.yaml`
- Quality thresholds: Filters by rating scores
- Multiprocessing: Auto-detects CPU count (configurable)
- Output fields: Only `uid` and `messages` (no metadata)

**Features:**
- Removes hints from problem descriptions
- Extracts function signatures
- Removes docstrings from code
- Filters by quality ratings
- Parallel processing for speed

**Output format:**
```json
{
  "uid": "08eb6bdc5d79d502",
  "messages": [
    {"role": "user", "content": "Problem description\n\nFunction signature"},
    {"role": "assistant", "content": "Function body only"}
  ]
}
```

## Pipeline Overview

The complete data generation pipeline consists of six stages:

1. **Problem Description Generation** → `data/generated/problems_desc/{fim|l2r}/`
2. **Function Skeleton Generation** → `data/generated/func_skeletons/{fim|l2r}/`
3. **Function Implementation Generation** → `data/generated/func_implementations/{fim|l2r}/`
4. **Code Quality Rating** → `data/generated/func_ratings/{fim|l2r}/`
5. **Rating Analysis & Visualization** → `data/analysis/rating_comparison/`
6. **ChatML Format Conversion** → `data/generated/chatml/{fim|l2r}/`

Each stage can be run independently or as part of the full pipeline.

## Testing

Test API client connectivity:
```bash
python scripts/test_client.py
```

