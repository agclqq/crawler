"""Word 转 PDF 转换工具"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional
from loguru import logger

try:
    from docx2pdf import convert as docx2pdf_convert
except ImportError:
    docx2pdf_convert = None


class WordToPdfConverter:
    """Word 文档转 PDF 转换器"""

    def __init__(self):
        """初始化转换器"""
        self._libreoffice_path = self._find_libreoffice()

    def _find_libreoffice(self) -> Optional[str]:
        """查找 LibreOffice 可执行文件路径

        Returns:
            LibreOffice 可执行文件路径，如果未找到则返回 None
        """
        # Windows 常见路径
        windows_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]

        # Linux/Mac 路径
        unix_paths = ["soffice", "/usr/bin/soffice", "/usr/local/bin/soffice"]

        # 检查系统路径中的 soffice
        if shutil.which("soffice"):
            return "soffice"

        # 检查 Windows 路径
        for path in windows_paths:
            if Path(path).exists():
                return path

        # 检查 Unix 路径
        for path in unix_paths:
            if Path(path).exists():
                return path

        return None

    def convert_with_libreoffice(
        self, word_path: str, output_dir: Optional[str] = None
    ) -> str:
        """使用 LibreOffice 将 Word 文档转换为 PDF

        Args:
            word_path: Word 文档路径
            output_dir: 输出目录，如果为 None 则使用 Word 文档所在目录

        Returns:
            生成的 PDF 文件路径

        Raises:
            RuntimeError: 当 LibreOffice 未安装或转换失败时
        """
        if not self._libreoffice_path:
            raise RuntimeError("LibreOffice 未安装，无法进行转换")

        word_file = Path(word_path)
        if not word_file.exists():
            raise FileNotFoundError(f"Word 文件不存在: {word_path}")

        # 确定输出目录
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = word_file.parent

        logger.info(f"使用 LibreOffice 转换: {word_path} -> {output_path}")

        try:
            # 使用 LibreOffice 命令行转换
            # --headless: 无界面模式
            # --convert-to pdf: 转换为 PDF
            # --outdir: 输出目录
            cmd = [
                self._libreoffice_path,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_path),
                str(word_file),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60, check=True
            )

            # 生成的 PDF 文件名
            pdf_file = output_path / f"{word_file.stem}.pdf"

            if pdf_file.exists():
                logger.info(f"PDF 文件已生成: {pdf_file}")
                return str(pdf_file)
            else:
                raise RuntimeError(f"PDF 文件未生成: {pdf_file}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("转换超时")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"LibreOffice 转换失败: {e.stderr}")

    def convert_with_docx2pdf(
        self, word_path: str, pdf_path: Optional[str] = None
    ) -> str:
        """使用 docx2pdf 库将 Word 文档转换为 PDF

        Args:
            word_path: Word 文档路径
            pdf_path: PDF 输出路径，如果为 None 则自动生成

        Returns:
            生成的 PDF 文件路径

        Raises:
            RuntimeError: 当 docx2pdf 未安装或转换失败时
        """
        if docx2pdf_convert is None:
            raise RuntimeError(
                "docx2pdf 库未安装，请运行: pip install docx2pdf"
            )

        word_file = Path(word_path)
        if not word_file.exists():
            raise FileNotFoundError(f"Word 文件不存在: {word_path}")

        # 确定输出路径
        if pdf_path:
            pdf_file = Path(pdf_path)
            pdf_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            pdf_file = word_file.parent / f"{word_file.stem}.pdf"

        logger.info(f"使用 docx2pdf 转换: {word_path} -> {pdf_file}")

        try:
            docx2pdf_convert(str(word_file), str(pdf_file))
            logger.info(f"PDF 文件已生成: {pdf_file}")
            return str(pdf_file)
        except Exception as e:
            raise RuntimeError(f"docx2pdf 转换失败: {e}")

    def convert(
        self,
        word_path: str,
        pdf_path: Optional[str] = None,
        prefer_libreoffice: bool = True,
    ) -> str:
        """将 Word 文档转换为 PDF（自动选择最佳方法）

        Args:
            word_path: Word 文档路径
            pdf_path: PDF 输出路径，如果为 None 则自动生成
            prefer_libreoffice: 是否优先使用 LibreOffice（默认 True）

        Returns:
            生成的 PDF 文件路径

        Raises:
            RuntimeError: 当所有转换方法都失败时
        """
        word_file = Path(word_path)
        if not word_file.exists():
            raise FileNotFoundError(f"Word 文件不存在: {word_path}")

        # 确定输出路径
        if pdf_path:
            pdf_file = Path(pdf_path)
        else:
            pdf_file = word_file.parent / f"{word_file.stem}.pdf"

        # 如果输出文件已存在，先删除
        if pdf_file.exists():
            logger.warning(f"PDF 文件已存在，将被覆盖: {pdf_file}")
            pdf_file.unlink()

        # 尝试转换方法
        methods = []

        if prefer_libreoffice and self._libreoffice_path:
            methods.append(("LibreOffice", self._convert_with_libreoffice_safe))
        elif self._libreoffice_path:
            methods.append(("LibreOffice", self._convert_with_libreoffice_safe))

        if docx2pdf_convert:
            methods.append(("docx2pdf", self._convert_with_docx2pdf_safe))

        if not methods:
            raise RuntimeError(
                "未找到可用的转换方法。请安装 LibreOffice 或 docx2pdf 库"
            )

        # 尝试每种方法
        last_error = None
        for method_name, method_func in methods:
            try:
                logger.info(f"尝试使用 {method_name} 进行转换...")
                if method_name == "LibreOffice":
                    # LibreOffice 需要输出目录
                    result = method_func(word_path, str(pdf_file.parent))
                    # 如果生成的文件名不同，重命名
                    generated_pdf = Path(result)
                    if generated_pdf != pdf_file:
                        generated_pdf.rename(pdf_file)
                    return str(pdf_file)
                else:
                    return method_func(word_path, str(pdf_file))
            except Exception as e:
                logger.warning(f"{method_name} 转换失败: {e}")
                last_error = e
                continue

        # 所有方法都失败
        raise RuntimeError(
            f"所有转换方法都失败。最后一个错误: {last_error}"
        )

    def _convert_with_libreoffice_safe(
        self, word_path: str, output_dir: str
    ) -> str:
        """LibreOffice 转换的安全包装（用于异常处理）"""
        return self.convert_with_libreoffice(word_path, output_dir)

    def _convert_with_docx2pdf_safe(
        self, word_path: str, pdf_path: str
    ) -> str:
        """docx2pdf 转换的安全包装（用于异常处理）"""
        return self.convert_with_docx2pdf(word_path, pdf_path)

