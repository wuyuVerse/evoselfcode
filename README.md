## 用于代码生成大语言模型的迭代自训练策略（项目框架）

本项目实现基于研究大纲的端到端框架：以描述→代码（D2C）与代码→描述（C2D）双向模型为核心，结合随机采样、困惑度评分与筛选、迭代自训练与反向翻译（dual learning），并在 HumanEval / MBPP / LCB / BigCodeBench 等基准进行评测。

### 目录结构

```
evoselfcode/
  evoselfcode/              # Python 包
    cli.py                  # Typer CLI 入口
    config.py               # 配置加载与合并
    io_utils.py             # JSONL I/O、数据集工具
    logging_utils.py        # 结构化日志
    constants.py            # 常量与默认路径
    pipeline/               # 训练与数据生成流水线模块
      sampling.py           # 随机采样/生成候选
      scoring.py            # 困惑度/其他评分
      filtering.py          # 候选筛选
      train_sft.py          # D2C/C2D SFT 训练（骨架）
      dual_model.py         # 反向模型训练（C2D）
      iteration.py          # 迭代自训练主循环
    evaluation/
      humaneval.py          # HumanEval 评测（骨架）
      mbpp.py               # MBPP 评测（骨架）
      lcb.py                # LiveCodeBench 评测（骨架）
      bigcodebench.py       # BigCodeBench 评测（骨架）
  configs/
    base.yaml               # 全局默认配置
    generation.yaml         # 生成/采样配置
    train_d2c.yaml          # 描述→代码训练配置
    train_c2d.yaml          # 代码→描述训练配置
    iterate.yaml            # 迭代自训练配置
  data/
    raw/                    # 原始/起始数据（JSONL: {"prompt","code"}）
    processed/              # 规范化数据
    generated/              # 模型生成的候选与打分
    eval/                   # 评测相关缓存
  checkpoints/              # 模型权重输出
  logs/                     # 运行日志
```

### 快速开始

1. 准备环境

```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

2. 数据生成（FIM 函数名生成）

```bash
# 方式1：使用脚本
bash scripts/generate_funcnames.sh

# 方式2：使用 Python 脚本
python scripts/generate_funcnames.py

# 方式3：使用 CLI
python -m evoselfcode.cli datagen generate-names --config configs/datagen.yaml
```

3. 训练管线

```bash
# 生成候选样本
python -m evoselfcode.cli pipeline generate --config configs/generation.yaml

# 评分
python -m evoselfcode.cli pipeline score --config configs/generation.yaml

# 过滤
python -m evoselfcode.cli pipeline filter --config configs/generation.yaml

# 训练 D2C 模型
python -m evoselfcode.cli pipeline train-d2c --config configs/train_d2c.yaml

# 训练 C2D 模型
python -m evoselfcode.cli pipeline train-c2d --config configs/train_c2d.yaml

# 迭代训练
python -m evoselfcode.cli pipeline iterate --config configs/iterate.yaml
```

4. 评测

```bash
# 评测单个基准
python -m evoselfcode.cli eval humaneval --ckpt checkpoints/latest

# 评测所有基准
python -m evoselfcode.cli eval all --ckpt checkpoints/latest
```

### 说明

- 初期实现以清晰的接口和数据布局为主，便于逐步替换为真实训练/评测逻辑。
- 依赖较多，如需 GPU/加速请参考各库官方文档（Transformers/Accelerate 等）。
- 研究大纲详见 `研究大纲.md`。


