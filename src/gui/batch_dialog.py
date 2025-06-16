from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QComboBox, QCheckBox, QListWidget, QMessageBox,
    QRadioButton, QInputDialog, QLineEdit, QWidget
)
from PySide6.QtCore import Qt, Signal, Slot, QThread
from pathlib import Path
import os

from src.core.ocr_engine import OCREngine
from src.core.config import Config
from src.utils.file_utils import FileUtils

class BatchOCRWorker(QThread):
    """
    批量OCR处理线程
    
    继承自QThread，用于在后台线程中执行批量OCR处理任务，
    避免在处理大量PDF文件时阻塞主UI线程。
    可以报告总体进度、单个文件进度和处理结果。
    
    信号:
        progress_updated: 发送处理进度信息 (当前索引, 总数, 文件路径, 结果码)
        file_progress_updated: 发送单个文件的处理进度 (当前进度, 总进度)
        finished: 处理完成后发送结果字典
    """
    progress_updated = Signal(int, int, str, int)  # 修改为发送状态码而不是布尔值
    file_progress_updated = Signal(int, int)  # 当前文件的进度
    finished = Signal(dict)
    
    def __init__(self, engine, files, output_dir, options):
        """
        初始化批量OCR工作线程
        
        Args:
            engine (OCREngine): OCR引擎实例
            files (list): 要处理的文件路径列表
            output_dir (str): 输出目录路径
            options (dict): OCR处理选项
        """
        super().__init__()
        self.engine = engine
        self.files = files
        self.output_dir = output_dir
        self.options = options
    
    def run(self):
        """
        线程执行方法
        
        遍历文件列表，对每个文件进行OCR处理，
        收集处理结果并通过信号报告进度。
        完成后发送finished信号，包含所有文件的处理结果。
        """
        results = {}
        total = len(self.files)
        
        # 确保输出目录存在
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, input_file in enumerate(self.files):
            input_path = Path(input_file)
            output_file = output_path / f"{input_path.stem}_ocr{input_path.suffix}"
            
            # 处理文件并获取结果码
            result_code = self.engine.process_file(input_file, output_file, self.options)
            results[input_file] = result_code
            
            # 发送进度更新
            success = result_code > 0  # 成功或已OCR过都视为"成功"
            self.progress_updated.emit(i + 1, total, input_file, result_code)
        
        self.finished.emit(results)

