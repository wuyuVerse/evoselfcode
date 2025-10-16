# Quick Start Guide

## 🚀 现在可以开始使用了！

所有代码已经配置好，可以直接运行。

### 1. API 测试 ✅

API 端点已验证可用：
- **Endpoint:** `http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local`
- **Model:** `Qwen2.5-Coder-32B`
- **FIM Mode:** 使用特殊 token `<|fim_prefix|>`, `<|fim_suffix|>`, `<|fim_middle|>`

### 2. 运行函数名生成

三种方式任选其一：

#### 方式 1: 使用 CLI
```bash
python -m evoselfcode.cli datagen generate-names --config configs/datagen.yaml
```

#### 方式 2: 使用 Shell 脚本
```bash
bash scripts/generate_funcnames.sh
```

#### 方式 3: 使用 Python 脚本
```bash
python scripts/generate_funcnames.py
```

### 3. 输出结果

生成的文件会保存在 `data/generated/names/`：
- `fim_raw.jsonl` - FIM 模式生成的函数名
- `l2r_raw.jsonl` - L2R 模式生成的函数名  
- `combined_raw.jsonl` - 合并所有结果

每行格式：
```json
{
  "func_name": "checkio",
  "source": "FIM",
  "raw_text": "checkio"
}
```

### 4. 配置说明

#### `configs/model.yaml` - 模型配置
```yaml
api:
  base_url: "http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local"
  timeout_s: 60
  max_retries: 3
  
  concurrency:
    max_concurrent_requests: 10  # 并发请求数
  
  fim:
    mode: "special_tokens"  # FIM 模式
    prefix_token: "<|fim_prefix|>"
    suffix_token: "<|fim_suffix|>"
    middle_token: "<|fim_middle|>"

models:
  default: "Qwen2.5-Coder-32B"
```

#### `configs/datagen.yaml` - 数据生成配置
```yaml
namegen:
  temperature: 0.4
  top_p: 0.9
  max_new_tokens: 16
  n: 4              # 每批次样本数
  num_batches: 2    # 批次数
  stop: ["(", " ", "\n"]
```

### 5. 代码架构

现在使用模块化的设计：

```python
# 直接使用 Service
from evoselfcode.services import DataGenService
import asyncio

# 创建服务（自动加载配置）
service = DataGenService.from_config_path("configs/datagen.yaml")

# 生成函数名（FIM 模式）
async def generate():
    results = await service.generate_function_names(mode="FIM")
    print(f"Generated {len(results)} function names")
    return results

# 运行
asyncio.run(generate())
```

### 6. 核心特性

✅ **异步高并发**: 使用 asyncio + semaphore 控制并发  
✅ **批量生成**: 一次请求生成多个样本 (n=4)  
✅ **自动重试**: 失败自动重试，指数退避  
✅ **过滤器链**: 正则 + 弱名黑名单自动过滤  
✅ **模块化设计**: Service → Core → Clients 清晰分层  
✅ **配置驱动**: 所有参数都可配置  

### 7. 性能

假设单个请求耗时 2 秒：

| 模式 | 总样本 | 耗时 |
|------|--------|------|
| 串行 | 8 | 16秒 |
| 并发 (n=4, batches=2) | 8 | ~4秒 |

**提速 4 倍！**

### 8. 下一步

1. ✅ 函数名生成（已完成）
2. 🔄 代码续写生成（即将实现）
3. 🔄 评分与过滤（即将实现）
4. 🔄 训练管线集成

### 9. 故障排查

#### 问题：API 连接超时
```bash
# 测试 API 连通性
curl http://qwen2code32-0.t-skyinfer-wzhang.svc.cluster.local/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen2.5-Coder-32B", "prompt": "test", "max_tokens": 5}'
```

#### 问题：生成结果为空
- 检查 `configs/datagen.yaml` 中的 `weaklist` 是否过滤了所有结果
- 降低过滤条件的严格程度

#### 问题：并发过高导致错误
- 降低 `max_concurrent_requests` (默认 10)
- 减少 `num_batches` 或 `n` 参数

### 10. 查看日志

日志会输出到 `logs/run.log` 和控制台，包括：
- 生成参数
- 请求详情
- 过滤统计
- 最终结果

示例输出：
```
INFO: Generating function names: mode=FIM, batches=2, n=4
INFO: Generated 6/8 valid function names
INFO: Filter stats: {'regex': 1, 'weaklist': 1}
INFO: A/B Test Results:
  FIM: 6 total, 5 unique
  L2R: 7 total, 6 unique
```

---

## 📚 更多文档

- `docs/ARCHITECTURE.md` - 架构设计
- `docs/API_COMPATIBILITY.md` - API 兼容性测试
- `docs/ASYNC_CLIENT_USAGE.md` - 异步客户端使用
- `scripts/README.md` - 脚本使用说明

准备好了就开始运行吧！🎉

