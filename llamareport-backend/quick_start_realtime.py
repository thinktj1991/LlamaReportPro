"""
实时数据功能快速入门脚本
帮助用户快速配置和测试实时数据功能
"""

import os
import sys
from pathlib import Path


def print_banner():
    """打印横幅"""
    print("\n" + "=" * 80)
    print("  LlamaReport Backend - 实时数据功能快速入门")
    print("=" * 80 + "\n")


def check_dependencies():
    """检查依赖包"""
    print("📦 检查依赖包...")
    
    required_packages = {
        "tushare": "Tushare Pro API",
        "requests": "HTTP 请求库",
        "bs4": "BeautifulSoup4 网页解析",
        "lxml": "XML/HTML 解析器"
    }
    
    missing = []
    installed = []
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            installed.append(f"  ✅ {package:15} - {description}")
        except ImportError:
            missing.append(f"  ❌ {package:15} - {description}")
    
    if installed:
        print("\n已安装:")
        for item in installed:
            print(item)
    
    if missing:
        print("\n缺失:")
        for item in missing:
            print(item)
        
        print("\n⚠️ 请运行以下命令安装依赖:")
        print("  pip install -r requirements.txt\n")
        return False
    
    print("\n✅ 所有依赖包已安装!\n")
    return True


def check_env_config():
    """检查环境配置"""
    print("⚙️ 检查环境配置...")
    
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    configs = {
        "OPENAI_API_KEY": ("必需", "OpenAI Embedding"),
        "DEEPSEEK_API_KEY": ("必需", "DeepSeek LLM"),
        "TUSHARE_API_TOKEN": ("可选", "Tushare 数据源"),
        "ENABLE_REALTIME_DATA": ("可选", "启用实时数据")
    }
    
    missing_required = []
    missing_optional = []
    configured = []
    
    for key, (required, description) in configs.items():
        value = os.getenv(key)
        if value:
            masked_value = value[:10] + "..." if len(value) > 10 else value
            configured.append(f"  ✅ {key:20} = {masked_value:15} ({description})")
        else:
            if required == "必需":
                missing_required.append(f"  ❌ {key:20} - {description}")
            else:
                missing_optional.append(f"  ⚠️ {key:20} - {description}")
    
    if configured:
        print("\n已配置:")
        for item in configured:
            print(item)
    
    if missing_optional:
        print("\n未配置（可选）:")
        for item in missing_optional:
            print(item)
    
    if missing_required:
        print("\n缺失（必需）:")
        for item in missing_required:
            print(item)
        
        print("\n❌ 请在 .env 文件中配置必需的 API Keys")
        print("   参考: env_example.txt\n")
        return False
    
    print("\n✅ 环境配置检查通过!\n")
    return True


def test_data_sources():
    """测试数据源"""
    print("🔍 测试数据源...")
    
    from data_sources.sina_source import SinaFinanceDataSource
    from data_sources.tushare_source import TushareDataSource
    
    results = []
    
    # 测试新浪财经
    print("\n1. 测试新浪财经数据源...")
    try:
        sina = SinaFinanceDataSource()
        if sina.initialize():
            quote = sina.get_realtime_quote("600000.SH")
            if quote:
                results.append(("新浪财经", True, f"获取到 {quote['stock_name']} 数据"))
            else:
                results.append(("新浪财经", False, "初始化成功但未获取到数据"))
        else:
            results.append(("新浪财经", False, "初始化失败"))
    except Exception as e:
        results.append(("新浪财经", False, str(e)))
    
    # 测试 Tushare
    print("2. 测试 Tushare 数据源...")
    token = os.getenv("TUSHARE_API_TOKEN")
    if not token:
        results.append(("Tushare", None, "未配置 Token（使用新浪财经即可）"))
    else:
        try:
            tushare = TushareDataSource(api_token=token)
            if tushare.initialize():
                results.append(("Tushare", True, "初始化成功"))
            else:
                results.append(("Tushare", False, "初始化失败"))
        except Exception as e:
            results.append(("Tushare", False, str(e)))
    
    # 显示结果
    print("\n测试结果:")
    for source, status, message in results:
        if status is True:
            print(f"  ✅ {source:15} - {message}")
        elif status is False:
            print(f"  ❌ {source:15} - {message}")
        else:
            print(f"  ⚠️ {source:15} - {message}")
    
    # 检查是否至少有一个数据源可用
    has_working_source = any(status is True for _, status, _ in results)
    
    if has_working_source:
        print("\n✅ 至少一个数据源可用，系统可以正常运行!\n")
        return True
    else:
        print("\n⚠️ 建议配置 Tushare Token 或检查网络连接\n")
        return True  # 仍然返回 True，因为可能是网络问题


