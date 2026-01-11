import numpy as np
import random
from abc import ABC, abstractmethod
from src.mechanics import Mechanics

class BaseStrategy(ABC):
    """
    策略基类 (Abstract Base Class)。
    所有具体的博弈策略（如 TFT, Joss, Friedman）都必须继承此类。
    """
    def __init__(self, my_size, name="Base"):
        """
        Args:
            my_size (float): 我方矿池大小 (0 < m < 1)
            name (str): 策略名称 (用于图表显示)
        """
        self.my_size = my_size
        self.name = name
        # 浮点数比较的容差，小于此值视为 0 (合作)
        self.EPSILON = 1e-6 

    @abstractmethod
    def make_decision(self, opp_size, history_vectors):
        """
        根据历史记录做出本轮决策。
        
        Args:
            opp_size (float): 对手矿池大小
            history_vectors (list of tuples): 历史记录列表。
                格式: [(my_x_t0, opp_x_t0), (my_x_t1, opp_x_t1), ...]
                如果列表为空，说明是第一轮 (t=0)。
                
        Returns:
            float: 本轮的攻击算力 (x)
        """
        pass

    def _is_attack(self, x_val):
        """辅助函数：判断某个 x 值是否构成攻击 (Defect)"""
        return x_val > self.EPSILON


class StaticStrategy(BaseStrategy):
    """
    静态策略：无论发生什么，永远输出固定的攻击率。
    用于测试或模拟“完全和平 / 完全战争”的对照组。
    """
    def __init__(self, my_size, fixed_attack_rate, name=None):
        if name is None:
            name = f"Static({fixed_attack_rate})"
        super().__init__(my_size, name)
        self.fixed_x = fixed_attack_rate

    def make_decision(self, opp_size, history_vectors):
        # 确保攻击率不超过自身算力
        return min(self.fixed_x, self.my_size)


class RandomStrategy(BaseStrategy):
    """
    随机策略：Axelrod 锦标赛中的 'RANDOM'。
    每一轮以 50% 概率合作 (x=0)，50% 概率背叛 (x=BestResponse)。
    """
    def __init__(self, my_size, prob_attack=0.5, name="Random"):
        super().__init__(my_size, name)
        self.prob = prob_attack

    def make_decision(self, opp_size, history_vectors):
        # 随机决定是否攻击
        if random.random() < self.prob:
            # 如果决定攻击，则计算针对"和平对手"的最佳偷袭攻击率
            # (这里简化假设对手是和平的，或者可以使用对手上一轮的状态)
            opp_prev_x = 0
            if history_vectors:
                 _, opp_prev_x = history_vectors[-1]
            
            return Mechanics.get_best_response(self.my_size, opp_size, opp_prev_x)
        else:
            return 0.0


class TitForTatStrategy(BaseStrategy):
    """
    以牙还牙 (Tit For Tat)：Axelrod 锦标赛的冠军策略。
    
    逻辑:
    1. 第一轮合作 (x=0)。
    2. 之后每一轮，单纯模仿对手上一轮的动作：
       - 如果对手上一轮攻击 (x > 0)，我本轮也攻击 (x = BestResponse to opp_last_x)。
       - 如果对手上一轮和平 (x = 0)，我本轮也和平。
    """
    def __init__(self, my_size, name="TFT"):
        super().__init__(my_size, name)

    def make_decision(self, opp_size, history_vectors):
        # 第一轮：表现出友善 (Niceness)
        if not history_vectors:
            return 0.0
        
        # 获取对手上一轮的动作
        _, opp_prev_x = history_vectors[-1]
        
        # 决策逻辑
        if self._is_attack(opp_prev_x):
            # 报复 (Retaliation)：计算针对对手上一轮攻击力度的最佳反击
            return Mechanics.get_best_response(self.my_size, opp_size, opp_prev_x)
        else:
            # 宽恕 (Forgiveness)：对手停手，我也停手
            return 0.0


class JossStrategy(TitForTatStrategy):
    """
    狡猾者 (Joss)：Axelrod 锦标赛中的"麻烦制造者"。
    
    逻辑:
    1. 大部分时间像 TFT 一样行动。
    2. 但是，有 10% 的概率，即使对手和平，Joss 也会发起偷袭 (Sneaky Defection)。
    3. 如果 TFT 逻辑本身决定要攻击，Joss 也会攻击。
    """
    def __init__(self, my_size, sneak_prob=0.1, name="Joss"):
        super().__init__(my_size, name)
        self.sneak_prob = sneak_prob

    def make_decision(self, opp_size, history_vectors):
        # 1. 先获取 TFT 的建议决策
        tft_decision = super().make_decision(opp_size, history_vectors)
        
        # 2. 检查是否本来就要攻击
        if self._is_attack(tft_decision):
            return tft_decision
        
        # 3. 如果 TFT 建议和平，Joss 尝试偷袭
        if random.random() < self.sneak_prob:
            # 偷袭：计算针对"和平对手"的最佳攻击率
            return Mechanics.get_best_response(self.my_size, opp_size, 0.0)
        
        return 0.0


class FriedmanStrategy(BaseStrategy):
    """
    永不原谅 (Friedman / Grim Trigger)。
    
    逻辑:
    1. 起始合作。
    2. 一旦对手在历史上任何时候攻击过 (x > 0)，
       Friedman 将在剩余的所有轮次中一直保持攻击状态。
    """
    def __init__(self, my_size, name="Friedman"):
        super().__init__(my_size, name)
        self.is_betrayed = False

    def make_decision(self, opp_size, history_vectors):
        # 如果还没有被背叛过，检查历史记录
        if not self.is_betrayed and history_vectors:
            for _, opp_x in history_vectors:
                if self._is_attack(opp_x):
                    self.is_betrayed = True
                    break
        
        if self.is_betrayed:
            # 处于战争状态：针对对手上一轮的行为进行最优攻击
            # 即使对手上一轮停手了(x=0)，Grim Trigger 依然会攻击(BestResponse to 0)
            opp_prev_x = 0
            if history_vectors:
                _, opp_prev_x = history_vectors[-1]
            return Mechanics.get_best_response(self.my_size, opp_size, opp_prev_x)
        else:
            # 和平状态
            return 0.0


