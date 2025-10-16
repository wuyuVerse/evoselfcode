# Data Generation Usage Guide

## Quick Start

### 1. Configure datagen.yaml

Edit `configs/datagen.yaml` to set your API endpoint and parameters:

```yaml
api:
  base_url: "http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local"
  api_key: ""  # Optional
  fim:
    use_chat_for_fim: false  # true for chat.completions, false for completions

model: "Qwen2.5-Coder-32B"
```

### 2. Generate Function Names (A/B Test: FIM vs L2R)

Run the function name generation pipeline:

```bash
python -m evoselfcode.cli datagen-names --config configs/datagen.yaml
```

This will:
- Generate function names using FIM mode
- Generate function names using L2R (left-to-right) mode
- Filter results by regex and weaklist
- Save outputs to `data/generated/names/`:
  - `fim_raw.jsonl`: FIM results
  - `l2r_raw.jsonl`: L2R results  
  - `combined_raw.jsonl`: All results

### 3. Output Format

Each line in the output JSONL:

```json
{
  "func_name": "reservoir_sampling",
  "source": "FIM",
  "raw_text": "reservoir_sampling"
}
```

## Configuration Details

### Prompts (in datagen.yaml)

```yaml
prompts:
  global_prefix: "This is an algorithm function.\n\n"
  
  funcname:
    fim:
      prefix: "This is an algorithm function.\n\ndef "
      suffix: "():\n"
    l2r:
      prompt: "This is an algorithm function.\n\ndef "
  
  codegen:
    template: |
      This is an algorithm function.

      def {func_name}():
          """
          {description}
          """
```

### Generation Parameters

```yaml
namegen:
  temperature: 0.4
  top_p: 0.9
  max_new_tokens: 16
  n: 4  # Number of samples per request
  stop: ["(", " ", "\n"]
  weaklist:  # Filtered out function names
    - "foo"
    - "bar"
    - "test"
```

### Filters

```yaml
filters:
  name_regex: "^[a-z_][a-z0-9_]{2,64}$"  # Valid Python function name
  min_code_len: 16
  enable_ast: true
  enable_ruff: false
```

## FIM Modes

### Option 1: completions API (default)

```yaml
api:
  fim:
    use_chat_for_fim: false
```

Request format:
```python
client.completions.create(
    prompt="This is an algorithm function.\n\ndef ",
    suffix="():\n",
    ...
)
```

### Option 2: chat.completions API

```yaml
api:
  fim:
    use_chat_for_fim: true
    prefix_key: "prefix"
    suffix_key: "suffix"
```

Request format:
```python
client.chat.completions.create(
    messages=[{"role": "user", "content": ""}],
    extra_body={
        "prefix": "This is an algorithm function.\n\ndef ",
        "suffix": "():\n"
    },
    ...
)
```

## Programmatic Usage

```python
from pathlib import Path
from evoselfcode.config import RunConfig
from evoselfcode.clients import OpenAICompletionClient
from evoselfcode.datagen.pipeline.namegen import generate_funcnames_fim

# Load config
config = RunConfig.from_file(Path("configs/datagen.yaml"))

# Initialize client
client = OpenAICompletionClient(
    base_url="http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local",
    model="Qwen2.5-Coder-32B",
    use_chat_for_fim=False,
)

# Generate FIM
fim_results = generate_funcnames_fim(client, config, mode="FIM")

# Generate L2R
l2r_results = generate_funcnames_fim(client, config, mode="L2R")

print(f"FIM: {len(fim_results)} valid names")
print(f"L2R: {len(l2r_results)} valid names")
```

## Next Steps

After generating function names:
1. Review and select high-quality names
2. Use selected names for Stage B: Code Generation
3. Filter generated code with AST/syntax checks
4. Score candidates with perplexity/quality metrics

See `docs/DATAGEN_Qwen2.5_Coder_32B.md` for full pipeline design.

