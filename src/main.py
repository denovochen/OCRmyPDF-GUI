import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLocale

from src.gui.main_window import MainWindow
from src.core.config import Config

def setup_logging():
    """设置日志系统"""
    log_dir = Path.home() / ".ocrmypdf-gui"
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / "ocrmypdf-gui.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

def main():
    """程序入口"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("启动 OCRmyPDF GUI")
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("OCRmyPDF GUI")
    app.setOrganizationName("OCRmyPDF")
    
    # 加载配置
    config = Config()
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 