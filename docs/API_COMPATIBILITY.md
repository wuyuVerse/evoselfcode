# API Compatibility Test Results

## API Endpoint
`http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local`

## Test Results

### ✅ 1. Chat Completions (Standard)
**Endpoint:** `/v1/chat/completions`

**Status:** ✅ **Working**

**Example:**
```bash
curl -X POST http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen2.5-Coder-32B",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### ✅ 2. Completions (Standard)
**Endpoint:** `/v1/completions`

**Status:** ✅ **Working**

**Example:**
```bash
curl -X POST http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen2.5-Coder-32B",
    "prompt": "def ",
    "max_tokens": 20,
    "n": 2,
    "stop": ["(", "\n"]
  }'
```

**Response:**
```json
{
  "choices": [
    {"text": " is_prime", ...},
    {"text": " factorial", ...}
  ]
}
```

### ✅ 3. FIM (Fill-in-Middle) with Special Tokens
**Endpoint:** `/v1/completions`

**Status:** ✅ **Working**

**Method:** Use special tokens in prompt: `<|fim_prefix|>`, `<|fim_suffix|>`, `<|fim_middle|>`

**Example:**
```bash
curl -X POST http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen2.5-Coder-32B",
    "prompt": "<|fim_prefix|>def <|fim_suffix|>():<|fim_middle|>",
    "max_tokens": 16,
    "n": 4,
    "stop": ["(", " ", "\n", "<|fim_suffix|>"]
  }'
```

**Response:**
```json
{
  "choices": [
    {"text": "checkio"},
    {"text": "factorial"},
    {"text": "fibonacci"},
    {"text": "is_prime"}
  ]
}
```

### ❌ 4. FIM via `suffix` Parameter
**Endpoint:** `/v1/completions`

**Status:** ❌ **Not Supported**

**Error:**
```json
{
  "error": {
    "message": "suffix is not currently supported",
    "type": "BadRequestError",
    "code": 400
  }
}
```

### ❌ 5. FIM via Chat Completions `extra_body`
**Endpoint:** `/v1/chat/completions`

**Status:** ❌ **Not Working Correctly**

The API accepts `extra_body` with `prefix`/`suffix` but doesn't use them properly for FIM.

## Recommended Approach

### For Function Name Generation (FIM)
Use **special tokens** in completions:

```python
prompt = "<|fim_prefix|>This is an algorithm function.\n\ndef <|fim_suffix|>():<|fim_middle|>"

response = client.completions.create(
    model="Qwen2.5-Coder-32B",
    prompt=prompt,
    max_tokens=16,
    n=4,
    stop=["(", " ", "\n", "<|fim_suffix|>"]
)
```

### For Code Generation (L2R)
Use **standard completions**:

```python
prompt = "This is an algorithm function.\n\ndef sample_function():\n    \"\"\"\n    Description here\n    \"\"\"\n"

response = client.completions.create(
    model="Qwen2.5-Coder-32B",
    prompt=prompt,
    max_tokens=512,
    n=4
)
```

## Implementation Notes

1. **FIM Mode:** Use special tokens `<|fim_prefix|>`, `<|fim_suffix|>`, `<|fim_middle|>` in prompt
2. **Stop Tokens:** Include `<|fim_suffix|>` in stop tokens to prevent model from generating it
3. **Temperature:** Lower values (0.3-0.4) for more consistent results
4. **Batch Generation:** Use `n` parameter for multiple samples per request

## Configuration Updates Needed

Update `configs/model.yaml`:
```yaml
api:
  fim:
    mode: "special_tokens"  # Use special tokens instead of suffix parameter
    fim_prefix_token: "<|fim_prefix|>"
    fim_suffix_token: "<|fim_suffix|>"
    fim_middle_token: "<|fim_middle|>"
```

