# 代码质量评分分析工具

## 功能概述

分析和可视化 FIM 和 L2R 两种生成模式下的代码质量评分数据，生成：

1. **雷达图（Radar Chart）**：对比 FIM 和 L2R 在 5 个维度上的平均分数
2. **分布直方图（Distribution Histograms）**：展示每个维度的分数分布情况
3. **统计报告（Statistics Report）**：详细的数值统计（均值、中位数、标准差等）

## 五个评分维度

1. **Problem Design Quality** - 问题设计质量
2. **Function Definition & Naming** - 函数定义与命名质量
3. **Algorithmic Correctness** - 算法正确性
4. **Algorithmic Efficiency** - 算法效率
5. **Code Readability & Structure** - 代码可读性与结构

## 使用方法

### 基本用法（使用默认路径）

```bash
python scripts/datagen/analyze_ratings.py
```

默认输入路径：
- FIM: `data/generated/func_ratings/fim/ratings.jsonl`
- L2R: `data/generated/func_ratings/l2r/ratings.jsonl`

默认输出目录：
- `data/analysis/rating_comparison/`

### 自定义输入路径

```bash
python scripts/datagen/analyze_ratings.py \
  --fim-path data/generated/func_ratings/fim/ratings.jsonl \
  --l2r-path data/generated/func_ratings/l2r/ratings.jsonl
```

### 自定义输出目录

```bash
python scripts/datagen/analyze_ratings.py \
  --output-dir results/my_analysis
```

### 调试模式

```bash
python scripts/datagen/analyze_ratings.py --log-level DEBUG
```

## 输出文件

运行后会在输出目录生成 3 个文件：

### 1. `radar_chart.png`
**5 维度雷达图**，对比 FIM 和 L2R 的平均分数：
- 蓝色：FIM 模式
- 紫红色：L2R 模式
- 坐标轴刻度：1-5 分

### 2. `distribution_histograms.png`
**5 个子图的分布直方图**：
- 每个子图展示一个维度的分数分布
- 蓝色柱：FIM 分数分布
- 紫红色柱：L2R 分数分布
- 虚线：各自的平均分

### 3. `statistics_report.txt`
**详细统计报告**，包含：
- 每个维度的均值、中位数、标准差
- FIM vs L2R 的差异
- 整体平均分对比

## 示例输出

### 雷达图示例
```
       Problem Design (5.0)
              /\
             /  \
 Readability /    \ Function Definition
      (4.8) /  FIM \ (4.6)
            \      /
             \    /
              \  /
    Efficiency \ / Correctness
        (4.5)   V   (4.9)
```

### 统计报告示例
```
================================================================================
CODE QUALITY RATING STATISTICS REPORT
================================================================================

## Overall Summary

FIM Total Samples: 2401
L2R Total Samples: 2189

================================================================================
## Dimension-wise Statistics
================================================================================

### Problem Design Quality

FIM:
  Mean:   4.523
  Median: 5.000
  Std:    0.721
  Count:  2401

L2R:
  Mean:   4.489
  Median: 5.000
  Std:    0.748
  Count:  2189

Difference (L2R - FIM): -0.034

--------------------------------------------------------------------------------
...
```

## 日志输出

日志文件保存在：
```
logs/datagen/rating_analysis/YYYYMMDD_HHMMSS.log
```

INFO 级别日志示例：
```
============================================================
Rating Analysis Configuration
============================================================
FIM ratings path: data/generated/func_ratings/fim/ratings.jsonl
L2R ratings path: data/generated/func_ratings/l2r/ratings.jsonl
Output directory: data/analysis/rating_comparison
Log level: INFO
============================================================
Loading ratings...
Loaded 2401 ratings from data/generated/func_ratings/fim/ratings.jsonl
Loaded 2189 ratings from data/generated/func_ratings/l2r/ratings.jsonl
Extracting scores...
Generating radar chart...
Saved radar chart to data/analysis/rating_comparison/radar_chart.png
Generating distribution histograms...
Saved distribution histograms to data/analysis/rating_comparison/distribution_histograms.png
Generating statistics report...
Saved statistics report to data/analysis/rating_comparison/statistics_report.txt
============================================================
✅ Analysis complete!
   Outputs saved to: data/analysis/rating_comparison
   - radar_chart.png
   - distribution_histograms.png
   - statistics_report.txt
============================================================
```

