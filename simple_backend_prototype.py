#!/usr/bin/env python3
"""
简化的后端API原型
演示如何将核心功能转换为API接口
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 验证必要的环境变量
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is required")

app = FastAPI(
    title="LlamaReport Backend API",
    description="简化的年报分析后端API",
    version="1.0.0"
)

# 全局变量存储处理状态
processed_documents: Dict[str, Any] = {}
rag_engine = None

class QueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    document_id: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global rag_engine
    
    try:
        # 初始化RAG引擎
        from llama_index.core import VectorStoreIndex, StorageContext
        from llama_index.vector_stores.chroma import ChromaVectorStore
        import chromadb
        
        # 创建持久化的ChromaDB客户端
        storage_dir = Path("./storage_simple")
        storage_dir.mkdir(exist_ok=True)
        
        chroma_client = chromadb.PersistentClient(path=str(storage_dir))
        
        # 尝试获取现有集合，如果不存在则创建
        try:
            chroma_collection = chroma_client.get_collection("documents")
        except:
            chroma_collection = chroma_client.create_collection("documents")
        
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # 尝试加载现有索引，如果不存在则创建空索引
        try:
            rag_engine = VectorStoreIndex.from_vector_store(
                vector_store, storage_context=storage_context
            )
        except:
            rag_engine = VectorStoreIndex([], storage_context=storage_context)
        
        print("✅ RAG引擎初始化成功")
        
    except Exception as e:
        print(f"❌ RAG引擎初始化失败: {e}")
        rag_engine = None

@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "LlamaReport Backend API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/upload - 上传PDF文件",
            "/process/{document_id} - 处理文档",
            "/query - RAG问答",
            "/documents - 获取文档列表",
            "/status - 系统状态"
        ]
    }

@app.get("/status")
async def get_status():
    """获取系统状态"""
    return {
        "rag_engine_ready": rag_engine is not None,
        "documents_count": len(processed_documents),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "storage_path": "./storage_simple"
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传PDF文件"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        # 保存上传的文件
        upload_dir = Path("./uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 生成文档ID
        document_id = file.filename.replace('.pdf', '').replace(' ', '_')
        
        # 存储文档信息
        processed_documents[document_id] = {
            "filename": file.filename,
            "file_path": str(file_path),
            "status": "uploaded",
            "processed": False
        }
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "uploaded",
            "message": "文件上传成功，请调用 /process 接口处理文档"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.post("/process/{document_id}")
async def process_document(document_id: str):
    """处理文档，提取内容并建立索引"""
    if document_id not in processed_documents:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_info = processed_documents[document_id]
    if doc_info["processed"]:
        return {"message": "文档已经处理过", "document_id": document_id}
    
    try:
        from llama_index.readers.file import PDFReader
        from llama_index.core import Document
        
        # 读取PDF文件
        pdf_reader = PDFReader()
        documents = pdf_reader.load_data(Path(doc_info["file_path"]))
        
        # 添加元数据
        for doc in documents:
            doc.metadata["document_id"] = document_id
            doc.metadata["filename"] = doc_info["filename"]
        
        # 添加到RAG索引
        if rag_engine is not None:
            rag_engine.insert_nodes([doc.as_node() for doc in documents])
        
        # 更新处理状态
        processed_documents[document_id].update({
            "status": "processed",
            "processed": True,
            "page_count": len(documents),
            "total_text_length": sum(len(doc.text) for doc in documents)
        })
        
        return {
            "document_id": document_id,
            "status": "processed",
            "page_count": len(documents),
            "total_text_length": sum(len(doc.text) for doc in documents),
            "message": "文档处理完成，可以进行问答查询"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """RAG问答查询"""
    if rag_engine is None:
        raise HTTPException(status_code=500, detail="RAG引擎未初始化")
    
    try:
        # 创建查询引擎
        query_engine = rag_engine.as_query_engine()
        
        # 执行查询
        response = query_engine.query(request.question)
        
        # 提取来源信息
        sources = []
        if hasattr(response, 'source_nodes'):
            for node in response.source_nodes:
                source_info = {
                    "document_id": node.metadata.get("document_id", "unknown"),
                    "filename": node.metadata.get("filename", "unknown"),
                    "text_snippet": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                    "score": getattr(node, 'score', 0.0)
                }
                sources.append(source_info)
        
        return QueryResponse(
            answer=str(response),
            sources=sources,
            document_id=request.document_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.get("/documents")
async def get_documents():
    """获取已处理的文档列表"""
    return {
        "documents": processed_documents,
        "total_count": len(processed_documents)
    }

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """删除文档"""
    if document_id not in processed_documents:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        doc_info = processed_documents[document_id]
        
        # 删除文件
        if os.path.exists(doc_info["file_path"]):
            os.remove(doc_info["file_path"])
        
        # 从内存中删除
        del processed_documents[document_id]
        
        return {"message": f"文档 {document_id} 删除成功"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动简化的后端API服务...")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔍 交互式API: http://localhost:8000/redoc")
    
    uvicorn.run(
        "simple_backend_prototype:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
