import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QComboBox, QCheckBox, QGroupBox, QListWidget, 
    QMessageBox, QStatusBar, QMenu, QMenuBar, QLineEdit
)
from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QAction

from src.core.ocr_engine import OCREngine
from src.core.config import Config
from src.utils.file_utils import FileUtils
from src.gui.settings import SettingsDialog
from src.gui.batch_dialog import BatchDialog

class OCRWorker(QThread):
    """
    OCR处理线程
    
    继承自QThread，用于在后台线程中执行OCR处理任务，
    避免在处理大型PDF文件时阻塞主UI线程。
    使用信号机制向主线程报告处理进度和结果。
    
    信号:
        progress_updated: 发送处理进度信息 (当前文件索引, 总文件数, 文件路径, 是否成功)
        finished: 处理完成后发送结果字典
    """
    progress_updated = Signal(int, int, str, bool)
    finished = Signal(dict)
    
    def __init__(self, engine, files, output_dir, options):
        """
        初始化OCR工作线程
        
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
        
        调用OCREngine的process_batch方法处理文件，
        并通过进度回调函数发送进度信号。
        完成后发送finished信号，包含处理结果。
        """
        results = self.engine.process_batch(
            self.files, 
            self.output_dir, 
            self.options,
            lambda current, total, file, success: self.progress_updated.emit(current, total, file, success)
        )
        self.finished.emit(results)

