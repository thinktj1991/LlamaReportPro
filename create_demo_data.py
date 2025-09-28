"""
创建演示数据来展示AI功能
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_demo_financial_data():
    """创建演示财务数据"""
    
    # 创建三家示例公司的财务数据
    demo_companies = {
        "科技创新公司": {
            "company_info": {
                "industry": "科技",
                "founded": "2015",
                "employees": 1200,
                "description": "专注于人工智能和云计算的科技公司"
            },
            "financial_metrics": {
                # 基础财务指标
                "revenue": 1500000000,  # 15亿营业收入
                "net_income": 180000000,  # 1.8亿净利润
                "total_assets": 8000000000,  # 80亿总资产
                "total_liabilities": 3000000000,  # 30亿总负债
                "shareholders_equity": 5000000000,  # 50亿股东权益
                "current_assets": 4000000000,  # 40亿流动资产
                "current_liabilities": 1500000000,  # 15亿流动负债
                "cash_and_equivalents": 2000000000,  # 20亿现金
                "operating_cash_flow": 250000000,  # 2.5亿经营现金流
                
                # 计算比率
                "gross_margin": 0.65,  # 毛利率65%
                "net_margin": 0.12,   # 净利率12%
                "roe": 0.036,         # ROE 3.6%
                "roa": 0.0225,        # ROA 2.25%
                "current_ratio": 2.67, # 流动比率2.67
                "debt_to_equity": 0.6,  # 负债权益比0.6
                
                # 历史数据（用于趋势分析）
                "historical_revenue": [1000000000, 1200000000, 1350000000, 1500000000],
                "historical_net_income": [100000000, 140000000, 160000000, 180000000],
                "historical_years": ["2020", "2021", "2022", "2023"]
            },
            "risk_indicators": {
                "liquidity_risk": "low",
                "profitability_trend": "improving",
                "debt_level": "moderate",
                "cash_position": "strong"
            }
        },
        
        "传统制造企业": {
            "company_info": {
                "industry": "制造业",
                "founded": "1995",
                "employees": 3500,
                "description": "大型机械制造企业，产品出口全球"
            },
            "financial_metrics": {
                "revenue": 2200000000,  # 22亿营业收入
                "net_income": 110000000,  # 1.1亿净利润
                "total_assets": 12000000000,  # 120亿总资产
                "total_liabilities": 8000000000,  # 80亿总负债
                "shareholders_equity": 4000000000,  # 40亿股东权益
                "current_assets": 5000000000,  # 50亿流动资产
                "current_liabilities": 3000000000,  # 30亿流动负债
                "cash_and_equivalents": 800000000,  # 8亿现金
                "operating_cash_flow": 180000000,  # 1.8亿经营现金流
                
                "gross_margin": 0.35,  # 毛利率35%
                "net_margin": 0.05,   # 净利率5%
                "roe": 0.0275,        # ROE 2.75%
                "roa": 0.0092,        # ROA 0.92%
                "current_ratio": 1.67, # 流动比率1.67
                "debt_to_equity": 2.0,  # 负债权益比2.0（较高）
                
                "historical_revenue": [1800000000, 1950000000, 2100000000, 2200000000],
                "historical_net_income": [80000000, 95000000, 105000000, 110000000],
                "historical_years": ["2020", "2021", "2022", "2023"]
            },
            "risk_indicators": {
                "liquidity_risk": "medium",
                "profitability_trend": "stable",
                "debt_level": "high",
                "cash_position": "adequate"
            }
        },
        
        "新兴生物医药": {
            "company_info": {
                "industry": "生物医药",
                "founded": "2018",
                "employees": 800,
                "description": "专注于创新药物研发的生物医药公司"
            },
            "financial_metrics": {
                "revenue": 500000000,  # 5亿营业收入
                "net_income": -50000000,  # -5000万净利润（研发期亏损）
                "total_assets": 3000000000,  # 30亿总资产
                "total_liabilities": 800000000,  # 8亿总负债
                "shareholders_equity": 2200000000,  # 22亿股东权益
                "current_assets": 2000000000,  # 20亿流动资产
                "current_liabilities": 400000000,  # 4亿流动负债
                "cash_and_equivalents": 1500000000,  # 15亿现金（融资所得）
                "operating_cash_flow": -80000000,  # -8000万经营现金流
                
                "gross_margin": 0.80,  # 毛利率80%（高毛利）
                "net_margin": -0.10,  # 净利率-10%（亏损）
                "roe": -0.023,        # ROE -2.3%
                "roa": -0.017,        # ROA -1.7%
                "current_ratio": 5.0, # 流动比率5.0（现金充裕）
                "debt_to_equity": 0.36,  # 负债权益比0.36
                
                "historical_revenue": [100000000, 250000000, 380000000, 500000000],
                "historical_net_income": [-80000000, -70000000, -60000000, -50000000],
                "historical_years": ["2020", "2021", "2022", "2023"]
            },
            "risk_indicators": {
                "liquidity_risk": "low",
                "profitability_trend": "improving_losses",
                "debt_level": "low",
                "cash_position": "excellent"
            }
        }
    }
    
    return demo_companies

def save_demo_data():
    """保存演示数据到文件"""
    
    demo_data = create_demo_financial_data()
    
    # 保存为JSON文件
    with open('demo_financial_data.json', 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)
    
    print("✅ 演示数据已保存到 demo_financial_data.json")
    
    # 创建CSV格式的数据用于分析
    financial_summary = []
    
    for company_name, data in demo_data.items():
        metrics = data['financial_metrics']
        row = {
            'company': company_name,
            'industry': data['company_info']['industry'],
            'revenue': metrics['revenue'],
            'net_income': metrics['net_income'],
            'total_assets': metrics['total_assets'],
            'shareholders_equity': metrics['shareholders_equity'],
            'current_ratio': metrics['current_ratio'],
            'debt_to_equity': metrics['debt_to_equity'],
            'roe': metrics['roe'],
            'roa': metrics['roa'],
            'net_margin': metrics['net_margin']
        }
        financial_summary.append(row)
    
    df = pd.DataFrame(financial_summary)
    df.to_csv('demo_financial_summary.csv', index=False, encoding='utf-8-sig')
    
    print("✅ 财务摘要已保存到 demo_financial_summary.csv")
    
    # 创建时间序列数据
    time_series_data = []
    
    for company_name, data in demo_data.items():
        metrics = data['financial_metrics']
        for i, year in enumerate(metrics['historical_years']):
            row = {
                'company': company_name,
                'year': year,
                'revenue': metrics['historical_revenue'][i],
                'net_income': metrics['historical_net_income'][i]
            }
            time_series_data.append(row)
    
    ts_df = pd.DataFrame(time_series_data)
    ts_df.to_csv('demo_time_series.csv', index=False, encoding='utf-8-sig')
    
    print("✅ 时间序列数据已保存到 demo_time_series.csv")
    
    return demo_data

def create_demo_analysis_report():
    """创建演示分析报告"""
    
    report = """
