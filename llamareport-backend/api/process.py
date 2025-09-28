"""
文档处理API接口
"""

from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

from core.document_processor import DocumentProcessor
from core.table_extractor import TableExtractor
from core.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/process", tags=["process"])

# 全局处理器实例（延迟初始化）
document_processor = None
table_extractor = None
rag_engine = None

def get_processors():
    """获取处理器实例（延迟初始化）"""
    global document_processor, table_extractor, rag_engine

    if document_processor is None:
        document_processor = DocumentProcessor()
    if table_extractor is None:
        table_extractor = TableExtractor()
    if rag_engine is None:
        rag_engine = RAGEngine()

    return document_processor, table_extractor, rag_engine

class ProcessRequest(BaseModel):
    filename: str
    build_index: bool = True

class ProcessMultipleRequest(BaseModel):
    filenames: list[str]
    build_index: bool = True

@router.post("/file")
async def process_file(request: ProcessRequest):
    """
    处理单个文件
    
    Args:
        request: 处理请求
        
    Returns:
        处理结果
    """
    try:
        # 获取处理器实例
        document_processor, table_extractor, rag_engine = get_processors()

        filename = request.filename
        build_index = request.build_index

        # 检查文件是否存在
        file_path = Path("uploads") / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

        # 验证文件
        if not document_processor.validate_file(str(file_path)):
            raise HTTPException(status_code=400, detail=f"文件验证失败: {filename}")

        logger.info(f"开始处理文件: {filename}")

        # 处理文档
        doc_result = document_processor.process_file(str(file_path), filename)

        # 提取表格
        processed_docs = {filename: doc_result}
        extracted_tables = table_extractor.extract_tables(processed_docs)
        
        # 构建索引（如果需要）
        index_built = False
        if build_index:
            try:
                index_built = rag_engine.build_index(processed_docs, extracted_tables)
                logger.info(f"索引构建{'成功' if index_built else '失败'}")
            except Exception as e:
                logger.warning(f"索引构建失败: {str(e)}")
        
        # 生成处理摘要
        doc_summary = document_processor.get_document_summary(doc_result['documents'])
        table_stats = table_extractor.get_table_statistics(extracted_tables)

        # 将Document对象转换为可序列化的字典
        serializable_doc_result = {
            'filename': doc_result['filename'],
            'documents': [
                {
                    'doc_id': doc.doc_id,
                    'text': doc.text[:500] + "..." if len(doc.text) > 500 else doc.text,  # 截断长文本
                    'metadata': doc.metadata,
                    'text_length': len(doc.text)
                } for doc in doc_result['documents']
            ],
            'detailed_content': doc_result['detailed_content'],
            'page_count': doc_result['page_count'],
            'total_text_length': doc_result['total_text_length'],
            'processing_method': doc_result['processing_method']
        }

        result = {
            "message": "文件处理完成",
            "filename": filename,
            "processing_summary": {
                "document_info": {
                    "page_count": doc_result['page_count'],
                    "total_text_length": doc_result['total_text_length'],
                    "processing_method": doc_result['processing_method']
                },
                "document_summary": doc_summary,
                "table_info": {
                    "total_tables": table_stats['total_tables'],
                    "financial_tables": table_stats['financial_tables'],
                    "average_importance": table_stats['average_importance']
                },
                "index_info": {
                    "index_built": index_built,
                    "index_stats": rag_engine.get_index_stats() if index_built else None
                }
            },
            "detailed_results": {
                "document_data": serializable_doc_result,
                "extracted_tables": extracted_tables[filename] if filename in extracted_tables else []
            }
        }
        
        logger.info(f"文件处理完成: {filename}")
        return JSONResponse(status_code=200, content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理文件失败 {request.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")

@router.post("/files")
async def process_multiple_files(request: ProcessMultipleRequest):
    """
    处理多个文件
    
    Args:
        request: 批量处理请求
        
    Returns:
        批量处理结果
    """
    try:
        filenames = request.filenames
        build_index = request.build_index
        
        if not filenames:
            raise HTTPException(status_code=400, detail="没有指定文件")
        
        if len(filenames) > 10:
            raise HTTPException(status_code=400, detail="一次最多处理10个文件")
        
        logger.info(f"开始批量处理 {len(filenames)} 个文件")
        
        results = []
        all_processed_docs = {}
        all_extracted_tables = {}
        
        # 处理每个文件
        for filename in filenames:
            try:
                file_path = Path("uploads") / filename
                if not file_path.exists():
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "message": f"文件不存在: {filename}"
                    })
                    continue
                
                # 验证文件
                if not document_processor.validate_file(str(file_path)):
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "message": f"文件验证失败: {filename}"
                    })
                    continue
                
                # 处理文档
                doc_result = document_processor.process_file(str(file_path), filename)
                all_processed_docs[filename] = doc_result
                
                # 提取表格
                processed_docs = {filename: doc_result}
                extracted_tables = table_extractor.extract_tables(processed_docs)
                all_extracted_tables.update(extracted_tables)
                
                # 生成摘要
                doc_summary = document_processor.get_document_summary(doc_result['documents'])
                table_stats = table_extractor.get_table_statistics(extracted_tables)
                
                results.append({
                    "filename": filename,
                    "status": "success",
                    "summary": {
                        "page_count": doc_result['page_count'],
                        "total_text_length": doc_result['total_text_length'],
                        "table_count": table_stats['total_tables'],
                        "financial_tables": table_stats['financial_tables']
                    }
                })
                
                logger.info(f"文件处理成功: {filename}")
                
            except Exception as e:
                results.append({
                    "filename": filename,
                    "status": "error",
                    "message": str(e)
                })
                logger.error(f"处理文件失败 {filename}: {str(e)}")
        
        # 构建统一索引（如果需要）
        index_built = False
        if build_index and all_processed_docs:
            try:
                index_built = rag_engine.build_index(all_processed_docs, all_extracted_tables)
                logger.info(f"统一索引构建{'成功' if index_built else '失败'}")
            except Exception as e:
                logger.warning(f"统一索引构建失败: {str(e)}")
        
        # 统计结果
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = len(results) - success_count
        
        # 生成总体统计
        total_table_stats = table_extractor.get_table_statistics(all_extracted_tables)
        
        result = {
            "message": f"批量处理完成: {success_count} 成功, {error_count} 失败",
            "total_files": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "overall_summary": {
                "total_documents": len(all_processed_docs),
                "total_tables": total_table_stats['total_tables'],
                "financial_tables": total_table_stats['financial_tables'],
                "index_built": index_built,
                "index_stats": rag_engine.get_index_stats() if index_built else None
            },
            "file_results": results
        }
        
        logger.info(f"批量处理完成: {success_count}/{len(filenames)} 成功")
        return JSONResponse(status_code=200, content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")

@router.get("/status")
async def get_processing_status():
    """
    获取处理状态
    
    Returns:
        当前处理状态
    """
    try:
        # 获取上传文件数量
        upload_dir = Path("uploads")
        uploaded_files = 0
        if upload_dir.exists():
            uploaded_files = len([f for f in upload_dir.iterdir() if f.is_file()])
        
        # 获取索引状态
        index_stats = rag_engine.get_index_stats()
        
        status = {
            "system_status": "ready",
            "uploaded_files": uploaded_files,
            "index_status": index_stats,
            "supported_formats": [".pdf"],
            "max_file_size": "50MB",
            "max_batch_size": 10
        }
        
        return JSONResponse(status_code=200, content=status)
        
    except Exception as e:
        logger.error(f"获取处理状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取处理状态失败: {str(e)}")

@router.post("/rebuild-index")
async def rebuild_index():
    """
    重建索引
    
    Returns:
        重建结果
    """
    try:
        # 清空现有索引
        rag_engine.clear_index()
        
        # 获取所有已处理的文档（这里简化处理，实际应该从存储中恢复）
        upload_dir = Path("uploads")
        if not upload_dir.exists():
            raise HTTPException(status_code=400, detail="没有找到上传的文件")
        
        # 重新处理所有文件并构建索引
        pdf_files = [f.name for f in upload_dir.iterdir() if f.suffix.lower() == '.pdf']
        
        if not pdf_files:
            raise HTTPException(status_code=400, detail="没有找到PDF文件")
        
        all_processed_docs = {}
        all_extracted_tables = {}
        
        for filename in pdf_files:
            try:
                file_path = upload_dir / filename
                
                # 处理文档
                doc_result = document_processor.process_file(str(file_path), filename)
                all_processed_docs[filename] = doc_result
                
                # 提取表格
                processed_docs = {filename: doc_result}
                extracted_tables = table_extractor.extract_tables(processed_docs)
                all_extracted_tables.update(extracted_tables)
                
            except Exception as e:
                logger.warning(f"重建索引时处理文件失败 {filename}: {str(e)}")
        
        # 构建索引
        if all_processed_docs:
            index_built = rag_engine.build_index(all_processed_docs, all_extracted_tables)
            
            if index_built:
                index_stats = rag_engine.get_index_stats()
                return JSONResponse(
                    status_code=200,
                    content={
                        "message": "索引重建成功",
                        "processed_files": len(all_processed_docs),
                        "index_stats": index_stats
                    }
                )
            else:
                raise HTTPException(status_code=500, detail="索引重建失败")
        else:
            raise HTTPException(status_code=400, detail="没有可处理的文档")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重建索引失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重建索引失败: {str(e)}")
