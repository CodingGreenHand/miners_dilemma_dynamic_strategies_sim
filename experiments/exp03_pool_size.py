import numpy as np
import matplotlib.pyplot as plt
import os
from src.mechanics import Mechanics

# --- 中文显示配置 (Windows) ---
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置默认字体为“黑体”
plt.rcParams['axes.unicode_minus'] = False    # 解决负号 '-' 显示为方块的问题
# ---------------------------

def run_experiment():
    # 遍历矿池大小 m1 从 1% 到 45%
    # 假设 m2 固定为 20%
    m1_range = np.linspace(0.01, 0.45, 50)
    m2 = 0.20
    
    gains = []
    
    for m1 in m1_range:
        # 计算和平收益
        p_peace, _ = Mechanics.calculate_absolute_payoff(m1, m2, 0, 0)
        
        # 计算针对和平的最佳攻击收益 (单方攻击)
        opt_x = Mechanics.get_best_response(m1, m2, 0)
        p_attack, _ = Mechanics.calculate_absolute_payoff(m1, m2, opt_x, 0)
        
        # 计算收益提升百分比
        gain_pct = (p_attack - p_peace) / p_peace * 100
        gains.append(gain_pct)
        
    # 绘图
    plt.figure(figsize=(8, 5))
    plt.plot(m1_range * 100, gains, color='purple', linewidth=2)
    plt.title('攻击激励与矿池大小的关系 (对手算力 m=20%)', fontsize=12)
    plt.xlabel('我方矿池大小 (%)')
    plt.ylabel('单方攻击带来的收益提升 (%)')
    plt.grid(True, alpha=0.3)

    save_dir = 'results/figures'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"Created directory: {save_dir}")
    
    plt.savefig(f'{save_dir}/exp03_size_sensitivity.png')
    print("Experiment 3 Completed. Figure saved.")

if __name__ == "__main__":
    run_experiment()