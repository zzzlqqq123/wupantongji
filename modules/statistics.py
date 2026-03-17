"""
统计计算模块
负责实时计算各项统计数据和误判率
"""


class Statistics:
    """统计数据计算器"""

    def __init__(self):
        self.total_count = 0           # 总图片数
        self.misjudgment_count = 0     # 误判数量
        self.detection_count = 0       # 检出数量
        self.type_counts = {}          # 各误判类型的计数
        self.detection_type_counts = {}  # 各检出类型的计数
        self.total_capacity = 0        # 总产能（用户输入）

    def set_total_capacity(self, capacity):
        """
        设置总产能

        Args:
            capacity: 总产能数量
        """
        if capacity > 0:
            self.total_capacity = capacity

    def get_total_capacity(self):
        """
        获取总产能

        Returns:
            int: 总产能数量
        """
        return self.total_capacity

    def record_misjudgment(self, selected_types):
        """
        记录误判数据

        Args:
            selected_types: 选中的误判类型列表
        """
        self.total_count += 1
        self.misjudgment_count += 1

        # 统计各误判类型的数量
        for type_name in selected_types:
            if type_name not in self.type_counts:
                self.type_counts[type_name] = 0
            self.type_counts[type_name] += 1

    def record_detection(self, selected_types=None):
        """记录检出数据"""
        self.total_count += 1
        self.detection_count += 1
        # 如果选择了类型，则记录为该类型检出
        if selected_types:
            for type_name in selected_types:
                if type_name not in self.detection_type_counts:
                    self.detection_type_counts[type_name] = 0
                self.detection_type_counts[type_name] += 1

    def remove_misjudgment(self, types):
        """
        移除误判数据（用于修改标注）
        Args:
            types: 要移除的误判类型列表
        """
        if self.misjudgment_count > 0:
            self.misjudgment_count -= 1
        if self.total_count > 0:
            self.total_count -= 1

        # 移除各误判类型的计数
        for type_name in types:
            if type_name in self.type_counts and self.type_counts[type_name] > 0:
                self.type_counts[type_name] -= 1

    def remove_detection(self, types=None):
        """移除检出数据（用于修改标注）"""
        if self.detection_count > 0:
            self.detection_count -= 1
        if self.total_count > 0:
            self.total_count -= 1
        # 回退对应类型的检出计数
        if types:
            for type_name in types:
                if type_name in self.detection_type_counts and self.detection_type_counts[type_name] > 0:
                    self.detection_type_counts[type_name] -= 1

    def get_misjudgment_rate(self):
        """
        计算总误判率
        公式：误判数量 / 总产能 * 100%

        Returns:
            float: 误判率（百分比）
        """
        if self.total_capacity == 0:
            return 0.0
        return (self.misjudgment_count / self.total_capacity) * 100

    def get_detection_rate(self):
        """
        计算总检出率

        Returns:
            float: 检出率（百分比）
        """
        if self.total_count == 0:
            return 0.0
        return (self.detection_count / self.total_count) * 100

    def get_type_rates(self):
        """
        计算各类型误判率
        计算公式：该类型误判数量 / 总产能 * 100%

        Returns:
            dict: 各类型的误判率字典
        """
        rates = {}
        if self.total_capacity == 0:
            return rates

        for type_name, count in self.type_counts.items():
            rate = (count / self.total_capacity) * 100
            rates[type_name] = round(rate, 2)

        return rates

    def get_summary(self):
        """
        获取统计摘要

        Returns:
            dict: 包含所有统计数据的字典
        """
        return {
            'total': self.total_count,
            'misjudgment': self.misjudgment_count,
            'detection': self.detection_count,
            'misjudgment_rate': round(self.get_misjudgment_rate(), 2),
            'detection_rate': round(self.get_detection_rate(), 2),
            'type_rates': self.get_type_rates(),
            'type_counts': self.type_counts.copy(),  # 添加类型数量
            'detection_type_counts': self.detection_type_counts.copy(),  # 添加检出类型数量
            'total_capacity': self.total_capacity  # 添加总产能
        }

    def reset(self):
        """重置所有统计数据"""
        self.total_count = 0
        self.misjudgment_count = 0
        self.detection_count = 0
        self.type_counts = {}
        self.detection_type_counts = {}

    def get_type_counts(self):
        """
        获取各误判类型的原始计数

        Returns:
            dict: 各类型的计数字典
        """
        return self.type_counts.copy()

    def get_detection_type_counts(self):
        """
        获取各检出类型的原始计数

        Returns:
            dict: 各类型的计数字典
        """
        return self.detection_type_counts.copy()
