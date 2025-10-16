# 数据生成模块架构重构文档

## 重构概述

本次重构将数据生成逻辑从 `services` 层迁移到 `datagen/preprocess` 核心模块，实现了清晰的分层架构和批量异步调用优化。

## 新架构

### 目录结构

```
evoselfcode/
├── datagen/
│   ├── preprocess/              # 核心数据预处理模块
│   │   ├── __init__.py
│   │   ├── problemgen.py        # 算法题描述生成器
│   │   └── skeletongen.py       # 函数骨架生成器
│   ├── prompts.py               # Prompt 构建器
│   └── filters/                 # 过滤器模块
│       ├── names.py
│       └── code.py
├── services/
│   └── datagen_service.py       # 编排层（调用 preprocess 模块）
├── core/                        # 核心基础设施
│   ├── config_manager.py
│   ├── client_manager.py
│   ├── prompt_builder.py
│   └── filter_chain.py
└── scripts/                     # 运行脚本
    ├── generate_funcnames.py    # 生成问题描述
    └── generate_skeletons.py    # 生成函数骨架
```

## 核心模块职责

### 1. `datagen/preprocess/problemgen.py` - ProblemGenerator

**职责**：生成算法题描述（FIM/L2R 模式）

**核心功能**：
- ✅ 使用 `complete_batch_async()` 批量异步调用
- ✅ 自动计算批次大小（基于 client.semaphore）
- ✅ Hash 去重（SHA256[:16] 作为 UID）
- ✅ 增量写入磁盘（每 N 个样本批量写入）
- ✅ Rich 进度条可视化

**关键方法**：
```python
async def generate(
    mode: Literal["FIM", "L2R"],
    num_samples: int,
    output_dir: Path,
    temperature: float = 1.0,
    top_p: float = 0.95,
    max_tokens: int = 2048,
    stop: Optional[List[str]] = None,
    batch_write_size: int = 50
) -> List[Dict]
```

**优化**：
- 批量调用：从单个循环改为 `complete_batch_async()`，显著提升吞吐量
- 并发管理：自动读取 `client.semaphore._value` 确定最大并发数
- 非阻塞 I/O：使用 `asyncio.to_thread()` 异步写入文件

### 2. `datagen/preprocess/skeletongen.py` - SkeletonGenerator

**职责**：从问题描述生成 Python 函数骨架

**核心功能**：
- ✅ 使用 `complete_batch_async()` 批量异步调用
- ✅ AST 语法验证（`ast.parse()`）
- ✅ 函数名正则提取
- ✅ Hash 去重 + 增量写入
- ✅ Rich 进度条可视化

**关键方法**：
```python
async def generate(
    input_file: Path,
    output_dir: Path,
    prompt_template: str,
    num_samples: Optional[int] = None,
    temperature: float = 0.7,
    top_p: float = 0.95,
    max_tokens: int = 512,
    stop: Optional[List[str]] = None,
    batch_write_size: int = 50,
    problem_key: str = "problem_description"
) -> List[Dict]
```

**优化**：
- 批量调用：一次性处理多个问题描述，减少 API 调用开销
- 智能批次：根据问题数量和并发数自动计算批次
- 输入流式读取：避免将所有问题加载到内存

### 3. `services/datagen_service.py` - DataGenService (编排层)

**职责**：高层编排，组合调用底层生成器

**核心功能**：
- 配置加载与合并（main + model config）
- 初始化 `ProblemGenerator` 和 `SkeletonGenerator`
- 提供统一 API：`generate_problems()`, `generate_skeletons()`, `generate_full_pipeline()`

**设计模式**：
```python
# 旧架构（不好）
class DataGenService:
    async def generate_function_names():
        # 直接实现所有逻辑...
        client = ...
        for batch in ...:
            results = await client.complete_batch_async(...)
            # 处理、去重、写入...

# 新架构（好）
class DataGenService:
    def __init__(self, ...):
        self.problem_gen = ProblemGenerator(...)  # 核心模块
        self.skeleton_gen = SkeletonGenerator(...)
    
    async def generate_problems(mode, num_samples):
        # 仅做参数准备和调用
        return await self.problem_gen.generate(...)
```

**优势**：
- 职责分离：Service 只负责编排，核心逻辑在 preprocess 模块
- 可测试性：各模块独立，可单独测试
- 可复用性：preprocess 模块可被其他 Service 调用

## 批量异步调用优化

### 旧实现（单个循环）

```python
for i in range(num_samples):
    result = await client._complete_async(prompt, ...)  # 单个请求
    # 处理...
```

**问题**：
- 低吞吐量：每次只发送 1 个请求
- 等待时间长：串行执行，总时间 = 单次时间 × 样本数

### 新实现（批量调用）

```python
# 自动计算批次
max_concurrent = getattr(client.semaphore, '_value', 5)
num_batches = math.ceil(num_samples / max_concurrent)

for batch_idx in range(num_batches):
    batch_size = min(max_concurrent, remaining)
    batch_prompts = [base_prompt] * batch_size
    
    # 批量异步调用
    batch_results = await client.complete_batch_async(
        prompts=batch_prompts,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=1,
        stop=stop
    )
    # 处理所有结果...
```

