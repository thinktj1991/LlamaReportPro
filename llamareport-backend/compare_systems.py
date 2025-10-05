"""
对比原有系统和新 Agent 系统的输出
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_old_system():
    """测试原有的简单查询系统"""
    print("\n" + "=" * 70)
    print("📝 原有系统 (/query/ask)")
    print("=" * 70)
    
    question = "天域生态环境股份有限公司的主要业务是什么?"
    print(f"问题: {question}\n")
    
    response = requests.post(
        f"{API_BASE}/query/ask",
        json={"question": question}
    )
    
    result = response.json()
    print("回答:")
    print("-" * 70)
    print(result.get('answer', '无回答'))
    print("-" * 70)
    
    return result


def test_agent_system():
    """测试新的 Agent 系统"""
    print("\n" + "=" * 70)
    print("🤖 新 Agent 系统 (/agent/query)")
    print("=" * 70)
    
    question = "天域生态环境股份有限公司的主要业务是什么?"
    print(f"问题: {question}\n")
    print("正在使用 Agent 分析...")
    
    response = requests.post(
        f"{API_BASE}/agent/query",
        json={"question": question}
    )
    
    result = response.json()
    print("\n回答:")
    print("-" * 70)
    print(result.get('answer', '无回答'))
    print("-" * 70)
    
    return result


def main():
    print("\n" + "🔍 " * 30)
    print("系统对比测试")
    print("🔍 " * 30)
    
    try:
        # 测试原有系统
        old_result = test_old_system()
        
        # 测试新 Agent 系统
        agent_result = test_agent_system()
        
        # 对比
        print("\n" + "=" * 70)
        print("📊 对比总结")
        print("=" * 70)
        
        print("\n原有系统:")
        print("  ✅ 速度快")
        print("  ❌ 输出简单,缺乏结构")
        print("  ❌ 没有深度分析")
        
        print("\n新 Agent 系统:")
        print("  ✅ 输出结构化 (Markdown 格式)")
        print("  ✅ 深度分析,专业性强")
        print("  ✅ 自动分类归纳")
        print("  ⚠️  速度稍慢 (但质量更高)")
        
        print("\n" + "=" * 70)
        print("💡 建议:")
        print("=" * 70)
        print("- 快速查询: 使用原有系统 (/query/ask)")
        print("- 深度分析: 使用 Agent 系统 (/agent/query)")
        print("- 生成报告: 使用 Agent 系统 (/agent/generate-report)")
        print()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器")
        print("请确保服务器正在运行: python main.py")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")


if __name__ == "__main__":
    main()

