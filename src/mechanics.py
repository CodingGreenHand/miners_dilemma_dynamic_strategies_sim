import numpy as np
from scipy.optimize import minimize_scalar

class Mechanics:
    """
    物理引擎层：严格基于 Eyal 的 'The Miner's Dilemma' 论文公式实现。
    不包含任何策略逻辑，仅负责数学计算和数值优化。
    """

    @staticmethod
    def _calculate_effective_rates(m1, m2, x1_2, x2_1, total_m=1.0):
        """
        计算直接有效算力 (Effective Mining Rates - R)。
        
        [cite_start]对应论文公式 (9)[cite: 551]:
        R1 = (m1 - x1_2) / (m - x1_2 - x2_1)
        R2 = (m2 - x2_1) / (m - x1_2 - x2_1)
        
        Args:
            m1, m2: 矿池大小 (0 < m < 1)
            x1_2: 矿池1对矿池2的攻击算力
            x2_1: 矿池2对矿池1的攻击算力
            total_m: 全网总算力，默认为 1 (归一化)
            
        Returns:
            (R1, R2): 双方的有效挖矿率
        """
        # 计算全网有效算力 (Total Effective Mining Power)
        # 注意：这里假设未参与攻击的第三方矿工算力也是有效的
        m_effective = total_m - x1_2 - x2_1
        
        # 防止除零错误 (极个别极端情况)
        if m_effective <= 1e-9:
            return 0.0, 0.0
            
        R1 = (m1 - x1_2) / m_effective
        R2 = (m2 - x2_1) / m_effective
        
        return R1, R2

    @staticmethod
    def calculate_revenue_densities(m1, m2, x1_2, x2_1):
        """
        计算收益密度 (Revenue Density - r)。
        
        [cite_start]对应论文公式 (11)[cite: 561]:
        r1 = (m2*R1 + x1_2*(R1+R2)) / (m1*m2 + m1*x1_2 + m2*x2_1)
        
        收益密度 r=1 代表正常 Solo 挖矿收益。r>1 代表收益增加。
        
        Returns:
            (r1, r2): 双方的收益密度
        """
        # 1. 先获取有效算力 R
        R1, R2 = Mechanics._calculate_effective_rates(m1, m2, x1_2, x2_1)
        
        # 2. 计算分母 (Shared Denominator)
        # 论文 Eq. 11 的分母部分：m1*m2 + m1*x1_2 + m2*x2_1
        denominator = (m1 * m2) + (m1 * x1_2) + (m2 * x2_1)
        
        if denominator <= 0:
            return 0.0, 0.0
            
        # 3. 计算分子 (Numerators)
        # Pool 1 分子: m2*R1 + x1_2*(R1+R2)
        num1 = (m2 * R1) + (x1_2 * (R1 + R2))
        
        # Pool 2 分子: m1*R2 + x2_1*(R1+R2)
        num2 = (m1 * R2) + (x2_1 * (R1 + R2))
        
        r1 = num1 / denominator
        r2 = num2 / denominator
        
        return r1, r2

    @staticmethod
    def calculate_absolute_payoff(m1, m2, x1_2, x2_1):
        """
        计算每一轮的绝对收益 (Absolute Payoff)。
        这是 Axelrod 锦标赛排名的依据。
        
        Payoff = 收益密度(r) * 矿池大小(m)
        """
        r1, r2 = Mechanics.calculate_revenue_densities(m1, m2, x1_2, x2_1)
        
        payoff1 = r1 * m1
        payoff2 = r2 * m2
        
        return payoff1, payoff2

    @staticmethod
    def get_best_response(my_m, opp_m, opp_x_fixed):
        """
        寻找最佳响应攻击率 (Best Response)。
        
        [cite_start]对应论文逻辑[cite: 565]:
        x_opt = argmax r_my(x, opp_x_fixed)
        
        使用了 scipy.optimize.minimize_scalar 来寻找数值解。
        
        Args:
            my_m: 我方矿池大小
            opp_m: 对手矿池大小
            opp_x_fixed: 对手当前的攻击率 (假设固定)
            
        Returns:
            optimal_x: 能最大化我方收益的攻击算力
        """
        
        # 定义目标函数 (取负值，因为我们要 maximize 收益，而 scipy 是 minimize)
        def objective(my_x_candidate):
            # 这是一个对称博弈，我们暂时把我方当做 Pool 1，对手当做 Pool 2
            # 来调用 calculate_absolute_payoff
            p1, _ = Mechanics.calculate_absolute_payoff(
                m1=my_m, 
                m2=opp_m, 
                x1_2=my_x_candidate, 
                x2_1=opp_x_fixed
            )
            return -p1 # 取负
            
        # 约束条件：攻击算力不能小于0，也不能大于我方拥有的总算力
        # [cite_start]论文提及可行域: 0 <= x <= m [cite: 573]
        bounds = (0.0, my_m)
        
        result = minimize_scalar(
            objective,
            bounds=bounds,
            method='bounded',
            options={'xatol': 1e-5} # 精度控制
        )
        
        if result.success:
            return result.x
        else:
            # 如果优化失败，保守返回 0
            return 0.0

