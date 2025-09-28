"""
简化的文档处理器
专注于PDF文档的文本提取和预处理
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from llama_index.core import Document
from llama_index.readers.file import PDFReader
import pdfplumber

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """简化的文档处理器"""
    
    def __init__(self):
        self.pdf_reader = PDFReader()
    
    def process_file(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        处理文件并提取内容
        
        Args:
            file_path: 文件路径
            filename: 文件名
            
        Returns:
            处理结果字典
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 检查文件类型
            if not filename.lower().endswith('.pdf'):
                raise ValueError("目前只支持PDF文件")
            
            # 使用LlamaIndex提取文档
            documents = self.pdf_reader.load_data(Path(file_path))
            
            # 使用pdfplumber提取详细内容
            detailed_content = self._extract_detailed_content(file_path)
            
            # 添加元数据
            for i, doc in enumerate(documents):
                doc.metadata.update({
                    'filename': filename,
                    'page_number': i + 1,
                    'source': 'pdf_processor'
                })
            
            result = {
                'filename': filename,
                'documents': documents,
                'detailed_content': detailed_content,
                'page_count': len(detailed_content['pages']),
                'total_text_length': sum(len(doc.text) for doc in documents),
                'processing_method': 'simple_pdf_processor'
            }
            
            logger.info(f"成功处理文档: {filename}, 页数: {result['page_count']}")
            return result
            
        except Exception as e:
            logger.error(f"处理文档失败 {filename}: {str(e)}")
            raise
    
    def _extract_detailed_content(self, pdf_path: str) -> Dict[str, Any]:
        """
        使用pdfplumber提取详细内容
        """
        content = {
            'pages': [],
            'metadata': {},
            'total_pages': 0
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                content['metadata'] = pdf.metadata or {}
                content['total_pages'] = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    page_content = {
                        'page_number': i + 1,
                        'text': page.extract_text() or '',
                        'tables': [],
                        'images': len(page.images),
                        'width': page.width,
                        'height': page.height
                    }
                    
                    # 提取表格
                    tables = page.extract_tables()
                    if tables:
                        for j, table in enumerate(tables):
                            if table and len(table) > 0:
                                page_content['tables'].append({
                                    'table_id': f"page_{i+1}_table_{j+1}",
                                    'data': table,
                                    'rows': len(table),
                                    'cols': len(table[0]) if table[0] else 0
                                })
                    
                    content['pages'].append(page_content)
                    
        except Exception as e:
            logger.error(f"提取详细内容失败: {str(e)}")
            raise
        
        return content
    
    def extract_text_chunks(self, documents: List[Document], chunk_size: int = 1024, chunk_overlap: int = 200) -> List[Document]:
        """
        将文档分块处理
        
        Args:
            documents: 文档列表
            chunk_size: 块大小
            chunk_overlap: 重叠大小
            
        Returns:
            分块后的文档列表
        """
        from llama_index.core.text_splitter import TokenTextSplitter
        
        text_splitter = TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        chunked_docs = []
        for doc in documents:
            chunks = text_splitter.split_text(doc.text)
            for i, chunk in enumerate(chunks):
                chunk_doc = Document(
                    text=chunk,
                    metadata={
                        **doc.metadata,
                        'chunk_id': i,
                        'total_chunks': len(chunks)
                    }
                )
                chunked_docs.append(chunk_doc)
        
        logger.info(f"文档分块完成: {len(documents)} -> {len(chunked_docs)} 块")
        return chunked_docs
    
    def validate_file(self, file_path: str, max_size: int = 50 * 1024 * 1024) -> bool:
        """
        验证文件
        
        Args:
            file_path: 文件路径
            max_size: 最大文件大小（字节）
            
        Returns:
            是否有效
        """
        try:
            path = Path(file_path)
            
            # 检查文件是否存在
            if not path.exists():
                logger.error(f"文件不存在: {file_path}")
                return False
            
            # 检查文件大小
            file_size = path.stat().st_size
            if file_size > max_size:
                logger.error(f"文件过大: {file_size} > {max_size}")
                return False
            
            # 检查文件扩展名
            if not path.suffix.lower() == '.pdf':
                logger.error(f"不支持的文件类型: {path.suffix}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"文件验证失败: {str(e)}")
            return False
    
    def get_document_summary(self, documents: List[Document]) -> Dict[str, Any]:
        """
        获取文档摘要信息
        """
        if not documents:
            return {}
        
        total_text = ' '.join([doc.text for doc in documents])
        
        summary = {
            'document_count': len(documents),
            'total_characters': len(total_text),
            'total_words': len(total_text.split()),
            'average_doc_length': sum(len(doc.text) for doc in documents) / len(documents),
            'metadata_keys': list(documents[0].metadata.keys()) if documents else []
        }
        
        return summary
