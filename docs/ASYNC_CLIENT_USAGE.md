# Async Client Usage Guide

## 异步客户端使用说明

项目现在使用异步客户端 `AsyncOpenAICompletionClient` 实现高并发请求，提升数据生成效率。

## 核心特性

### 1. 高并发支持
- 使用 `asyncio` 和 `Semaphore` 控制并发数
- 支持批量请求（batch requests）
- 自动速率限制（rate limiting）

### 2. 配置文件

#### `configs/model.yaml` - 模型与 API 配置

```yaml
api:
  base_url: "http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local"
  api_key: ""
  timeout_s: 60
  max_retries: 3
  
  # 并发控制
  concurrency:
    max_concurrent_requests: 10  # 最大并发请求数
    rate_limit_per_second: 5     # 每秒最多请求数
    semaphore_size: 10           # 信号量大小
  
  # FIM 配置
  fim:
    use_chat_for_fim: false
    prefix_key: "prefix"
    suffix_key: "suffix"

models:
  default: "Qwen2.5-Coder-32B"
```

#### `configs/datagen.yaml` - 数据生成配置

```yaml
# 引用 model.yaml
model_config: "configs/model.yaml"

namegen:
  temperature: 0.4
  top_p: 0.9
  max_new_tokens: 16
  n: 4              # 每批次样本数
  num_batches: 2    # 批次数（总样本 = n * num_batches）
  stop: ["(", " ", "\n"]
```

### 3. 客户端初始化

```python
from evoselfcode.clients import AsyncOpenAICompletionClient
from evoselfcode.model_config import load_model_config, get_client_config

# 加载配置
model_cfg = load_model_config()  # 自动从 configs/model.yaml 加载
client_cfg = get_client_config(model_cfg)

# 初始化客户端
client = AsyncOpenAICompletionClient(
    base_url=client_cfg["base_url"],
    api_key=client_cfg["api_key"],
    model=client_cfg["model"],
    timeout_s=client_cfg["timeout_s"],
    max_retries=client_cfg["max_retries"],
    use_chat_for_fim=client_cfg["use_chat_for_fim"],
    max_concurrent=client_cfg["max_concurrent"],
    rate_limit_per_second=client_cfg["rate_limit_per_second"],
)
```

### 4. 异步调用方式

#### 单个请求（同步包装）

```python
# 使用同步包装器（内部会 asyncio.run）
results = client.complete(
    prompt="This is an algorithm function.\n\ndef ",
    max_tokens=16,
    temperature=0.4,
    n=4,
)
```

#### 批量请求（高并发）

```python
import asyncio

async def generate_batch():
    # 准备多个 prompt
    prompts = [
        "This is an algorithm function.\n\ndef ",
        "This is an algorithm function.\n\ndef ",
        # ... 更多 prompts
    ]
    
    # 批量异步生成（自动并发控制）
    results = await client.complete_batch_async(
        prompts=prompts,
        max_tokens=16,
        temperature=0.4,
        n=4,
    )
    
    # results 是列表的列表: [[batch1_results], [batch2_results], ...]
    return results

# 运行
results = asyncio.run(generate_batch())
```

#### FIM 批量请求

```python
async def generate_fim_batch():
    # 准备多个 (prefix, suffix) 对
    pairs = [
        ("This is an algorithm function.\n\ndef ", "():\n"),
        ("This is an algorithm function.\n\ndef ", "():\n"),
        # ... 更多 pairs
    ]
    
    # 批量 FIM 生成
    results = await client.complete_fim_batch_async(
        prefix_suffix_pairs=pairs,
        max_tokens=16,
        temperature=0.4,
        n=4,
    )
    
    return results

results = asyncio.run(generate_fim_batch())
```

### 5. 并发控制说明

#### Semaphore（信号量）
控制同时进行的请求数：
```python
max_concurrent = 10  # 最多同时 10 个请求
```

#### Rate Limiting（速率限制）
控制每秒请求数，避免超过 API 限制：
```python
rate_limit_per_second = 5  # 每秒最多 5 个请求
```

#### 重试机制
失败时自动重试，使用指数退避：
```python
max_retries = 3
# 重试间隔: 1s, 2s, 4s
```

### 6. 实际使用示例

在 `namegen.py` 中的使用：

```python
async def generate_funcnames_async(client, config, mode="FIM", num_batches=1):
    # 准备批量请求
    if mode == "FIM":
        prefix_suffix_pairs = [(prefix, suffix)] * num_batches
        all_results = await client.complete_fim_batch_async(
            prefix_suffix_pairs=prefix_suffix_pairs,
            max_tokens=16,
            temperature=0.4,
            n=4,
        )
    else:
        prompts = [prompt] * num_batches
        all_results = await client.complete_batch_async(
            prompts=prompts,
            max_tokens=16,
            temperature=0.4,
            n=4,
        )
    
    return process_results(all_results)

# 在主函数中运行
fim_candidates, l2r_candidates = asyncio.run(run_generation())
```

### 7. 性能优势

假设：
- 单个请求耗时：2 秒
- 需要生成：100 个样本

**串行方式（旧）：**
- 总耗时：100 × 2s = 200 秒

**并发方式（新）：**
- 并发数：10
- 总耗时：(100 / 10) × 2s = 20 秒
- **提速 10 倍！**

### 8. 常见问题

#### Q: 如何调整并发数？
A: 修改 `configs/model.yaml` 中的 `concurrency.max_concurrent_requests`

#### Q: 遇到速率限制怎么办？
A: 降低 `concurrency.rate_limit_per_second` 或减少 `max_concurrent_requests`

#### Q: 如何监控并发性能？
A: 查看日志中的时间戳和完成数量

### 9. 最佳实践

1. **根据 API 限制调整并发数**：不要超过服务端限制
2. **使用批量方法**：`complete_batch_async` 比多次调用 `complete` 更高效
3. **合理设置超时**：网络不稳定时增加 `timeout_s`
4. **监控日志**：观察重试和失败情况
5. **分批处理大量数据**：避免一次性加载过多数据到内存

### 10. 运行示例

```bash
# 使用默认配置运行函数名生成
python -m evoselfcode.cli datagen generate-names --config configs/datagen.yaml

# 或使用脚本
bash scripts/generate_funcnames.sh
python scripts/generate_funcnames.py
```

生成过程会：
1. 从 `model.yaml` 加载 API 和并发配置
2. 从 `datagen.yaml` 加载生成参数
3. 使用异步客户端批量生成
4. 自动应用并发控制和速率限制
5. 输出结果到 `data/generated/names/`

查看日志可以看到并发效果！

