"""
图片加载模块
负责遍历文件夹、加载图片和管理图片索引
"""
import os


class ImageLoader:
    """图片加载器"""

    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']

    def __init__(self):
        self.image_folder = None
        self.image_list = []
        self.current_index = 0

    def load_folder(self, folder_path):
        """
        加载文件夹中的所有图片

        Args:
            folder_path: 文件夹路径

        Raises:
            FileNotFoundError: 文件夹不存在
            ValueError: 文件夹中没有支持的图片文件
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")

        if not os.path.isdir(folder_path):
            raise ValueError(f"路径不是文件夹: {folder_path}")

        self.image_folder = folder_path
        self.image_list = []

        # 遍历文件夹，查找所有支持的图片文件
        for filename in os.listdir(folder_path):
            if self._is_image_file(filename):
                self.image_list.append(os.path.join(folder_path, filename))

        # 按文件名排序
        self.image_list.sort()
        self.current_index = 0

        if len(self.image_list) == 0:
            raise ValueError(f"文件夹中没有找到支持的图片文件 (支持的格式: {', '.join(self.SUPPORTED_FORMATS)})")

    def get_current_image(self):
        """
        获取当前图片路径

        Returns:
            str: 当前图片路径，如果索引超出范围返回None
        """
        if 0 <= self.current_index < len(self.image_list):
            return self.image_list[self.current_index]
        return None

    def next_image(self):
        """
        切换到下一张图片

        Returns:
            str: 下一张图片路径，如果没有更多图片返回None
        """
        self.current_index += 1
        return self.get_current_image()

    def previous_image(self):
        """
        切换到上一张图片

        Returns:
            str: 上一张图片路径，如果没有上一张返回None
        """
        if self.current_index > 0:
            self.current_index -= 1
            return self.get_current_image()
        return None

    def has_next(self):
        """
        是否还有下一张图片

        Returns:
            bool: 如果还有下一张图片返回True
        """
        return self.current_index < len(self.image_list)

    def get_progress(self):
        """
        获取进度信息

        Returns:
            tuple: (已处理数量, 总图片数)
        """
        # 已处理数量 = 当前索引 + 1，但不超过总数
        processed = min(self.current_index + 1, len(self.image_list))
        return (processed, len(self.image_list))

    def get_total_count(self):
        """
        获取图片总数

        Returns:
            int: 图片总数
        """
        return len(self.image_list)

    def reset(self):
        """重置索引到第一张图片"""
        self.current_index = 0

    def is_empty(self):
        """
        是否为空（没有加载图片）

        Returns:
            bool: 如果没有图片返回True
        """
        return len(self.image_list) == 0

    def _is_image_file(self, filename):
        """
        判断是否为图片文件

        Args:
            filename: 文件名

        Returns:
            bool: 如果是支持的图片格式返回True
        """
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.SUPPORTED_FORMATS
