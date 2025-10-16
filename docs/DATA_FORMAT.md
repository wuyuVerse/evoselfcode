# Data Output Formats

This document describes the output format for generated data.

## Function Name Generation Output

### Location
- **FIM mode**: `data/generated/names/fim/fim_results.jsonl`
- **L2R mode**: `data/generated/names/l2r/l2r_results.jsonl`

### Format
Each line is a JSON object with the following fields:

```json
{
  "func_name": "calculate_sum",
  "source": "FIM",
  "raw_text": "calculate_sum"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `func_name` | string | The extracted function name (after filtering and validation) |
| `source` | string | Generation mode: `"FIM"` or `"L2R"` |
| `raw_text` | string | Raw text returned by the model before extraction |

### Filters Applied

The function names go through several filters:

1. **Regex validation**: Must match `^[a-z_][a-z0-9_]{2,64}$`
   - Start with lowercase letter or underscore
   - Contain only lowercase letters, digits, and underscores
   - Length between 2-64 characters

2. **Weaklist filtering**: Excludes common weak names like:
   - `foo`, `bar`, `tmp`, `test`
   - `func`, `function`, `my_func`
   - `main`, `solution`, `answer`
   - `example`, `sample`

3. **Deduplication**: Removes duplicate function names

### Statistics

After generation, the logger outputs filter statistics:
```
Generated 85/100 valid function names
Filter stats: {'regex': 92, 'weaklist': 89, 'deduped': 85}
```

This shows how many candidates passed each filter stage.

---

## Code Generation Output (TODO)

### Location
- `data/generated/code/{mode}/code_results.jsonl`

### Format
```json
{
  "func_name": "calculate_sum",
  "description": "Calculate the sum of two numbers",
  "code": "def calculate_sum(a, b):\n    return a + b",
  "source": "FIM",
  "syntax_valid": true,
  "perplexity": 2.34
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `func_name` | string | Function name |
| `description` | string | Function description (docstring) |
| `code` | string | Complete generated function code |
| `source` | string | Generation mode |
| `syntax_valid` | boolean | Whether the code passes `ast.parse()` |
| `perplexity` | float | Optional perplexity score from scoring model |

---

## Logging Structure

### Log Directory Structure

```
logs/
├── datagen/
│   ├── fim/
│   │   ├── 20250116_143022.log
│   │   └── 20250116_150341.log
│   └── l2r/
│       ├── 20250116_143525.log
│       └── 20250116_151202.log
├── training/
│   ├── d2c/
│   └── c2d/
└── evaluation/
    ├── humaneval/
    ├── mbpp/
    └── lcb/
```

### Log Format

Each log entry follows this format:
```
2025-01-16 14:30:22 | INFO     | datagen.fim | Generating function names: mode=FIM, total_samples=100
2025-01-16 14:30:22 | INFO     | datagen.fim | Batching: 10 batches, 10 samples per batch, max_concurrent=10
2025-01-16 14:30:25 | INFO     | datagen.fim | Generated 85/100 valid function names
2025-01-16 14:30:25 | INFO     | datagen.fim | Filter stats: {'regex': 92, 'weaklist': 89, 'deduped': 85}
```

### Log Levels

- **INFO**: General progress and statistics
- **DEBUG**: Detailed prompt content and intermediate results
- **WARNING**: Non-critical issues (e.g., some samples failed)
- **ERROR**: Critical errors that stop execution
- **EXCEPTION**: Errors with full traceback

### Console vs File Output

- **Console**: Colorful output with Rich formatting, shows real-time progress
- **File**: Plain text with full details, persisted for later analysis

### Usage Example

```python
from evoselfcode.utils.logger import setup_task_logger

# Setup logger for a specific task
logger = setup_task_logger("datagen", "fim")

logger.info("Starting generation...")
logger.debug(f"Prompt: {prompt[:100]}...")
logger.warning("Some samples were filtered out")
logger.error("Failed to connect to API")
```

---

## Best Practices

1. **Always check logs** after generation to verify:
   - How many samples were filtered
   - What the filter statistics show
   - Any errors or warnings

2. **Analyze output files** to understand:
   - Quality of generated function names
   - Distribution of FIM vs L2R results
   - Common patterns or issues

3. **Monitor file sizes** to ensure:
   - Expected number of samples were generated
   - No excessive duplicates
   - Output files are not empty

4. **Compare modes** by looking at:
   - FIM vs L2R statistics
   - Unique function name counts
   - Quality metrics (if available)

