"""
图片缓存管理模块
负责生成和管理图片金字塔缓存，显著提升缩放性能
"""
from PIL import Image, ImageTk


class ImageCacheManager:
    """图片金字塔缓存管理器"""

    def __init__(self):
        """初始化缓存管理器"""
        self.pyramid = {}  # {scale: PhotoImage}
        self.fit_scale = 1.0  # 当前适应屏幕的缩放比例
        self.base_scales = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]

    def generate_pyramid(self, original_image, fit_scale):
        """
        预生成图片金字塔缓存

        Args:
            original_image: 原始PIL图片对象
            fit_scale: 适应屏幕的缩放比例

        性能: 使用BILINEAR算法平衡速度和质量，9个级别预生成
        """
        self.pyramid = {}
        self.fit_scale = fit_scale
        original_width, original_height = original_image.size

        for scale in self.base_scales:
            # 计算实际缩放后的尺寸
            actual_scale = fit_scale * scale
            new_width = int(original_width * actual_scale)
            new_height = int(original_height * actual_scale)

            # 使用BILINEAR算法预生成（速度和质量平衡）
            try:
                resized_image = original_image.resize(
                    (new_width, new_height),
                    Image.Resampling.BILINEAR
                )
                self.pyramid[scale] = ImageTk.PhotoImage(resized_image)
            except Exception as e:
                print(f"生成缓存级别 {scale} 失败: {e}")

    def get_cached_image(self, target_scale):
        """
        获取最接近的缓存图片

        Args:
            target_scale: 目标缩放比例

        Returns:
            tuple: (PhotoImage对象, 实际使用的缩放比例)
        """
        if not self.pyramid:
            return None, 1.0

        # 找到最接近的缓存级别
        closest_scale = min(self.pyramid.keys(), key=lambda x: abs(x - target_scale))
        return self.pyramid[closest_scale], closest_scale

    def generate_high_quality(self, original_image, target_scale, fit_scale):
        """
        生成高质量图片（缩放结束时调用）

        Args:
            original_image: 原始PIL图片对象
            target_scale: 目标缩放比例
            fit_scale: 适应屏幕的缩放比例

        Returns:
            PhotoImage: 使用LANCZOS高质量算法生成的图片
        """
        original_width, original_height = original_image.size
        actual_scale = fit_scale * target_scale
        new_width = int(original_width * actual_scale)
        new_height = int(original_height * actual_scale)

        # 使用LANCZOS算法生成高质量图片
        resized_image = original_image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )
        return ImageTk.PhotoImage(resized_image)

    def clear(self):
        """清除所有缓存"""
        self.pyramid = {}
        self.fit_scale = 1.0

    def is_cache_available(self):
        """
        检查缓存是否可用

        Returns:
            bool: 缓存是否已生成
        """
        return len(self.pyramid) > 0
