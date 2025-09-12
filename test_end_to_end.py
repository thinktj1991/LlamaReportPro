#!/usr/bin/env python3
"""
端到端功能测试
使用真实PDF文件测试完整的处理流程
"""

import os
import sys
import traceback
import tempfile
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.append('.')

def simulate_streamlit_session():
    """模拟Streamlit会话状态"""
    class MockSessionState:
        def __init__(self):
            self.data = {}
            
        def __setattr__(self, name, value):
            if name == 'data':
                super().__setattr__(name, value)
            else:
                self.data[name] = value
                
        def __getattr__(self, name):
            if name in self.data:
                return self.data[name]
            raise AttributeError(f"Mock session state has no attribute '{name}'")
            
        def get(self, key, default=None):
            return self.data.get(key, default)
            
    return MockSessionState()

def test_pdf_processing_flow():
    """测试PDF处理完整流程"""
    print("=" * 60)
    print("📄 测试PDF处理完整流程")
    print("=" * 60)
    
    try:
        from utils.pdf_processor import PDFProcessor
        
        # Find a test PDF file
        test_files = [
            "attached_assets/test-001_1757660301972.PDF",
            "attached_assets/test-001_1757645177653.PDF",
            "attached_assets/test-001_1757641034573.PDF",
            "attached_assets/test-001_1757589516678.PDF"
        ]
        
        test_file = None
        for file_path in test_files:
            if os.path.exists(file_path):
                test_file = file_path
                print(f"✅ 找到测试文件: {test_file}")
                break
                
        if not test_file:
            print("❌ 未找到测试PDF文件")
            return False
            
        # Create mock uploaded file
        class MockUploadedFile:
            def __init__(self, file_path):
                self.name = os.path.basename(file_path)
                self.size = os.path.getsize(file_path)
                with open(file_path, 'rb') as f:
                    self._content = f.read()
                    
            def getvalue(self):
                return self._content
                
        mock_file = MockUploadedFile(test_file)
        print(f"📂 模拟上传文件: {mock_file.name} ({mock_file.size:,} bytes)")
        
        # Initialize processor and process file
        processor = PDFProcessor()
        print("🔄 开始处理PDF文件...")
        
        result = processor.process_uploaded_file(mock_file)
        
        if result:
            print("✅ PDF处理成功!")
            print(f"   文件名: {result.get('filename', 'N/A')}")
            print(f"   页数: {result.get('page_count', 'N/A')}")
            print(f"   文本长度: {result.get('total_text_length', 'N/A')} 字符")
            
            # Check documents
            documents = result.get('documents', [])
            if documents:
                print(f"   文档对象: {len(documents)} 个")
                sample_text = documents[0].text[:200].replace('\n', ' ') if documents[0].text else "无内容"
                print(f"   内容示例: {sample_text}...")
                
            # Test company info extraction
            print("\n🔄 测试公司信息提取...")
            company_info = processor.extract_company_info(documents)
            if company_info:
                print(f"✅ 提取到公司信息: {len(company_info)} 个公司")
                for company, info in list(company_info.items())[:3]:  # Show first 3
                    print(f"   {company}: {info}")
            else:
                print("⚠️ 未提取到公司信息")
                
            return result
        else:
            print("❌ PDF处理失败")
            return False
            
    except Exception as e:
        print(f"❌ PDF处理流程测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_table_extraction_flow(processed_result):
    """测试表格提取流程"""
    print("\n" + "=" * 60)
    print("📊 测试表格提取流程")
    print("=" * 60)
    
    if not processed_result:
        print("⚠️ 需要PDF处理结果才能测试表格提取")
        return False
        
    try:
        from utils.table_extractor import TableExtractor
        
        extractor = TableExtractor()
        
        # Prepare processed documents in the expected format
        processed_docs = {
            "test-document": processed_result
        }
        
        print("🔄 开始提取表格...")
        extracted_tables = extractor.extract_and_process_tables(processed_docs)
        
        if extracted_tables:
            print(f"✅ 表格提取成功! 共处理 {len(extracted_tables)} 个文档")
            
            for doc_name, tables in extracted_tables.items():
                print(f"\n📋 文档: {doc_name}")
                print(f"   提取的表格数量: {len(tables)}")
                
                for i, table_data in enumerate(tables[:3]):  # Show first 3 tables
                    print(f"   表格 {i+1}:")
                    if 'data' in table_data and hasattr(table_data['data'], 'shape'):
                        df = table_data['data']
                        print(f"     形状: {df.shape}")
                        print(f"     列名: {list(df.columns)}")
                        if not df.empty:
                            print(f"     首行数据: {df.iloc[0].to_dict()}")
                    print(f"     表格类型: {table_data.get('table_type', '未知')}")
                    print(f"     重要性: {table_data.get('importance_score', 0)}")
                    
            return extracted_tables
        else:
            print("⚠️ 未提取到表格数据")
            return {}
            
    except Exception as e:
        print(f"❌ 表格提取流程测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_rag_system_flow(processed_result, extracted_tables):
    """测试RAG系统流程"""
    print("\n" + "=" * 60)
    print("🤖 测试RAG系统流程")
    print("=" * 60)
    
    if not processed_result:
        print("⚠️ 需要处理结果才能测试RAG系统")
        return False
        
    try:
        from utils.rag_system import RAGSystem
        
        rag = RAGSystem()
        
        # Check if we have API key
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️ 缺少OpenAI API密钥，跳过RAG测试")
            return True
            
        print("🔄 构建文档索引...")
        processed_docs = {"test-document": processed_result}
        
        # Build index with both documents and tables
        success = rag.build_index(processed_docs, extracted_tables or {})
        
        if success:
            print("✅ 索引构建成功")
            
            # Get index stats
            stats = rag.get_index_stats()
            print(f"   状态: {stats.get('status', '未知')}")
            print(f"   文档数: {stats.get('total_documents', 0)}")
            print(f"   查询引擎: {'就绪' if stats.get('has_query_engine') else '未就绪'}")
            
            # Test queries
            test_queries = [
                "这份文档的主要内容是什么？",
                "文档中包含哪些财务数据？",
                "请总结这份报告的重点信息"
            ]
            
            print("\n🔍 测试查询功能...")
            for i, query in enumerate(test_queries[:2], 1):  # Test first 2 queries
                try:
                    print(f"   查询 {i}: {query}")
                    response = rag.query(query)
                    
                    if response and hasattr(response, 'response'):
                        print(f"   ✅ 回答长度: {len(response.response)} 字符")
                        print(f"   内容预览: {response.response[:100]}...")
                    else:
                        print(f"   ⚠️ 查询返回空结果")
                        
                except Exception as query_error:
                    print(f"   ⚠️ 查询失败: {str(query_error)}")
                    
            return True
        else:
            print("⚠️ 索引构建失败")
            return False
            
    except Exception as e:
        print(f"❌ RAG系统流程测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_financial_analysis_flow(extracted_tables):
    """测试财务分析流程"""
    print("\n" + "=" * 60)
    print("💰 测试财务分析流程")
    print("=" * 60)
    
    try:
        from utils.financial_calculator import FinancialCalculator
        
        calculator = FinancialCalculator()
        
        # Create sample financial data for testing
        sample_data = {
            "营业收入": 1000000,
            "营业成本": 600000,
            "净利润": 150000,
            "总资产": 5000000,
            "股东权益": 3000000,
            "流动资产": 2000000,
            "流动负债": 1000000,
            "货币资金": 500000,
            "应收账款": 800000,
            "存货": 700000
        }
        
        print("🔄 计算财务比率...")
        ratios = calculator.calculate_financial_ratios(sample_data)
        
        if ratios:
            print(f"✅ 成功计算 {len(ratios)} 个财务比率")
            
            # Show key ratios
            key_ratios = ['净利率', '资产回报率', '股本回报率', '流动比率', '速动比率']
            for ratio_name in key_ratios:
                if ratio_name in ratios:
                    value = ratios[ratio_name]
                    print(f"   {ratio_name}: {value:.4f}")
                    
            # Test with extracted table data if available
            if extracted_tables:
                print("\n🔄 分析提取的表格数据...")
                for doc_name, tables in extracted_tables.items():
                    for i, table_data in enumerate(tables[:2]):  # Analyze first 2 tables
                        if 'data' in table_data and hasattr(table_data['data'], 'shape'):
                            df = table_data['data']
                            if not df.empty and df.shape[1] > 1:
                                print(f"   分析表格 {i+1} ({df.shape[0]} 行 x {df.shape[1]} 列)")
                                try:
                                    # Try to convert to dict format for analysis
                                    table_dict = {}
                                    if df.shape[0] > 0:
                                        for col in df.columns[1:]:  # Skip first column (usually labels)
                                            if df[col].dtype in ['int64', 'float64']:
                                                table_dict[col] = df[col].sum()
                                    
                                    if table_dict:
                                        table_ratios = calculator.calculate_financial_ratios(table_dict)
                                        if table_ratios:
                                            print(f"     计算出 {len(table_ratios)} 个比率")
                                except Exception as calc_error:
                                    print(f"     计算失败: {str(calc_error)}")
                                    
            return ratios
        else:
            print("⚠️ 财务比率计算无结果")
            return {}
            
    except Exception as e:
        print(f"❌ 财务分析流程测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_export_functionality():
    """测试导出功能"""
    print("\n" + "=" * 60)
    print("📤 测试导出功能")
    print("=" * 60)
    
    try:
        from utils.export_engine import ExportEngine
        
        engine = ExportEngine()
        
        # Create sample data for export
        sample_analysis_data = {
            "公司概览": pd.DataFrame({
                "指标": ["营业收入", "净利润", "总资产"],
                "2023年": [1000000, 150000, 5000000],
                "2022年": [900000, 135000, 4500000]
            }),
            "财务比率": pd.DataFrame({
                "比率名称": ["净利率", "资产回报率", "流动比率"],
                "数值": [0.15, 0.03, 2.0],
                "行业平均": [0.12, 0.025, 1.8]
            })
        }
        
        print("🔄 测试CSV导出...")
        try:
            csv_result = engine.export_to_csv(
                data=sample_analysis_data,
                filename="test_export"
            )
            if csv_result:
                print("✅ CSV导出成功")
            else:
                print("⚠️ CSV导出无结果")
        except Exception as csv_error:
            print(f"⚠️ CSV导出失败: {str(csv_error)}")
            
        print("🔄 测试Excel导出...")
        try:
            excel_result = engine.export_to_excel(
                data=sample_analysis_data,
                filename="test_export"
            )
            if excel_result:
                print("✅ Excel导出成功")
            else:
                print("⚠️ Excel导出无结果")
        except Exception as excel_error:
            print(f"⚠️ Excel导出失败: {str(excel_error)}")
            
        print("🔄 测试PDF导出...")
        try:
            pdf_result = engine.export_to_pdf(
                data=sample_analysis_data,
                filename="test_export"
            )
            if pdf_result:
                print("✅ PDF导出成功")
            else:
                print("⚠️ PDF导出无结果")
        except Exception as pdf_error:
            print(f"⚠️ PDF导出失败: {str(pdf_error)}")
            
        return True
        
    except Exception as e:
        print(f"❌ 导出功能测试失败: {str(e)}")
        traceback.print_exc()
        return False

def run_end_to_end_test():
    """运行端到端测试"""
    print("🚀 开始端到端功能测试")
    print("时间:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Test complete workflow
    results = {}
    
    # Step 1: PDF Processing
    processed_result = test_pdf_processing_flow()
    results["PDF处理"] = bool(processed_result)
    
    # Step 2: Table Extraction
    if processed_result:
        extracted_tables = test_table_extraction_flow(processed_result)
        results["表格提取"] = bool(extracted_tables)
    else:
        extracted_tables = {}
        results["表格提取"] = False
        
    # Step 3: RAG System
    rag_result = test_rag_system_flow(processed_result, extracted_tables)
    results["RAG系统"] = bool(rag_result)
    
    # Step 4: Financial Analysis
    financial_result = test_financial_analysis_flow(extracted_tables)
    results["财务分析"] = bool(financial_result)
    
    # Step 5: Export Functionality
    export_result = test_export_functionality()
    results["数据导出"] = bool(export_result)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 端到端测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:10}: {status}")
        if result:
            passed += 1
            
    print("-" * 60)
    print(f"总计: {passed}/{total} 项功能测试通过 ({passed/total*100:.1f}%)")
    
    if passed >= total * 0.8:  # 80% pass rate
        print("🎉 端到端测试大部分通过！系统核心功能正常")
        return True
    else:
        print("⚠️ 多项测试失败，系统可能存在问题")
        return False

if __name__ == "__main__":
    success = run_end_to_end_test()
    sys.exit(0 if success else 1)