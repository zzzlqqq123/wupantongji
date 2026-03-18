"""
GUI界面管理模块
负责创建和管理所有UI组件 - 工业风格设计
视口渲染技术（参考C#实现）：支持5000%+缩放流畅体验
"""
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import ttkbootstrap as ttkb
from PIL import Image, ImageTk
import os
import time
import sys

# 添加项目根目录到路径，以便导入utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.version_utils import get_version_string, get_formatted_version

# 性能监控装饰器（可选，用于测试）
def performance_monitor(func):
    """性能监控装饰器，测量函数执行时间"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        if elapsed_ms > 50:  # 仅报告超过50ms的操作
            print(f"[性能] {func.__name__}: {elapsed_ms:.2f}ms")
        return result
    return wrapper


class GUIManager:
    """GUI界面管理器 - 工业风格"""

    def __init__(self, root, app):
        """
        初始化GUI管理器

        Args:
            root: Tkinter根窗口
            app: 应用程序主对象
        """
        self.root = root
        self.app = app
        self.checkbox_vars = {}  # 存储复选框变量

        # 获取版本信息
        self.version_string = get_version_string()
        self.version_display = get_formatted_version()

        # 图片显示相关（使用Canvas）
        self.image_canvas = None  # Canvas对象
        self.canvas_image = None  # Canvas上的图片对象
        self.original_image = None  # 原始图片对象
        self.current_photo = None  # 当前显示的PhotoImage对象
        self.current_image_path = None  # 当前图片路径

        # 视口渲染参数（参考C#的CvDisplayGraphicsMat）
        # PixelSize: 图片像素在屏幕上的显示大小（单位：屏幕像素/图片像素）
        self.pixel_size_x = 1.0  # X方向像素大小
        self.pixel_size_y = 1.0  # Y方向像素大小
        
        # DisplayOrigin: 图片显示区域的左上角在Canvas坐标系中的位置
        self.display_origin_x = 0.0  # X轴原点位置
        self.display_origin_y = 0.0  # Y轴原点位置

        # 拖动相关
        self.drag_start_x = 0  # 拖动起始X坐标（屏幕坐标）
        self.drag_start_y = 0  # 拖动起始Y坐标（屏幕坐标）
        self.is_dragging = False  # 是否正在拖动

        # 性能优化：节流控制
        self.last_drag_time = 0  # 上次拖动时间
        self.drag_throttle_ms = 16  # 拖动节流：16ms (60fps)
        
        # PanedWindow 用于左右分栏
        self.paned_window = None

        self.setup_window()
        self.create_widgets()

    # ==================== 坐标变换系统 ====================
    # 参考C#实现：CvDisplayGraphicsMat.cs
    
    def get_display_rect(self):
        """
        获取图片在Canvas上的显示矩形（参考C#的DispRect属性）
        
        Returns:
            tuple: (x, y, width, height) Canvas坐标系中的显示矩形
        """
        if self.original_image is None:
            return (0, 0, 0, 0)
        
        img_width, img_height = self.original_image.size
        disp_width = img_width * self.pixel_size_x
        disp_height = img_height * self.pixel_size_y
        
        return (self.display_origin_x, self.display_origin_y, disp_width, disp_height)
    
    def screen_to_image(self, screen_x, screen_y):
        """
        屏幕坐标转图片像素坐标（参考C#的TransformPixelPostion方法）
        
        Args:
            screen_x: Canvas上的X坐标
            screen_y: Canvas上的Y坐标
            
        Returns:
            tuple: (image_x, image_y) 图片像素坐标，如果超出范围返回(-1, -1)
        """
        if self.original_image is None:
            return (-1, -1)
        
        # 计算相对于显示原点的偏移
        offset_x = screen_x - self.display_origin_x
        offset_y = screen_y - self.display_origin_y
        
        # 转换为图片坐标
        image_x = int(offset_x / self.pixel_size_x)
        image_y = int(offset_y / self.pixel_size_y)
        
        # 边界检查
        img_width, img_height = self.original_image.size
        if 0 <= image_x < img_width and 0 <= image_y < img_height:
            return (image_x, image_y)
        else:
            return (-1, -1)
    
    def image_to_screen(self, image_x, image_y):
        """
        图片像素坐标转屏幕坐标
        
        Args:
            image_x: 图片像素X坐标
            image_y: 图片像素Y坐标
            
        Returns:
            tuple: (screen_x, screen_y) Canvas坐标
        """
        screen_x = self.display_origin_x + image_x * self.pixel_size_x
        screen_y = self.display_origin_y + image_y * self.pixel_size_y
        return (screen_x, screen_y)
    
    def calculate_visible_rect(self):
        """
        计算当前视图对应的原图矩形区域（参考C#的OnPaint方法，第138-171行）
        这是视口裁剪渲染的核心算法
        
        Returns:
            tuple: (x, y, width, height) 原图像素坐标系中的可见矩形
                   如果没有图片则返回None
        """
        if self.original_image is None:
            return None
        
        # 获取Canvas尺寸
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # 获取图片尺寸
        img_width, img_height = self.original_image.size
        
        # 计算可见区域的起始像素坐标（参考C#的showMatRect计算）
        if self.display_origin_x < 0:
            # 图片左边缘在Canvas左侧，需要裁剪左边部分
            start_x = int(abs(self.display_origin_x) / self.pixel_size_x)
            draw_start_x = 0
        else:
            # 图片左边缘在Canvas内
            start_x = 0
            draw_start_x = self.display_origin_x
        
        if self.display_origin_y < 0:
            # 图片上边缘在Canvas上方，需要裁剪上边部分
            start_y = int(abs(self.display_origin_y) / self.pixel_size_y)
            draw_start_y = 0
        else:
            # 图片上边缘在Canvas内
            start_y = 0
            draw_start_y = self.display_origin_y
        
        # 计算可见区域的宽度和高度（像素数量）
        visible_width = int((canvas_width - draw_start_x) / self.pixel_size_x) + 1
        visible_height = int((canvas_height - draw_start_y) / self.pixel_size_y) + 1
        
        # 边界限制
        start_x = max(0, min(start_x, img_width - 1))
        start_y = max(0, min(start_y, img_height - 1))
        
        # 计算实际可见宽高
        visible_width = min(visible_width, img_width - start_x)
        visible_height = min(visible_height, img_height - start_y)
        
        # 确保至少有1个像素
        visible_width = max(1, visible_width)
        visible_height = max(1, visible_height)
        
        return (start_x, start_y, visible_width, visible_height)
    
    def zoom(self, x_scale, y_scale, zoom_origin_x, zoom_origin_y):
        """
        缩放图片（参考C#的Zoom方法，U_DisPlay.cs第360-389行）
        
        Args:
            x_scale: X方向缩放因子（>1放大，<1缩小）
            y_scale: Y方向缩放因子
            zoom_origin_x: 缩放中心X坐标（Canvas坐标系）
            zoom_origin_y: 缩放中心Y坐标（Canvas坐标系）
        """
        if self.original_image is None:
            return
        
        # 计算新的像素大小
        new_pixel_size_x = abs(x_scale) * self.pixel_size_x
        new_pixel_size_y = abs(y_scale) * self.pixel_size_y
        
        # 边界检查1: 像素大小有效性
        if new_pixel_size_x <= 0 or new_pixel_size_y <= 0:
            return
        
        # 边界检查2: 最小缩放限制（不能小于0.01倍）
        MIN_PIXEL_SIZE = 0.01
        if new_pixel_size_x < MIN_PIXEL_SIZE or new_pixel_size_y < MIN_PIXEL_SIZE:
            return
        
        # 边界检查3: 最大缩放限制（基于Canvas尺寸，避免过度放大）
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # 计算缩放后能显示的图片像素数量
        disp_pixel_x = int(canvas_width / new_pixel_size_x)
        disp_pixel_y = int(canvas_height / new_pixel_size_y)
        
        # 如果缩放过大导致无法显示任何像素，则拒绝缩放
        if disp_pixel_x < 1 or disp_pixel_y < 1:
            return
        
        # 边界检查4: 限制最大像素大小（例如：最多50000倍）
        MAX_PIXEL_SIZE = 50000.0
        if new_pixel_size_x > MAX_PIXEL_SIZE or new_pixel_size_y > MAX_PIXEL_SIZE:
            return
        
        # 获取显示矩形
        disp_rect = self.get_display_rect()
        
        # 判断缩放中心是否在显示区域内
        is_mouse_in = (disp_rect[0] <= zoom_origin_x <= disp_rect[0] + disp_rect[2] and
                       disp_rect[1] <= zoom_origin_y <= disp_rect[1] + disp_rect[3])
        
        if is_mouse_in:
            # 以鼠标位置为中心缩放（关键算法）
            # 计算鼠标相对于显示原点的距离
            dis_x = zoom_origin_x - self.display_origin_x
            dis_y = zoom_origin_y - self.display_origin_y
            
            # 按缩放因子调整距离
            dis_x *= x_scale
            dis_y *= y_scale
            
            # 更新显示原点，使鼠标指向的像素点保持不变
            self.display_origin_x = zoom_origin_x - dis_x
            self.display_origin_y = zoom_origin_y - dis_y
        
        # 更新像素大小
        self.pixel_size_x = new_pixel_size_x
        self.pixel_size_y = new_pixel_size_y
    
    def fit_image_to_canvas(self):
        """
        使图片适应Canvas大小（参考C#的Fit方法，U_DisPlay.cs第400-423行）
        """
        if self.original_image is None:
            return
        
        # 获取Canvas和图片尺寸
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        img_width, img_height = self.original_image.size
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # 计算适配比例（保持宽高比）
        canvas_aspect = canvas_width / canvas_height
        image_aspect = img_width / img_height
        
        if canvas_aspect > image_aspect:
            # Canvas更宽，以高度为准
            new_height = canvas_height
            new_width = img_width * (new_height / img_height)
        else:
            # Canvas更高或相等，以宽度为准
            new_width = canvas_width
            new_height = img_height * (new_width / img_width)
        
        # 设置像素大小
        self.pixel_size_x = new_width / img_width
        self.pixel_size_y = new_height / img_height
        
        # 计算显示矩形
        disp_width = img_width * self.pixel_size_x
        disp_height = img_height * self.pixel_size_y
        
        # 居中显示
        self.display_origin_x = (canvas_width - disp_width) / 2.0
        self.display_origin_y = (canvas_height - disp_height) / 2.0
    
    def original_size(self):
        """
        以原始尺寸显示图片（参考C#的OriginalSize方法）
        """
        if self.original_image is None:
            return
        
        # 1:1显示
        self.pixel_size_x = 1.0
        self.pixel_size_y = 1.0
        self.display_origin_x = 0.0
        self.display_origin_y = 0.0

    def setup_window(self):
        """设置窗口属性 - 使用工业风格主题"""
        self.root.title(f"误判统计系统 {self.version_display}")

        # 使用超级英雄主题（深色工业风）
        style = ttkb.Style(theme="superhero")
        self.style = style

        # 窗口图标和大小
        self.root.state('zoomed')  # Windows最大化
        
    def adjust_paned_window_sash(self):
        """调整PanedWindow分割位置为70:30比例"""
        if self.paned_window:
            try:
                # 获取PanedWindow的实际宽度
                window_width = self.paned_window.winfo_width()
                if window_width > 100:  # 确保窗口已经渲染完成
                    # 计算70%位置
                    split_position = int(window_width * 0.70)
                    # 设置分割线位置
                    self.paned_window.sash_place(0, split_position, 0)
                else:
                    # 窗口尚未完成布局时延迟重试，避免右侧面板被挤压到0宽度
                    self.root.after(100, self.adjust_paned_window_sash)
            except Exception as e:
                print(f"调整分割位置失败: {e}")

    def create_widgets(self):
        """创建所有UI组件 - 工业风格，左右布局"""
        # 顶部菜单栏
        self.create_menu()

        # 主容器 - 使用 ttkbootstrap 的 Frame
        main_frame = ttkb.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 使用 PanedWindow 实现精确的70:30比例分割
        self.paned_window = tk.PanedWindow(
            main_frame,
            orient=tk.HORIZONTAL,
            sashwidth=6,
            bg='#404040',
            sashrelief=tk.RAISED,
            showhandle=False
        )
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # 左侧容器：图片显示区域（70%）
        left_container = ttkb.Frame(self.paned_window)
        self.paned_window.add(left_container, stretch="always")
        
        # 图片显示区域
        self.create_image_display(left_container)

        # 右侧容器：其他信息（30%）
        right_container = ttkb.Frame(self.paned_window)
        self.paned_window.add(right_container, stretch="never")
        # 给右侧面板设置最小宽度，防止被压缩隐藏
        self.paned_window.paneconfigure(right_container, minsize=280)
        
        # 误判类型复选框区
        self.create_checkbox_area(right_container)

        # 操作按钮区
        self.create_action_buttons(right_container)

        # 统计数据显示区
        self.create_statistics_display(right_container)
        
        # 延迟设置初始分割位置，确保窗口已完全渲染
        self.root.after(100, self.adjust_paned_window_sash)

    def create_menu(self):
        """创建顶部菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="选择文件夹", command=self.on_select_folder)
        file_menu.add_separator()

        # 导出子菜单
        export_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="导出统计报告", menu=export_menu)
        export_menu.add_command(label="导出为TXT格式", command=lambda: self.on_export_report('txt'))
        export_menu.add_command(label="导出为Excel格式", command=lambda: self.on_export_report('excel'))
        export_menu.add_separator()
        export_menu.add_command(label="导出误判图片", command=self.on_export_images)

        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_exit)

        # 配置菜单
        config_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="配置", menu=config_menu)
        config_menu.add_command(label="设置总产能", command=self.on_set_capacity)
        config_menu.add_separator()
        config_menu.add_command(label="设置误判类型", command=self.on_configure_types)

    def create_image_display(self, parent):
        """创建图片显示区域 - 工业风格"""
        # 图片显示框架 - 使用 LabelFrame
        image_frame = ttkb.LabelFrame(
            parent,
            text=" 📷 图像检测区 ",
            padding=10
        )
        # 占据整个左侧容器
        image_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部工具栏
        toolbar = ttkb.Frame(image_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # 左侧：导航按钮（上下排版，避免与左右键混淆）
        nav_frame = ttkb.Frame(toolbar)
        nav_frame.pack(side=tk.LEFT, padx=2)

        self.prev_btn = ttkb.Button(
            nav_frame,
            text="▲ 上一张 (↑)",
            command=self.on_previous_image_with_feedback,
            width=12,
            bootstyle="secondary"
        )
        self.prev_btn.pack(side=tk.TOP, pady=(0, 2))

        self.next_btn = ttkb.Button(
            nav_frame,
            text="▼ 下一张 (↓)",
            command=self.on_next_image_with_feedback,
            width=12,
            bootstyle="secondary"
        )
        self.next_btn.pack(side=tk.TOP, pady=(2, 0))

        # 中间：标注状态标签
        self.annotation_label = ttkb.Label(
            toolbar,
            text="● 未标注",
            font=("Segoe UI", 11, "bold"),
            bootstyle="inverse-secondary",
            padding=(15, 8)
        )
        self.annotation_label.pack(side=tk.LEFT, padx=20)

        # 右侧：缩放提示和还原按钮
        self.zoom_label = ttkb.Label(
            toolbar,
            text="🔍 100%",
            font=("Segoe UI", 9)
        )
        self.zoom_label.pack(side=tk.RIGHT, padx=5)

        reset_btn = ttkb.Button(
            toolbar,
            text="⟲ 还原",
            command=self.reset_image_size,
            width=8,
            bootstyle="info-outline"
        )
        reset_btn.pack(side=tk.RIGHT, padx=5)

        # 图片名称显示区域
        filename_frame = ttkb.Frame(image_frame)
        filename_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 图片名称标签
        self.filename_label = ttkb.Label(
            filename_frame,
            text="📄 未选择图片",
            font=("Microsoft YaHei UI", 10),
            bootstyle="inverse-dark",
            padding=(10, 5),
            anchor="w"  # 左对齐
        )
        self.filename_label.pack(fill=tk.X)

        # 图片显示 Canvas - 深色工业背景
        canvas_frame = ttkb.Frame(image_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.image_canvas = tk.Canvas(
            canvas_frame,
            bg='#1a1a1a',
            highlightthickness=2,
            highlightbackground='#303030',
            highlightcolor='#007bff'
        )
        self.image_canvas.pack(fill=tk.BOTH, expand=True)

        # 绑定鼠标滚轮事件
        self.image_canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.image_canvas.bind('<Button-4>', self.on_mouse_wheel)
        self.image_canvas.bind('<Button-5>', self.on_mouse_wheel)

        # 绑定鼠标拖动事件
        self.image_canvas.bind('<ButtonPress-1>', self.on_drag_start)
        self.image_canvas.bind('<B1-Motion>', self.on_drag_motion)
        self.image_canvas.bind('<ButtonRelease-1>', self.on_drag_end)

    def create_checkbox_area(self, parent):
        """创建误判类型复选框区域 - 工业风格"""
        checkbox_frame = ttkb.LabelFrame(
            parent,
            text=" ⚙️ 缺陷类型选择 ",
            padding=8
        )
        checkbox_frame.pack(fill=tk.X, pady=(0, 5))

        # 复选框容器
        self.checkbox_container = ttkb.Frame(checkbox_frame)
        self.checkbox_container.pack(fill=tk.X, pady=5)

        # 初始化复选框
        self.refresh_checkboxes(self.app.misjudgment_types if hasattr(self.app, 'misjudgment_types') else [])

        # 误判原因输入框
        reason_frame = ttkb.Frame(checkbox_frame)
        reason_frame.pack(fill=tk.X, pady=(8, 0))

        reason_label = ttkb.Label(reason_frame, text="误判原因（可选）:", font=('Segoe UI', 10))
        reason_label.pack(side=tk.LEFT, padx=(0, 5))

        self.misjudgment_reason_var = tk.StringVar(value="")
        self.misjudgment_reason_entry = ttkb.Entry(
            reason_frame,
            textvariable=self.misjudgment_reason_var,
            font=('Segoe UI', 10)
        )
        self.misjudgment_reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_action_buttons(self, parent):
        """创建操作按钮区域 - 工业风格"""
        button_frame = ttkb.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 5))

        # 误判按钮（红色工业风）
        self.misjudgment_btn = ttkb.Button(
            button_frame,
            text="✗ 误判 (←)",
            command=self.on_misjudgment_with_feedback,
            width=18,
            bootstyle="danger-outline"
        )
        self.misjudgment_btn.pack(side=tk.LEFT, padx=5)

        # 检出按钮（绿色工业风）
        self.detection_btn = ttkb.Button(
            button_frame,
            text="✓ 检出 (→)",
            command=self.on_detection_with_feedback,
            width=18,
            bootstyle="success-outline"
        )
        self.detection_btn.pack(side=tk.LEFT, padx=5)

    def create_statistics_display(self, parent):
        """创建统计数据显示区域 - 工业风格"""
        # 实时统计数据面板
        stats_frame = ttkb.LabelFrame(
            parent,
            text=" 📊 实时统计数据 ",
            padding=8
        )
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 使用 Text 组件显示统计数据
        self.stats_text = tk.Text(
            stats_frame,
            font=("Consolas", 9),
            bg='#0a0a0a',
            fg='#00ff00',
            insertbackground='white',
            state='disabled',
            relief='flat',
            padx=10,
            pady=8
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # 版本信息标签 - 添加在统计区域底部
        version_frame = ttkb.Frame(stats_frame)
        version_frame.pack(fill=tk.X, pady=(3, 0))

        self.version_label = ttkb.Label(
            version_frame,
            text=f"🔖 {self.version_display}",
            font=("Segoe UI", 8),
            bootstyle="inverse-secondary"
        )
        self.version_label.pack(side=tk.RIGHT)

        # 操作说明面板（放在统计数据下方）
        self.create_instruction_panel(parent)

        # 初始化统计显示
        self.update_statistics_display({})

    def create_instruction_panel(self, parent):
        """创建操作说明面板"""
        instruction_frame = ttkb.LabelFrame(
            parent,
            text=" 📖 操作说明 ",
            padding=8,
            bootstyle="info"
        )
        instruction_frame.pack(fill=tk.BOTH, expand=True)

        # 使用Text组件显示操作步骤，支持多行和自动换行
        instruction_text = tk.Text(
            instruction_frame,
            font=("Segoe UI", 9),
            bg='#2a2a2a',
            fg='#ffffff',
            state='disabled',
            relief='flat',
            wrap=tk.WORD,
            padx=6,
            pady=4
        )
        instruction_text.pack(fill=tk.BOTH, expand=True)

        # 操作步骤内容
        steps = """【快捷键操作】
• ↑ 键：上一张图片
• ↓ 键：下一张图片
• ← 键：误判
• → 键：检出
• 1-9 键：快速选择/取消缺陷类型

【基本操作步骤】
1. 配置 → 设置误判种类（首次设置，后续自动读取config.json）
2. 文件 → 选择文件夹
3. 配置 → 设置总产能
4. 查看图片，标注误判或检出
   • 误判：选择类型+填写原因（可为空）
   • 检出：直接点击检出按钮，或选择类型后点击检出按钮（会统计检出类型，不选择则统计为检出）
5. 完成后，文件 → 导出统计报告 → 导出Excel格式"""

        instruction_text.config(state='normal')
        instruction_text.insert(tk.END, steps)
        instruction_text.config(state='disabled')

    def refresh_checkboxes(self, misjudgment_types):
        """
        根据配置动态刷新复选框 - 工业风格，支持自动换行

        Args:
            misjudgment_types: 误判类型列表
        """
        # 清除旧的复选框
        for widget in self.checkbox_container.winfo_children():
            widget.destroy()

        self.checkbox_vars = {}

        # 创建自定义样式来设置字体
        style = ttkb.Style()
        style.configure("LargeCheckbutton.TCheckbutton", font=("Segoe UI", 10, "bold"))

        # 使用 grid 布局实现自动换行
        # 根据复选框数量和名称长度，每行显示2个复选框（适应30%窗口宽度）
        checkboxes_per_row = 2
        
        for index, type_name in enumerate(misjudgment_types):
            row = index // checkboxes_per_row
            col = index % checkboxes_per_row

            var = tk.BooleanVar()

            # 动态生成快捷键提示（显示所有缺陷类型）
            shortcut_hint = f" ({index + 1})"

            checkbox = ttkb.Checkbutton(
                self.checkbox_container,
                text=f"{type_name}{shortcut_hint}",
                variable=var,
                bootstyle="success-round-toggle",
                style="LargeCheckbutton.TCheckbutton"
            )
            # 使用 grid 布局，sticky="w" 左对齐
            checkbox.grid(row=row, column=col, padx=5, pady=3, sticky="w")
            self.checkbox_vars[type_name] = var
        
        # 配置列权重，使两列均匀分布
        self.checkbox_container.columnconfigure(0, weight=1)
        self.checkbox_container.columnconfigure(1, weight=1)

    def update_image_display(self, image_path):
        """
        更新图片显示 - 视口渲染版本
        
        Args:
            image_path: 图片文件路径
        """
        if image_path is None or not os.path.exists(image_path):
            self.image_canvas.delete("all")
            self.image_canvas.create_text(
                400, 300,
                text='请选择文件夹',
                fill='white',
                font=('Arial', 14)
            )
            self.original_image = None
            self.current_image_path = None
            self.canvas_image = None
            self.update_annotation_status(None)
            # 更新图片名称显示
            if hasattr(self, 'filename_label'):
                self.filename_label.config(text="📄 未选择图片")
            return
        
        try:
            self.current_image_path = image_path
            
            # 加载原始图片
            self.original_image = Image.open(image_path)
            
            # 更新图片名称显示
            if hasattr(self, 'filename_label'):
                filename = os.path.basename(image_path)
                self.filename_label.config(text=f"📄 {filename}")
            
            # 等待Canvas完成布局
            self.root.update()
            
            # 自动适应Canvas大小
            self.fit_image_to_canvas()
            
            # 使用视口渲染显示图片
            self.display_image_on_canvas()
            
            # 更新标注状态显示
            self.update_annotation_status(image_path)
            
        except Exception as e:
            self.image_canvas.delete("all")
            self.image_canvas.create_text(
                400, 300,
                text=f'加载失败: {str(e)}',
                fill='white',
                font=('Arial', 12)
            )
            self.original_image = None
            self.update_annotation_status(None)
            # 更新图片名称显示为错误状态
            if hasattr(self, 'filename_label'):
                filename = os.path.basename(image_path) if image_path else "未知"
                self.filename_label.config(text=f"❌ 加载失败: {filename}")


    # 可选：启用性能监控，用于测试和调试
    # @performance_monitor
    def display_image_on_canvas(self, use_high_quality=False):
        """
        在Canvas上显示图片 - 视口裁剪渲染版本
        （参考C#的OnPaint方法，CvDisplayGraphicsMat.cs第138-205行）
        
        核心优化：只渲染和缩放Canvas可见区域，而非整张图片
        性能：5000%缩放时仍保持流畅（<50ms），内存占用恒定
        
        Args:
            use_high_quality: 是否使用高质量插值算法（LANCZOS）
        """
        if self.original_image is None:
            return
        
        try:
            # 清空Canvas（绘制背景色）
            self.image_canvas.delete("all")
            
            # 步骤1: 计算可见区域在原图中的矩形范围
            visible_rect = self.calculate_visible_rect()
            if visible_rect is None:
                return
            
            start_x, start_y, visible_width, visible_height = visible_rect
            
            # 边界检查：确保裁剪区域有效
            if visible_width <= 0 or visible_height <= 0:
                return
            
            # 步骤2: 从原图裁剪可见部分（关键优化：只处理可见区域）
            crop_box = (start_x, start_y, start_x + visible_width, start_y + visible_height)
            cropped_image = self.original_image.crop(crop_box)
            
            # 步骤3: 计算裁剪区域在Canvas上的显示尺寸
            display_width = int(visible_width * self.pixel_size_x)
            display_height = int(visible_height * self.pixel_size_y)
            
            # 确保至少1像素
            display_width = max(1, display_width)
            display_height = max(1, display_height)
            
            # 边界检查：限制最大显示尺寸（避免生成超大位图）
            MAX_DISPLAY_SIZE = 10000
            display_width = min(display_width, MAX_DISPLAY_SIZE)
            display_height = min(display_height, MAX_DISPLAY_SIZE)
            
            # 步骤4: 缩放到显示尺寸（只缩放可见部分，非常快）
            # 选择插值算法：高倍数放大用NEAREST（速度最快），其他用BILINEAR
            if self.pixel_size_x >= 5.0 or self.pixel_size_y >= 5.0:
                # 高倍数放大使用NEAREST，避免模糊
                resample_method = Image.Resampling.NEAREST
            elif use_high_quality:
                # 需要高质量时使用LANCZOS
                resample_method = Image.Resampling.LANCZOS
            else:
                # 默认使用BILINEAR（速度和质量平衡）
                resample_method = Image.Resampling.BILINEAR
            
            resized_image = cropped_image.resize(
                (display_width, display_height),
                resample_method
            )
            
            # 步骤5: 转换为PhotoImage
            self.current_photo = ImageTk.PhotoImage(resized_image)
            
            # 步骤6: 计算绘制起始位置
            # 如果图片部分在Canvas外，需要调整绘制位置
            if self.display_origin_x < 0:
                draw_x = 0
            else:
                draw_x = self.display_origin_x
            
            if self.display_origin_y < 0:
                draw_y = 0
            else:
                draw_y = self.display_origin_y
            
            # 步骤7: 在Canvas上绘制图片
            self.canvas_image = self.image_canvas.create_image(
                draw_x, draw_y,
                image=self.current_photo,
                anchor='nw'  # 左上角锚点
            )
            
            # 步骤8: 更新缩放提示
            if self.original_image:
                zoom_percent = int(self.pixel_size_x * 100)
                self.zoom_label.config(text=f"🔍 {zoom_percent}%")
            
        except Exception as e:
            print(f"视口渲染失败: {e}")



    def on_drag_start(self, event):
        """开始拖动"""
        if self.original_image is None:
            return
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True

    def on_drag_motion(self, event):
        """拖动过程 - 视口渲染版本（节流 + 实时更新）"""
        if not self.is_dragging or self.original_image is None:
            return
        
        # 节流检查：限制为60fps
        now = time.time() * 1000
        if now - self.last_drag_time < self.drag_throttle_ms:
            return
        self.last_drag_time = now
        
        # 计算拖动距离
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        # 更新显示原点（参考C#的OnMouseMove方法）
        self.display_origin_x += dx
        self.display_origin_y += dy
        
        # 更新起始位置
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # 重新渲染（视口裁剪，非常快）
        self.display_image_on_canvas()

    def on_drag_end(self, event):
        """结束拖动"""
        self.is_dragging = False

    def on_mouse_wheel(self, event):
        """
        处理鼠标滚轮事件 - 视口渲染版本
        
        Args:
            event: 鼠标事件对象
            
        性能：无论缩放倍数多大，都能保持流畅（<50ms）
        """
        if self.original_image is None:
            return
        
        # 获取鼠标在Canvas上的位置
        mouse_x = event.x
        mouse_y = event.y
        
        # 确定缩放方向和速度
        if event.num == 5 or event.delta < 0:
            # 向下滚动，缩小
            scale_factor = 0.8
        else:
            # 向上滚动，放大
            scale_factor = 1.25
        
        # 调用zoom方法（参考C#实现）
        self.zoom(scale_factor, scale_factor, mouse_x, mouse_y)
        
        # 立即重新渲染（视口裁剪，非常快）
        self.display_image_on_canvas()

    def reset_image_size(self):
        """还原图片到适应屏幕的大小（Fit模式）"""
        if self.original_image is None:
            return
        
        # 重新适应Canvas大小
        self.fit_image_to_canvas()
        
        # 重新渲染
        self.display_image_on_canvas()

    def update_statistics_display(self, stats_data):
        """
        更新统计数据显示 - 工业风格表格

        Args:
            stats_data: 统计数据字典
        """
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)

        if not stats_data or stats_data.get('total', 0) == 0:
            stats_text = "╔═══════════════════════════════╗\n"
            stats_text += "║    📊 等待数据输入...       ║\n"
            stats_text += "╚═══════════════════════════════╝"
        else:
            total = stats_data.get('total', 0)
            misjudgment = stats_data.get('misjudgment', 0)
            detection = stats_data.get('detection', 0)
            misjudgment_rate = stats_data.get('misjudgment_rate', 0)
            detection_rate = stats_data.get('detection_rate', 0)
            type_rates = stats_data.get('type_rates', {})
            type_counts = stats_data.get('type_counts', {})

            # 工业风格边框表格（适应较窄区域）
            stats_text = "╔═══════════════════════════════╗\n"
            stats_text += "║   📊 实时检测统计数据       ║\n"
            stats_text += "╠═══════════════════════════════╣\n"
            stats_text += f"║ 总检测数: {total:<5}              ║\n"
            stats_text += f"║ 误判数量: {misjudgment:<5}              ║\n"
            stats_text += f"║ 检出数量: {detection:<5}              ║\n"
            stats_text += "╠═══════════════════════════════╣\n"
            stats_text += f"║ 误判率: {misjudgment_rate:>6.2f}%              ║\n"
            stats_text += f"║ 检出率: {detection_rate:>6.2f}%              ║\n"

            if type_counts:
                stats_text += "╠═══════════════════════════════╣\n"
                stats_text += "║ 📋 各类型误判统计:          ║\n"
                # 每行显示1个类型（适应较窄空间）
                type_items = list(type_counts.items())
                for type_name, count in type_items:
                    rate = type_rates.get(type_name, 0)
                    stats_text += f"║ • {type_name:<6} {count:>2}次 {rate:>5.2f}%   ║\n"

            stats_text += "╚═══════════════════════════════╝"

        self.stats_text.insert(tk.END, stats_text)
        self.stats_text.config(state='disabled')

    def update_progress_display(self, current, total):
        """
        更新进度显示 - 工业风格

        Args:
            current: 当前进度
            total: 总数
        """
        self.stats_text.config(state='normal')

        # 获取当前文本
        current_text = self.stats_text.get(1.0, tk.END)

        # 如果已有进度信息，先删除
        if "\n\n╔" in current_text:
            lines = current_text.split("\n\n╔")[0]
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, lines)

        # 添加进度信息
        if total > 0:
            progress_percent = (current / total) * 100
            progress_bar_length = 25  # 调整进度条长度以适应较窄空间
            filled_length = int(progress_bar_length * current / total)
            bar = '█' * filled_length + '░' * (progress_bar_length - filled_length)

            progress_text = "\n\n"
            progress_text += "╔═══════════════════════════════╗\n"
            progress_text += "║ 📈 检测进度                  ║\n"
            progress_text += "╠═══════════════════════════════╣\n"
            progress_text += f"║ {bar} ║\n"
            progress_text += f"║ {current}/{total} ({progress_percent:.1f}%)              ║\n"
            progress_text += "╚═══════════════════════════════╝"

            self.stats_text.insert(tk.END, progress_text)

        self.stats_text.config(state='disabled')

    def clear_checkboxes(self):
        """清空所有复选框的选择和误判原因"""
        for var in self.checkbox_vars.values():
            var.set(False)

        # 清空误判原因输入框
        if hasattr(self, 'misjudgment_reason_var'):
            self.misjudgment_reason_var.set("")

    def get_selected_types(self):
        """
        获取选中的误判类型

        Returns:
            list: 选中的误判类型列表
        """
        selected = []
        for type_name, var in self.checkbox_vars.items():
            if var.get():
                selected.append(type_name)
        return selected

    def flash_button(self, button, original_style, flash_style="info", duration=150):
        """
        按钮闪烁视觉反馈效果

        Args:
            button: 要闪烁的按钮对象
            original_style: 原始bootstyle样式
            flash_style: 闪烁时的样式（默认info）
            duration: 闪烁持续时间（毫秒）
        """
        try:
            # 设置为高亮样式
            button.configure(bootstyle=flash_style)
            # 定时恢复原始样式
            self.root.after(duration, lambda: button.configure(bootstyle=original_style))
        except Exception:
            # 出错时确保恢复原始样式
            self.root.after(duration, lambda: button.configure(bootstyle=original_style))

    def toggle_type_by_index(self, index):
        """
        通过索引切换复选框状态（键盘快捷键调用）

        Args:
            index: 复选框索引（从0开始）
        """
        # 获取当前的误判类型列表
        type_names = list(self.checkbox_vars.keys())

        # 检查索引是否有效
        if 0 <= index < len(type_names):
            type_name = type_names[index]
            var = self.checkbox_vars[type_name]

            # 切换复选框状态
            current_state = var.get()
            var.set(not current_state)

    def get_misjudgment_reason(self):
        """
        获取误判原因输入框的值

        Returns:
            str: 误判原因，如果为空则返回空字符串
        """
        if hasattr(self, 'misjudgment_reason_var'):
            return self.misjudgment_reason_var.get().strip()
        return ""

    # 事件处理方法
    def on_select_folder(self):
        """选择文件夹事件"""
        self.app.select_folder()

    def on_misjudgment(self):
        """误判按钮点击事件"""
        self.app.handle_misjudgment()

    def on_detection(self):
        """检出按钮点击事件"""
        self.app.handle_detection()

    def on_set_capacity(self):
        """设置总产能事件"""
        self.app.set_capacity()

    def on_configure_types(self):
        """配置误判类型事件"""
        self.app.configure_types()

    def on_export_report(self, format_type='txt'):
        """
        导出报告事件

        Args:
            format_type: 导出格式 ('txt', 'excel')
        """
        self.app.export_report(format_type)

    def on_exit(self):
        """退出事件"""
        if self.app.confirm_exit():
            self.root.quit()

    def on_previous_image(self):
        """上一张图片事件"""
        self.app.previous_image()

    def on_next_image(self):
        """下一张图片事件"""
        self.app.next_image_manual()

    def on_previous_image_with_feedback(self):
        """上一张图片（带视觉反馈）"""
        self.flash_button(self.prev_btn, "secondary", "info")
        self.on_previous_image()

    def on_next_image_with_feedback(self):
        """下一张图片（带视觉反馈）"""
        self.flash_button(self.next_btn, "secondary", "info")
        self.on_next_image()

    def on_misjudgment_with_feedback(self):
        """误判操作（带视觉反馈）"""
        self.flash_button(self.misjudgment_btn, "danger-outline", "danger")
        self.on_misjudgment()

    def on_detection_with_feedback(self):
        """检出操作（带视觉反馈）"""
        self.flash_button(self.detection_btn, "success-outline", "success")
        self.on_detection()

    def update_annotation_status(self, image_path):
        """
        更新图片标注状态显示 - 工业风格

        Args:
            image_path: 图片文件路径
        """
        if image_path is None:
            self.annotation_label.config(
                text="● 未标注",
                bootstyle="inverse-secondary"
            )
            return

        # 获取图片文件名
        image_name = os.path.basename(image_path)

        # 从 data_handler 获取标注信息
        result = self.app.data_handler.get_image_result(image_name)

        if result is None:
            # 未标注 - 灰色
            self.annotation_label.config(
                text="● 未标注",
                bootstyle="inverse-secondary"
            )
        elif result['result'] == 'detection':
            # 检出 - 绿色
            self.annotation_label.config(
                text="✓ 已检出",
                bootstyle="inverse-success"
            )
        else:
            # 误判 - 红色，显示类型
            types = result.get('types', [])
            if types:
                types_text = ', '.join(types)
                self.annotation_label.config(
                    text=f"✗ 误判: {types_text}",
                    bootstyle="inverse-danger"
                )
            else:
                self.annotation_label.config(
                    text="✗ 误判",
                    bootstyle="inverse-danger"
                )

    def show_info(self, title, message):
        """显示信息对话框"""
        messagebox.showinfo(title, message)

    def show_warning(self, title, message):
        """显示警告对话框"""
        messagebox.showwarning(title, message)

    def show_error(self, title, message):
        """显示错误对话框"""
        messagebox.showerror(title, message)

    def ask_yes_no(self, title, message):
        """
        显示是/否确认对话框

        Returns:
            bool: 用户选择是返回True，否则返回False
        """
        return messagebox.askyesno(title, message)
    
    # ==================== 进度对话框 ====================
    
    def create_progress_dialog(self, title, initial_message):
        """
        创建进度对话框
        
        Args:
            title: 对话框标题
            initial_message: 初始消息
            
        Returns:
            dict: 包含对话框组件的字典
        """
        # 创建顶层窗口
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x180")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (180 // 2)
        dialog.geometry(f"500x180+{x}+{y}")
        
        # 禁止关闭
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # 标题标签
        title_label = tk.Label(
            dialog, 
            text=title,
            font=('Arial', 14, 'bold'),
            pady=15
        )
        title_label.pack()
        
        # 消息标签
        message_label = tk.Label(
            dialog,
            text=initial_message,
            font=('Arial', 11),
            pady=10
        )
        message_label.pack()
        
        # 进度条框架
        progress_frame = tk.Frame(dialog)
        progress_frame.pack(fill=tk.X, padx=30, pady=10)
        
        # 使用ttkbootstrap的进度条
        progress_bar = ttkb.Progressbar(
            progress_frame,
            mode='determinate',
            bootstyle="success-striped",
            length=440
        )
        progress_bar.pack(fill=tk.X)
        
        # 百分比标签
        percent_label = tk.Label(
            dialog,
            text="0%",
            font=('Arial', 10)
        )
        percent_label.pack()
        
        # 更新显示
        dialog.update()
        
        return {
            'dialog': dialog,
            'message_label': message_label,
            'progress_bar': progress_bar,
            'percent_label': percent_label
        }
    
    def update_progress_dialog(self, progress_dialog, current, total, message):
        """
        更新进度对话框
        
        Args:
            progress_dialog: create_progress_dialog 返回的字典
            current: 当前进度值
            total: 总进度值
            message: 显示的消息
        """
        if progress_dialog is None:
            return
        
        try:
            # 更新消息
            progress_dialog['message_label'].config(text=message)
            
            # 更新进度条
            percent = (current / total * 100) if total > 0 else 0
            progress_dialog['progress_bar']['value'] = percent
            
            # 更新百分比标签
            progress_dialog['percent_label'].config(text=f"{int(percent)}%")
            
            # 刷新显示
            progress_dialog['dialog'].update()
        except Exception as e:
            print(f"更新进度对话框时出错: {e}")
    
    def close_progress_dialog(self, progress_dialog):
        """
        关闭进度对话框
        
        Args:
            progress_dialog: create_progress_dialog 返回的字典
        """
        if progress_dialog is None:
            return
        
        try:
            progress_dialog['dialog'].grab_release()
            progress_dialog['dialog'].destroy()
        except Exception as e:
            print(f"关闭进度对话框时出错: {e}")
    
    # ==================== 菜单回调 ====================
    
    def on_export_images(self):
        """导出误判图片菜单回调"""
        self.app.export_images()
