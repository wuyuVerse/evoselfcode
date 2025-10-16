# Qwen2.5-Coder-32B 数据生成设计（描述 → 代码）

> 方案：函数名生成（FIM vs 续写 A/B 对比）+ 统一续写生成完整函数体；
> 推理服务（可配置）：`http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local`

---

## 1) 目标与产出
- 从任务描述构建高质量 Python 函数实现数据。
- 两阶段：
  - A 阶段（函数名生成）：FIM 与 续写 A/B 对比，筛选合规、贴合的函数名。
  - B 阶段（代码续写）：固定使用续写模式生成完整函数体。
- 输出（JSONL 每行一条）：
```json
{"desc": "...", "func_name": "sample_random", "source": "FIM", "code": "def sample_random(...): ...", "meta": {"params": {...}, "seed": 42}}
```

---

## 2) 目录与模块（结构）
```
evoselfcode/
  clients/
    __init__.py
    base.py          # 抽象接口：complete() / score()
    openai.py        # OpenAI 兼容 completion 客户端
    endpoint.py      # 自定义端点字段映射客户端
    scoring.py       # 基于模型的评分（logprobs/perplexity）
  datagen/
    __init__.py
    prompts.py
    schemas.py        # 统一数据结构（样本、候选、打分）
    writer.py         # JSONL 写入/分片/命名
    pipeline/
      __init__.py
      orchestrator.py  # 调度 A/B 函数名与代码续写两阶段
      namegen.py       # 函数名生成（FIM/L2R）+ 过滤 + 统计
      codegen.py       # 代码续写 + 语法/质量检查 + 去重
      abtest.py        # 阶段A A/B 指标统计
    filters/
      __init__.py
      names.py         # 名称正则/弱名/去重
      code.py          # AST/ruff/去重
    utils/
      __init__.py
      ast_tools.py
      hashing.py
      ruff.py

data/
  generated/
    names/
      raw.jsonl        # 阶段A原始输出
      filtered.jsonl   # 过滤后
      metrics.json     # 合规率/多样性等
    code/
      raw.jsonl        # 阶段B原始输出
      filtered.jsonl   # 过滤后
      scored.jsonl     # 可选：模型评分结果（ppl/logprob）
      metrics.json
```

配置（建议新增）：`configs/datagen.yaml`
- `api`: base_url, mode(openai|endpoint), route, headers, field_map
- `namegen`: temperature, top_p, max_new_tokens, n, stop, weaklist
- `codegen`: temperature, top_p, max_new_tokens, n
- `filters`: name_regex, min_code_len, enable_ast, enable_ruff
- `io`: input_desc_path, out_names_dir, out_code_dir, concurrency, shard_size

---

## 3) 服务与 API
- 默认地址：`http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local`
- OpenAI 兼容 `/v1/completions`（推荐）；或自定义 `/generate`（通过 field_map 适配）。
- 请求示例（OpenAI 兼容，函数名生成）：
```json
{
  "model": "Qwen2.5-Coder-32B",
  "prompt": "<PROMPT>",
  "max_tokens": 16,
  "temperature": 0.4,
  "top_p": 0.9,
  "n": 4,
  "stop": ["(", " ", "\n"],
  "stream": false
}
```
- 失败重试：指数退避；超时可配置；日志落在 `logs/`。

### 客户端设计（生成 + 评分）
- 抽象接口（`clients/base.py`）：
```python
class CompletionClient:
    def complete(self, prompt: str, *, max_tokens: int, temperature: float,
                 top_p: float, n: int = 1, stop: list[str] | None = None,
                 logprobs: int | bool | None = None, extra: dict | None = None) -> list[dict]:
        """返回 [{"text": str, "tokens": [...], "logprobs": [...]}]（字段因服务而异）。"""

class ScoringClient:
    def perplexity(self, text: str) -> float: ...
    def token_logprobs(self, text: str) -> list[float]: ...
```
- 具体实现：
  - `clients/openai.py`：OpenAI 兼容 completion；支持 `logprobs`（若服务实现）。
  - `clients/endpoint.py`：通过 `field_map` 适配自定义字段名；统一返回格式。
  - `clients/scoring.py`：
    - 优先使用服务端 `logprobs/echo` 能力直接取对数概率；
    - 若不支持，则退化为近似（不可用时可禁用评分）。
- FIM/L2R 适配：
  - `prompts.py` 统一组装文本；FIM 通过 `<fim_prefix>/<fim_middle>/<fim_suffix>` 协议或等效提示模拟；
  - 客户端仅透传 `prompt` 与采样参数。
- 鲁棒性：
  - 超时/重试/熔断；HTTP 5xx/backoff；并发限速（令牌桶）；
  - 可配置 headers（如鉴权）；
  - 统一异常与重试日志。

---

## 4) Prompt 规范
- 全局前缀统一：`This is an algorithm function.\n\n`

A) 函数名生成（A/B）共用上下文：
```
This is an algorithm function.

def
```
- FIM（主方案）：
```
<fim_prefix>
This is an algorithm function.

def <fim_middle>():
<fim_suffix>
```
  - 仅在 `<fim_middle>` 生成函数名；`():` 放在 `<fim_suffix>`。
  - 采样：temperature=0.4, top_p=0.9, max_new_tokens=16, n=4, stop=["("," ","\n"].
- 续写（对照组）：
```
This is an algorithm function.

def
```
  - 直接从 `