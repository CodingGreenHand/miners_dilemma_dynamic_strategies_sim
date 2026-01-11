# 矿工困境仿真：基于重复博弈的区块链扣块攻击研究 (The Miner's Dilemma Simulation)

本项目是《区块链与数字资产》课程的期末研究项目。它结合了 **Ittay Eyal** 的扣块攻击（Block Withholding Attack）理论模型与 **Robert Axelrod** 的重复囚徒困境（Iterated Prisoner's Dilemma）博弈框架，通过数值仿真探究了在长期对抗环境下，不同矿池策略的演化与收益表现。

## 📖 项目背景

在比特币网络中，矿池之间存在一种被称为“扣块攻击”的非技术性攻击手段。虽然理论上单次攻击是纳什均衡点（即“公地悲剧”），但在现实世界中，矿池之间似乎维持着一种微妙的和平。

本项目试图回答以下问题：

1. 在大规模算力差异下，攻击的经济诱惑有多大？
2. 在重复博弈中，类似“以牙还牙”（Tit-for-Tat）的策略能否抑制攻击？
3. 在多策略混战中，哪种策略（攻击、和平、报复、偷袭）能获得最高的长期收益？

**核心参考文献：**

* [1] Eyal, I. (2015). *The Miner's Dilemma*. In 2015 IEEE Symposium on Security and Privacy.

* [2] Axelrod, R. (1980). *Effective Choice in the Prisoner's Dilemma*. Journal of Conflict Resolution.

## 🏗️ 项目结构

本项目采用模块化设计，将物理引擎（数学计算）、策略逻辑与仿真环境解耦。

```text
MinerDilemmaSim/
│
├── src/                        # 核心源代码
│   ├── mechanics.py            # [物理层] 实现 Eyal 的有效算力与收益密度公式 (基于 SciPy 优化)
│   ├── strategies.py           # [策略层] 实现 TFT, Friedman, Joss, Nash 等博弈策略
│   └── environment.py          # [环境层] 负责单场对局的循环控制与数据记录
│
├── experiments/                # 实验脚本 (对应论文实验章节)
│   ├── exp01_tournament.py     # 实验一：策略锦标赛 (生成热力图与排名)
│   ├── exp02_echo_effect.py    # 实验二：回声效应分析 (Joss vs TFT)
│   ├── exp03_pool_size.py      # 实验三：矿池大小敏感性分析
│
├── results/                    # 输出结果
│   └── figures/                # 仿真生成的图表 (.png)
│
├── utils/                      # 工具模块 (可选)
├── requirements.txt            # 依赖库列表
└── README.md                   # 项目说明文档

```

## ⚡ 快速开始

### 1. 环境准备

本项目基于 Python 3.9+ 开发。建议使用虚拟环境运行。

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 安装依赖
pip install numpy scipy pandas matplotlib seaborn

```

### 2. 单元测试

在运行大型实验前，建议先运行各模块的内置测试，确保逻辑正确。

```bash
# 测试物理引擎 (验证 Eyal 公式与纳什均衡点)
python -m src.mechanics

# 测试策略逻辑 (验证 TFT 的宽恕性与 Friedman 的记仇机制)
python -m src.strategies

# 测试仿真环境 (运行一局 10 轮的对战)
python -m src.environment

```

## 🧪 运行实验

本项目包含三个核心实验，直接运行对应的脚本即可在 `results/figures/` 目录下生成图表。

**注意：请务必在项目根目录下，使用 `python -m` 方式运行。**

### 实验一：策略锦标赛 (Tournament)

模拟所有策略（Peace, TFT, Friedman, Joss, Random, Nash）两两对战 200 轮，计算总收益矩阵与排名。

```bash
python -m experiments.exp01_tournament

```

> **预期结果：** 生成热力图。验证“友善”策略（Peace/TFT）因避免了战争成本，总分优于激进策略（Nash/Joss）。

### 实验二：回声效应 (Echo Effect)

模拟 TFT 策略对抗 Joss 策略（10% 概率偷袭）。

```bash
python -m experiments.exp02_echo_effect

```

> **预期结果：** 生成时间序列图。展示一次随机偷袭如何引发双方无休止的报复震荡，最终导致双输。

### 实验三：矿池大小敏感性 (Size Sensitivity)

分析我方矿池算力规模（1% - 45%）与单方攻击获利百分比的关系。

```bash
python -m experiments.exp03_pool_size

```

> **预期结果：** 生成曲线图。验证矿池越大，发动攻击的边际收益越高。

## 📊 关键策略说明

| 策略名 | 简称 | 行为逻辑 | 来源 |
| --- | --- | --- | --- |
| **Peace** | 和平 | 永远不攻击 ()。 | 对照组 |
| **Tit For Tat** | TFT | 第一轮合作，之后模仿对手上一轮的攻击力度。 | Axelrod|
| **Friedman** | 记仇 | 合作直到对手攻击一次，之后永远保持最大攻击力度。 | Axelrod|
| **Joss** | 狡猾 | 类似 TFT，但有 10% 概率在对手合作时偷袭。 | Axelrod|
| **Nash** | 纳什 | 每一轮都计算针对对手上一轮的最佳响应（Best Response）。 | Eyal|
| **Random** | 随机 | 50% 概率攻击，50% 概率和平。 | 对照组 |

## 🛠️ 技术栈

* **NumPy & SciPy**: 用于数值计算和非线性规划求解（寻找最佳攻击率 ）。
* **Pandas**: 用于结构化存储博弈历史数据。
* **Matplotlib & Seaborn**: 用于绘制学术级图表（已配置 SimHei 中文支持）。

## 📝 许可证

本项目为课程作业，仅供学术交流使用。

---

**Author:** CodingGreenHand
**Date:** 2026-01-11
