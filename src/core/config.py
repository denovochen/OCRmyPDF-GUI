import json
import os
from pathlib import Path
import logging

class Config:
    """
    配置管理类
    
    负责应用程序配置的加载、保存和访问操作。
    管理用户偏好设置、最近使用的文件和目录以及默认OCR选项。
    使用JSON格式存储配置，保存在用户主目录的.ocrmypdf-gui文件夹中。
    
    属性:
        logger: 日志记录器，用于记录配置操作的日志
        config_dir: 配置目录路径
        config_file: 配置文件路径
        default_config: 默认配置字典
        current_config: 当前使用的配置字典
    """
    
    def __init__(self):
        """
        初始化配置管理器
        
        设置配置文件路径、初始化默认配置，并从磁盘加载现有配置（如果存在）。
        如果配置文件不存在，将使用默认配置并创建新的配置文件。
        """
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.home() / ".ocrmypdf-gui"
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "recent_files": [],             # 最近使用的文件列表
            "recent_output_dirs": [],       # 最近使用的输出目录列表
            "default_options": {            # 默认OCR选项
                "deskew": True,             # 自动校正倾斜页面
                "rotate_pages": True,       # 自动旋转页面
                "clean": False,             # 清理图像
                "output_type": "pdfa",      # 输出文件类型
                "jobs": 4                   # 并行处理任务数
            },
            "ui": {                         # 用户界面设置
                "theme": "system",          # 主题（跟随系统、亮色、暗色）
                "language": "zh_CN"         # 界面语言
            }
        }
        self.current_config = self.default_config.copy()
        self.load_config()
    
    def load_config(self):
        """
        从磁盘加载配置文件
        
        如果配置目录不存在，则创建该目录。
        如果配置文件存在，则读取并与默认配置合并。
        如果配置文件不存在或加载失败，则使用默认配置。
        """
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置，保留默认值
                    self._merge_config(self.current_config, loaded_config)
                self.logger.info("配置文件加载成功")
            except Exception as e:
                self.logger.error(f"加载配置文件出错: {e}")
        else:
            self.logger.info("配置文件不存在，使用默认配置")
            self.save_config()
    
    def save_config(self):
        """
        保存配置到磁盘
        
        将当前配置以JSON格式写入配置文件。
        如果保存过程中出现错误，将记录错误日志。
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_config, f, indent=2, ensure_ascii=False)
            self.logger.info("配置文件保存成功")
        except Exception as e:
            self.logger.error(f"保存配置文件出错: {e}")
    
    def _merge_config(self, target, source):
        """
        递归合并配置字典
        
        将source字典中的值合并到target字典中，保留原有结构。
        对于嵌套字典，递归合并内部结构。
        
        Args:
            target: 目标字典，合并结果将存储在此
            source: 源字典，其值将合并到目标字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value
    
    def get(self, key, default=None):
        """
        获取配置项值
        
        支持使用点号分隔的多级键名访问嵌套配置项。
        
        Args:
            key: 配置项键名，如'ui.theme'或'default_options.deskew'
            default: 如果配置项不存在，返回的默认值
        
        Returns:
            配置项的值，如果不存在则返回默认值
        """
        keys = key.split('.')
        value = self.current_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """
        设置配置项值
        
        支持使用点号分隔的多级键名设置嵌套配置项。
        设置后会自动保存配置到磁盘。
        
        Args:
            key: 配置项键名，如'ui.theme'或'default_options.deskew'
            value: 要设置的值
        """
        keys = key.split('.')
        target = self.current_config
        
        for i, k in enumerate(keys[:-1]):
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
        self.save_config()
    
    def add_recent_file(self, file_path):
        """
        添加最近使用的文件
        
        如果文件已在列表中，则将其移到列表首位。
        保留最近使用的10个文件。
        
        Args:
            file_path: 文件路径
        """
        recent_files = self.get('recent_files', [])
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        # 保留最近的10个文件
        self.set('recent_files', recent_files[:10])
    
    def add_recent_output_dir(self, dir_path):
        """
        添加最近使用的输出目录
        
        如果目录已在列表中，则将其移到列表首位。
        保留最近使用的10个目录。
        
        Args:
            dir_path: 目录路径
        """
        recent_dirs = self.get('recent_output_dirs', [])
        if dir_path in recent_dirs:
            recent_dirs.remove(dir_path)
        recent_dirs.insert(0, dir_path)
        # 保留最近的10个目录
        self.set('recent_output_dirs', recent_dirs[:10]) 