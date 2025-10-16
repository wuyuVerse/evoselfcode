# EvoSelfCode Architecture

## 设计原则

1. **分层架构**：清晰的层次划分
2. **依赖注入**：通过工厂模式创建对象
3. **配置驱动**：统一的配置管理
4. **模块解耦**：每个模块职责单一

## 架构层次

```
┌─────────────────────────────────────┐
│         CLI Layer (命令行)          │
│   - 用户交互                         │
│   - 参数解析                         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Service Layer (业务服务)       │
│   - DataGenService                   │
│   - TrainingService                  │
│   - EvaluationService                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Core Layer (核心功能)         │
│   - ClientManager (客户端管理)      │
│   - ConfigManager (配置管理)        │
│   - FilterChain (过滤链)            │
│   - PromptBuilder (Prompt构建)      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Infrastructure (基础设施)        │
│   - AsyncOpenAIClient                │
│   - IO Utils                         │
│   - Logging                          │
└─────────────────────────────────────┘
```

## 模块职责

### 1. Core Module (`evoselfcode/core/`)

**ConfigManager** - 统一配置管理
- 加载和合并配置文件
- 提供配置访问接口
- 验证配置有效性

**ClientManager** - 客户端工厂
- 创建和管理 API 客户端
- 处理连接池
- 统一异常处理

**PromptBuilder** - Prompt 构建器
- 从配置构建 prompt
- 模板渲染
- 变量替换

**FilterChain** - 过滤器链
- 组合多个过滤器
- 链式处理
- 统计信息

### 2. Service Module (`evoselfcode/services/`)

**DataGenService** - 数据生成服务
- 函数名生成（FIM/L2R）
- 代码生成
- 批量处理协调

**TrainingService** - 训练服务
- D2C/C2D 训练
- 迭代训练循环

**EvaluationService** - 评测服务
- 统一的评测接口
- 多基准测试协调

### 3. Clients Module (`evoselfcode/clients/`)

**AsyncOpenAIClient** - 异步 API 客户端
- HTTP 通信
- 并发控制
- 重试机制

**ScoringClient** - 评分客户端
- Perplexity 计算
- Logprobs 处理

### 4. Utils Module (`evoselfcode/utils/`)

**IO Utils** - 文件 I/O
- JSONL 读写
- 批量处理
- 数据验证

**Filter Utils** - 过滤工具
- 正则过滤
- AST 检查
- 去重工具

## 数据流

```
Config Files
    ↓
ConfigManager ← 加载配置
    ↓
ClientManager ← 创建客户端
    ↓
Service Layer ← 业务逻辑
    ↓
    ├→ PromptBuilder ← 构建 prompt
    ├→ AsyncClient ← API 调用
    ├→ FilterChain ← 过滤结果
    └→ IO Utils ← 保存输出
```

## 重构计划

### Phase 1: Core 模块化
- [x] 创建 `core/` 目录
- [ ] ConfigManager
- [ ] ClientManager  
- [ ] PromptBuilder
- [ ] FilterChain

### Phase 2: Service 层
- [ ] DataGenService
- [ ] TrainingService
- [ ] EvaluationService

### Phase 3: 简化 Clients
- [ ] 移除 rate_limit
- [ ] 统一接口
- [ ] 改进错误处理

### Phase 4: CLI 重构
- [ ] 使用 Service 层
- [ ] 减少直接依赖
- [ ] 统一错误处理

## 使用示例

### Before (当前)
```python
# 散落在各处的代码
config = RunConfig.from_file(...)
model_cfg = merge_model_config(...)
client_cfg = get_client_config(...)
client = AsyncOpenAICompletionClient(**client_cfg)
# ... 业务逻辑
```

### After (重构后)
```python
# 统一的服务入口
from evoselfcode.services import DataGenService

service = DataGenService.from_config("configs/datagen.yaml")
results = await service.generate_function_names(mode="FIM")
```

## 配置文件结构

```yaml
# configs/base.yaml - 基础配置
project:
  name: evoselfcode
  version: 0.1.0

# configs/api.yaml - API 配置
api:
  base_url: "..."
  timeout_s: 60
  max_concurrent: 10

# configs/datagen.yaml - 数据生成配置
datagen:
  prompts: {...}
  generation: {...}
  filters: {...}
```

## 目录结构（重构后）

```
evoselfcode/
  core/
    __init__.py
    config_manager.py
    client_manager.py
    prompt_builder.py
    filter_chain.py
  
  services/
    __init__.py
    datagen_service.py
    training_service.py
    evaluation_service.py
  
  clients/
    __init__.py
    base.py
    async_openai.py
    scoring.py
  
  utils/
    __init__.py
    io.py
    filters.py
    validation.py
  
  cli/
    (保持不变，但使用 services)
  
  models/
    __init__.py
    schemas.py  # Pydantic models
```

## 优势

1. **可测试性**：每个模块独立，易于单元测试
2. **可维护性**：职责清晰，修改影响范围小
3. **可扩展性**：新增功能只需实现接口
4. **可复用性**：Service 可被 CLI/API/Notebook 复用

