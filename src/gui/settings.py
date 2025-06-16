from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QComboBox, QCheckBox,
    QGroupBox, QSpinBox, QRadioButton, QMessageBox,
    QWidget
)
from PySide6.QtCore import Qt

from src.core.config import Config
from src.core.ocr_engine import OCREngine

class SettingsDialog(QDialog):
    """
    设置对话框
    
    提供应用程序各项设置的配置界面，包括常规设置、OCR设置和界面设置。
    使用选项卡组织不同类别的设置，提供直观的设置界面。
    设置更改后保存到配置文件中，供应用程序其他部分使用。
    """
    
    def __init__(self, parent=None):
        """
        初始化设置对话框
        
        创建配置实例，设置窗口基本属性，初始化UI组件。
        
        Args:
            parent: 父窗口，默认为None
        """
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(500, 400)
        
        self.config = Config()
        self.init_ui()
    
    def init_ui(self):
        """
        初始化用户界面
        
        创建选项卡式布局，包含常规、OCR和界面三个选项卡，
        以及确定和取消按钮。
        """
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 常规选项卡
        general_tab = QWidget()
        tab_widget.addTab(general_tab, "常规")
        self.setup_general_tab(general_tab)
        
        # OCR选项卡
        ocr_tab = QWidget()
        tab_widget.addTab(ocr_tab, "OCR")
        self.setup_ocr_tab(ocr_tab)
        
        # 界面选项卡
        ui_tab = QWidget()
        tab_widget.addTab(ui_tab, "界面")
        self.setup_ui_tab(ui_tab)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def setup_general_tab(self, tab):
        """
        设置常规选项卡
        
        创建并布局常规设置选项，包括启动选项和文件历史设置。
        
        Args:
            tab: 要设置的选项卡控件
        """
        layout = QVBoxLayout(tab)
        
        # 启动选项
        startup_group = QGroupBox("启动选项")
        startup_layout = QVBoxLayout(startup_group)
        
        self.check_update_cb = QCheckBox("启动时检查更新")
        self.check_update_cb.setChecked(self.config.get('general.check_update_on_startup', False))
        
        self.show_welcome_cb = QCheckBox("显示欢迎页面")
        self.show_welcome_cb.setChecked(self.config.get('general.show_welcome', True))
        
        self.remember_window_cb = QCheckBox("记住窗口大小和位置")
        self.remember_window_cb.setChecked(self.config.get('general.remember_window_geometry', True))
        
        startup_layout.addWidget(self.check_update_cb)
        startup_layout.addWidget(self.show_welcome_cb)
        startup_layout.addWidget(self.remember_window_cb)
        
        # 文件历史
        history_group = QGroupBox("文件历史")
        history_layout = QVBoxLayout(history_group)
        
        recent_files_layout = QHBoxLayout()
        recent_files_layout.addWidget(QLabel("最近文件数量:"))
        self.recent_files_spin = QSpinBox()
        self.recent_files_spin.setRange(0, 30)
        self.recent_files_spin.setValue(self.config.get('general.max_recent_files', 10))
        recent_files_layout.addWidget(self.recent_files_spin)
        recent_files_layout.addStretch()
        
        self.clear_history_btn = QPushButton("清除历史记录")
        self.clear_history_btn.clicked.connect(self.clear_history)
        
        history_layout.addLayout(recent_files_layout)
        history_layout.addWidget(self.clear_history_btn)
        
        layout.addWidget(startup_group)
        layout.addWidget(history_group)
        layout.addStretch()
    
    def setup_ocr_tab(self, tab):
        """
        设置OCR选项卡
        
        创建并布局OCR设置选项，包括默认语言设置、处理选项和输出类型设置。
        
        Args:
            tab: 要设置的选项卡控件
        """
        layout = QVBoxLayout(tab)
        
        # 默认语言
        language_group = QGroupBox("默认OCR语言")
        language_layout = QVBoxLayout(language_group)
        
        self.language_combo = QComboBox()
        self.language_combo.setToolTip("选择默认的OCR识别语言")
        
        # 添加可用的语言
        ocr_engine = OCREngine()
        # 常用语言列表
        common_langs = ['eng', 'chi_sim', 'chi_tra', 'jpn', 'kor']
        
        # 首先添加常用语言
        if ocr_engine.available_languages:
            # 添加常用语言组
            common_available = [lang for lang in common_langs if lang in ocr_engine.available_languages]
            if common_available:
                self.language_combo.addItem("--- 常用语言 ---", None)
                for lang_code in common_available:
                    lang_name = ocr_engine.get_language_name(lang_code)
                    self.language_combo.addItem(lang_name, lang_code)
                
                # 添加其他语言组
                other_available = [lang for lang in ocr_engine.available_languages 
                                  if lang not in common_langs]
                if other_available:
                    self.language_combo.addItem("--- 其他语言 ---", None)
                    # 按名称排序
                    other_langs_sorted = sorted(
                        other_available,
                        key=lambda x: ocr_engine.get_language_name(x)
                    )
                    for lang_code in other_langs_sorted:
                        lang_name = ocr_engine.get_language_name(lang_code)
                        self.language_combo.addItem(lang_name, lang_code)
            else:
                # 如果没有常用语言，直接添加所有语言
                for lang_code in ocr_engine.available_languages:
                    lang_name = ocr_engine.get_language_name(lang_code)
                    self.language_combo.addItem(lang_name, lang_code)
            
        # 设置当前默认语言
        default_lang = self.config.get('default_options.language', 'eng')
        index = self.language_combo.findData(default_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        # 添加刷新语言列表按钮
        lang_buttons_layout = QHBoxLayout()
        self.refresh_langs_btn = QPushButton("刷新语言列表")
        self.refresh_langs_btn.clicked.connect(self.refresh_languages)
        lang_buttons_layout.addWidget(self.refresh_langs_btn)
            
        language_layout.addWidget(self.language_combo)
        language_layout.addLayout(lang_buttons_layout)
        
        # 默认选项
        options_group = QGroupBox("默认处理选项")
        options_layout = QVBoxLayout(options_group)
        
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
        
        # 输出类型
        output_group = QGroupBox("默认输出类型")
        output_layout = QVBoxLayout(output_group)
        
        self.output_type_combo = QComboBox()
        self.output_type_combo.addItems(["pdf", "pdfa", "pdfa-1", "pdfa-2", "pdfa-3"])
        self.output_type_combo.setCurrentText(self.config.get('default_options.output_type', 'pdfa'))
        
        output_layout.addWidget(self.output_type_combo)
        
        layout.addWidget(language_group)
        layout.addWidget(options_group)
        layout.addWidget(output_group)
        layout.addStretch()
    
    def setup_ui_tab(self, tab):
        """
        设置界面选项卡
        
        创建并布局界面设置选项，包括主题和语言设置。
        
        Args:
            tab: 要设置的选项卡控件
        """
        layout = QVBoxLayout(tab)
        
        # 主题设置
        theme_group = QGroupBox("主题")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_system_rb = QRadioButton("跟随系统")
        self.theme_light_rb = QRadioButton("浅色主题")
        self.theme_dark_rb = QRadioButton("深色主题")
        
        current_theme = self.config.get('ui.theme', 'system')
        if current_theme == 'light':
            self.theme_light_rb.setChecked(True)
        elif current_theme == 'dark':
            self.theme_dark_rb.setChecked(True)
        else:
            self.theme_system_rb.setChecked(True)
        
        theme_layout.addWidget(self.theme_system_rb)
        theme_layout.addWidget(self.theme_light_rb)
        theme_layout.addWidget(self.theme_dark_rb)
        
        # 语言设置
        language_group = QGroupBox("界面语言")
        language_layout = QVBoxLayout(language_group)
        
        self.ui_language_combo = QComboBox()
        self.ui_language_combo.addItem("简体中文", "zh_CN")
        self.ui_language_combo.addItem("English", "en_US")
        
        current_lang = self.config.get('ui.language', 'zh_CN')
        index = self.ui_language_combo.findData(current_lang)
        if index >= 0:
            self.ui_language_combo.setCurrentIndex(index)
        
        language_note = QLabel("注：更改语言设置需要重启应用程序才能生效")
        language_note.setStyleSheet("color: gray;")
        
        language_layout.addWidget(self.ui_language_combo)
        language_layout.addWidget(language_note)
        
        layout.addWidget(theme_group)
        layout.addWidget(language_group)
        layout.addStretch()
    
    def clear_history(self):
        """
        清除历史记录
        
        清空最近使用的文件和输出目录列表，并弹出确认提示。
        """
        self.config.set('recent_files', [])
        self.config.set('recent_output_dirs', [])
        QMessageBox.information(self, "已清除", "已清除所有历史记录")
    
    def accept(self):
        """
        确定按钮点击处理
        
        保存所有设置到配置文件中，并关闭对话框。
        """
        # 保存常规设置
        self.config.set('general.check_update_on_startup', self.check_update_cb.isChecked())
        self.config.set('general.show_welcome', self.show_welcome_cb.isChecked())
        self.config.set('general.remember_window_geometry', self.remember_window_cb.isChecked())
        self.config.set('general.max_recent_files', self.recent_files_spin.value())
        
        # 保存OCR设置
        lang_index = self.language_combo.currentIndex()
        lang_data = self.language_combo.itemData(lang_index)
        
        # 如果选择了分隔符，尝试找到下一个有效选项
        if lang_data is None:
            for i in range(lang_index + 1, self.language_combo.count()):
                next_data = self.language_combo.itemData(i)
                if next_data:
                    lang_data = next_data
                    break
            # 如果没有找到，使用默认语言
            if lang_data is None:
                lang_data = 'eng'
        
        self.config.set('default_options.language', lang_data)
        self.config.set('default_options.deskew', self.deskew_cb.isChecked())
        self.config.set('default_options.rotate_pages', self.rotate_cb.isChecked())
        self.config.set('default_options.clean', self.clean_cb.isChecked())
        self.config.set('default_options.optimize', self.optimize_cb.isChecked())
        self.config.set('default_options.output_type', self.output_type_combo.currentText())
        
        # 保存界面设置
        if self.theme_light_rb.isChecked():
            theme = 'light'
        elif self.theme_dark_rb.isChecked():
            theme = 'dark'
        else:
            theme = 'system'
        
        self.config.set('ui.theme', theme)
        self.config.set('ui.language', self.ui_language_combo.currentData())
        
        super().accept()
    
    def refresh_languages(self):
        """
        刷新语言列表
        
        重新获取系统中已安装的Tesseract语言包，并更新语言下拉列表。
        保存当前选择的语言，并在刷新后尝试恢复选择。
        """
        # 保存当前选择的语言
        current_lang = self.language_combo.currentData()
        
        # 清空语言下拉列表
        self.language_combo.clear()
        
        # 重新获取语言列表
        ocr_engine = OCREngine()
        # 这会重新检测可用的语言
        ocr_engine = OCREngine()
        
        # 重新填充语言下拉列表
        common_langs = ['eng', 'chi_sim', 'chi_tra', 'jpn', 'kor']
        
        if ocr_engine.available_languages:
            # 添加常用语言组
            common_available = [lang for lang in common_langs if lang in ocr_engine.available_languages]
            if common_available:
                self.language_combo.addItem("--- 常用语言 ---", None)
                for lang_code in common_available:
                    lang_name = ocr_engine.get_language_name(lang_code)
                    self.language_combo.addItem(lang_name, lang_code)
                
                # 添加其他语言组
                other_available = [lang for lang in ocr_engine.available_languages 
                                  if lang not in common_langs]
                if other_available:
                    self.language_combo.addItem("--- 其他语言 ---", None)
                    # 按名称排序
                    other_langs_sorted = sorted(
                        other_available,
                        key=lambda x: ocr_engine.get_language_name(x)
                    )
                    for lang_code in other_langs_sorted:
                        lang_name = ocr_engine.get_language_name(lang_code)
                        self.language_combo.addItem(lang_name, lang_code)
            else:
                # 如果没有常用语言，直接添加所有语言
                for lang_code in ocr_engine.available_languages:
                    lang_name = ocr_engine.get_language_name(lang_code)
                    self.language_combo.addItem(lang_name, lang_code)
        
        # 恢复之前选择的语言
        if current_lang:
            index = self.language_combo.findData(current_lang)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
        
        # 显示刷新结果
        QMessageBox.information(
            self,
            "刷新完成",
            f"已刷新语言列表，找到 {len(ocr_engine.available_languages)} 种语言"
        )

    def download_language_pack(self):
        """下载Tesseract语言包 - 已移除"""
        pass
