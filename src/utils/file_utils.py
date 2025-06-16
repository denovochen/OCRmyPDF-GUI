import os
import shutil
from pathlib import Path
import logging

class FileUtils:
    """
    文件工具类
    
    提供文件和目录操作的通用工具方法，包括目录创建、文件验证、
    文件搜索、文件大小计算和文件复制等功能。
    所有方法均为静态方法，可直接通过类名调用，无需实例化。
    
    主要功能:
        - 目录创建和验证
        - PDF文件验证
        - 目录内PDF文件搜索
        - 文件大小格式化
        - 文件复制
    """
    
    @staticmethod
    def ensure_dir(dir_path):
        """
        确保目录存在，如果不存在则创建
        
        使用pathlib创建目录，支持创建多级目录结构。
        如果目录已存在，则不会引发错误。
        
        Args:
            dir_path (str or Path): 要创建的目录路径
            
        Returns:
            bool: 如果目录创建成功或已存在则返回True，创建失败则返回False
        """
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"创建目录失败: {e}")
            return False
    
    @staticmethod
    def is_valid_pdf(file_path):
        """
        检查文件是否是有效的PDF文件
        
        检查包含三个步骤:
        1. 检查文件是否存在
        2. 检查文件扩展名是否为.pdf (不区分大小写)
        3. 检查文件头部是否包含PDF标识 (%PDF-)
        
        Args:
            file_path (str or Path): 要检查的文件路径
            
        Returns:
            bool: 如果文件是有效的PDF文件则返回True，否则返回False
        """
        if not Path(file_path).exists():
            return False
        
        # 简单检查文件扩展名
        if not str(file_path).lower().endswith('.pdf'):
            return False
        
        # 检查文件头部是否包含PDF标识
        try:
            with open(file_path, 'rb') as f:
                header = f.read(5)
                return header == b'%PDF-'
        except Exception:
            return False
    
    @staticmethod
    def get_pdf_files_in_dir(dir_path, recursive=False):
        """
        获取目录中的所有PDF文件
        
        搜索指定目录中的所有PDF文件，可选择是否递归搜索子目录。
        使用is_valid_pdf方法验证每个找到的PDF文件。
        
        Args:
            dir_path (str or Path): 要搜索的目录路径
            recursive (bool): 是否递归搜索子目录，默认为False
            
        Returns:
            list: 包含所有找到的PDF文件绝对路径的列表，如果目录不存在或不是目录则返回空列表
        """
        pdf_files = []
        dir_path = Path(dir_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return pdf_files
        
        if recursive:
            # 递归搜索目录及其所有子目录
            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_path = Path(root) / file
                    if FileUtils.is_valid_pdf(file_path):
                        pdf_files.append(str(file_path))
        else:
            # 只搜索当前目录，不包括子目录
            for file in dir_path.iterdir():
                if file.is_file() and FileUtils.is_valid_pdf(file):
                    pdf_files.append(str(file))
        
        return pdf_files
    
    @staticmethod
    def get_file_size_str(file_path):
        """
        获取文件大小的人类可读字符串表示
        
        将文件大小从字节转换为更易读的单位（B, KB, MB, GB, TB, PB）。
        使用1024作为转换基数，保留一位小数。
        
        Args:
            file_path (str or Path): 文件路径
            
        Returns:
            str: 格式化的文件大小字符串，如 "1.2 MB"，如果文件不存在或发生错误则返回"未知大小"
        """
        try:
            size = Path(file_path).stat().st_size
            
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
                
            return f"{size:.1f} PB"
        except Exception:
            return "未知大小"
    
    @staticmethod
    def copy_file(src, dst):
        """
        复制文件，保留元数据
        
        使用shutil.copy2复制文件，该方法会尝试保留文件的元数据
        （如创建时间、修改时间、访问时间、权限等）。
        
        Args:
            src (str or Path): 源文件路径
            dst (str or Path): 目标文件路径
            
        Returns:
            bool: 复制成功则返回True，失败则返回False
        """
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logging.error(f"复制文件失败: {e}")
            return False 