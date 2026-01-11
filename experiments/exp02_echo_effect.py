import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.strategies import TitForTatStrategy, JossStrategy
from src.environment import GameMatch

# --- 中文显示配置 (Windows) ---
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置默认字体为“黑体”
plt.rcParams['axes.unicode_minus'] = False    # 解决负号 '-' 显示为方块的问题
# ---------------------------

def run_experiment():
    # 设置：两个势均力敌的矿池
    m = 0.2
    
    # 对抗：TFT vs Joss
    # Joss 有 10% 概率偷袭，TFT 会反击
    agent_a = TitForTatStrategy(m, name="TFT")
    agent_b = JossStrategy(m, sneak_prob=0.1, name="Joss")
    
    match = GameMatch(agent_a, agent_b)
    df = match.run(rounds=100) # 跑 100 轮足以看清趋势
    
    # 绘图
    plt.figure(figsize=(12, 5))
    
    # 子图 1: 攻击率变化
    plt.subplot(1, 2, 1)
    plt.plot(df['Round'], df['Attack_A'], label='TFT 攻击率', marker='o', markersize=2, alpha=0.7)
    plt.plot(df['Round'], df['Attack_B'], label='Joss 攻击率', marker='x', markersize=2, alpha=0.7)
    plt.title('攻击率随时间变化 (回声效应)', fontsize = 12)
    plt.xlabel('轮数 (Round)')
    plt.ylabel('攻击率 (x)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 子图 2: 收益密度变化
    # 我们关注 r (Revenue Density)，即绝对收益除以矿池大小
    # Revenue_A 是绝对收益，所以 r = Revenue / m
    plt.subplot(1, 2, 2)
    plt.plot(df['Round'], df['Revenue_A']/m, label='TFT 收益密度y', color='green')
    plt.plot(df['Round'], df['Revenue_B']/m, label='Joss 收益密度', color='red')
    plt.axhline(1.0, color='gray', linestyle='--', label='和平基准 (r=1)')
    plt.title('收益密度 (Revenue Density)')
    plt.xlabel('轮数 (Round)')
    plt.ylabel('收益密度 (r)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()

    save_dir = 'results/figures'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"Created directory: {save_dir}")

    plt.savefig(f'{save_dir}/exp02_echo_effect.png')
    print(f"Experiment 2 Completed. Figure saved to {save_dir}/")

if __name__ == "__main__":
    run_experiment()