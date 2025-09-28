"""
文件上传API接口
"""

import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# 支持的文件类型
ALLOWED_EXTENSIONS = {'.pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    """
    上传单个文件
    
    Args:
        file: 上传的文件
        
    Returns:
        上传结果
    """
    try:
        # 验证文件
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 检查文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 检查文件大小
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大: {len(file_content)} bytes。最大允许: {MAX_FILE_SIZE} bytes"
            )
        
        # 确保上传目录存在
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # 生成安全的文件名
        safe_filename = _generate_safe_filename(file.filename)
        file_path = upload_dir / safe_filename
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"文件上传成功: {safe_filename}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "文件上传成功",
                "filename": safe_filename,
                "file_path": str(file_path),
                "file_size": len(file_content),
                "file_type": file_ext
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.post("/files")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    上传多个文件
    
    Args:
        files: 上传的文件列表
        
    Returns:
        上传结果列表
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="没有选择文件")
        
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="一次最多上传10个文件")
        
        results = []
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        for file in files:
            try:
                # 验证单个文件
                if not file.filename:
                    results.append({
                        "filename": "unknown",
                        "status": "error",
                        "message": "文件名不能为空"
                    })
                    continue
                
                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in ALLOWED_EXTENSIONS:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": f"不支持的文件类型: {file_ext}"
                    })
                    continue
                
                # 读取文件内容
                file_content = await file.read()
                if len(file_content) > MAX_FILE_SIZE:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": f"文件过大: {len(file_content)} bytes"
                    })
                    continue
                
                # 保存文件
                safe_filename = _generate_safe_filename(file.filename)
                file_path = upload_dir / safe_filename
                
                with open(file_path, "wb") as f:
                    f.write(file_content)
                
                results.append({
                    "filename": safe_filename,
                    "original_filename": file.filename,
                    "status": "success",
                    "file_path": str(file_path),
                    "file_size": len(file_content),
                    "file_type": file_ext
                })
                
                logger.info(f"文件上传成功: {safe_filename}")
                
            except Exception as e:
                results.append({
                    "filename": file.filename if file.filename else "unknown",
                    "status": "error",
                    "message": str(e)
                })
                logger.error(f"文件 {file.filename} 上传失败: {str(e)}")
        
        # 统计结果
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = len(results) - success_count
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"批量上传完成: {success_count} 成功, {error_count} 失败",
                "total_files": len(results),
                "success_count": success_count,
                "error_count": error_count,
                "results": results
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量文件上传失败: {str(e)}")

@router.get("/list")
async def list_uploaded_files():
    """
    列出已上传的文件
    
    Returns:
        文件列表
    """
    try:
        upload_dir = Path("uploads")
        if not upload_dir.exists():
            return JSONResponse(
                status_code=200,
                content={
                    "message": "上传目录不存在",
                    "files": []
                }
            )
        
        files = []
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                file_info = {
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "file_size": file_path.stat().st_size,
                    "file_type": file_path.suffix.lower(),
                    "created_time": file_path.stat().st_ctime
                }
                files.append(file_info)
        
        # 按创建时间排序
        files.sort(key=lambda x: x["created_time"], reverse=True)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"找到 {len(files)} 个文件",
                "total_files": len(files),
                "files": files
            }
        )
        
    except Exception as e:
        logger.error(f"列出文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列出文件失败: {str(e)}")

@router.delete("/file/{filename}")
async def delete_file(filename: str):
    """
    删除指定文件
    
    Args:
        filename: 文件名
        
    Returns:
        删除结果
    """
    try:
        upload_dir = Path("uploads")
        file_path = upload_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="不是有效的文件")
        
        # 删除文件
        file_path.unlink()
        
        logger.info(f"文件删除成功: {filename}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "文件删除成功",
                "filename": filename
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.delete("/clear")
async def clear_uploads():
    """
    清空上传目录
    
    Returns:
        清空结果
    """
    try:
        upload_dir = Path("uploads")
        if not upload_dir.exists():
            return JSONResponse(
                status_code=200,
                content={
                    "message": "上传目录不存在",
                    "deleted_count": 0
                }
            )
        
        deleted_count = 0
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1
        
        logger.info(f"清空上传目录: 删除了 {deleted_count} 个文件")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"清空完成，删除了 {deleted_count} 个文件",
                "deleted_count": deleted_count
            }
        )
        
    except Exception as e:
        logger.error(f"清空上传目录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清空上传目录失败: {str(e)}")

def _generate_safe_filename(filename: str) -> str:
    """生成安全的文件名"""
    import re
    import time
    
    # 移除路径分隔符和特殊字符
    safe_name = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # 添加时间戳避免重名
    name_parts = safe_name.rsplit('.', 1)
    if len(name_parts) == 2:
        name, ext = name_parts
        timestamp = int(time.time())
        safe_name = f"{name}_{timestamp}.{ext}"
    else:
        timestamp = int(time.time())
        safe_name = f"{safe_name}_{timestamp}"
    
    return safe_name
