"""
Agent 系统快速启动脚本
帮助用户快速测试 Agent 功能
"""

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🚀 LlamaReport Agent 系统快速启动")
    print("=" * 70 + "\n")
    
    # 步骤 1: 检查环境
    print("📋 步骤 1/5: 检查环境配置")
    print("-" * 70)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API Key (用于 Embedding)",
        "DEEPSEEK_API_KEY": "DeepSeek API Key (用于对话模型)"
    }
    
    missing_vars = []
    for var, desc in required_vars.items():
        if os.getenv(var):
            print(f"✅ {desc}: 已配置")
        else:
            print(f"❌ {desc}: 未配置")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ 缺少环境变量: {', '.join(missing_vars)}")
        print("请在 .env 文件中配置这些变量后重试。\n")
        return
    
    print("\n✅ 环境配置检查通过!\n")
    
    # 步骤 2: 检查 RAG 引擎
    print("📋 步骤 2/5: 检查 RAG 引擎")
    print("-" * 70)
    
    from core.rag_engine import RAGEngine
    
    rag = RAGEngine()
    
    if rag.load_existing_index():
        print("✅ RAG 引擎已初始化,索引已加载")
        
        # 测试查询
        test_result = rag.query("公司名称是什么?")
        if not test_result.get('error'):
            print(f"✅ RAG 查询测试成功")
            print(f"   测试问题: 公司名称是什么?")
            print(f"   回答: {test_result['answer'][:100]}...")
        else:
            print(f"⚠️ RAG 查询测试失败: {test_result.get('answer')}")
    else:
        print("❌ RAG 引擎未初始化")
        print("\n请先完成以下步骤:")
        print("1. 启动服务器: python main.py")
        print("2. 上传 PDF 文档: POST /upload")
        print("3. 处理文档: POST /process/{document_id}")
        print("\n然后重新运行此脚本。\n")
        return
    
    print("\n✅ RAG 引擎检查通过!\n")
    
    # 步骤 3: 初始化 Agent
    print("📋 步骤 3/5: 初始化 Report Agent")
    print("-" * 70)
    
    from agents.report_agent import ReportAgent
    
    try:
        agent = ReportAgent(rag.query_engine)
        print("✅ Report Agent 初始化成功")
    except Exception as e:
        print(f"❌ Report Agent 初始化失败: {str(e)}")
        return
    
    print("\n✅ Agent 初始化完成!\n")
    
    # 步骤 4: 测试 Agent 查询
    print("📋 步骤 4/5: 测试 Agent 查询功能")
    print("-" * 70)
    
    test_questions = [
        "公司的主要业务是什么?",
        "2023年的营业收入是多少?",
        "公司有哪些业务亮点?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n测试查询 {i}/{len(test_questions)}: {question}")
        try:
            result = await agent.query(question)
            if result["status"] == "success":
                print(f"✅ 查询成功")
                print(f"   回答: {result['answer'][:150]}...")
            else:
                print(f"❌ 查询失败: {result.get('error')}")
        except Exception as e:
            print(f"❌ 查询异常: {str(e)}")
    
    print("\n✅ Agent 查询测试完成!\n")
    
    # 步骤 5: 生成示例报告
    print("📋 步骤 5/5: 生成示例报告")
    print("-" * 70)
    
    # 从 RAG 中获取公司信息
    company_info = rag.query("这是哪家公司的年报?年份是多少?")
    
    print("\n请输入报告信息:")
    company_name = input("公司名称 (直接回车使用默认): ").strip()
    if not company_name:
        company_name = "示例公司"
    
    year = input("年份 (直接回车使用 2023): ").strip()
    if not year:
        year = "2023"
    
    print(f"\n正在生成 {company_name} {year}年 的年报分析...")
    print("这可能需要几分钟时间,请耐心等待...\n")
    
    try:
        # 生成单个章节作为示例(完整报告需要更长时间)
        print("生成财务点评章节...")
        result = await agent.generate_section(
            section_name="financial_review",
            company_name=company_name,
            year=year
        )
        
        if result["status"] == "success":
            print("✅ 财务点评章节生成成功!")
            
            # 保存到文件
            output_dir = Path("reports")
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / f"{company_name}_{year}_financial_review.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result["content"])
            
            print(f"✅ 报告已保存到: {output_file}")
            print(f"\n报告预览 (前500字符):")
            print("-" * 70)
            print(result["content"][:500])
            print("...")
            print("-" * 70)
        else:
            print(f"❌ 生成失败: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ 生成异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 完成
    print("\n" + "=" * 70)
    print("🎉 快速启动完成!")
    print("=" * 70)
    
    print("\n📚 下一步:")
    print("1. 查看完整使用指南: AGENT_SYSTEM_GUIDE.md")
    print("2. 启动 API 服务器: python main.py")
    print("3. 使用 API 生成完整报告: POST /agent/generate-report")
    print("\n示例 API 调用:")
    print("""
    curl -X POST "http://localhost:8000/agent/generate-report" \\
      -H "Content-Type: application/json" \\
      -d '{
        "company_name": "%s",
        "year": "%s",
        "save_to_file": true
      }'
    """ % (company_name, year))
    
    print("\n✨ 祝使用愉快!\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断,退出程序。")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

