"""
配置管理模块
负责加载和保存误判类型配置
"""
import json
import os
from datetime import datetime


class ConfigManager:
    """配置管理器"""

    CONFIG_FILE = "config.json"

    def __init__(self):
        self.config = {}

    def load_types(self):
        """
        加载误判类型配置
        如果配置文件不存在，返回默认配置
        """
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                return self.config.get('misjudgment_types', [])
            except json.JSONDecodeError as e:
                print(f"配置文件格式错误: {e}")
                return self._create_default_config()
            except Exception as e:
                print(f"加载配置时发生错误: {e}")
                return self._create_default_config()
        else:
            return self._create_default_config()

    def _create_default_config(self):
        """创建默认配置"""
        default_types = ["化锡NG", "隔离膜NG", "跳线偏移NG", "几字形NG", "跳线搭接NG"]
        self.save_types(default_types)
        return default_types

    def save_types(self, types_list):
        """
        保存误判类型配置

        Args:
            types_list: 误判类型列表
        """
        self.config['misjudgment_types'] = types_list
        self.config['version'] = "1.0"
        self.config['last_updated'] = datetime.now().strftime("%Y-%m-%d")

        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置时发生错误: {e}")
            return False

    def add_type(self, new_type):
        """
        添加新的误判类型

        Args:
            new_type: 新的误判类型名称

        Returns:
            bool: 添加成功返回True，已存在或失败返回False
        """
        types = self.load_types()
        if new_type not in types:
            types.append(new_type)
            return self.save_types(types)
        return False

    def remove_type(self, type_name):
        """
        删除误判类型

        Args:
            type_name: 要删除的误判类型名称

        Returns:
            bool: 删除成功返回True，不存在或失败返回False
        """
        types = self.load_types()
        if type_name in types:
            # 至少保留一个误判类型
            if len(types) <= 1:
                print("至少需要保留一个误判类型")
                return False
            types.remove(type_name)
            return self.save_types(types)
        return False

    def update_types(self, types_list):
        """
        更新误判类型列表

        Args:
            types_list: 新的误判类型列表

        Returns:
            bool: 更新成功返回True
        """
        if not types_list:
            print("误判类型列表不能为空")
            return False
        return self.save_types(types_list)