class NashEquilibriumStrategy(BaseStrategy):
    """
    纳什均衡策略：无论对手做什么，始终采用静态纳什均衡的攻击率。
    这代表了 Eyal 论文中预期的"理性但由于缺乏沟通导致的双输"状态。
    
    注意：这需要预先通过迭代计算出均衡点，这里简化为每轮动态寻找。
    在多次迭代后，双方如果是 Nash vs Nash，会自动收敛到均衡点。
    """
    def __init__(self, my_size, name="Nash"):
        super().__init__(my_size, name)
        # 简单的缓存，避免第一轮不知道打多少
        # 实际上第一轮打多少不重要，很快会收敛
        self.last_attack = 0.0

    def make_decision(self, opp_size, history_vectors):
        # 纳什策略本质上是：假设对手是理性的，我也要是理性的。
        # 在不知道均衡点具体数值的情况下，
        # 最简单的逼近方法是：每一轮都针对对手上一轮做 Best Response。
        # 如果对手也是 Nash 策略，几轮后就会稳定在均衡点。
        
        if not history_vectors:
            # 第一轮试探性攻击 (或者根据 Eyal 论文，预估一个非零值)
            # 这里为了展示效果，第一轮可以使用针对和平的最佳响应
            return Mechanics.get_best_response(self.my_size, opp_size, 0.0)
        
        _, opp_prev_x = history_vectors[-1]
        return Mechanics.get_best_response(self.my_size, opp_size, opp_prev_x)
    
# --- 策略逻辑测试代码 ---
if __name__ == "__main__":
    print("=== Strategy Logic Verification ===\n")
    
    # 模拟参数
    my_m = 0.2
    opp_m = 0.2
    
    # ---------------------------------------------------------
    # Test 1: Tit For Tat (以牙还牙)
    # ---------------------------------------------------------
    print("Test 1: TFT Logic")
    tft = TitForTatStrategy(my_m)
    
    # case 1: 第一轮，应该是和平的
    history = [] 
    act1 = tft.make_decision(opp_m, history)
    print(f"  [Round 1] History=[] -> Action={act1:.6f} (Expected: 0.0)")
    
    # case 2: 对手上一轮攻击了 (0.05)，应该反击
    history = [(0, 0.05)]
    act2 = tft.make_decision(opp_m, history)
    print(f"  [Round 2] Opp_Prev=0.05 -> Action={act2:.6f} (Expected: >0, BestResponse)")
    
    # case 3: 对手上一轮停手了 (0.0)，应该宽恕
    history = [(0, 0.05), (0.02, 0.0)]
    act3 = tft.make_decision(opp_m, history)
    print(f"  [Round 3] Opp_Prev=0.0 -> Action={act3:.6f} (Expected: 0.0)")
    
    if act1 == 0 and act2 > 0 and act3 == 0:
        print("  >> TFT Logic PASSED ✅")
    else:
        print("  >> TFT Logic FAILED ❌")
    print("-" * 30)

    # ---------------------------------------------------------
    # Test 2: Friedman (Grim Trigger / 永不原谅)
    # ---------------------------------------------------------
    print("Test 2: Friedman Logic")
    grim = FriedmanStrategy(my_m)
    
    # case 1: 第一轮和平
    act1 = grim.make_decision(opp_m, [])
    print(f"  [Round 1] History=[] -> Action={act1:.6f} (Expected: 0.0)")
    
    # case 2: 对手攻击，触发扳机
    history = [(0, 0.05)]
    act2 = grim.make_decision(opp_m, history)
    print(f"  [Round 2] Opp_Prev=0.05 -> Action={act2:.6f} (Expected: >0)")
    
    # case 3: 对手后来求饶了 (0.0)，但我应该继续攻击！
    history = [(0, 0.05), (0.02, 0.0)]
    act3 = grim.make_decision(opp_m, history)
    print(f"  [Round 3] Opp_Prev=0.0 -> Action={act3:.6f} (Expected: >0, Grudge Held!)")
    
    if act1 == 0 and act2 > 0 and act3 > 0:
        print("  >> Friedman Logic PASSED ✅")
    else:
        print("  >> Friedman Logic FAILED ❌")
    print("-" * 30)

    # ---------------------------------------------------------
    # Test 3: Joss (概率偷袭)
    # ---------------------------------------------------------
    print("Test 3: Joss Logic (Probabilistic)")
    # 强制让偷袭概率为 100% 以便测试，或者跑多次统计
    # 这里我们只测它能不能正常运行
    joss = JossStrategy(my_m, sneak_prob=0.1)
    
    sneak_count = 0
    test_runs = 100
    # 模拟 100 次面对和平对手的情况
    for _ in range(test_runs):
        act = joss.make_decision(opp_m, [(0, 0)]) # 对手上一轮是和平的
        if act > 0:
            sneak_count += 1
            
    print(f"  [Sneak Test] Faced 100 peaceful rounds. Attacked {sneak_count} times.")
    print(f"  (Expected approx 10 times, allowing randomness)")
    
    if sneak_count > 0:
        print("  >> Joss Logic PASSED (Sneak behavior detected) ✅")
    else:
        print("  >> Joss Logic WARNING (No attacks? Check probability) ⚠️")