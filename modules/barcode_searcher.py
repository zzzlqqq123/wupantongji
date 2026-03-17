"""
条码搜索模块
负责从图片文件名中提取条码，并在指定路径下搜索包含相同条码的所有图片
"""
import os


class BarcodeSearcher:
    """条码搜索器"""
    
    # 支持的图片格式（与ImageLoader保持一致）
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
    
    @staticmethod
    def extract_barcode(filename):
        """
        从文件名中提取条码（第一个下划线之前的部分）
        
        Args:
            filename: 文件名（可以是完整路径或仅文件名）
            
        Returns:
            str: 提取的条码，如果没有下划线则返回整个文件名（不含扩展名）
            
        Examples:
            >>> extract_barcode("E4FXT126A297300307602068_NG_20260129112027975.jpg")
            'E4FXT126A297300307602068'
            
            >>> extract_barcode("test.jpg")
            'test'
        """
        # 获取不带路径的文件名
        base_name = os.path.basename(filename)
        
        # 去除扩展名
        name_without_ext = os.path.splitext(base_name)[0]
        
        # 提取第一个下划线之前的部分
        if '_' in name_without_ext:
            return name_without_ext.split('_')[0]
        else:
            return name_without_ext
    
    @staticmethod
    def is_image_file(filename):
        """
        判断是否为支持的图片文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 如果是支持的图片格式返回True
        """
        ext = os.path.splitext(filename)[1].lower()
        return ext in BarcodeSearcher.SUPPORTED_FORMATS
    
    @staticmethod
    def is_ng_image(filename):
        """
        判断图片文件名中是否包含"NG"标识
        使用更严格的匹配规则，避免误匹配包含"NG"子字符串的其他词（如RUNNING）
        
        Args:
            filename: 文件名（可以是完整路径或仅文件名）
            
        Returns:
            bool: 如果文件名中包含"NG"标识返回True
            
        Examples:
            >>> is_ng_image("E4FXT126A297300307602068_NG_20260129112027975.jpg")
            True
            
            >>> is_ng_image("E4FXT126A297300307602068_OK_20260129112027975.jpg")
            False
            
            >>> is_ng_image("RUNNING_test.jpg")
            False  # 不会误匹配包含"NG"的其他词
        """
        # 获取不带路径和扩展名的文件名
        base_name = os.path.basename(filename)
        name_without_ext = os.path.splitext(base_name)[0].upper()
        
        # 检查是否包含"_NG_"或以"_NG"结尾或以"NG_"开头
        # 这样可以避免误匹配如"RUNNING"、"MANAGING"等包含"NG"的词
        return ('_NG_' in name_without_ext or 
                name_without_ext.endswith('_NG') or 
                name_without_ext.startswith('NG_'))
    
    @staticmethod
    def contains_barcode(filename, barcode):
        """
        判断文件名中是否包含指定的条码
        
        Args:
            filename: 文件名（可以是完整路径或仅文件名）
            barcode: 要查找的条码字符串
            
        Returns:
            bool: 如果文件名中包含该条码返回True
            
        Examples:
            >>> contains_barcode("E4FXT126A297300307602068_NG_20260129.jpg", "E4FXT126A297300307602068")
            True
            
            >>> contains_barcode("some_prefix_E4FXT126A297300307602068_NG.jpg", "E4FXT126A297300307602068")
            True
        """
        # 获取不带路径的文件名
        base_name = os.path.basename(filename)
        # 检查文件名中是否包含条码
        return barcode in base_name
    
    @staticmethod
    def search_images_by_barcodes(search_root, barcodes, ng_only=True):
        """
        在指定根目录下搜索包含指定条码的所有图片（包括所有子文件夹）
        
        Args:
            search_root: 搜索的根目录路径
            barcodes: 要搜索的条码列表（set或list）
            ng_only: 是否只搜索文件名中包含"NG"的图片，默认为True
            
        Returns:
            dict: {条码: [图片路径列表]} 的字典
            
        Example:
            >>> barcodes = ['E4FXT126A297300307602068', 'E4FXT126A297300307602069']
            >>> result = search_images_by_barcodes('E:\\Image\\2026-01-28-白班', barcodes)
            >>> # 返回: {'E4FXT126A297300307602068': ['path1_NG.jpg', 'path2_NG.jpg'], ...}
            >>> # 只返回文件名中同时包含条码和"NG"的图片
        """
        if not os.path.exists(search_root):
            return {}
        
        # 转换为集合以提高查找效率
        barcode_set = set(barcodes) if not isinstance(barcodes, set) else barcodes
        
        # 结果字典：{条码: [图片路径列表]}
        result = {barcode: [] for barcode in barcode_set}
        
        # 递归遍历所有文件
        for dirpath, dirnames, filenames in os.walk(search_root):
            # 遍历当前文件夹中的所有文件
            for filename in filenames:
                # 只处理图片文件
                if not BarcodeSearcher.is_image_file(filename):
                    continue
                
                # 如果需要只搜索NG图片，检查文件名中是否包含"NG"
                if ng_only and not BarcodeSearcher.is_ng_image(filename):
                    continue
                
                # 检查文件名中是否包含目标条码
                for barcode in barcode_set:
                    if BarcodeSearcher.contains_barcode(filename, barcode):
                        full_path = os.path.join(dirpath, filename)
                        result[barcode].append(full_path)
                        break  # 找到匹配的条码后跳出循环
        
        return result
    
    @staticmethod
    def get_parent_folder(folder_path, levels=1):
        """
        获取文件夹的父目录
        
        Args:
            folder_path: 文件夹路径
            levels: 向上查找的级数，默认为1
            
        Returns:
            str: 父目录路径
            
        Example:
            >>> get_parent_folder('E:\\Image\\2026-01-28-白班\\检测拼接总图\\NG', levels=1)
            'E:\\Image\\2026-01-28-白班\\检测拼接总图'
            
            >>> get_parent_folder('E:\\Image\\2026-01-28-白班\\检测拼接总图\\NG', levels=2)
            'E:\\Image\\2026-01-28-白班'
        """
        current_path = folder_path
        for _ in range(levels):
            current_path = os.path.dirname(current_path)
        return current_path
    
    @staticmethod
    def get_search_root(folder_path):
        """
        获取图片搜索的根目录（默认向上2级）
        
        用于导出功能：当用户选择某个子文件夹（如NG文件夹）时，
        需要在上两级目录中搜索所有同条码的图片。
        
        Args:
            folder_path: 用户选择的文件夹路径
            
        Returns:
            str: 搜索根目录路径（向上2级）
            
        Example:
            >>> get_search_root('E:\\Image\\2026-01-28-白班\\检测拼接总图\\NG')
            'E:\\Image\\2026-01-28-白班'
        """
        return BarcodeSearcher.get_parent_folder(folder_path, levels=2)