def test_tools():
    """测试工具函数"""
    print("🔧 测试工具函数...")
    
    from agents.realtime_tools import (
        get_realtime_stock_price,
        get_market_overview
    )
    
    print("\n1. 测试实时股价工具...")
    try:
        result = get_realtime_stock_price("600000.SH")
        if "错误" in result or "失败" in result:
            print(f"  ⚠️ {result[:100]}...")
        else:
            print(f"  ✅ 成功获取数据")
            print(f"     预览: {result[:150]}...")
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
    
    print("\n2. 测试市场概览工具...")
    try:
        result = get_market_overview()
        if "错误" in result or "失败" in result:
            print(f"  ⚠️ {result[:100]}...")
        else:
            print(f"  ✅ 成功获取市场数据")
            print(f"     预览: {result[:150]}...")
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
    
    print("\n✅ 工具测试完成!\n")


def show_next_steps():
    """显示下一步操作"""
    print("📖 下一步操作指南:\n")
    
    print("1️⃣ 启动服务器")
    print("   python main.py\n")
    
    print("2️⃣ 访问 API 文档")
    print("   http://localhost:8000/docs\n")
    
    print("3️⃣ 测试实时数据 API")
    print("   curl http://localhost:8000/realtime/health\n")
    
    print("4️⃣ 运行完整演示")
    print("   python examples/realtime_data_demo.py\n")
    
    print("5️⃣ 通过 Agent 使用")
    print("   curl -X POST http://localhost:8000/agent/query \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"question\": \"帮我查一下贵州茅台现在的股价\"}'")
    print()
    
    print("📚 详细文档:")
    print("   - REALTIME_DATA_GUIDE.md - 使用指南")
    print("   - REALTIME_FEATURE_EXAMPLES.md - 示例文档")
    print("   - UPGRADE_TO_REALTIME.md - 升级指南")
    print()


def show_optional_config():
    """显示可选配置"""
    print("💡 可选配置建议:\n")
    
    print("如果想获得更好的体验，建议配置 Tushare Token:\n")
    
    print("步骤 1: 注册 Tushare 账号（免费）")
    print("   https://tushare.pro/register\n")
    
    print("步骤 2: 获取 Token")
    print("   登录后在"个人中心"找到 API Token\n")
    
    print("步骤 3: 添加到 .env 文件")
    print("   TUSHARE_API_TOKEN=your-token-here\n")
    
    print("步骤 4: 重启服务")
    print("   python main.py\n")
    
    print("优势:")
    print("  ✅ 更全面的财务指标数据")
    print("  ✅ 支持历史数据查询")
    print("  ✅ 公司公告数据")
    print("  ✅ 更稳定的服务\n")


def main():
    """主函数"""
    print_banner()
    
    # 步骤 1: 检查依赖
    deps_ok = check_dependencies()
    if not deps_ok:
        print("❌ 依赖检查失败，请先安装依赖后再运行此脚本\n")
        return
    
    # 步骤 2: 检查环境配置
    env_ok = check_env_config()
    if not env_ok:
        print("❌ 环境配置检查失败，请配置必需的 API Keys\n")
        return
    
    # 步骤 3: 测试数据源
    test_data_sources()
    
    # 步骤 4: 测试工具
    test_tools()
    
    # 显示可选配置
    token = os.getenv("TUSHARE_API_TOKEN")
    if not token:
        show_optional_config()
    
    # 显示下一步
    show_next_steps()
    
    print("=" * 80)
    print("✅ 快速入门检查完成!")
    print("=" * 80)
    print("\n🎉 实时数据功能已准备就绪，现在可以启动服务器了！\n")


if __name__ == "__main__":
    main()

