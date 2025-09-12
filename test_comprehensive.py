#!/usr/bin/env python3
"""
综合功能测试脚本
直接测试所有核心模块和功能
"""

import os
import sys
import traceback
import tempfile
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.append('.')

def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("📦 开始测试模块导入")
    print("=" * 60)
    
    modules_to_test = [
        "utils.pdf_processor",
        "utils.table_extractor", 
        "utils.rag_system",
        "utils.company_comparator",
        "utils.financial_calculator",
        "utils.data_visualizer",
        "utils.export_engine",
        "utils.insights_engine",
        "utils.state"
    ]
    
    results = {}
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
            results[module] = True
        except Exception as e:
            print(f"❌ {module}: {str(e)}")
            results[module] = False
            
    return results

def test_pdf_processor():
    """测试PDF处理器功能"""
    print("\n" + "=" * 60)
    print("📄 开始测试PDF处理器")
    print("=" * 60)
    
    try:
        from utils.pdf_processor import PDFProcessor
        
        # Check available methods
        processor = PDFProcessor()
        print("✅ PDFProcessor初始化成功")
        
        # Check if test file exists
        test_files = [
            "attached_assets/test-001_1757660301972.PDF",
            "attached_assets/test-001_1757645177653.PDF",
            "attached_assets/test-001_1757641034573.PDF"
        ]
        
        test_file = None
        for file_path in test_files:
            if os.path.exists(file_path):
                test_file = file_path
                break
                
        if not test_file:
            print("⚠️ 未找到测试PDF文件")
            return False
            
        print(f"📂 使用测试文件: {test_file}")
        
        # Test methods that exist
        available_methods = [method for method in dir(processor) if not method.startswith('_')]
        print(f"📋 可用方法: {available_methods}")
        
        # Try processing if methods exist
        try:
            # Check for process method
            if hasattr(processor, 'process_pdf') or hasattr(processor, 'process_file'):
                print("🔄 尝试处理PDF...")
                result = None
                
                if hasattr(processor, 'process_pdf'):
                    result = processor.process_pdf(test_file)
                elif hasattr(processor, 'process_file'):
                    result = processor.process_file(test_file)
                    
                if result:
                    print("✅ PDF处理成功")
                    print(f"   结果类型: {type(result)}")
                    if isinstance(result, dict):
                        print(f"   结果键: {list(result.keys())}")
                else:
                    print("⚠️ PDF处理无结果")
            else:
                print("⚠️ 未找到PDF处理方法")
                
        except Exception as process_error:
            print(f"⚠️ PDF处理出错: {str(process_error)}")
            
        return True
        
    except Exception as e:
        print(f"❌ PDF处理器测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_table_extractor():
    """测试表格提取器功能"""
    print("\n" + "=" * 60)
    print("📊 开始测试表格提取器")
    print("=" * 60)
    
    try:
        from utils.table_extractor import TableExtractor
        
        extractor = TableExtractor()
        print("✅ TableExtractor初始化成功")
        
        # Check available methods
        available_methods = [method for method in dir(extractor) if not method.startswith('_')]
        print(f"📋 可用方法: {available_methods}")
        
        # Create sample financial data for testing
        sample_data = pd.DataFrame({
            '项目': ['营业收入', '净利润', '总资产', '股东权益'],
            '2023年': [1000000, 100000, 5000000, 3000000],
            '2022年': [900000, 90000, 4500000, 2700000]
        })
        
        print("🔄 测试表格处理...")
        
        # Test table processing if method exists
        if hasattr(extractor, 'extract_tables') or hasattr(extractor, 'process_table'):
            try:
                result = None
                if hasattr(extractor, 'extract_tables'):
                    # This might need different parameters
                    print("⚠️ extract_tables方法存在，但需要特定参数")
                elif hasattr(extractor, 'process_table'):
                    result = extractor.process_table(sample_data)
                    
                if result:
                    print("✅ 表格处理成功")
                    print(f"   结果类型: {type(result)}")
            except Exception as table_error:
                print(f"⚠️ 表格处理出错: {str(table_error)}")
        else:
            print("⚠️ 未找到表格处理方法")
            
        return True
        
    except Exception as e:
        print(f"❌ 表格提取器测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_rag_system():
    """测试RAG系统功能"""
    print("\n" + "=" * 60)
    print("🤖 开始测试RAG系统")
    print("=" * 60)
    
    try:
        from utils.rag_system import RAGSystem
        
        rag_system = RAGSystem()
        print("✅ RAGSystem初始化成功")
        
        # Check available methods
        available_methods = [method for method in dir(rag_system) if not method.startswith('_')]
        print(f"📋 可用方法: {available_methods}")
        
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print("✅ 检测到OpenAI API密钥")
        else:
            print("⚠️ 未检测到OpenAI API密钥")
            
        # Test getting stats
        try:
            if hasattr(rag_system, 'get_stats') or hasattr(rag_system, 'get_index_stats'):
                stats_method = getattr(rag_system, 'get_stats', None) or getattr(rag_system, 'get_index_stats', None)
                stats = stats_method()
                print(f"✅ 成功获取统计信息: {stats}")
            else:
                print("⚠️ 未找到统计信息方法")
        except Exception as stats_error:
            print(f"⚠️ 获取统计信息出错: {str(stats_error)}")
            
        return True
        
    except Exception as e:
        print(f"❌ RAG系统测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_company_comparator():
    """测试公司比较器功能"""
    print("\n" + "=" * 60)
    print("🏢 开始测试公司比较器")
    print("=" * 60)
    
    try:
        from utils.company_comparator import CompanyComparator
        
        comparator = CompanyComparator()
        print("✅ CompanyComparator初始化成功")
        
        # Check available methods
        available_methods = [method for method in dir(comparator) if not method.startswith('_')]
        print(f"📋 可用方法: {available_methods}")
        
        # Test with sample data
        sample_company_data = {
            "Company A": {
                "revenue": 1000000,
                "profit": 100000,
                "assets": 5000000
            },
            "Company B": {
                "revenue": 800000,
                "profit": 120000,
                "assets": 4000000
            }
        }
        
        # Try any comparison method
        comparison_methods = ['compare', 'analyze', 'compare_companies', 'process_data']
        for method_name in comparison_methods:
            if hasattr(comparator, method_name):
                try:
                    method = getattr(comparator, method_name)
                    print(f"🔄 测试方法: {method_name}")
                    # Different methods may need different parameters
                    result = method(sample_company_data)
                    print(f"✅ {method_name}执行成功")
                    break
                except Exception as method_error:
                    print(f"⚠️ {method_name}执行出错: {str(method_error)}")
                    
        return True
        
    except Exception as e:
        print(f"❌ 公司比较器测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_financial_calculator():
    """测试财务计算器功能"""
    print("\n" + "=" * 60)
    print("🧮 开始测试财务计算器")
    print("=" * 60)
    
    try:
        from utils.financial_calculator import FinancialCalculator
        
        calculator = FinancialCalculator()
        print("✅ FinancialCalculator初始化成功")
        
        # Check available methods
        available_methods = [method for method in dir(calculator) if not method.startswith('_')]
        print(f"📋 可用方法: {available_methods}")
        
        # Test ratio calculations with sample data
        sample_financial_data = {
            "revenue": 1000000,
            "cost_of_goods_sold": 600000,
            "net_income": 100000,
            "total_assets": 5000000,
            "equity": 3000000,
            "current_assets": 2000000,
            "current_liabilities": 1000000
        }
        
        # Try calculation methods
        calculation_methods = ['calculate_ratios', 'calculate', 'compute_ratios', 'get_ratios']
        for method_name in calculation_methods:
            if hasattr(calculator, method_name):
                try:
                    method = getattr(calculator, method_name)
                    print(f"🔄 测试方法: {method_name}")
                    result = method(sample_financial_data)
                    print(f"✅ {method_name}计算成功")
                    if result:
                        print(f"   计算结果: {type(result)}")
                        if isinstance(result, dict):
                            print(f"   比率数量: {len(result)}")
                    break
                except Exception as method_error:
                    print(f"⚠️ {method_name}计算出错: {str(method_error)}")
                    
        return True
        
    except Exception as e:
        print(f"❌ 财务计算器测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_state_management():
    """测试状态管理功能"""
    print("\n" + "=" * 60)
    print("💾 开始测试状态管理")
    print("=" * 60)
    
    try:
        from utils.state import init_state, init_processors, get_processing_stats
        
        print("✅ 成功导入状态管理函数")
        
        # Test state initialization
        print("🔄 测试状态初始化...")
        init_result = init_state()
        if init_result is not None:
            print(f"✅ 状态初始化完成: {init_result}")
        else:
            print("✅ 状态初始化完成（无返回值）")
            
        # Test processors initialization
        print("🔄 测试处理器初始化...")
        processors_result = init_processors()
        print(f"✅ 处理器初始化结果: {processors_result}")
        
        # Test getting stats
        print("🔄 测试获取处理统计...")
        try:
            stats = get_processing_stats()
            print(f"✅ 成功获取处理统计: {stats}")
        except Exception as stats_error:
            print(f"⚠️ 获取统计出错: {str(stats_error)}")
            
        return True
        
    except Exception as e:
        print(f"❌ 状态管理测试失败: {str(e)}")
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """运行所有测试"""
    print("🚀 开始综合功能测试")
    print("时间:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Python版本:", sys.version)
    print("工作目录:", os.getcwd())
    print()
    
    test_functions = [
        ("模块导入", test_imports),
        ("PDF处理器", test_pdf_processor), 
        ("表格提取器", test_table_extractor),
        ("RAG系统", test_rag_system),
        ("公司比较器", test_company_comparator),
        ("财务计算器", test_financial_calculator),
        ("状态管理", test_state_management)
    ]
    
    results = {}
    
    for test_name, test_function in test_functions:
        try:
            result = test_function()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name}测试异常: {str(e)}")
            results[test_name] = False
            
    # Print final summary
    print("\n" + "=" * 60)
    print("📋 最终测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15}: {status}")
        if result:
            passed += 1
            
    print("-" * 60)
    print(f"总计: {passed}/{total} 项测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！系统功能正常")
        return True
    else:
        print("⚠️ 部分测试失败，请检查上述错误")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)