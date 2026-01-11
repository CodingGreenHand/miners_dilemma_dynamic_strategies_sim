import pandas as pd
import seaborn as sns
import os
import matplotlib.pyplot as plt
from src.strategies import TitForTatStrategy, FriedmanStrategy, JossStrategy, RandomStrategy, NashEquilibriumStrategy, StaticStrategy
from src.environment import GameMatch

# --- 中文显示配置 (Windows) ---
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置默认字体为“黑体”
plt.rcParams['axes.unicode_minus'] = False    # 解决负号 '-' 显示为方块的问题
# ---------------------------

def run_experiment():
    # 定义参赛选手
    # 统一使用 m=0.2 (20% 算力) 保证公平
    m = 0.2
    strategies = [
        TitForTatStrategy(m, name="TFT"),
        FriedmanStrategy(m, name="Friedman"),
        JossStrategy(m, sneak_prob=0.1, name="Joss"),
        RandomStrategy(m, prob_attack=0.5, name="Random"),
        NashEquilibriumStrategy(m, name="Nash"), # 代表"总是背叛/总是理性"
        StaticStrategy(m, fixed_attack_rate=0.0, name="Peace") # 总是合作
    ]
    
    results = []
    
    # 双重循环：人人对抗
    print("Running Tournament...")
    for agent_a in strategies:
        row_scores = {}
        for agent_b in strategies:
            # 重新实例化以重置内部状态 (非常重要!)
            # Python 对象传递是引用的，必须创建新对象或重置状态
            # 这里简单起见，我们假设 strategy 类很轻量，直接用新对象有点麻烦
            # 更优雅的方式是在 Strategy 类里加个 reset() 方法
            # 但为了不改动 strategies.py，我们这里手动重置关键状态
            if hasattr(agent_a, 'is_betrayed'): agent_a.is_betrayed = False
            if hasattr(agent_b, 'is_betrayed'): agent_b.is_betrayed = False
            
            # 注意：对于 Random 和 Joss，由于随机性，应该多跑几轮取平均
            # 这里为了演示，只跑一轮 200 次
            match = GameMatch(agent_a, agent_b)
            df = match.run(rounds=200)
            
            total_score = df['Revenue_A'].sum()
            row_scores[agent_b.name] = total_score
            
        # 记录该选手的得分详情
        entry = row_scores.copy()
        entry['Agent'] = agent_a.name
        results.append(entry)

    # 处理数据
    df_res = pd.DataFrame(results)
    df_res.set_index('Agent', inplace=True)
    
    # 计算平均分并排名
    df_res['Average_Score'] = df_res.mean(axis=1)
    df_res = df_res.sort_values('Average_Score', ascending=False)
    
    print("\nTournament Results (Average Score per Match):")
    print(df_res['Average_Score'])


    # 定义翻译字典
    name_map = {
        'Peace': '和平(Peace)',
        'Friedman': '记仇(Friedman)',
        'TFT': '以牙还牙(TFT)',
        'Random': '随机(Random)',
        'Joss': '狡猾(Joss)',
        'Nash': '纳什(Nash)'
    }
    
    # 重命名索引和列 (为了画图好看)
    heatmap_data = df_res.drop(columns=['Average_Score'])
    heatmap_data.index = heatmap_data.index.map(lambda x: name_map.get(x, x))
    heatmap_data.columns = heatmap_data.columns.map(lambda x: name_map.get(x, x))

    # 绘制热力图
    plt.figure(figsize=(10, 8))
    sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="YlGnBu")
    
    # 标题和标签
    plt.title('锦标赛玩家A收益矩阵 (200轮总收益)', fontsize=14)
    plt.ylabel('玩家 A (行)', fontsize=12)
    plt.xlabel('玩家 B (列)', fontsize=12)
    
    plt.tight_layout()

    save_dir = 'results/figures'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"Created directory: {save_dir}")
    
    plt.savefig(f'{save_dir}/exp01_tournament_heatmap.png')
    print("Experiment 1 Completed. Figure saved.")

if __name__ == "__main__":
    run_experiment()