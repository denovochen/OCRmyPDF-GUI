#!/usr/bin/env python3
"""
OCRmyPDF GUI 启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 导入主模块
from src.main import main

if __name__ == "__main__":
    main() 