## 依赖库

此工具依赖以下 Python 库：
- `matplotlib` - 图表生成
- `numpy` - 数值计算

如果未安装，请运行：
```bash
pip install matplotlib numpy
```

## 核心模块

核心实现位于：
```
evoselfcode/datagen/preprocess/rating_analyzer.py
```

主要类：
- `RatingAnalyzer` - 主分析类，包含所有分析和可视化方法

## 完整数据流水线

```
1. Problem Description  →  problems_desc/{fim|l2r}/problems.jsonl
                           ↓
2. Function Skeleton    →  func_skeletons/{fim|l2r}/skeletons.jsonl
                           ↓
3. Implementation       →  func_implementations/{fim|l2r}/implementations.jsonl
                           ↓
4. Quality Rating       →  func_ratings/{fim|l2r}/ratings.jsonl
                           ↓
5. Analysis & Viz       →  data/analysis/rating_comparison/
                              ├── radar_chart.png
                              ├── distribution_histograms.png
                              └── statistics_report.txt
```

## 故障排查

### 找不到评分文件
```
Error: No rating files found. Please generate ratings first.
```

**解决方法**：先运行评分生成脚本
```bash
python scripts/datagen/generate_ratings.py --source fim
python scripts/datagen/generate_ratings.py --source l2r
```

### ImportError: No module named 'matplotlib'
```bash
pip install matplotlib numpy
```

### 图表显示中文乱码
工具已自动配置字体，如仍有问题，可安装：
```bash
# Ubuntu/Debian
sudo apt-get install fonts-dejavu-core

# 或使用系统默认字体
```

## 参数说明

```
--fim-path PATH       FIM 评分文件路径（默认：data/generated/func_ratings/fim/ratings.jsonl）
--l2r-path PATH       L2R 评分文件路径（默认：data/generated/func_ratings/l2r/ratings.jsonl）
--output-dir PATH     输出目录（默认：data/analysis/rating_comparison）
--log-level LEVEL     日志级别（DEBUG|INFO|WARNING|ERROR，默认：INFO）
```

## 示例工作流

```bash
# 1. 生成 FIM 评分数据
bash scripts/datagen/generate_ratings_fim.sh

# 2. 生成 L2R 评分数据
bash scripts/datagen/generate_ratings_l2r.sh

# 3. 等待评分完成（监控日志）
tail -f logs/datagen/rating_fim/*.log

# 4. 运行分析
python scripts/datagen/analyze_ratings.py

# 5. 查看结果
open data/analysis/rating_comparison/radar_chart.png
open data/analysis/rating_comparison/distribution_histograms.png
cat data/analysis/rating_comparison/statistics_report.txt
```

## 高级用法

### 只分析 FIM 数据
```bash
python scripts/datagen/analyze_ratings.py \
  --fim-path data/generated/func_ratings/fim/ratings.jsonl \
  --l2r-path /dev/null
```

### 批量对比多个版本
```bash
# 对比不同实验版本
for version in v1 v2 v3; do
  python scripts/datagen/analyze_ratings.py \
    --fim-path experiments/$version/fim_ratings.jsonl \
    --l2r-path experiments/$version/l2r_ratings.jsonl \
    --output-dir results/comparison_$version
done
```

## 性能特点

- **内存优化**：流式处理 JSONL 文件，不一次性加载全部数据
- **快速执行**：典型数据集（~2000 样本）分析时间 < 5 秒
- **高质量输出**：300 DPI 图表，适合论文和报告

## 贡献者

如需扩展功能（如添加新的图表类型），请修改：
- 核心逻辑：`evoselfcode/datagen/preprocess/rating_analyzer.py`
- 入口脚本：`scripts/datagen/analyze_ratings.py`

