# 客户端使用说明

## 1. 配置文件

配置位于 `configs/datagen.yaml`，主要参数：

```yaml
api:
  base_url: "http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local"
  api_key: ""  # 可选
  mode: "openai"  # openai | chat | endpoint
  fim:
    use_chat_for_fim: false  # true=chat.completions, false=completions
    prefix_key: "prefix"
    suffix_key: "suffix"
```

## 2. 客户端类型

### 2.1 OpenAICompletionClient

位于 `evoselfcode/clients/openai.py`，支持：

#### 正常 Completion

```python
from evoselfcode.clients import OpenAICompletionClient

client = OpenAICompletionClient(
    base_url="http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local",
    model="Qwen2.5-Coder-32B",
)

results = client.complete(
    prompt="This is an algorithm function.\n\ndef ",
    max_tokens=16,
    temperature=0.4,
    top_p=0.9,
    n=4,
    stop=["(", " ", "\n"],
)
# 返回: [{"text": "sample_random"}, {"text": "quick_sort"}, ...]
```

#### FIM via completions.create

```python
client = OpenAICompletionClient(
    base_url="...",
    use_chat_for_fim=False,  # 使用 completions 接口
)

results = client.complete_fim(
    prefix="This is an algorithm function.\n\ndef ",
    suffix="():\n",
    max_tokens=16,
    temperature=0.4,
    n=4,
)
```

#### FIM via chat.completions.create

```python
client = OpenAICompletionClient(
    base_url="...",
    use_chat_for_fim=True,  # 使用 chat.completions 接口
    prefix_key="prefix",
    suffix_key="suffix",
)

results = client.complete_fim(
    prefix="This is an algorithm function.\n\ndef ",
    suffix="():\n",
    max_tokens=16,
    temperature=0.4,
    n=4,
)
```

### 2.2 OpenAIScoringClient

位于 `evoselfcode/clients/scoring.py`，用于评分：

```python
from evoselfcode.clients import OpenAIScoringClient

scorer = OpenAIScoringClient(
    base_url="...",
    model="Qwen2.5-Coder-32B",
)

# 计算困惑度
ppl = scorer.perplexity("def sample_random():\n    pass\n")

# 获取 token logprobs
logprobs = scorer.token_logprobs("def sample_random():\n    pass\n")
```

### 2.3 CustomEndpointClient

位于 `evoselfcode/clients/endpoint.py`，用于自定义端点（通过 field_map 映射）。

## 3. Prompt 模板

位于 `evoselfcode/datagen/prompts.py`：

```python
from evoselfcode.datagen.prompts import (
    build_funcname_prompt_fim,
    build_funcname_prompt_l2r,
    build_codegen_prompt,
)

# FIM 模式函数名生成
prefix, suffix = build_funcname_prompt_fim()
# prefix = "This is an algorithm function.\n\ndef "
# suffix = "():\n"

# 续写模式函数名生成
prompt = build_funcname_prompt_l2r()
# prompt = "This is an algorithm function.\n\ndef "

# 代码续写
code_prompt = build_codegen_prompt(
    func_name="sample_random",
    description="Implement reservoir sampling for a stream of items."
)
```

## 4. 完整流程示例

### 阶段 A：函数名生成（FIM vs L2R A/B 对比）

```python
from evoselfcode.clients import OpenAICompletionClient
from evoselfcode.datagen.prompts import build_funcname_prompt_fim, build_funcname_prompt_l2r

client = OpenAICompletionClient(base_url="...", use_chat_for_fim=False)

# FIM 模式
prefix, suffix = build_funcname_prompt_fim()
fim_results = client.complete_fim(
    prefix=prefix,
    suffix=suffix,
    max_tokens=16,
    temperature=0.4,
    n=4,
    stop=["(", " ", "\n"],
)

# L2R 模式
l2r_prompt = build_funcname_prompt_l2r()
l2r_results = client.complete(
    prompt=l2r_prompt,
    max_tokens=16,
    temperature=0.4,
    n=4,
    stop=["(", " ", "\n"],
)

# 过滤与统计（后续在 filters/ 和 abtest.py 中实现）
```

### 阶段 B：代码续写

```python
from evoselfcode.datagen.prompts import build_codegen_prompt

func_name = "sample_random"
description = "Implement reservoir sampling for a stream."

code_prompt = build_codegen_prompt(func_name, description)
code_results = client.complete(
    prompt=code_prompt,
    max_tokens=512,
    temperature=0.3,
    n=4,
)

# 过滤、AST 检查、去重（后续在 filters/code.py 中实现）
```

### 评分（可选）

```python
from evoselfcode.clients import OpenAIScoringClient

scorer = OpenAIScoringClient(base_url="...", model="...")

for result in code_results:
    code = result["text"]
    ppl = scorer.perplexity(code)
    result["ppl"] = ppl
```

## 5. 与配置集成

后续在 `datagen/pipeline/` 中将结合 `configs/datagen.yaml` 自动初始化客户端并执行流程。

