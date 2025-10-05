"""
验证 Agent 前端集成
检查 static/index.html 是否正确添加了 Agent 功能
"""

import os
import sys

def check_index_html():
    """检查 index.html 文件"""
    print("\n" + "=" * 70)
    print("📁 检查 static/index.html")
    print("=" * 70)
    
    html_file = "static/index.html"
    
    if not os.path.exists(html_file):
        print(f"❌ 文件不存在: {html_file}")
        return False
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键修改
    checks = {
        "marked.js 库": "marked.min.js" in content,
        "Agent 按钮": "Agent 智能分析" in content,
        "askQuestionWithAgent 函数": "function askQuestionWithAgent" in content,
        "Agent API 调用": "/agent/query" in content,
        "Markdown 渲染": "marked.parse" in content,
        "Markdown CSS 样式": "#queryResult h1" in content or "#queryResult h2" in content,
        "Agent 按钮样式": "667eea" in content and "764ba2" in content,
    }
    
    all_passed = True
    for check_name, check_result in checks.items():
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False
    
    return all_passed


def check_backend_running():
    """检查后端是否运行"""
    print("\n" + "=" * 70)
    print("🔍 检查后端服务")
    print("=" * 70)
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正在运行")
            return True
        else:
            print(f"⚠️ 后端响应异常: HTTP {response.status_code}")
            return False
    except ImportError:
        print("⚠️ 需要安装 requests 库: pip install requests")
        return False
    except Exception as e:
        print("❌ 无法连接到后端服务")
        print("   请运行: python main.py")
        return False


def check_agent_api():
    """检查 Agent API"""
    print("\n" + "=" * 70)
    print("🤖 检查 Agent API")
    print("=" * 70)
    
    try:
        import requests
        response = requests.get("http://localhost:8000/agent/status", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ Agent API 可用")
            print(f"   - RAG 引擎: {'✅' if result.get('rag_engine_initialized') else '❌'}")
            print(f"   - Report Agent: {'✅' if result.get('report_agent_initialized') else '❌'}")
            print(f"   - 索引已加载: {'✅' if result.get('index_loaded') else '❌'}")
            print(f"   - 系统就绪: {'✅' if result.get('ready') else '❌'}")
            return result.get('ready', False)
        else:
            print(f"⚠️ Agent API 响应异常: HTTP {response.status_code}")
            return False
    except ImportError:
        print("⚠️ 需要安装 requests 库: pip install requests")
        return False
    except Exception as e:
        print(f"❌ 检查 Agent API 时发生错误: {str(e)}")
        return False


def print_usage_guide():
    """打印使用指南"""
    print("\n" + "=" * 70)
    print("📖 使用指南")
    print("=" * 70)
    
    print("""
1. 启动后端服务器 (如果还没启动):
   python main.py

2. 访问前端:
   http://localhost:8000

3. 使用 Agent 功能:
   - 上传并处理 PDF 文档
   - 在问题框输入问题
   - 点击 "🤖 Agent 智能分析" 按钮
   - 查看结构化的 Markdown 回答

4. 对比两个系统:
   - 🔍 提问: 快速查询,简单回答
   - 🤖 Agent 智能分析: 深度分析,结构化输出

5. 查看详细文档:
   - TEST_AGENT_FRONTEND.md
    """)


def main():
    """主函数"""
    print("\n" + "🧪 " * 30)
    print("Agent 前端集成验证")
    print("🧪 " * 30)
    
    # 检查文件修改
    files_ok = check_index_html()
    
    # 检查后端
    backend_ok = check_backend_running()
    
    # 检查 Agent API
    agent_ok = False
    if backend_ok:
        agent_ok = check_agent_api()
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 验证总结")
    print("=" * 70)
    
    print(f"\n文件修改: {'✅ 通过' if files_ok else '❌ 失败'}")
    print(f"后端服务: {'✅ 运行中' if backend_ok else '❌ 未运行'}")
    print(f"Agent API: {'✅ 就绪' if agent_ok else '❌ 未就绪'}")
    
    if files_ok and backend_ok and agent_ok:
        print("\n" + "=" * 70)
        print("🎉 所有检查通过! Agent 功能已成功集成到前端!")
        print("=" * 70)
        print("\n现在访问: http://localhost:8000")
        print("你会看到紫色的 '🤖 Agent 智能分析' 按钮!")
        print_usage_guide()
        return True
    else:
        print("\n" + "=" * 70)
        print("⚠️ 部分检查未通过")
        print("=" * 70)
        
        if not files_ok:
            print("\n❌ 文件修改不完整")
            print("   请检查 static/index.html 是否正确修改")
        
        if not backend_ok:
            print("\n❌ 后端未运行")
            print("   请运行: python main.py")
        
        if backend_ok and not agent_ok:
            print("\n❌ Agent API 未就绪")
            print("   请确保已上传并处理文档")
        
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 验证过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