# --- 测试代码 ---
if __name__ == "__main__":
    import pandas as pd
    
    # 设置打印格式
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    print("=== Mechanics Module Verification ===\n")

    # -------------------------------------------------------------------------
    # Scenario 1: 单方攻击获利验证 (The Profitable Attack)
    # 目的: 证明在对方不防守时，存在一个最佳攻击率 x，使得攻击者收益 > 和平收益
    # -------------------------------------------------------------------------
    print("--- Scenario 1: Unilateral Attack Profitability ---")
    m1, m2 = 0.2, 0.2  # 两个 20% 算力的矿池
    
    # 1. 基准：和平状态 (Peace)
    p1_peace, p2_peace = Mechanics.calculate_absolute_payoff(m1, m2, 0, 0)
    print(f"[Peace] Both cooperate:")
    print(f"  P1 Payoff: {p1_peace:.6f}")
    print(f"  P2 Payoff: {p2_peace:.6f}")

    # 2. 计算最佳攻击率 (Optimal Attack)
    # 假设 P2 不攻击 (x2_1 = 0)，P1 寻找最佳 x1_2
    opt_x1 = Mechanics.get_best_response(m1, m2, 0)
    p1_attack, p2_sucker = Mechanics.calculate_absolute_payoff(m1, m2, opt_x1, 0)
    
    print(f"\n[Attack] P1 attacks with optimal rate x={opt_x1:.6f} (P2 sleeps):")
    print(f"  P1 Payoff: {p1_attack:.6f} (Change: {(p1_attack - p1_peace)/p1_peace*100:+.4f}%)")
    print(f"  P2 Payoff: {p2_sucker:.6f} (Change: {(p2_sucker - p2_peace)/p2_peace*100:+.4f}%)")
    
    if p1_attack > p1_peace:
        print("  >> VERIFIED: Unilateral attack is PROFITABLE.")
    else:
        print("  >> FAILED: Attack is not profitable.")

    print("\n" + "-"*50 + "\n")

    # -------------------------------------------------------------------------
    # Scenario 2: 纳什均衡与囚徒困境 (Nash Equilibrium & Prisoner's Dilemma)
    # 目的: 模拟双方互相调整攻击率，最终收敛到纳什均衡，并验证此时双方收益 < 和平收益
    # -------------------------------------------------------------------------
    print("--- Scenario 2: Nash Equilibrium (Iterative Finding) ---")
    
    # 初始状态
    curr_x1, curr_x2 = 0.0, 0.0
    print(f"Iter 0: x1={curr_x1:.4f}, x2={curr_x2:.4f}")

    # 简单的最佳响应动力学迭代 (Best Response Dynamics)
    # 每一轮，双方都根据对方上一轮的策略，调整自己的策略到最优
    for i in range(1, 11):
        # 注意：这里是同步更新 (Simultaneous Update)，模拟同时决策
        # P1 针对旧的 x2 优化
        new_x1 = Mechanics.get_best_response(m1, m2, curr_x2)
        # P2 针对旧的 x1 优化 (由于对称性 m1=m2，结果应该与 x1 相同)
        new_x2 = Mechanics.get_best_response(m2, m1, curr_x1)
        
        curr_x1, curr_x2 = new_x1, new_x2
        
        # 计算当前收益
        p1_curr, p2_curr = Mechanics.calculate_absolute_payoff(m1, m2, curr_x1, curr_x2)
        print(f"Iter {i}: x1={curr_x1:.4f}, x2={curr_x2:.4f} => P1={p1_curr:.6f}, P2={p2_curr:.6f}")

    print("\n[Equilibrium Result]")
    print(f"  Nash Equilibrium Attack Rate: {curr_x1:.6f}")
    print(f"  Equilibrium Payoff: {p1_curr:.6f}")
    print(f"  Peace Payoff      : {p1_peace:.6f}")
    
    loss_pct = (p1_curr - p1_peace) / p1_peace * 100
    print(f"  Net Loss vs Peace : {loss_pct:.4f}%")
    
    if p1_curr < p1_peace:
        print("  >> VERIFIED: The Miner's Dilemma exists (Nash Payoff < Peace Payoff).")
    else:
        print("  >> FAILED: No dilemma found.")