# OCRmyPDF GUI

OCRmyPDF-GUI是一个图形用户界面，让[OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF)命令行工具的强大功能变得简单易用。通过直观的界面，您可以为扫描的PDF文件添加文本层，使其可搜索和可复制粘贴，而无需记忆复杂的命令行参数。

![OCRmyPDF-GUI截图](docs/images/screenshot.png)

## 主要特点

- **简洁直观的图形界面**：无需命令行知识，即可使用OCRmyPDF的全部功能
- **批量处理**：一次处理多个PDF文件，并显示详细进度
- **拖放支持**：直接拖放文件到程序窗口
- **多语言OCR支持**：支持100多种语言的文本识别
- **智能文件命名**：支持多种输出文件命名选项，包括自定义前缀
- **高级OCR选项**：自动校正倾斜页面、自动旋转、清理图像等
- **配置管理**：保存和加载常用OCR配置
- **详细状态反馈**：提供处理状态和结果的清晰反馈

## 功能演示

```
OCRmyPDF-GUI提供以下功能：

✓ 添加OCR文本层到PDF文件
✓ 处理单个或批量PDF文件
✓ 多语言文档识别
✓ 自动校正倾斜页面
✓ 自动旋转页面
✓ 优化输出文件大小
✓ 自定义输出文件命名
✓ 保存常用处理配置
```

## 安装要求

- Python 3.7+
- OCRmyPDF
- Tesseract OCR
- PySide6 (Qt for Python)

## 安装步骤

### 1. 安装OCRmyPDF和其依赖

```bash
# macOS
brew install ocrmypdf

# Ubuntu/Debian
sudo apt install ocrmypdf

# Fedora
sudo dnf install ocrmypdf

# Windows (WSL)
sudo apt install ocrmypdf

# 或使用pip
pip install ocrmypdf
```

### 2. 安装GUI依赖

```bash
pip install PySide6
```

### 3. 克隆本仓库

```bash
git clone https://github.com/yourusername/OCRmyPDF-GUI.git
cd OCRmyPDF-GUI
```

### 4. 运行应用程序

```bash
python run.py
```

## 安装Tesseract语言包

默认情况下，OCRmyPDF只安装英语语言包。要使用其他语言进行OCR，需要安装额外的语言包：

### macOS

```bash
# 安装所有语言包
brew install tesseract-lang

# 或者手动安装特定语言包
# 1. 下载语言包文件，例如简体中文：
# https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata
# 2. 复制到Tesseract的tessdata目录：
# sudo cp chi_sim.traineddata /opt/homebrew/share/tessdata/
# 或
# sudo cp chi_sim.traineddata /usr/local/share/tessdata/
```

### Ubuntu/Debian

```bash
# 安装特定语言包，例如简体中文：
sudo apt-get install tesseract-ocr-chi-sim

# 查看所有可用语言包：
apt-cache search tesseract-ocr
```

### Fedora

```bash
# 安装特定语言包，例如简体中文：
sudo dnf install tesseract-langpack-chi_sim

# 查看所有可用语言包：
dnf search tesseract
```

### Windows

1. 从以下网址下载所需语言包文件：
   https://github.com/tesseract-ocr/tessdata/

2. 将下载的`.traineddata`文件放置在Tesseract安装目录的tessdata文件夹中，通常位于：
   `C:\Program Files\Tesseract-OCR\tessdata`

### 常用语言代码

- `eng` - 英语
- `chi_sim` - 简体中文
- `chi_tra` - 繁体中文
- `jpn` - 日语
- `kor` - 韩语
- `fra` - 法语
- `deu` - 德语
- `rus` - 俄语
- `spa` - 西班牙语
- `ita` - 意大利语

更多信息请参考：[OCRmyPDF语言包文档](https://ocrmypdf.readthedocs.io/en/latest/languages.html)

## 项目结构

```
OCRmyPDF-GUI/
├── src/                      # 源代码
│   ├── core/                 # 核心功能
│   │   ├── config.py         # 配置管理
│   │   └── ocr_engine.py     # OCR引擎封装
│   ├── gui/                  # 图形界面
│   │   ├── main_window.py    # 主窗口
│   │   ├── batch_dialog.py   # 批量处理对话框
│   │   └── settings.py       # 设置对话框
│   └── utils/                # 工具函数
│       └── file_utils.py     # 文件操作工具
├── run.py                    # 启动脚本
└── README.md                 # 项目说明
```

## 开发计划

- [ ] 高级OCR选项扩展
- [ ] 多语言界面支持
- [ ] 暗黑模式
- [ ] 自定义输出文件名模板
- [ ] 处理历史记录
- [ ] 集成PDF预览功能

## 贡献指南

我们欢迎并感谢所有形式的贡献！以下是一些参与项目的方式：

1. **提交问题和建议**：如果您发现bug或有改进建议，请[创建issue](https://github.com/yourusername/OCRmyPDF-GUI/issues/new)。

2. **提交代码**：
   - Fork 这个仓库
   - 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
   - 提交您的更改 (`git commit -m 'Add some amazing feature'`)
   - 推送到分支 (`git push origin feature/amazing-feature`)
   - 开启一个Pull Request

3. **改进文档**：帮助我们完善文档，包括README、安装说明或用户指南。

请确保您的代码符合项目的代码风格，并添加适当的测试。

## 关于OCRmyPDF

本项目是[OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF)命令行工具的图形界面封装。OCRmyPDF是一个强大的工具，可以为扫描的PDF文件添加OCR文本层，使其可搜索和可复制粘贴。OCRmyPDF-GUI旨在让更多不熟悉命令行的用户能够轻松使用OCRmyPDF的强大功能。

## 许可证

本项目采用[Mozilla Public License 2.0 (MPL-2.0)](https://www.mozilla.org/en-US/MPL/2.0/)许可证，与OCRmyPDF原项目保持一致。

## 致谢

- [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) - 强大的OCR工具
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR引擎
- [Qt for Python (PySide6)](https://wiki.qt.io/Qt_for_Python) - GUI框架 