**优势**：
- ✅ 高吞吐量：并发发送多个请求（默认 5-100 个）
- ✅ 自动管理：`client.semaphore` 内部控制并发数
- ✅ 时间节省：理论加速 = max_concurrent 倍

## 数据流

```
1. 问题描述生成
   ┌─────────────────────────┐
   │ generate_funcnames.py   │ (脚本)
   └───────────┬─────────────┘
               ↓
   ┌─────────────────────────┐
   │ DataGenService          │ (编排层)
   │  .generate_problems()   │
   └───────────┬─────────────┘
               ↓
   ┌─────────────────────────┐
   │ ProblemGenerator        │ (核心模块)
   │  .generate()            │
   │   → complete_batch_async│
   │   → 去重 + 增量写入     │
   └───────────┬─────────────┘
               ↓
   data/generated/problems_desc/{mode}/
     ├── {mode}_results.jsonl
     └── hash_table.txt

2. 函数骨架生成
   ┌─────────────────────────┐
   │ generate_skeletons.py   │ (脚本)
   └───────────┬─────────────┘
               ↓
   ┌─────────────────────────┐
   │ DataGenService          │ (编排层)
   │  .generate_skeletons()  │
   └───────────┬─────────────┘
               ↓
   ┌─────────────────────────┐
   │ SkeletonGenerator       │ (核心模块)
   │  .generate()            │
   │   → 读取问题描述        │
   │   → complete_batch_async│
   │   → AST 验证 + 去重     │
   │   → 增量写入            │
   └───────────┬─────────────┘
               ↓
   data/generated/func_skeletons/{mode}/
     ├── skeletons.jsonl
     └── hash_table.txt
```

## 性能优化总结

| 优化项 | 旧实现 | 新实现 | 提升 |
|--------|--------|--------|------|
| API 调用 | 单个循环 | `complete_batch_async()` | ~5-100x 吞吐量 |
| 并发控制 | 手动管理 | Semaphore 自动管理 | 更稳定 |
| 文件写入 | 同步阻塞 | `asyncio.to_thread()` | 非阻塞 |
| 进度显示 | 简单日志 | Rich 进度条 | 更直观 |
| 去重 | 运行时检查 | Hash 表 + 文件持久化 | 支持断点续跑 |

## 使用示例

### 生成问题描述

```bash
# FIM 模式生成 100 个问题
python scripts/generate_funcnames.py --mode fim --num-samples 100

# L2R 模式生成 100 个问题
python scripts/generate_funcnames.py --mode l2r --num-samples 100
```

### 生成函数骨架

```bash
# 从 FIM 问题生成骨架（前 50 个）
python scripts/generate_skeletons.py --source fim --num-samples 50

# 从 L2R 问题生成骨架（全部）
python scripts/generate_skeletons.py --source l2r
```

## 配置文件

- `configs/datagen/fim.yaml` - FIM 问题生成配置
- `configs/datagen/l2r.yaml` - L2R 问题生成配置
- `configs/skeleton.yaml` - 骨架生成配置
- `configs/model.yaml` - 模型 API 配置（共享）

## 日志输出

- 问题生成：`logs/scripts/problems_{mode}/`
- 骨架生成：`logs/scripts/skeleton_{mode}/`
- 详细日志：`logs/datagen/{module}/{mode}/`

## 输出格式

### 问题描述 JSONL

```json
{
  "uid": "c44f3e2939259ef2",
  "problem_description": "Title: ...\nDescription: ...",
  "source": "FIM",
  "raw_text": "..."
}
```

### 函数骨架 JSONL

```json
{
  "uid": "27c8257479fe929d",
  "source": "FIM",
  "problem_text": "Title: ...",
  "skeleton_code": "def func_name(...):\n    \"\"\"...\"\"\"\n",
  "function_name": "func_name",
  "valid": true
}
```

## 未来扩展

### 添加新生成器

在 `evoselfcode/datagen/preprocess/` 下创建新模块：

```python
# evoselfcode/datagen/preprocess/codegen.py
class CodeGenerator:
    """从骨架生成完整代码实现"""
    
    async def generate(
        input_file: Path,
        output_dir: Path,
        ...
    ) -> List[Dict]:
        # 批量异步调用
        batch_results = await client.complete_batch_async(...)
        # 去重 + 增量写入
        ...
```

然后在 `DataGenService` 中编排：

```python
class DataGenService:
    def __init__(self, ...):
        self.problem_gen = ProblemGenerator(...)
        self.skeleton_gen = SkeletonGenerator(...)
        self.code_gen = CodeGenerator(...)  # 新增
    
    async def generate_full_pipeline(self):
        problems = await self.problem_gen.generate(...)
        skeletons = await self.skeleton_gen.generate(...)
        codes = await self.code_gen.generate(...)  # 新增
        return {"problems": ..., "skeletons": ..., "codes": ...}
```

## 重构总结

✅ **架构清晰**：核心逻辑在 `datagen/preprocess`，编排在 `services`  
✅ **性能提升**：批量异步调用 + 非阻塞 I/O  
✅ **可维护性**：模块化设计，职责分离  
✅ **可扩展性**：轻松添加新生成器  
✅ **可测试性**：各模块独立可测  
✅ **用户体验**：Rich 进度条 + 详细日志  

---

**重构完成时间**：2025-10-17  
**测试状态**：✅ 所有功能正常