class MainWindow(QMainWindow):
    """
    应用程序主窗口类
    
    提供主要的用户界面，包括文件选择、OCR选项设置和处理控制。
    支持文件拖放、批处理和基本设置管理。
    处理单个或多个PDF文件的OCR，并显示处理进度和结果。
    """
    
    def __init__(self):
        """
        初始化主窗口
        
        设置窗口基本属性，创建配置和OCR引擎实例，
        初始化UI组件，并启用文件拖放功能。
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("OCRmyPDF GUI")
        self.resize(800, 600)
        self.setAcceptDrops(True)  # 启用拖放功能
        
        # 创建配置和OCR引擎实例
        self.config = Config()
        self.ocr_engine = OCREngine()
        self.selected_files = []  # 存储选中的文件路径
        
        # 初始化UI组件
        self.init_ui()
        self.logger.info("主窗口初始化完成")
    
    def init_ui(self):
        """
        初始化用户界面
        
        创建和布局所有UI组件，包括：
        - 菜单栏和状态栏
        - 文件选择区域
        - 输出目录和文件命名选项
        - OCR语言和处理选项
        - 进度显示和控制按钮
        """
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        # 添加文件按钮
        file_buttons_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("添加文件")
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn = QPushButton("添加文件夹")
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.clear_files_btn = QPushButton("清除文件")
        self.clear_files_btn.clicked.connect(self.clear_files)
        file_buttons_layout.addWidget(self.add_files_btn)
        file_buttons_layout.addWidget(self.add_folder_btn)
        file_buttons_layout.addWidget(self.clear_files_btn)
        file_buttons_layout.addStretch()
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        
        file_layout.addLayout(file_buttons_layout)
        file_layout.addWidget(self.file_list)
        
        # 输出目录选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_edit = QComboBox()
        self.output_dir_edit.setEditable(True)
        self.output_dir_edit.addItems(self.config.get('recent_output_dirs', []))  # 加载最近使用的目录
        self.output_dir_btn = QPushButton("浏览...")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_dir_edit, 1)
        output_layout.addWidget(self.output_dir_btn)
        
        # 输出文件命名选项
        naming_layout = QHBoxLayout()
        naming_layout.addWidget(QLabel("输出文件命名:"))
        self.naming_combo = QComboBox()
        self.naming_combo.addItems(["原文件名_ocr", "原文件名", "自定义前缀_原文件名"])
        self.naming_combo.currentIndexChanged.connect(self.on_naming_option_changed)
        naming_layout.addWidget(self.naming_combo, 1)
        
        # 自定义前缀输入框
        self.prefix_layout = QHBoxLayout()
        self.prefix_layout.addWidget(QLabel("自定义前缀:"))
        self.prefix_edit = QLineEdit("OCR_")
        self.prefix_layout.addWidget(self.prefix_edit, 1)
        
        # 初始时隐藏前缀输入框
        self.prefix_widget = QWidget()
        self.prefix_widget.setLayout(self.prefix_layout)
        self.prefix_widget.setVisible(False)  # 默认隐藏，仅当选择"自定义前缀"选项时显示
        
        # OCR选项组
        options_group = QGroupBox("OCR选项")
        options_layout = QVBoxLayout(options_group)
        
        # 语言选择
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("OCR语言:"))
        self.language_combo = QComboBox()
        self.language_combo.setToolTip("选择OCR识别使用的语言")
        
        # 添加可用的语言，分为常用语言和其他语言两组
        common_langs = ['eng', 'chi_sim', 'chi_tra', 'jpn', 'kor']  # 常用语言列表
        
        if self.ocr_engine.available_languages:
            # 添加常用语言组
            common_available = [lang for lang in common_langs if lang in self.ocr_engine.available_languages]
            if common_available:
                # 添加组标题项（不可选）
                self.language_combo.addItem("--- 常用语言 ---", None)
                for lang_code in common_available:
                    lang_name = self.ocr_engine.get_language_name(lang_code)
                    self.language_combo.addItem(lang_name, lang_code)
                
                # 添加其他语言组
                other_available = [lang for lang in self.ocr_engine.available_languages 
                                  if lang not in common_langs]
                if other_available:
                    # 添加组标题项（不可选）
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
        options_layout.addLayout(language_layout)
        
        # OCR处理选项复选框
        self.deskew_cb = QCheckBox("自动校正倾斜页面")
        self.deskew_cb.setChecked(self.config.get('default_options.deskew', True))
        self.rotate_cb = QCheckBox("自动旋转页面")
        self.rotate_cb.setChecked(self.config.get('default_options.rotate_pages', True))
        self.clean_cb = QCheckBox("清理图像")
        self.clean_cb.setChecked(self.config.get('default_options.clean', False))
        self.optimize_cb = QCheckBox("优化输出文件大小")
        self.optimize_cb.setChecked(self.config.get('default_options.optimize', True))
        
        options_layout.addWidget(self.deskew_cb)
        options_layout.addWidget(self.rotate_cb)
        options_layout.addWidget(self.clean_cb)
        options_layout.addWidget(self.optimize_cb)
        
        # 进度显示区域
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label = QLabel("准备就绪")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始OCR处理")
        self.start_btn.clicked.connect(self.start_ocr)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_ocr)
        self.cancel_btn.setEnabled(False)  # 初始状态下禁用取消按钮
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        # 添加所有元素到主布局
        main_layout.addWidget(file_group)
        main_layout.addLayout(output_layout)
        main_layout.addLayout(naming_layout)
        main_layout.addWidget(self.prefix_widget)
        main_layout.addWidget(options_group)
        main_layout.addLayout(progress_layout)
        main_layout.addLayout(buttons_layout)
    
    def create_menu_bar(self):
        """
        创建应用程序菜单栏
        
        包含文件、编辑和帮助三个主菜单，提供常用功能的快捷访问。
        文件菜单：添加文件、添加文件夹、批量处理、退出
        编辑菜单：清除文件列表、设置
        帮助菜单：关于
        """
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        
        # 文件菜单
        file_menu = QMenu("文件(&F)", self)
        menu_bar.addMenu(file_menu)
        
        add_files_action = QAction("添加文件(&A)...", self)
        add_files_action.triggered.connect(self.add_files)
        file_menu.addAction(add_files_action)
        
        add_folder_action = QAction("添加文件夹(&D)...", self)
        add_folder_action.triggered.connect(self.add_folder)
        file_menu.addAction(add_folder_action)
        
        file_menu.addSeparator()
        
        batch_action = QAction("批量处理(&B)...", self)
        batch_action.triggered.connect(self.show_batch_dialog)
        file_menu.addAction(batch_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = QMenu("编辑(&E)", self)
        menu_bar.addMenu(edit_menu)
        
        clear_action = QAction("清除文件列表(&C)", self)
        clear_action.triggered.connect(self.clear_files)
        edit_menu.addAction(clear_action)
        
        settings_action = QAction("设置(&S)...", self)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = QMenu("帮助(&H)", self)
        menu_bar.addMenu(help_menu)
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
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
        同时更新状态栏显示添加的文件数量，并将文件路径保存到最近使用文件列表中。
        
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
        self.statusBar.showMessage(f"已添加 {len(self.selected_files)} 个文件")
        
        # 保存最近使用的文件
        for file in new_files:
            self.config.add_recent_file(file)
    
    def clear_files(self):
        """
        清除文件列表
        
        清空选定的文件列表和界面上的文件列表显示，
        同时更新状态栏显示。
        """
        self.selected_files = []
        self.file_list.clear()
        self.status_label.setText("文件列表已清空")
        self.statusBar.showMessage("文件列表已清空")
    
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
    
    def start_ocr(self):
        """
        开始OCR处理
        
        收集用户设置的OCR选项，创建工作线程执行OCR处理。
        处理前会进行必要的参数检查，如确保选择了文件和输出目录。
        对于单个文件，直接处理并显示结果；对于多个文件，启动工作线程并显示进度。
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
        
        # 添加处理选项
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
        
        # 如果只有一个文件，先检查是否已OCR过
        if len(self.selected_files) == 1:
            input_file = self.selected_files[0]
            input_path = Path(input_file)
            # 使用前缀和后缀构建输出文件名
            output_file = Path(output_dir) / f"{file_prefix}{input_path.stem}{file_suffix}{input_path.suffix}"
            
            # 检查是否已OCR过
            result_code = self.ocr_engine.process_file(input_file, output_file, options)
            
            if result_code == 2:  # 已OCR过
                QMessageBox.information(
                    self,
                    "文件已OCR过",
                    f"文件 {input_path.name} 已有文本层，无需再次OCR处理。"
                )
                return
            
            # 如果成功或失败，也直接显示结果并返回
            if result_code == 1:
                QMessageBox.information(
                    self,
                    "处理完成",
                    f"文件 {input_path.name} OCR处理成功。"
                )
                # 添加到最近使用的输出目录
                self.config.add_recent_output_dir(output_dir)
                return
            else:
                QMessageBox.critical(
                    self,
                    "处理失败",
                    f"文件 {input_path.name} OCR处理失败，请查看日志了解详情。"
                )
                return
        
        # 多个文件时，禁用UI元素
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.add_files_btn.setEnabled(False)
        self.add_folder_btn.setEnabled(False)
        self.clear_files_btn.setEnabled(False)
        self.output_dir_btn.setEnabled(False)
        self.output_dir_edit.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("处理中...")
        self.statusBar.showMessage("OCR处理中...")
        
        # 创建并启动工作线程
        self.worker = OCRWorker(
            self.ocr_engine,
            self.selected_files,
            output_dir,
            options
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.ocr_finished)
        self.worker.start()
    
    def cancel_ocr(self):
        """
        取消OCR处理
        
        终止正在运行的OCR工作线程，更新状态显示，
        并重新启用被禁用的UI元素。
        """
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.status_label.setText("处理已取消")
            self.statusBar.showMessage("OCR处理已取消")
            
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
        self.output_dir_btn.setEnabled(True)
        self.output_dir_edit.setEnabled(True)
    
    @Slot(int, int, str, bool)
    def update_progress(self, current, total, file, success):
        """
        更新进度显示
        
        接收来自OCR工作线程的进度信号，更新进度条和状态文本。
        使用HTML格式化状态文本，成功显示为绿色，失败显示为红色。
        
        Args:
            current (int): 当前处理的文件索引（从1开始）
            total (int): 总文件数
            file (str): 当前处理的文件路径
            success (bool): 处理是否成功
        """
        percent = int(current * 100 / total)
        self.progress_bar.setValue(percent)
        
        file_name = Path(file).name
        if success:
            status = "<span style='color: green;'>成功</span>"
        else:
            status = "<span style='color: red;'>失败</span>"
        
        status_text = f"处理 {file_name}: {status} ({current}/{total})"
        self.status_label.setText(status_text)
        self.statusBar.showMessage(f"处理 {file_name}: {'成功' if success else '失败'} ({current}/{total})")
    
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
        
        # 统计处理结果
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
        self.statusBar.showMessage(status_msg)
        
        # 启用UI元素
        self.enable_ui()
        
        # 构建完成消息
        message = f"OCR处理已完成\n成功: {success_count} 文件"
        if already_ocr_count > 0:
            message += f"\n已OCR过: {already_ocr_count} 文件"
        message += f"\n失败: {failed_count} 文件"
        
        # 显示完成消息
        QMessageBox.information(
            self,
            "处理完成",
            message
        )
    
    def show_settings(self):
        """
        显示设置对话框
        
        创建并显示设置对话框，如果用户确认设置更改，
        则更新UI以反映新的默认设置。
        """
        dialog = SettingsDialog(self)
        if dialog.exec():
            # 更新UI以反映新设置
            self.deskew_cb.setChecked(self.config.get('default_options.deskew', True))
            self.rotate_cb.setChecked(self.config.get('default_options.rotate_pages', True))
            self.clean_cb.setChecked(self.config.get('default_options.clean', False))
            self.optimize_cb.setChecked(self.config.get('default_options.optimize', True))
    
    def show_batch_dialog(self):
        """
        显示批量处理对话框
        
        创建并显示批量处理对话框，允许用户一次处理多个文件，
        并提供更详细的批处理选项。
        """
        dialog = BatchDialog(self)
        dialog.exec()
    
    def show_about(self):
        """
        显示关于对话框
        
        显示应用程序的版本信息和基本说明。
        """
        QMessageBox.about(
            self,
            "关于 OCRmyPDF GUI",
            "OCRmyPDF GUI v0.1.0\n\n"
            "OCRmyPDF的图形用户界面\n\n"
            "基于OCRmyPDF开源项目\n"
            "https://github.com/ocrmypdf/OCRmyPDF"
        )
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        拖拽进入事件处理
        
        当用户拖拽文件到窗口上方时触发。
        如果拖拽内容包含URL（文件路径），则接受拖拽动作。
        
        Args:
            event (QDragEnterEvent): 拖拽进入事件对象
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """
        拖拽放下事件处理
        
        当用户在窗口中放下拖拽的文件时触发。
        处理拖拽的文件或文件夹，将PDF文件添加到文件列表中。
        
        Args:
            event (QDropEvent): 拖拽放下事件对象
        """
        urls = event.mimeData().urls()
        files = []
        
        for url in urls:
            path = url.toLocalFile()
            if Path(path).is_dir():
                # 如果是目录，获取目录中的所有PDF文件
                pdf_files = FileUtils.get_pdf_files_in_dir(path, recursive=True)
                files.extend(pdf_files)
            elif FileUtils.is_valid_pdf(path):
                # 如果是PDF文件，直接添加
                files.append(path)
        
        if files:
            self.add_files_to_list(files)
        
        event.acceptProposedAction()
    
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