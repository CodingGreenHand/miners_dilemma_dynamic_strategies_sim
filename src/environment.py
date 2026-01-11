import pandas as pd
from src.mechanics import Mechanics

class GameMatch:
    """
    单场博弈控制器 (Simulation Environment)。
    负责管理两个矿池策略之间的 N 轮对局，计算分数并记录日志。
    """
    def __init__(self, agent_a, agent_b):
        """
        Args:
            agent_a (BaseStrategy): 策略实例 A
            agent_b (BaseStrategy): 策略实例 B
        """
        self.agent_a = agent_a
        self.agent_b = agent_b
        
        # 比赛日志，用于存储每一轮的详细数据
        self.history = [] 
        
        # 策略内部需要的历史记录格式 (用于传给 make_decision)
        # 格式: [(x_a, x_b), (x_a, x_b), ...]
        self.history_vectors = []

    def run(self, rounds=200):
        """
        执行仿真循环。
        
        Args:
            rounds (int): 总轮数 (Axelrod 锦标赛标准为 200)
            
        Returns:
            pd.DataFrame: 包含完整对局记录的数据表
        """
        # 重置状态
        self.history = []
        self.history_vectors = []
        
        # 初始化累积收益
        cum_revenue_a = 0.0
        cum_revenue_b = 0.0
        
        for t in range(1, rounds + 1):
            # 1. 决策阶段 (Decision Phase)
            # 双方同时根据之前的历史做出决策
            # 注意：传入 history_vectors 时，需要根据视角反转
            # A 看历史: [(a, b), ...]
            # B 看历史: [(b, a), ...] -> 需要把 tuple 里的元素反转一下传给 B
            
            # 准备 B 的视角历史 (交换位置)
            history_for_b = [(xb, xa) for (xa, xb) in self.history_vectors]
            
            # 获取动作 (攻击算力 x)
            # 注意：传入的是对方的矿池大小
            x_a = self.agent_a.make_decision(self.agent_b.my_size, self.history_vectors)
            x_b = self.agent_b.make_decision(self.agent_a.my_size, history_for_b)
            
            # 2. 计算阶段 (Calculation Phase)
            # 使用物理引擎计算本轮收益
            r_a, r_b = Mechanics.calculate_absolute_payoff(
                self.agent_a.my_size, 
                self.agent_b.my_size, 
                x_a, 
                x_b
            )
            
            # 累加收益
            cum_revenue_a += r_a
            cum_revenue_b += r_b
            
            # 3. 记录阶段 (Logging Phase)
            # 更新历史向量 (供下一轮决策使用)
            self.history_vectors.append((x_a, x_b))
            
            # 记录详细日志 (供分析使用)
            record = {
                "Round": t,
                "Pool_A": self.agent_a.name,
                "Pool_B": self.agent_b.name,
                "Size_A": self.agent_a.my_size,
                "Size_B": self.agent_b.my_size,
                "Attack_A": x_a,
                "Attack_B": x_b,
                "Revenue_A": r_a,
                "Revenue_B": r_b,
                "Cum_Rev_A": cum_revenue_a,
                "Cum_Rev_B": cum_revenue_b
            }
            self.history.append(record)
            
        # 转换为 DataFrame 返回
        return pd.DataFrame(self.history)

# --- 环境测试代码 (追加到文件末尾) ---
if __name__ == "__main__":
    from src.strategies import TitForTatStrategy, RandomStrategy, FriedmanStrategy
    
    print("=== Environment Verification ===\n")
    
    # 场景：TFT (Pool A) vs Random (Pool B)
    # 矿池大小设定为非对称，模拟真实情况
    m_a = 0.25
    m_b = 0.15
    
    strategy_a = TitForTatStrategy(m_a, name="TFT_Agent")
    strategy_b = RandomStrategy(m_b, prob_attack=0.5, name="Random_Agent")
    # 或者试试 Friedman
    # strategy_b = FriedmanStrategy(m_b, name="Friedman_Agent")
    
    print(f"Match: {strategy_a.name} ({m_a}) vs {strategy_b.name} ({m_b})")
    
    match = GameMatch(strategy_a, strategy_b)
    df_result = match.run(rounds=10) # 先跑 10 轮看看
    
    # 打印前几轮和后几轮的数据
    print("\nSimulation Logs (First 10 rounds):")
    print(df_result[["Round", "Attack_A", "Attack_B", "Revenue_A", "Revenue_B"]].to_string(index=False))
    
    print("\nTotal Revenue:")
    print(f"  {strategy_a.name}: {df_result['Revenue_A'].sum():.6f}")
    print(f"  {strategy_b.name}: {df_result['Revenue_B'].sum():.6f}")
    
    # 简单验证逻辑
    # 如果 Random 攻击了 (Attack_B > 0)，下一轮 TFT 必须反击 (Attack_A > 0)
    print("\nLogic Check:")
    attacks = df_result["Attack_B"].tolist()
    responses = df_result["Attack_A"].tolist()
    
    passed = True
    for i in range(len(attacks) - 1):
        if attacks[i] > 1e-6:
            if responses[i+1] < 1e-6:
                print(f"  [Round {i+2}] FAILED: Random attacked but TFT did not respond!")
                passed = False
            else:
                print(f"  [Round {i+2}] OK: Random attacked, TFT responded.")
    
    if passed:
        print(">> Environment Interaction Logic PASSED ✅")