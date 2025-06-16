import logging
import subprocess
from pathlib import Path
import sys
import os

class OCREngine:
    """
    OCR引擎类
    
    封装OCRmyPDF命令行工具的调用，提供PDF文件的OCR处理功能。
    负责检测OCRmyPDF和Tesseract的可用性、获取支持的语言列表、
    处理单个文件和批量处理多个文件，以及处理各种错误状态。
    
    属性:
        logger: 日志记录器
        available_languages: 系统中可用的Tesseract语言包列表
        last_error: 最近一次处理错误的详细信息
    """
    
    def __init__(self):
        """
        初始化OCR引擎
        
        检查OCRmyPDF命令行工具是否可用，并获取系统中已安装的Tesseract语言包列表。
        如果OCRmyPDF不可用，将记录错误并将可用语言列表设为空。
        """
        self.logger = logging.getLogger(__name__)
        # 检查命令行工具是否可用
        try:
            result = subprocess.run(
                ["ocrmypdf", "--version"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            if result.returncode == 0:
                self.logger.info(f"OCRmyPDF命令行工具可用: {result.stdout.strip()}")
                # 获取支持的语言列表
                self.available_languages = self.get_available_languages()
                self.logger.info(f"可用的OCR语言: {', '.join(self.available_languages)}")
            else:
                self.logger.warning("OCRmyPDF命令行工具返回错误")
                self.available_languages = []
        except FileNotFoundError:
            self.logger.error("OCRmyPDF命令行工具未找到")
            self.available_languages = []
    
    def get_available_languages(self):
        """
        获取系统中已安装的Tesseract语言包列表
        
        通过调用tesseract命令的--list-langs选项获取系统中已安装的所有语言包。
        
        Returns:
            list: 已安装的语言代码列表，如果获取失败则返回空列表
        """
        try:
            result = subprocess.run(
                ["tesseract", "--list-langs"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                # 解析输出，跳过第一行（标题行）
                languages = result.stdout.strip().split('\n')[1:]
                return [lang.strip() for lang in languages]
            return []
        except Exception as e:
            self.logger.error(f"获取语言列表失败: {e}")
            return []

    def get_language_name(self, lang_code):
        """
        获取语言代码对应的显示名称
        
        将Tesseract语言代码转换为用户友好的显示名称，同时显示中文和英文名称。
        
        Args:
            lang_code (str): 语言代码，如'eng'、'chi_sim'等
            
        Returns:
            str: 语言的显示名称，如'英语 (English)'、'简体中文 (Chinese Simplified)'等
                 如果没有对应的显示名称，则返回原始语言代码
        """
        language_names = {
            'eng': '英语 (English)',
            'chi_sim': '简体中文 (Chinese Simplified)',
            'chi_tra': '繁体中文 (Chinese Traditional)',
            'jpn': '日语 (Japanese)',
            'kor': '韩语 (Korean)',
            'fra': '法语 (French)',
            'deu': '德语 (German)',
            'rus': '俄语 (Russian)',
            'spa': '西班牙语 (Spanish)',
            'ita': '意大利语 (Italian)',
            'por': '葡萄牙语 (Portuguese)',
            'nld': '荷兰语 (Dutch)',
            'ara': '阿拉伯语 (Arabic)',
            'hin': '印地语 (Hindi)',
            'vie': '越南语 (Vietnamese)',
            'tha': '泰语 (Thai)',
            'tur': '土耳其语 (Turkish)',
            'heb': '希伯来语 (Hebrew)',
            'swe': '瑞典语 (Swedish)',
            'fin': '芬兰语 (Finnish)',
            'dan': '丹麦语 (Danish)',
            'nor': '挪威语 (Norwegian)',
            'pol': '波兰语 (Polish)',
            'ukr': '乌克兰语 (Ukrainian)',
            'ces': '捷克语 (Czech)',
            'slk': '斯洛伐克语 (Slovak)',
            'hun': '匈牙利语 (Hungarian)',
            'ron': '罗马尼亚语 (Romanian)',
            'bul': '保加利亚语 (Bulgarian)',
            'ell': '希腊语 (Greek)',
            'ind': '印度尼西亚语 (Indonesian)',
            'msa': '马来语 (Malay)',
            'cat': '加泰罗尼亚语 (Catalan)',
            'lav': '拉脱维亚语 (Latvian)',
            'lit': '立陶宛语 (Lithuanian)',
            'est': '爱沙尼亚语 (Estonian)'
        }
        return language_names.get(lang_code, lang_code)

    def process_file(self, input_file, output_file, options=None):
        """
        使用OCRmyPDF处理单个PDF文件
        
        处理前会检查输入文件是否存在、是否可读，以及输出目录是否可写。
        会自动检测文件是否已经OCR过，并返回相应的状态码。
        
        Args:
            input_file (str): 输入PDF文件路径
            output_file (str): 输出PDF文件路径
            options (dict): OCR处理选项，包括language、deskew、rotate_pages、clean、optimize等
        
        Returns:
            int: 处理结果状态码
                0 - 处理失败
                1 - 处理成功
                2 - 文件已有文本层（已OCR过）
        """
        if options is None:
            options = {}
            
        self.logger.info(f"处理文件: {input_file} -> {output_file}")
        
        # 检查输入文件是否存在
        if not Path(input_file).exists():
            self.logger.error(f"输入文件不存在: {input_file}")
            return 0
            
        # 检查输入文件是否可读
        if not os.access(input_file, os.R_OK):
            self.logger.error(f"输入文件不可读: {input_file}")
            return 0
            
        # 检查输出目录是否可写
        output_dir = Path(output_file).parent
        if not os.access(output_dir, os.W_OK):
            self.logger.error(f"输出目录不可写: {output_dir}")
            return 0
        
        # 处理文件
        result = self._process_file_internal(input_file, output_file, options, force_ocr=False)
        
        # 如果失败且错误是因为已有文本层，返回特殊状态码
        if not result and self._last_error_is_existing_text():
            self.logger.info(f"文件 {input_file} 已有文本层，无需OCR处理")
            return 2
        
        # 返回常规状态码
        return 1 if result else 0
    
    def _last_error_is_existing_text(self):
        """
        检查上次错误是否因为PDF已有文本层
        
        通过分析最近一次OCRmyPDF命令的错误输出，判断错误是否是因为文件已经有文本层。
        
        Returns:
            bool: 如果错误是因为文件已有文本层，则返回True，否则返回False
        """
        if hasattr(self, 'last_error') and isinstance(self.last_error, str):
            return "page already has text" in self.last_error
        return False
    
    def _process_file_internal(self, input_file, output_file, options, force_ocr=False):
        """
        内部方法：使用OCRmyPDF处理单个文件
        
        构建OCRmyPDF命令行参数，并执行命令进行OCR处理。
        
        Args:
            input_file (str): 输入PDF文件路径
            output_file (str): 输出PDF文件路径
            options (dict): OCR选项，包括language、deskew、rotate_pages、clean、optimize等
            force_ocr (bool): 是否强制OCR处理，即使文件已有文本层
        
        Returns:
            bool: 处理是否成功
        """
        # 构建命令行参数
        cmd = ["ocrmypdf"]
        
        # 添加优化选项（必须在其他选项之前）
        if options.get('optimize', False):
            cmd.extend(["-O", "1"])  # 使用1级优化
            self.logger.info("启用优化输出文件大小")
        
        # 添加语言选项
        lang = options.get('language', 'eng')
        if lang in self.available_languages:
            cmd.extend(["-l", lang])
            self.logger.info(f"使用语言: {lang}")
        else:
            self.logger.warning(f"不支持的语言: {lang}，使用默认语言(eng)")
            cmd.extend(["-l", "eng"])
        
        # 添加其他选项
        if options.get('deskew', False):
            cmd.append("--deskew")
            self.logger.info("启用自动校正倾斜页面")
            
        if options.get('rotate_pages', False):
            cmd.append("--rotate-pages")
            self.logger.info("启用自动旋转页面")
            
        if options.get('clean', False):
            cmd.append("--clean")
            self.logger.info("启用清理图像")
            
        if 'jobs' in options:
            cmd.extend(["--jobs", str(options['jobs'])])
            self.logger.info(f"使用 {options['jobs']} 个处理线程")
            
        if 'output_type' in options:
            cmd.extend(["--output-type", options['output_type']])
            self.logger.info(f"输出类型: {options['output_type']}")
            
        # 添加强制OCR选项
        if force_ocr:
            cmd.append("--force-ocr")
            self.logger.info("启用强制OCR处理")
        
        # 添加输入和输出文件（必须在最后）
        cmd.extend([str(input_file), str(output_file)])
        
        # 执行命令
        self.logger.debug(f"执行命令: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                self.logger.info("OCRmyPDF命令执行成功")
                return True
            else:
                self.last_error = result.stderr
                self.logger.error(f"OCRmyPDF命令执行失败: {result.stderr}")
                self.logger.error(f"命令输出: {result.stdout}")
                return False
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"执行OCRmyPDF命令时出错: {e}")
            return False
    
    def process_batch(self, file_list, output_dir, options=None, progress_callback=None):
        """
        批量处理多个PDF文件
        
        对多个PDF文件进行OCR处理，并可通过回调函数报告处理进度。
        支持自定义文件命名规则，包括添加前缀和后缀。
        
        Args:
            file_list (list): 输入PDF文件路径列表
            output_dir (str): 输出目录路径
            options (dict): OCR选项，除了process_file支持的选项外，还支持file_prefix和file_suffix
            progress_callback (callable): 进度回调函数，接收参数(current, total, file, success)
                                          current - 当前处理的文件索引（从1开始）
                                          total - 总文件数
                                          file - 当前处理的文件路径
                                          success - 处理是否成功（包括已OCR过）
            
        Returns:
            dict: 处理结果字典，键为输入文件路径，值为处理结果状态码（0-失败，1-成功，2-已OCR过）
        """
        results = {}
        total = len(file_list)
        
        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 获取文件命名选项
        file_prefix = options.get("file_prefix", "")
        file_suffix = options.get("file_suffix", "_ocr")
        
        for i, input_file in enumerate(file_list):
            input_path = Path(input_file)
            # 使用前缀和后缀构建输出文件名
            output_file = output_path / f"{file_prefix}{input_path.stem}{file_suffix}{input_path.suffix}"
            
            self.logger.info(f"处理文件 {i+1}/{total}: {input_file}")
            result_code = self.process_file(input_file, output_file, options)
            results[input_file] = result_code
            
            if progress_callback:
                # 对于回调，我们将状态码2（已OCR过）也视为"成功"，只是一种特殊的成功情况
                success = result_code > 0
                progress_callback(i + 1, total, input_file, success)
        
        return results 