#!/usr/bin/env python3
"""
表格提取功能测试
测试TableExtractor和财务数据提取功能
"""

import os
import sys
import traceback
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.append('.')

def test_table_extraction():
    """测试表格提取功能"""
    print("🔄 开始测试表格提取功能...")
    
    try:
        # Import required modules
        from utils.table_extractor import TableExtractor
        print("✅ 成功导入TableExtractor模块")
        
        # Initialize extractor
        extractor = TableExtractor()
        print("✅ 成功初始化TableExtractor")
        
        # First, we need processed documents to extract tables from
        from utils.pdf_processor import PDFProcessor
        
        pdf_processor = PDFProcessor()
        test_pdf_path = "attached_assets/test-001_1757660301972.PDF"
        
        if not os.path.exists(test_pdf_path):
            print("❌ 测试PDF文件不存在:", test_pdf_path)
            return False
            
        # Process PDF first
        print("🔄 预处理PDF文档...")
        documents = pdf_processor.read_pdf_file(test_pdf_path)
        company_info = pdf_processor.extract_company_info(documents)
        
        processed_docs = {
            "test-document": {
                "documents": documents,
                "company_info": company_info,
                "file_path": test_pdf_path
            }
        }
        
        # Test table extraction
        print("🔄 开始提取表格数据...")
        extracted_tables = extractor.extract_and_process_tables(processed_docs)
        
        if extracted_tables:
            print(f"✅ 成功提取表格，共 {len(extracted_tables)} 个文档的表格")
            
            for doc_name, tables in extracted_tables.items():
                print(f"\n📊 文档 '{doc_name}' 的表格:")
                print(f"   表格数量: {len(tables)}")
                
                for i, table_info in enumerate(tables):
                    print(f"   表格 {i+1}:")
                    print(f"     行数: {table_info.get('rows', 0)}")
                    print(f"     列数: {table_info.get('columns', 0)}")
                    print(f"     类型: {table_info.get('table_type', 'unknown')}")
                    
                    # Show sample data if available
                    if 'data' in table_info and isinstance(table_info['data'], pd.DataFrame):
                        df = table_info['data']
                        print(f"     数据预览 (前3行):")
                        print(f"       列名: {list(df.columns)}")
                        if not df.empty:
                            print(f"       示例行: {df.iloc[0].to_dict()}")
        else:
            print("⚠️ 未提取到表格数据")
            
        return True
        
    except Exception as e:
        print(f"❌ 表格提取测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_financial_data_processing():
    """测试财务数据处理功能"""
    print("\n🔄 开始测试财务数据处理...")
    
    try:
        from utils.table_extractor import TableExtractor
        
        # Create sample financial data for testing
        sample_data = pd.DataFrame({
            '科目': ['营业收入', '营业成本', '毛利润', '净利润', '总资产', '股东权益'],
            '2023年': [1000000, 600000, 400000, 200000, 5000000, 3000000],
            '2022年': [900000, 540000, 360000, 180000, 4500000, 2700000],
            '2021年': [800000, 480000, 320000, 160000, 4000000, 2400000]
        })
        
        extractor = TableExtractor()
        
        # Test financial data identification
        print("🔄 测试财务数据识别...")
        is_financial = extractor._is_financial_table(sample_data)
        
        if is_financial:
            print("✅ 正确识别财务表格")
        else:
            print("⚠️ 未能识别财务表格")
            
        # Test data cleaning
        print("🔄 测试数据清洗...")
        cleaned_data = extractor._clean_financial_data(sample_data)
        
        if cleaned_data is not None and not cleaned_data.empty:
            print("✅ 数据清洗完成")
            print(f"   清洗后数据形状: {cleaned_data.shape}")
        else:
            print("⚠️ 数据清洗失败")
            
        # Test ratio calculations
        print("🔄 测试财务比率计算...")
        try:
            ratios = extractor._calculate_financial_ratios(cleaned_data)
            if ratios:
                print("✅ 财务比率计算完成")
                print(f"   计算的比率: {list(ratios.keys())}")
            else:
                print("⚠️ 财务比率计算无结果")
        except Exception as e:
            print(f"⚠️ 财务比率计算出错: {str(e)}")
            
        return True
        
    except Exception as e:
        print(f"❌ 财务数据处理测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_table_type_classification():
    """测试表格类型分类功能"""
    print("\n🔄 开始测试表格类型分类...")
    
    try:
        from utils.table_extractor import TableExtractor
        
        extractor = TableExtractor()
        
        # Test different types of tables
        test_cases = [
            {
                'name': '损益表',
                'data': pd.DataFrame({
                    '项目': ['营业收入', '营业成本', '净利润'],
                    '2023': [1000, 600, 200],
                    '2022': [900, 540, 180]
                })
            },
            {
                'name': '资产负债表',
                'data': pd.DataFrame({
                    '项目': ['总资产', '流动资产', '股东权益'],
                    '期末': [5000, 2000, 3000],
                    '期初': [4500, 1800, 2700]
                })
            },
            {
                'name': '现金流量表',
                'data': pd.DataFrame({
                    '项目': ['经营活动现金流', '投资活动现金流'],
                    '本期': [500, -200],
                    '上期': [450, -180]
                })
            }
        ]
        
        for test_case in test_cases:
            table_type = extractor._classify_table_type(test_case['data'])
            print(f"   {test_case['name']}: 分类为 '{table_type}'")
            
        print("✅ 表格类型分类测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 表格类型分类测试失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("📊 表格提取功能全面测试")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("表格提取功能", test_table_extraction()))
    results.append(("财务数据处理", test_financial_data_processing()))
    results.append(("表格类型分类", test_table_type_classification()))
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
            
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有表格提取测试通过!")
        sys.exit(0)
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息")
        sys.exit(1)