# 📊 演示数据分析报告

## 🏢 公司概览

### 1. 科技创新公司
- **行业地位**: 科技行业领军企业
- **财务特点**: 高增长、高盈利、强现金流
- **投资亮点**: ROE稳定增长，现金充裕，负债合理

### 2. 传统制造企业  
- **行业地位**: 制造业龙头企业
- **财务特点**: 稳定增长、资产密集、负债较高
- **关注点**: 负债权益比偏高，需关注流动性管理

### 3. 新兴生物医药
- **行业地位**: 创新药研发企业
- **财务特点**: 高投入、暂时亏损、现金充裕
- **投资逻辑**: 研发驱动，长期价值，现金流管理良好

## 🔍 AI分析预期结果

### 异常检测
- 生物医药公司的负净利润会被标记为"正常异常"（研发期特征）
- 制造企业的高负债率可能触发风险警报
- 科技公司的高现金比例显示健康财务状况

### 风险分析
- **高风险**: 制造企业（高杠杆）
- **中等风险**: 生物医药（盈利不确定性）  
- **低风险**: 科技公司（财务稳健）

### 预测分析
- 科技公司：收入增长趋势明显，预测继续上升
- 制造企业：稳定增长模式，预测温和上升
- 生物医药：高增长但波动性大，需关注研发进展

## 🎯 如何使用这些数据

1. **导入数据**: 将JSON文件导入系统
2. **查看分析**: 进入AI洞察页面查看自动分析
3. **对比功能**: 使用公司对比功能横向分析
4. **问答测试**: 询问具体财务问题测试AI回答
5. **预测功能**: 查看时间序列预测结果

这些演示数据将让您充分体验LlamaReportPro的所有AI功能！
"""
    
    with open('DEMO_ANALYSIS_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ 演示分析报告已保存到 DEMO_ANALYSIS_REPORT.md")

def main():
    """主函数"""
    print("🎯 创建LlamaReportPro演示数据")
    print("="*50)
    
    # 创建并保存演示数据
    demo_data = save_demo_data()
    
    # 创建分析报告
    create_demo_analysis_report()
    
    print("\n" + "="*50)
    print("📊 演示数据创建完成！")
    print("="*50)
    
    print("\n📁 生成的文件:")
    print("  📄 demo_financial_data.json - 完整的公司财务数据")
    print("  📊 demo_financial_summary.csv - 财务指标摘要")
    print("  📈 demo_time_series.csv - 历史时间序列数据")
    print("  📋 DEMO_ANALYSIS_REPORT.md - 分析报告和使用指南")
    
    print("\n🚀 下一步操作:")
    print("  1. 启动应用: streamlit run app.py --server.port 8501")
    print("  2. 上传demo_financial_data.json文件")
    print("  3. 进入AI洞察页面查看分析结果")
    print("  4. 尝试问答系统和对比功能")
    
    print("\n💡 预期看到的AI功能:")
    print("  🔍 异常检测: 识别生物医药公司的研发期亏损模式")
    print("  ⚠️ 风险分析: 制造企业高负债风险预警")
    print("  🤖 AI洞察: 科技公司优秀财务表现分析")
    print("  📊 模式分析: 三个行业不同的财务特征")
    print("  📈 预测分析: 基于历史数据的增长预测")

if __name__ == "__main__":
    main()
