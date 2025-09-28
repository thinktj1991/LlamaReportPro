"""
LlamaReport Backend 启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 首先加载环境变量
load_dotenv()

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("[ERROR] Python版本过低，需要Python 3.8或更高版本")
        return False
    print(f"[OK] Python版本: {sys.version}")
    return True

def check_dependencies():
    """检查依赖包"""
    print("🔍 检查依赖包...")
    
    try:
        import fastapi
        import uvicorn
        import llama_index
        import chromadb
        import pandas
        import pdfplumber
        print("✅ 核心依赖包已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_environment():
    """检查环境变量"""
    print("🔍 检查环境变量...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️ 警告: 未设置OPENAI_API_KEY环境变量")
        print("RAG功能将无法正常工作")
        return False
    
    print("✅ OPENAI_API_KEY 已设置")
    return True

def setup_directories():
    """设置必要的目录"""
    print("📁 设置目录结构...")
    
    directories = [
        "uploads",
        "storage", 
        "storage/chroma"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 目录已创建: {directory}")

def run_tests():
    """运行测试"""
    print("运行系统测试...")

    try:
        result = subprocess.run([sys.executable, "test_simple.py"],
                              capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            print("[OK] 系统测试通过")
            return True
        else:
            print("[ERROR] 系统测试失败")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[ERROR] 运行测试失败: {e}")
        return False

def start_server():
    """启动服务器"""
    print("🚀 启动LlamaReport Backend服务器...")
    
    try:
        # 使用uvicorn启动
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")

def main():
    """主函数"""
    print("LlamaReport Backend 启动器")
    print("=" * 40)

    # 检查Python版本
    if not check_python_version():
        sys.exit(1)

    # 检查依赖包
    if not check_dependencies():
        print("\n安装依赖包:")
        print("pip install -r requirements.txt")
        sys.exit(1)

    # 设置目录
    setup_directories()

    # 检查环境变量
    env_ok = check_environment()
    if not env_ok:
        print("\n设置环境变量:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("或在.env文件中设置")

        response = input("\n是否继续启动？(y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # 运行测试
    if not run_tests():
        response = input("\n测试失败，是否仍要启动服务器？(y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print("\n" + "=" * 40)
    print("🎉 准备就绪！启动服务器...")
    print("📖 API文档: http://localhost:8000/docs")
    print("🏠 主页: http://localhost:8000")
    print("❤️ 健康检查: http://localhost:8000/health")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 40)
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()