class BatchDialog(QDialog):
    """
    批量处理对话框
    
    提供批量OCR处理的用户界面，包括文件选择、OCR选项设置、
    配置管理和处理控制等功能。
    相比主窗口，提供了更详细的批处理选项和进度显示。
    """
    
    def __init__(self, parent=None):
        """
        初始化批量处理对话框
        
        设置窗口基本属性，创建配置和OCR引擎实例，
        初始化UI组件。
        
        Args:
            parent: 父窗口，默认为None
        """
        super().__init__(parent)
        self.setWindowTitle("批量OCR处理")
        self.resize(700, 500)
        
        self.config = Config()
        self.ocr_engine = OCREngine()
        self.selected_files = []
        
        self.init_ui()
    
    def init_ui(self):
        """
        初始化用户界面
        
        创建和布局所有UI组件，包括：
        - 文件选择区域
        - 输出选项（目录和文件命名）
        - OCR选项（语言、配置文件、处理选项）
        - 进度显示（总进度和文件进度）
        - 控制按钮
        """
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        file_buttons_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("添加文件")
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn = QPushButton("添加文件夹")
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.clear_files_btn = QPushButton("清除")
        self.clear_files_btn.clicked.connect(self.clear_files)
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_files)
        
        file_buttons_layout.addWidget(self.add_files_btn)
        file_buttons_layout.addWidget(self.add_folder_btn)
        file_buttons_layout.addWidget(self.clear_files_btn)
        file_buttons_layout.addWidget(self.select_all_btn)
        file_buttons_layout.addStretch()
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        
        file_layout.addLayout(file_buttons_layout)
        file_layout.addWidget(self.file_list)
        
        # 输出选项
        output_group = QGroupBox("输出选项")
        output_layout = QVBoxLayout(output_group)
        
        # 输出目录
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_edit = QComboBox()
        self.output_dir_edit.setEditable(True)
        self.output_dir_edit.addItems(self.config.get('recent_output_dirs', []))
        self.output_dir_btn = QPushButton("浏览...")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(self.output_dir_edit, 1)
        output_dir_layout.addWidget(self.output_dir_btn)
        
        # 输出文件命名
        naming_layout = QHBoxLayout()
        naming_layout.addWidget(QLabel("输出文件命名:"))
        self.naming_combo = QComboBox()
        self.naming_combo.addItems(["原文件名_ocr", "原文件名", "自定义前缀_原文件名"])
        self.naming_combo.currentIndexChanged.connect(self.on_naming_option_changed)
        naming_layout.addWidget(self.naming_combo, 1)
        
        # 添加自定义前缀输入框
        self.prefix_layout = QHBoxLayout()
        self.prefix_layout.addWidget(QLabel("自定义前缀:"))
        self.prefix_edit = QLineEdit("OCR_")
        self.prefix_layout.addWidget(self.prefix_edit, 1)
        
        # 初始时隐藏前缀输入框
        self.prefix_widget = QWidget()
        self.prefix_widget.setLayout(self.prefix_layout)
        self.prefix_widget.setVisible(False)
        
        output_layout.addLayout(output_dir_layout)
        output_layout.addLayout(naming_layout)
        output_layout.addWidget(self.prefix_widget)
        
        # OCR选项
        ocr_group = QGroupBox("OCR选项")
        ocr_layout = QVBoxLayout(ocr_group)
        
        # 语言选择
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("OCR语言:"))
        self.language_combo = QComboBox()
        self.language_combo.setToolTip("选择OCR识别使用的语言")
        
        # 添加可用的语言
        # 常用语言列表
        common_langs = ['eng', 'chi_sim', 'chi_tra', 'jpn', 'kor']
        
        # 首先添加常用语言
        if self.ocr_engine.available_languages:
            # 添加常用语言组
            common_available = [lang for lang in common_langs if lang in self.ocr_engine.available_languages]
            if common_available:
                self.language_combo.addItem("--- 常用语言 ---", None)
                for lang_code in common_available:
                    lang_name = self.ocr_engine.get_language_name(lang_code)
                    self.language_combo.addItem(lang_name, lang_code)
                
                # 添加其他语言组
                other_available = [lang for lang in self.ocr_engine.available_languages 
                                  if lang not in common_langs]
                if other_available:
                    self.language_combo.addItem("--- 其他语言 ---", None)
                    # 按名称排序
                    other_langs_sorted = sorted(
                        other_available,
                        key=lambda x: self.ocr_engine.get_language_name(x)
                    )
                    for lang_code in other_langs_sorted:
                        lang_name = self.ocr_engine.get_language_name(lang_code)
                        self.language_combo.addItem(lang_name, lang_code)
            else:
                # 如果没有常用语言，直接添加所有语言
                for lang_code in self.ocr_engine.available_languages:
                    lang_name = self.ocr_engine.get_language_name(lang_code)
                    self.language_combo.addItem(lang_name, lang_code)
            
        # 设置默认语言
        default_lang = self.config.get('default_options.language', 'eng')
        index = self.language_combo.findData(default_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
            
        language_layout.addWidget(self.language_combo)
        ocr_layout.addLayout(language_layout)
        
        # 使用配置文件
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("使用配置文件:"))
        self.config_combo = QComboBox()
        self.config_combo.addItem("默认配置")
        # 添加已保存的配置
        self.load_saved_configs()
        self.config_combo.currentIndexChanged.connect(self.on_config_changed)
        self.save_config_btn = QPushButton("保存当前配置")
        self.save_config_btn.clicked.connect(self.save_current_config)
        config_layout.addWidget(self.config_combo, 1)
        config_layout.addWidget(self.save_config_btn)
        
        # 处理选项
        self.deskew_cb = QCheckBox("自动校正倾斜页面")
        self.deskew_cb.setChecked(self.config.get('default_options.deskew', True))
        
        self.rotate_cb = QCheckBox("自动旋转页面")
        self.rotate_cb.setChecked(self.config.get('default_options.rotate_pages', True))
        
        self.clean_cb = QCheckBox("清理图像")
        self.clean_cb.setChecked(self.config.get('default_options.clean', False))
        
        self.optimize_cb = QCheckBox("优化输出文件大小")
        self.optimize_cb.setChecked(self.config.get('default_options.optimize', True))
        
        # 添加到布局
        ocr_layout.addLayout(config_layout)
        ocr_layout.addWidget(self.deskew_cb)
        ocr_layout.addWidget(self.rotate_cb)
        ocr_layout.addWidget(self.clean_cb)
        ocr_layout.addWidget(self.optimize_cb)
        
        # 进度条
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 总进度
        total_progress_layout = QHBoxLayout()
        total_progress_layout.addWidget(QLabel("总进度:"))
        self.total_progress_bar = QProgressBar()
        total_progress_layout.addWidget(self.total_progress_bar)
        
        # 当前文件进度
        file_progress_layout = QHBoxLayout()
        file_progress_layout.addWidget(QLabel("当前文件:"))
        self.file_progress_bar = QProgressBar()
        file_progress_layout.addWidget(self.file_progress_bar)
        
        self.status_label = QLabel("准备就绪")
        
        progress_layout.addLayout(total_progress_layout)
        progress_layout.addLayout(file_progress_layout)
        progress_layout.addWidget(self.status_label)
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始批量处理")
        self.start_btn.clicked.connect(self.start_batch_ocr)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_batch_ocr)
        self.cancel_btn.setEnabled(False)
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.close_btn)
        
        # 添加所有元素到主布局
        main_layout.addWidget(file_group)
        main_layout.addWidget(output_group)
        main_layout.addWidget(ocr_group)
        main_layout.addWidget(progress_group)
        main_layout.addLayout(buttons_layout)
    
    def add_files(self):
        """
        添加文件按钮点击处理
        
        打开文件选择对话框，允许用户选择一个或多个PDF文件。
        选中的文件将添加到文件列表中并显示在界面上。
        """
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "选择PDF文件", 
            "", 
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        
        if files:
            self.add_files_to_list(files)
    
    def add_folder(self):
        """
        添加文件夹按钮点击处理
        
        打开文件夹选择对话框，允许用户选择一个包含PDF文件的文件夹。
        文件夹中的所有PDF文件(包括子文件夹中的PDF文件)将被添加到文件列表中。
        """
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择包含PDF文件的文件夹"
        )
        
        if folder:
            pdf_files = FileUtils.get_pdf_files_in_dir(folder, recursive=True)
            if pdf_files:
                self.add_files_to_list(pdf_files)
            else:
                QMessageBox.information(self, "提示", "所选文件夹中未找到PDF文件")
    
    def add_files_to_list(self, files):
        """
        将文件添加到文件列表
        
        过滤掉已经在列表中的文件，将新文件添加到列表并更新界面显示。
        
        Args:
            files (list): 要添加的文件路径列表
        """
        # 过滤已存在的文件
        new_files = [f for f in files if f not in self.selected_files]
        if not new_files:
            return
            
        self.selected_files.extend(new_files)
        
        # 更新列表显示
        self.file_list.clear()
        for file in self.selected_files:
            self.file_list.addItem(Path(file).name)
        
        # 更新状态
        self.status_label.setText(f"已添加 {len(self.selected_files)} 个文件")
        
        # 保存最近使用的文件
        for file in new_files:
            self.config.add_recent_file(file)
    
    def clear_files(self):
        """
        清除文件列表
        
        清空选定的文件列表和界面上的文件列表显示。
        """
        self.selected_files = []
        self.file_list.clear()
        self.status_label.setText("文件列表已清空")
    
    def select_all_files(self):
        """
        全选文件
        
        选中文件列表中的所有文件。
        """
        self.file_list.selectAll()
    
    def select_output_dir(self):
        """
        选择输出目录
        
        打开文件夹选择对话框，允许用户选择OCR处理结果的保存目录。
        选中的目录将显示在输出目录编辑框中，并保存到最近使用的目录列表中。
        """
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "选择输出目录",
            ""
        )
        
        if dir_path:
            self.output_dir_edit.setCurrentText(dir_path)
            self.config.add_recent_output_dir(dir_path)
    
    def save_current_config(self):
        """
        保存当前配置
        
        将当前OCR选项保存为命名配置，以便将来重用。
        弹出对话框让用户输入配置名称，然后保存到配置文件中。
        """
        # 获取当前配置名称
        config_name, ok = QInputDialog.getText(
            self,
            "保存配置",
            "请输入配置名称:",
            QLineEdit.Normal,
            "我的OCR配置"
        )
        
        if ok and config_name:
            # 收集当前配置
            current_config = {
                "language": self.language_combo.currentData(),
                "deskew": self.deskew_cb.isChecked(),
                "rotate_pages": self.rotate_cb.isChecked(),
                "clean": self.clean_cb.isChecked(),
                "optimize": self.optimize_cb.isChecked()
            }
            
            # 保存到配置中
            saved_configs = self.config.get('saved_configs', {})
            saved_configs[config_name] = current_config
            self.config.set('saved_configs', saved_configs)
            
            # 更新下拉框
            self.config_combo.addItem(config_name)
            self.config_combo.setCurrentText(config_name)
            
            QMessageBox.information(self, "成功", f"配置 \"{config_name}\" 已保存")
    
    def start_batch_ocr(self):
        """
        开始批量OCR处理
        
        收集用户设置的OCR选项和文件命名选项，创建工作线程执行批量OCR处理。
        处理前会进行必要的参数检查，如确保选择了文件和输出目录。
        开始处理后会禁用UI元素，直到处理完成或取消。
        """
        if not self.selected_files:
            QMessageBox.warning(self, "警告", "未选择文件")
            return
        
        output_dir = self.output_dir_edit.currentText()
        if not output_dir:
            QMessageBox.warning(self, "警告", "未选择输出目录")
            return
        
        # 确保输出目录存在
        if not FileUtils.ensure_dir(output_dir):
            QMessageBox.critical(self, "错误", f"无法创建输出目录: {output_dir}")
            return
        
        # 收集OCR选项
        options = {}
        
        # 获取选中的语言代码
        lang_index = self.language_combo.currentIndex()
        lang_data = self.language_combo.itemData(lang_index)
        if lang_data:  # 确保不是分隔符
            options["language"] = lang_data
        else:
            # 如果选中了分隔符，尝试找到下一个有效选项
            for i in range(lang_index + 1, self.language_combo.count()):
                next_data = self.language_combo.itemData(i)
                if next_data:
                    self.language_combo.setCurrentIndex(i)
                    options["language"] = next_data
                    break
            # 如果没有找到，使用默认语言
            if "language" not in options:
                options["language"] = "eng"
        
        options.update({
            "deskew": self.deskew_cb.isChecked(),
            "rotate_pages": self.rotate_cb.isChecked(),
            "clean": self.clean_cb.isChecked(),
            "optimize": self.optimize_cb.isChecked()
        })
        
        # 收集文件命名选项
        naming_option = self.naming_combo.currentIndex()
        if naming_option == 0:  # 原文件名_ocr
            file_suffix = "_ocr"
            file_prefix = ""
        elif naming_option == 1:  # 原文件名
            file_suffix = ""
            file_prefix = ""
        else:  # 自定义前缀_原文件名
            file_suffix = ""
            file_prefix = self.prefix_edit.text()
        
        options["file_prefix"] = file_prefix
        options["file_suffix"] = file_suffix
        
        # 禁用UI元素
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.add_files_btn.setEnabled(False)
        self.add_folder_btn.setEnabled(False)
        self.clear_files_btn.setEnabled(False)
        self.select_all_btn.setEnabled(False)
        self.output_dir_btn.setEnabled(False)
        self.output_dir_edit.setEnabled(False)
        
        # 重置进度条
        self.total_progress_bar.setValue(0)
        self.file_progress_bar.setValue(0)
        self.status_label.setText("处理中...")
        
        # 创建并启动工作线程
        self.worker = BatchOCRWorker(
            self.ocr_engine,
            self.selected_files,
            output_dir,
            options
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_progress_updated.connect(self.update_file_progress)
        self.worker.finished.connect(self.ocr_finished)
        self.worker.start()
    
    def cancel_batch_ocr(self):
        """
        取消批量OCR处理
        
        终止正在运行的OCR工作线程，更新状态显示，
        并重新启用被禁用的UI元素。
        """
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.status_label.setText("处理已取消")
            
        # 启用UI元素
        self.enable_ui()
    
    def enable_ui(self):
        """
        启用UI元素
        
        在OCR处理完成或取消后，重新启用之前被禁用的UI元素，
        使界面恢复到可交互状态。
        """
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.add_files_btn.setEnabled(True)
        self.add_folder_btn.setEnabled(True)
        self.clear_files_btn.setEnabled(True)
        self.select_all_btn.setEnabled(True)
        self.output_dir_btn.setEnabled(True)
        self.output_dir_edit.setEnabled(True)
    
    @Slot(int, int, str, int)
    def update_progress(self, current, total, file, result_code):
        """
        更新总进度显示
        
        接收来自OCR工作线程的进度信号，更新总进度条和状态文本。
        根据结果码显示不同颜色的状态文本：成功(绿色)、已OCR过(蓝色)、失败(红色)。
        
        Args:
            current (int): 当前处理的文件索引（从1开始）
            total (int): 总文件数
            file (str): 当前处理的文件路径
            result_code (int): 处理结果状态码（0-失败，1-成功，2-已OCR过）
        """
        percent = int(current * 100 / total)
        self.total_progress_bar.setValue(percent)
        
        file_name = Path(file).name
        
        # 根据状态码设置状态文本和颜色
        if result_code == 1:
            status = "成功"
            status_color = "green"
        elif result_code == 2:
            status = "已OCR过"
            status_color = "blue"
        else:
            status = "失败"
            status_color = "red"
            
        # 使用HTML格式化状态文本
        status_text = f"处理 {file_name}: <span style='color: {status_color};'>{status}</span> ({current}/{total})"
        self.status_label.setText(status_text)
    
    @Slot(int, int)
    def update_file_progress(self, current, total):
        """
        更新当前文件进度
        
        接收来自OCR工作线程的文件进度信号，更新文件进度条。
        
        Args:
            current (int): 当前处理进度
            total (int): 总进度
        """
        percent = int(current * 100 / total) if total > 0 else 0
        self.file_progress_bar.setValue(percent)
    
    @Slot(dict)
    def ocr_finished(self, results):
        """
        OCR处理完成回调
        
        接收来自OCR工作线程的完成信号，统计处理结果，
        更新状态显示，重新启用UI元素，并显示处理结果对话框。
        
        Args:
            results (dict): 处理结果字典，键为文件路径，值为处理结果状态码
        """
        success_count = 0
        already_ocr_count = 0
        failed_count = 0
        
        for result_code in results.values():
            if result_code == 1:  # 成功
                success_count += 1
            elif result_code == 2:  # 已OCR过
                already_ocr_count += 1
            else:  # 失败
                failed_count += 1
        
        total_count = len(results)
        
        # 构建状态消息
        status_msg = f"处理完成: {success_count}/{total_count} 文件成功"
        if already_ocr_count > 0:
            status_msg += f", {already_ocr_count} 文件已OCR过"
        
        self.status_label.setText(status_msg)
        
        # 启用按钮
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        
        # 构建完成消息
        message = f"批量OCR处理已完成\n成功: {success_count} 文件"
        if already_ocr_count > 0:
            message += f"\n已OCR过: {already_ocr_count} 文件"
        message += f"\n失败: {failed_count} 文件"
        
        # 显示完成消息
        QMessageBox.information(
            self,
            "处理完成",
            message
        )
    
    def load_saved_configs(self):
        """
        加载已保存的配置
        
        从配置文件中读取已保存的OCR配置，并添加到配置下拉列表中。
        """
        saved_configs = self.config.get('saved_configs', {})
        for config_name in saved_configs.keys():
            self.config_combo.addItem(config_name)
    
    def on_config_changed(self, index):
        """
        配置选择变更事件处理
        
        当用户选择不同的配置文件时触发。
        根据选择的配置更新UI中的OCR选项。
        
        Args:
            index (int): 当前选中配置的索引
        """
        config_name = self.config_combo.currentText()
        if config_name == "默认配置":
            # 加载默认配置
            self.deskew_cb.setChecked(self.config.get('default_options.deskew', True))
            self.rotate_cb.setChecked(self.config.get('default_options.rotate_pages', True))
            self.clean_cb.setChecked(self.config.get('default_options.clean', False))
            self.optimize_cb.setChecked(self.config.get('default_options.optimize', True))
            
            # 设置默认语言
            default_lang = self.config.get('default_options.language', 'eng')
            index = self.language_combo.findData(default_lang)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
        else:
            # 加载已保存的配置
            saved_configs = self.config.get('saved_configs', {})
            if config_name in saved_configs:
                config = saved_configs[config_name]
                
                # 设置选项
                self.deskew_cb.setChecked(config.get('deskew', True))
                self.rotate_cb.setChecked(config.get('rotate_pages', True))
                self.clean_cb.setChecked(config.get('clean', False))
                self.optimize_cb.setChecked(config.get('optimize', True))
                
                # 设置语言
                lang = config.get('language', 'eng')
                index = self.language_combo.findData(lang)
                if index >= 0:
                    self.language_combo.setCurrentIndex(index)
    
    def on_naming_option_changed(self, index):
        """
        命名选项变更事件处理
        
        当用户选择不同的文件命名选项时触发。
        如果选择了"自定义前缀_原文件名"选项，则显示前缀输入框，否则隐藏。
        
        Args:
            index (int): 当前选中选项的索引
        """
        # 如果选择了"自定义前缀_原文件名"，显示前缀输入框
        self.prefix_widget.setVisible(index == 2)  # 第三个选项的索引是2 