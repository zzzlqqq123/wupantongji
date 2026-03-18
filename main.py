"""
误判统计小程序 - 主程序
用于辅助质检人员快速统计图片缺陷的误判率

Version: v2.20
"""
import tkinter as tk
from tkinter import simpledialog
import os
from datetime import datetime

from modules.config_manager import ConfigManager
from modules.image_loader import ImageLoader
from modules.statistics import Statistics
from modules.data_handler import DataHandler
from modules.gui_manager import GUIManager


class MisjudgmentApp:
    """误判统计应用程序主类"""

    def __init__(self):
        # 初始化各管理器
        self.config_manager = ConfigManager()
        self.image_loader = ImageLoader()
        self.statistics = Statistics()
        self.data_handler = DataHandler()

        # 加载误判类型配置
        self.misjudgment_types = self.config_manager.load_types()

        # 创建GUI
        self.root = tk.Tk()
        self.gui_manager = GUIManager(self.root, self)

        # 绑定快捷键
        self.bind_shortcuts()

    def bind_shortcuts(self):
        """绑定快捷键"""
        # 图片导航 - 上下方向键（带视觉反馈）
        self.root.bind('<Up>', lambda e: self.gui_manager.on_previous_image_with_feedback())
        self.root.bind('<Down>', lambda e: self.gui_manager.on_next_image_with_feedback())

        # 误判/检出操作 - 左右方向键（带视觉反馈）
        self.root.bind('<Left>', lambda e: self.gui_manager.on_misjudgment_with_feedback())
        self.root.bind('<Right>', lambda e: self.gui_manager.on_detection_with_feedback())

        # 缺陷类型快速选择 - 数字键动态绑定（根据配置的缺陷类型数量）
        for index in range(len(self.misjudgment_types)):
            # 键盘按键名称为 Key-1, Key-2, ... Key-9
            key_name = f'<Key-{index + 1}>'
            self.root.bind(key_name, lambda e, idx=index: self.gui_manager.toggle_type_by_index(idx))

    def run(self):
        """启动应用程序"""
        self.root.mainloop()

    # 文件夹选择相关
    def select_folder(self):
        """选择图片文件夹"""
        folder_path = tk.filedialog.askdirectory(title="选择包含图片的文件夹")

        if not folder_path:
            return

        try:
            # 验证文件夹
            if not os.path.exists(folder_path):
                raise FileNotFoundError("文件夹不存在")

            # 加载图片
            self.image_loader.load_folder(folder_path)

            if self.image_loader.is_empty():
                raise ValueError("文件夹中没有找到支持的图片文件")

            # 显示第一张图片
            first_image = self.image_loader.get_current_image()
            self.gui_manager.update_image_display(first_image)

            # 重置统计数据
            self.statistics.reset()
            self.data_handler.start_session(folder_path)

            # 如果未设置总产能，默认使用图片总数作为总产能
            if self.statistics.get_total_capacity() == 0:
                total_images = self.image_loader.get_total_count()
                self.statistics.set_total_capacity(total_images)

            # 更新统计显示
            self.update_all_statistics()

            self.gui_manager.show_info("成功", f"成功加载 {self.image_loader.get_total_count()} 张图片")

        except FileNotFoundError as e:
            self.gui_manager.show_error("文件夹错误", str(e))
        except ValueError as e:
            self.gui_manager.show_error("错误", str(e))
        except Exception as e:
            self.gui_manager.show_error("错误", f"加载文件夹时发生错误: {e}")

    # 误判/检出处理
    def handle_misjudgment(self):
        """处理误判按钮点击"""
        # 检查是否已选择文件夹
        if self.image_loader.is_empty():
            self.gui_manager.show_warning("提示", "请先选择文件夹")
            return

        # 获取当前图片
        current_image = self.image_loader.get_current_image()
        if current_image is None:
            self.gui_manager.show_warning("提示", "没有可标注的图片")
            return

        # 获取选中的误判类型
        selected_types = self.gui_manager.get_selected_types()

        if not selected_types:
            self.gui_manager.show_warning("提示", "请至少选择一种误判类型！")
            return

        # 获取误判原因
        misjudgment_reason = self.gui_manager.get_misjudgment_reason()

        image_name = os.path.basename(current_image)

        # 检查是否已经标注过这张图片
        old_record = self.data_handler.get_image_result(image_name)

        if old_record is not None:
            # 已标注过，先移除旧的统计数据
            if old_record['result'] == 'misjudgment':
                # 旧的是误判，移除误判统计
                old_types = old_record.get('types', [])
                self.statistics.remove_misjudgment(old_types)
            else:
                # 旧的是检出，移除检出统计
                self.statistics.remove_detection()

        # 记录新的统计数据
        self.statistics.record_misjudgment(selected_types)
        self.data_handler.update_result(
            image_name,
            'misjudgment',
            selected_types,
            misjudgment_reason  # 传入误判原因
        )

        # 更新UI显示
        self.update_all_statistics()

        # 切换到下一张
        self.next_image()

    def handle_detection(self):
        """处理检出按钮点击"""
        # 检查是否已选择文件夹
        if self.image_loader.is_empty():
            self.gui_manager.show_warning("提示", "请先选择文件夹")
            return

        # 获取当前图片
        current_image = self.image_loader.get_current_image()
        if current_image is None:
            self.gui_manager.show_warning("提示", "没有可标注的图片")
            return

        image_name = os.path.basename(current_image)
        # 获取选中的类型（用于检出类型统计）
        selected_types = self.gui_manager.get_selected_types()

        # 检查是否已经标注过这张图片
        old_record = self.data_handler.get_image_result(image_name)

        if old_record is not None:
            # 已标注过，先移除旧的统计数据
            if old_record['result'] == 'misjudgment':
                # 旧的是误判，移除误判统计
                old_types = old_record.get('types', [])
                self.statistics.remove_misjudgment(old_types)
            else:
                # 旧的是检出，移除检出统计
                old_types = old_record.get('types', [])
                self.statistics.remove_detection(old_types)

        # 记录新的统计数据
        self.statistics.record_detection(selected_types)
        self.data_handler.update_result(
            image_name,
            'detection',
            selected_types
        )

        # 更新UI显示
        self.update_all_statistics()

        # 切换到下一张
        self.next_image()

    def next_image(self):
        """切换到下一张图片"""
        # 清空复选框选择
        self.gui_manager.clear_checkboxes()

        if self.image_loader.has_next():
            next_image_path = self.image_loader.next_image()
            self.gui_manager.update_image_display(next_image_path)
        else:
            # 所有图片处理完毕
            self.finish_session()

    def previous_image(self):
        """切换到上一张图片"""
        if self.image_loader.is_empty():
            return

        # 清空复选框选择
        self.gui_manager.clear_checkboxes()

        # 获取上一张图片
        prev_image_path = self.image_loader.previous_image()
        if prev_image_path:
            self.gui_manager.update_image_display(prev_image_path)
        else:
            # 已经在第一张，显示当前图片
            current_image = self.image_loader.get_current_image()
            if current_image:
                self.gui_manager.update_image_display(current_image)

    def next_image_manual(self):
        """手动切换到下一张图片（不会触发完成会话）"""
        if self.image_loader.is_empty():
            return

        # 清空复选框选择
        self.gui_manager.clear_checkboxes()

        # 获取下一张图片
        if self.image_loader.has_next():
            next_image_path = self.image_loader.next_image()
            if next_image_path:
                self.gui_manager.update_image_display(next_image_path)
        else:
            # 已经在最后一张，显示当前图片
            current_image = self.image_loader.get_current_image()
            if current_image:
                self.gui_manager.update_image_display(current_image)

    def finish_session(self):
        """完成统计会话"""
        summary = self.statistics.get_summary()
        type_rates = summary['type_rates']

        # 保存结果
        self.data_handler.save_session(summary, type_rates)

        # 不再显示对话框，避免阻塞用户操作
        # 用户可以通过查看统计数据和 results.json 来了解结果

    # 统计显示更新
    def update_all_statistics(self):
        """更新所有统计数据显示"""
        summary = self.statistics.get_summary()
        self.gui_manager.update_statistics_display(summary)

        # 更新进度 - 使用已标注数量而不是索引
        total_images = self.image_loader.get_total_count()
        annotated_count = summary['total']  # 使用实际已标注的数量
        self.gui_manager.update_progress_display(annotated_count, total_images)

    # 配置管理
    def configure_types(self):
        """配置误判类型"""
        # 创建配置对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("设置误判类型")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()

        # 说明标签
        label = tk.Label(dialog, text="当前误判类型（双击编辑，点击删除按钮移除）:", font=('Segoe UI', 12, 'bold'))
        label.pack(pady=15)

        # 类型列表框架
        list_frame = tk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # 列表框和滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Segoe UI', 12))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # 填充当前类型
        for type_name in self.misjudgment_types:
            listbox.insert(tk.END, type_name)

        # 按钮框架
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=15)

        def add_type():
            """添加新类型"""
            new_type = simpledialog.askstring("添加误判类型", "请输入新的误判类型名称:")
            if new_type and new_type.strip():
                new_type = new_type.strip()
                if new_type not in self.misjudgment_types:
                    self.misjudgment_types.append(new_type)
                    listbox.insert(tk.END, new_type)

        def remove_type():
            """删除选中的类型"""
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                # 至少保留一个类型
                if len(self.misjudgment_types) <= 1:
                    self.gui_manager.show_warning("提示", "至少需要保留一个误判类型")
                    return
                listbox.delete(index)
                self.misjudgment_types.pop(index)

        def save_types():
            """保存类型配置"""
            if self.config_manager.save_types(self.misjudgment_types):
                self.gui_manager.refresh_checkboxes(self.misjudgment_types)
                self.gui_manager.show_info("成功", "误判类型配置已保存")
                dialog.destroy()

        # 添加按钮
        add_btn = tk.Button(button_frame, text="添加", command=add_type, width=12, font=('Segoe UI', 11))
        add_btn.pack(side=tk.LEFT, padx=8)

        # 删除按钮
        remove_btn = tk.Button(button_frame, text="删除", command=remove_type, width=12, font=('Segoe UI', 11))
        remove_btn.pack(side=tk.LEFT, padx=8)

        # 保存按钮
        save_btn = tk.Button(button_frame, text="保存", command=save_types, width=12, bg='#4CAF50', fg='white', font=('Segoe UI', 11, 'bold'))
        save_btn.pack(side=tk.LEFT, padx=8)

    # 设置总产能
    def set_capacity(self):
        """设置总产能"""
        # 获取当前总产能
        current_capacity = self.statistics.get_total_capacity()

        # 创建输入对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("设置总产能")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # 说明标签
        instruction_label = tk.Label(
            dialog,
            text="总产能用于计算误判率\n误判率 = 误判数量 / 总产能 × 100%",
            font=('Arial', 11),
            fg='#333333'
        )
        instruction_label.pack(pady=20)

        # 输入框架
        input_frame = tk.Frame(dialog)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="总产能数量:", font=('Arial', 11)).pack(side=tk.LEFT, padx=5)

        capacity_var = tk.StringVar(value=str(current_capacity) if current_capacity > 0 else "")
        capacity_entry = tk.Entry(input_frame, textvariable=capacity_var, font=('Arial', 11), width=15)
        capacity_entry.pack(side=tk.LEFT, padx=5)

        # 按钮框架
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        def save_capacity():
            """保存总产能"""
            try:
                capacity_str = capacity_var.get().strip()
                if not capacity_str:
                    self.gui_manager.show_warning("提示", "请输入总产能数量")
                    return

                capacity = int(capacity_str)
                if capacity <= 0:
                    self.gui_manager.show_warning("提示", "总产能必须大于0")
                    return

                # 设置总产能
                self.statistics.set_total_capacity(capacity)

                # 更新统计显示
                self.update_all_statistics()

                self.gui_manager.show_info("成功", f"总产能已设置为 {capacity}")
                dialog.destroy()

            except ValueError:
                self.gui_manager.show_warning("提示", "请输入有效的数字")

        def cancel():
            """取消"""
            dialog.destroy()

        # 保存按钮
        save_btn = tk.Button(button_frame, text="保存", command=save_capacity, width=10, bg='#4CAF50', fg='white')
        save_btn.pack(side=tk.LEFT, padx=5)

        # 取消按钮
        cancel_btn = tk.Button(button_frame, text="取消", command=cancel, width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # 设置焦点到输入框
        capacity_entry.focus()
        dialog.wait_window()

    # 设置导出信息对话框
    def set_export_info_dialog(self):
        """
        显示导出信息输入对话框（在导出Excel时调用）

        Returns:
            tuple: (shift, production_line) 或 (None, None) 如果用户取消
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("设置导出信息")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # 说明文字
        instruction = tk.Label(
            dialog,
            text="请输入本次导出的统计信息",
            font=('Arial', 12, 'bold')
        )
        instruction.pack(pady=15)

        # 班次输入框
        shift_frame = tk.Frame(dialog)
        shift_frame.pack(pady=10, padx=20, fill=tk.X)
        tk.Label(shift_frame, text="统计班次:", font=('Arial', 11), width=12, anchor='w').pack(side=tk.LEFT)
        shift_var = tk.StringVar(value="")
        shift_entry = tk.Entry(shift_frame, textvariable=shift_var, font=('Arial', 11))
        shift_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 产线输入框
        line_frame = tk.Frame(dialog)
        line_frame.pack(pady=10, padx=20, fill=tk.X)
        tk.Label(line_frame, text="产线名称:", font=('Arial', 11), width=12, anchor='w').pack(side=tk.LEFT)
        line_var = tk.StringVar(value="")
        line_entry = tk.Entry(line_frame, textvariable=line_var, font=('Arial', 11))
        line_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 结果存储
        result = {'shift': None, 'line': None}

        def on_ok():
            result['shift'] = shift_var.get().strip()
            result['line'] = line_var.get().strip()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # 按钮框架
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="确定", command=on_ok, width=10,
                  bg='#4CAF50', fg='white', font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="取消", command=on_cancel, width=10,
                  font=('Arial', 11)).pack(side=tk.LEFT, padx=5)

        # 设置焦点到班次输入框
        shift_entry.focus()
        dialog.wait_window()

        return result['shift'], result['line']

    # 导出报告
    def export_report(self, format_type='txt'):
        """
        导出统计报告

        Args:
            format_type: 导出格式 ('txt', 'excel')
        """
        session_summary = self.data_handler.get_session_summary()
        if not session_summary.get('recorded_count', 0):
            self.gui_manager.show_warning("提示", "暂无统计数据可导出")
            return

        # 在导出前先更新当前会话的统计数据
        summary = self.statistics.get_summary()
        type_rates = summary['type_rates']
        self.data_handler.current_session['summary'] = summary
        self.data_handler.current_session['type_statistics'] = type_rates
        self.data_handler.current_session['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 如果是Excel导出，显示导出信息对话框
        if format_type == 'excel':
            shift, line = self.set_export_info_dialog()
            if shift is None:  # 用户取消
                return
            self.data_handler.current_session['shift'] = shift
            self.data_handler.current_session['production_line'] = line

        # 根据格式设置文件类型
        format_config = {
            'txt': {
                'extension': '.txt',
                'filetypes': [("文本文件", "*.txt"), ("所有文件", "*.*")],
                'method': self.data_handler.export_to_txt
            },
            'excel': {
                'extension': '.xlsx',
                'filetypes': [("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
                'method': self.data_handler.export_to_excel
            }
        }

        config = format_config.get(format_type, format_config['txt'])

        # 选择保存位置
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title=f"导出统计报告 ({format_type.upper()})",
            defaultextension=config['extension'],
            filetypes=config['filetypes']
        )

        if file_path:
            # Excel导出需要传入图片总数（NG图片数）
            if format_type == 'excel':
                total_images = self.image_loader.get_total_count()
                success = config['method'](file_path, total_images_count=total_images)
            else:
                success = config['method'](file_path)

            if success:
                self.gui_manager.show_info("成功", f"报告已导出到:\n{file_path}")
            else:
                self.gui_manager.show_error("错误", "导出报告失败")

    # 导出图片
    def export_images(self):
        """导出误判图片及同条码图片"""
        # 1. 检查是否有误判数据
        summary = self.statistics.get_summary()
        if summary.get('misjudgment', 0) == 0:
            self.gui_manager.show_warning("提示", "暂无误判数据可导出")
            return
        
        # 2. 检查是否已选择文件夹
        if self.image_loader.is_empty():
            self.gui_manager.show_warning("提示", "请先选择图片文件夹")
            return
        
        # 3. 选择导出目标文件夹
        from tkinter import filedialog
        output_folder = filedialog.askdirectory(title="选择导出图片的目标文件夹")
        if not output_folder:
            return
        
        # 4. 创建进度对话框
        progress_dialog = self.gui_manager.create_progress_dialog("导出图片", "正在准备导出...")
        
        def progress_callback(current, total, message):
            """进度回调函数"""
            self.gui_manager.update_progress_dialog(progress_dialog, current, total, message)
        
        try:
            # 5. 执行导出
            folder_path = self.image_loader.image_folder
            success, message, stats = self.data_handler.export_images(
                output_folder, 
                folder_path,
                progress_callback
            )
            
            # 6. 关闭进度对话框
            self.gui_manager.close_progress_dialog(progress_dialog)
            
            # 7. 显示结果
            if success:
                detail_msg = (
                    f"{message}\n\n"
                    f"导出路径: {output_folder}\n"
                    f"已生成导出清单.txt文件"
                )
                self.gui_manager.show_info("导出成功", detail_msg)
            else:
                self.gui_manager.show_error("导出失败", message)
                
        except Exception as e:
            # 确保关闭进度对话框
            self.gui_manager.close_progress_dialog(progress_dialog)
            self.gui_manager.show_error("错误", f"导出图片时发生错误: {e}")
    
    # 退出确认
    def confirm_exit(self):
        """确认退出"""
        if not self.image_loader.is_empty() and self.image_loader.has_next():
            return self.gui_manager.ask_yes_no(
                "确认退出",
                "当前还有未完成的统计任务，确定要退出吗？"
            )
        return True


def main():
    """主函数"""
    app = MisjudgmentApp()
    app.run()


if __name__ == "__main__":
    main()
