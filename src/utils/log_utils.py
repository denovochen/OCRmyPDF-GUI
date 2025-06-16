import logging
import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal

class QtLogHandler(logging.Handler, QObject):
    """Qt日志处理器，将日志消息发送到Qt信号"""
    
    log_message = Signal(str, int)  # 参数：消息文本，日志级别
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setFormatter(logging.Formatter('%(message)s'))
    
    def emit(self, record):
        msg = self.format(record)
        self.log_message.emit(msg, record.levelno)

class LogUtils:
    """日志工具类，提供日志相关的功能"""
    
    @staticmethod
    def setup_logging(log_file=None, console=True, level=logging.INFO):
        """
        设置日志系统
        
        Args:
            log_file: 日志文件路径，如果为None则不输出到文件
            console: 是否输出到控制台
            level: 日志级别
        """
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 添加控制台处理器
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        if log_file:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    @staticmethod
    def get_qt_handler():
        """
        获取Qt日志处理器
        
        Returns:
            QtLogHandler: Qt日志处理器实例
        """
        handler = QtLogHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        return handler
    
    @staticmethod
    def add_qt_handler(logger_name=None):
        """
        添加Qt日志处理器到指定的日志记录器
        
        Args:
            logger_name: 日志记录器名称，如果为None则使用根日志记录器
            
        Returns:
            QtLogHandler: 添加的Qt日志处理器
        """
        logger = logging.getLogger(logger_name)
        handler = LogUtils.get_qt_handler()
        logger.addHandler(handler)
        return handler 