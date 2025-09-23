"""
多格式文档处理器
支持PDF、Word、Excel、PowerPoint、CSV、图像等多种格式的文档处理
"""

import os
import tempfile
import logging
from typing import Dict, Any, List
from pathlib import Path

from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.readers.base import BaseReader

logger = logging.getLogger(__name__)

class MultiFormatProcessor:
    """多格式文档处理器"""
    
    def __init__(self):
        """初始化多格式处理器"""
        self.supported_formats = {
            '.pdf': 'PDF文档',
            '.docx': 'Word文档',
            '.xlsx': 'Excel文件',
            '.xls': 'Excel文件',
            '.pptx': 'PowerPoint文件',
            '.ppt': 'PowerPoint文件',
            '.csv': 'CSV数据文件',
            '.txt': '文本文件',
            '.md': 'Markdown文件',
            '.jpg': 'JPEG图像',
            '.jpeg': 'JPEG图像',
            '.png': 'PNG图像'
        }
        
        # 设置自定义文件提取器
        self.file_extractors = self._setup_file_extractors()
        
    def _setup_file_extractors(self) -> Dict[str, BaseReader]:
        """设置自定义文件提取器"""
        extractors = {}
        
        # CSV文件提取器
        extractors['.csv'] = CSVReader()
        
        # Excel文件提取器
        extractors['.xlsx'] = ExcelReader()
        extractors['.xls'] = ExcelReader()
        
        # 图像文件提取器（用于OCR）
        extractors['.jpg'] = ImageReader()
        extractors['.jpeg'] = ImageReader()
        extractors['.png'] = ImageReader()
        
        return extractors
    
    def process_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """
        处理上传的文件，支持多种格式
        """
        try:
            # 获取文件扩展名
            file_ext = self._get_file_extension(uploaded_file.name)
            file_type = self.supported_formats.get(file_ext, '未知格式')
            
            logger.info(f"开始处理 {file_type}: {uploaded_file.name}")
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # 使用SimpleDirectoryReader处理文件
                reader = SimpleDirectoryReader(
                    input_files=[tmp_path],
                    file_extractor=self.file_extractors
                )
                documents = reader.load_data()
                
                # 提取详细内容
                detailed_content = self._extract_detailed_content(tmp_path, file_ext)
                
                # 构建结果
                result = {
                    'filename': uploaded_file.name,
                    'file_type': file_type,
                    'file_extension': file_ext,
                    'documents': documents,
                    'detailed_content': detailed_content,
                    'page_count': len(detailed_content.get('pages', [])),
                    'total_text_length': len(' '.join([doc.text for doc in documents])),
                    'processing_method': 'multi_format_processor'
                }
                
                logger.info(f"✅ 成功处理 {file_type}: {uploaded_file.name}")
                return result
                
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logger.error(f"❌ 处理文件 {uploaded_file.name} 时出错: {str(e)}")
            raise e

    def get_processing_stats(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成多格式文件的处理统计信息
        """
        stats = {
            'filename': processed_data.get('filename', 'unknown'),
            'page_count': processed_data.get('page_count', 0),
            'text_length': processed_data.get('total_text_length', 0),
            'tables_found': 0,
            'images_found': 0,
            'file_type': processed_data.get('file_type', 'unknown')
        }

        try:
            # 根据文件类型计算统计信息
            if 'detailed_content' in processed_data:
                content = processed_data['detailed_content']

                if 'pages' in content:
                    for page in content['pages']:
                        # 计算表格数量（对于Excel/CSV文件）
                        if 'data' in page and isinstance(page['data'], list):
                            stats['tables_found'] += 1

                        # 计算图像数量
                        if 'images' in page:
                            if isinstance(page['images'], int):
                                stats['images_found'] += page['images']
                            elif isinstance(page['images'], list):
                                stats['images_found'] += len(page['images'])

                # 从元数据获取额外信息
                if 'metadata' in content:
                    metadata = content['metadata']
                    if 'total_rows' in metadata:
                        stats['data_rows'] = metadata['total_rows']
                    if 'total_columns' in metadata:
                        stats['data_columns'] = metadata['total_columns']
                    if 'total_sheets' in metadata:
                        stats['excel_sheets'] = metadata['total_sheets']

        except Exception as e:
            logger.error(f"Error calculating multi-format stats: {str(e)}")

        return stats
    
    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return Path(filename).suffix.lower()
    
    def _extract_detailed_content(self, file_path: str, file_ext: str) -> Dict[str, Any]:
        """提取文件的详细内容"""
        try:
            if file_ext == '.pdf':
                return self._extract_pdf_content(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return self._extract_excel_content(file_path)
            elif file_ext == '.csv':
                return self._extract_csv_content(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png']:
                return self._extract_image_content(file_path)
            else:
                # 对于其他格式，返回基本信息
                return {
                    'pages': [{'text': '文件内容已通过LlamaIndex处理'}],
                    'metadata': {'file_type': file_ext}
                }
                
        except Exception as e:
            logger.warning(f"提取详细内容失败: {str(e)}")
            return {
                'pages': [{'text': '无法提取详细内容'}],
                'metadata': {'error': str(e)}
            }
    
    def _extract_pdf_content(self, file_path: str) -> Dict[str, Any]:
        """提取PDF内容"""
        try:
            import pdfplumber
            
            pages = []
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    tables = page.extract_tables()
                    
                    pages.append({
                        'page_number': i + 1,
                        'text': page_text,
                        'tables': tables,
                        'width': page.width,
                        'height': page.height
                    })
            
            return {
                'pages': pages,
                'metadata': {
                    'total_pages': len(pages),
                    'file_type': 'pdf'
                }
            }
            
        except Exception as e:
            logger.error(f"PDF内容提取失败: {str(e)}")
            return {'pages': [], 'metadata': {'error': str(e)}}
    
    def _extract_excel_content(self, file_path: str) -> Dict[str, Any]:
        """提取Excel内容"""
        try:
            import pandas as pd
            
            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            sheets_data = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # 转换为文本描述
                sheet_text = f"工作表: {sheet_name}\n"
                sheet_text += f"行数: {len(df)}, 列数: {len(df.columns)}\n"
                sheet_text += f"列名: {', '.join(df.columns.astype(str))}\n"
                
                # 添加前几行数据作为示例
                if len(df) > 0:
                    sheet_text += "数据示例:\n"
                    sheet_text += df.head().to_string()
                
                sheets_data.append({
                    'sheet_name': sheet_name,
                    'text': sheet_text,
                    'data': df.to_dict('records')[:100],  # 限制数据量
                    'shape': df.shape
                })
            
            return {
                'pages': sheets_data,
                'metadata': {
                    'total_sheets': len(sheets_data),
                    'file_type': 'excel'
                }
            }
            
        except Exception as e:
            logger.error(f"Excel内容提取失败: {str(e)}")
            return {'pages': [], 'metadata': {'error': str(e)}}
    
    def _extract_csv_content(self, file_path: str) -> Dict[str, Any]:
        """提取CSV内容"""
        try:
            import pandas as pd
            
            df = pd.read_csv(file_path)
            
            # 生成文本描述
            csv_text = f"CSV文件内容\n"
            csv_text += f"行数: {len(df)}, 列数: {len(df.columns)}\n"
            csv_text += f"列名: {', '.join(df.columns.astype(str))}\n"
            csv_text += "数据示例:\n"
            csv_text += df.head(10).to_string()
            
            return {
                'pages': [{
                    'text': csv_text,
                    'data': df.to_dict('records')[:1000],  # 限制数据量
                    'shape': df.shape
                }],
                'metadata': {
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'file_type': 'csv'
                }
            }
            
        except Exception as e:
            logger.error(f"CSV内容提取失败: {str(e)}")
            return {'pages': [], 'metadata': {'error': str(e)}}
    
    def _extract_image_content(self, file_path: str) -> Dict[str, Any]:
        """提取图像内容（OCR）"""
        try:
            from PIL import Image
            
            # 获取图像基本信息
            with Image.open(file_path) as img:
                width, height = img.size
                mode = img.mode
                format_name = img.format
            
            # 简单的图像描述
            image_text = f"图像文件\n"
            image_text += f"尺寸: {width} x {height}\n"
            image_text += f"模式: {mode}\n"
            image_text += f"格式: {format_name}\n"
            image_text += "注意: 如需OCR文字识别，请考虑使用专门的OCR工具"
            
            return {
                'pages': [{
                    'text': image_text,
                    'image_info': {
                        'width': width,
                        'height': height,
                        'mode': mode,
                        'format': format_name
                    }
                }],
                'metadata': {
                    'file_type': 'image',
                    'dimensions': f"{width}x{height}"
                }
            }
            
        except Exception as e:
            logger.error(f"图像内容提取失败: {str(e)}")
            return {'pages': [], 'metadata': {'error': str(e)}}


class CSVReader(BaseReader):
    """CSV文件读取器"""
    
    def load_data(self, file, extra_info=None):
        try:
            import pandas as pd
            df = pd.read_csv(file)
            
            # 转换为文本
            text = f"CSV数据 ({len(df)}行 x {len(df.columns)}列)\n"
            text += f"列名: {', '.join(df.columns)}\n\n"
            text += df.to_string()
            
            return [Document(text=text, extra_info=extra_info or {})]
        except Exception as e:
            return [Document(text=f"CSV读取错误: {str(e)}", extra_info=extra_info or {})]


class ExcelReader(BaseReader):
    """Excel文件读取器"""
    
    def load_data(self, file, extra_info=None):
        try:
            import pandas as pd
            excel_file = pd.ExcelFile(file)
            
            all_text = ""
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file, sheet_name=sheet_name)
                sheet_text = f"\n工作表: {sheet_name}\n"
                sheet_text += f"({len(df)}行 x {len(df.columns)}列)\n"
                sheet_text += df.to_string()
                all_text += sheet_text + "\n"
            
            return [Document(text=all_text, extra_info=extra_info or {})]
        except Exception as e:
            return [Document(text=f"Excel读取错误: {str(e)}", extra_info=extra_info or {})]


class ImageReader(BaseReader):
    """图像文件读取器"""
    
    def load_data(self, file, extra_info=None):
        try:
            from PIL import Image
            
            with Image.open(file) as img:
                text = f"图像文件: {img.format} {img.size[0]}x{img.size[1]} {img.mode}"
                
            return [Document(text=text, extra_info=extra_info or {})]
        except Exception as e:
            return [Document(text=f"图像读取错误: {str(e)}", extra_info=extra_info or {})]
