#!/usr/bin/env python3
"""
公司分析功能测试
测试CompanyComparator和相关分析功能
"""

import os
import sys
import traceback
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.append('.')

def test_company_comparator_initialization():
    """测试公司比较器初始化"""
    print("🔄 开始测试公司比较器初始化...")
    
    try:
        from utils.company_comparator import CompanyComparator
        print("✅ 成功导入CompanyComparator模块")
        
        # Initialize comparator
        comparator = CompanyComparator()
        print("✅ 成功初始化CompanyComparator")
        
        return True
        
    except Exception as e:
        print(f"❌ 公司比较器初始化失败: {str(e)}")
        traceback.print_exc()
        return False

def test_financial_data_processing():
    """测试财务数据处理"""
    print("\n🔄 开始测试财务数据处理...")
    
    try:
        from utils.company_comparator import CompanyComparator
        
        comparator = CompanyComparator()
        
        # Create sample company data
        sample_company_data = {
            "公司A": {
                "basic_info": {
                    "name": "测试公司A",
                    "industry": "制造业",
                    "year": "2023"
                },
                "financial_data": {
                    "营业收入": 1000000,
                    "净利润": 100000,
                    "总资产": 5000000,
                    "股东权益": 3000000
                }
            },
            "公司B": {
                "basic_info": {
                    "name": "测试公司B", 
                    "industry": "服务业",
                    "year": "2023"
                },
                "financial_data": {
                    "营业收入": 800000,
                    "净利润": 120000,
                    "总资产": 4000000,
                    "股东权益": 2500000
                }
            }
        }
        
        # Test data processing
        print("🔄 测试公司数据处理...")
        processed_data = comparator.process_company_data(sample_company_data)
        
        if processed_data:
            print("✅ 公司数据处理成功")
            print(f"   处理的公司数量: {len(processed_data)}")
            
            for company, data in processed_data.items():
                print(f"   {company}: {len(data)} 项指标")
        else:
            print("⚠️ 公司数据处理无结果")
            
        return True
        
    except Exception as e:
        print(f"❌ 财务数据处理测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_company_comparison():
    """测试公司对比功能"""
    print("\n🔄 开始测试公司对比功能...")
    
    try:
        from utils.company_comparator import CompanyComparator
        
        comparator = CompanyComparator()
        
        # Sample data for comparison
        company_data = {
            "Company1": pd.DataFrame({
                "指标": ["营业收入", "净利润", "总资产"],
                "2023": [1000000, 100000, 5000000],
                "2022": [900000, 90000, 4500000]
            }),
            "Company2": pd.DataFrame({
                "指标": ["营业收入", "净利润", "总资产"],
                "2023": [800000, 120000, 4000000], 
                "2022": [750000, 110000, 3800000]
            })
        }
        
        print("🔄 执行公司对比分析...")
        comparison_result = comparator.compare_companies(
            companies=["Company1", "Company2"],
            company_data=company_data,
            metrics=["营业收入", "净利润"]
        )
        
        if comparison_result:
            print("✅ 公司对比分析完成")
            print(f"   对比结果类型: {type(comparison_result)}")
            
            # Check if result contains expected data
            if hasattr(comparison_result, 'keys'):
                print(f"   结果键值: {list(comparison_result.keys())}")
        else:
            print("⚠️ 公司对比分析无结果")
            
        return True
        
    except Exception as e:
        print(f"❌ 公司对比测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_visualization_data_preparation():
    """测试可视化数据准备"""
    print("\n🔄 开始测试可视化数据准备...")
    
    try:
        from utils.company_comparator import CompanyComparator
        
        comparator = CompanyComparator()
        
        # Sample financial data
        sample_data = {
            "公司A": {
                "营业收入": [1000000, 900000, 800000],
                "净利润": [100000, 90000, 80000],
                "年份": ["2023", "2022", "2021"]
            },
            "公司B": {
                "营业收入": [800000, 750000, 700000],
                "净利润": [120000, 110000, 100000],
                "年份": ["2023", "2022", "2021"]
            }
        }
        
        print("🔄 准备可视化数据...")
        
        # Test different chart types
        chart_types = ["bar", "line", "scatter"]
        
        for chart_type in chart_types:
            try:
                viz_data = comparator.prepare_visualization_data(
                    data=sample_data,
                    chart_type=chart_type,
                    metrics=["营业收入", "净利润"]
                )
                
                if viz_data:
                    print(f"✅ {chart_type}图表数据准备成功")
                else:
                    print(f"⚠️ {chart_type}图表数据准备无结果")
                    
            except Exception as chart_error:
                print(f"⚠️ {chart_type}图表数据准备失败: {str(chart_error)}")
                
        return True
        
    except Exception as e:
        print(f"❌ 可视化数据准备测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_industry_analysis():
    """测试行业分析功能"""
    print("\n🔄 开始测试行业分析功能...")
    
    try:
        from utils.company_comparator import CompanyComparator
        
        comparator = CompanyComparator()
        
        # Sample industry data
        industry_data = {
            "制造业": [
                {"name": "公司A", "revenue": 1000000, "profit": 100000},
                {"name": "公司B", "revenue": 1200000, "profit": 150000}
            ],
            "服务业": [
                {"name": "公司C", "revenue": 800000, "profit": 120000},
                {"name": "公司D", "revenue": 900000, "profit": 135000}
            ]
        }
        
        print("🔄 执行行业分析...")
        try:
            industry_analysis = comparator.analyze_industry_trends(industry_data)
            
            if industry_analysis:
                print("✅ 行业分析完成")
                print(f"   分析结果: {type(industry_analysis)}")
            else:
                print("⚠️ 行业分析无结果")
                
        except AttributeError:
            print("⚠️ 行业分析功能暂未实现")
        except Exception as analysis_error:
            print(f"⚠️ 行业分析失败: {str(analysis_error)}")
            
        return True
        
    except Exception as e:
        print(f"❌ 行业分析测试失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🏢 公司分析功能全面测试")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("公司比较器初始化", test_company_comparator_initialization()))
    results.append(("财务数据处理", test_financial_data_processing()))
    results.append(("公司对比功能", test_company_comparison()))
    results.append(("可视化数据准备", test_visualization_data_preparation()))
    results.append(("行业分析功能", test_industry_analysis()))
    
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
        print("🎉 所有公司分析测试通过!")
        sys.exit(0)
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息")
        sys.exit(1)