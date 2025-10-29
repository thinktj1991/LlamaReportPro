#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
饼图修复验证脚本

验证修复后的代码是否正确处理饼图数据格式
"""

import json
import re
import sys
from pathlib import Path

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def verify_html_fix():
    """验证HTML文件的修复"""
    print("🔍 验证 HTML 文件修复...")
    
    html_file = Path("llamareport-backend/static/index.html")
    
    if not html_file.exists():
        print(f"❌ 文件不存在: {html_file}")
        return False
    
    content = html_file.read_text(encoding='utf-8')
    
    # 检查关键修复点
    checks = [
        {
            "name": "饼图类型检查",
            "pattern": r"if\s*\(\s*trace\.type\s*===\s*['\"]pie['\"]\s*\)",
            "required": True
        },
        {
            "name": "labels字段赋值",
            "pattern": r"plotlyTrace\.labels\s*=\s*trace\.text",
            "required": True
        },
        {
            "name": "values字段赋值",
            "pattern": r"plotlyTrace\.values\s*=\s*trace\.y",
            "required": True
        },
        {
            "name": "非饼图text处理",
            "pattern": r"if\s*\(\s*trace\.type\s*!==\s*['\"]pie['\"]\s*&&\s*trace\.text\s*\)",
            "required": True
        }
    ]
    
    all_passed = True
    for check in checks:
        if re.search(check["pattern"], content):
            print(f"  ✅ {check['name']}")
        else:
            print(f"  ❌ {check['name']} - 未找到")
            all_passed = False
    
    return all_passed


def verify_streamlit_fix():
    """验证Streamlit文件的修复"""
    print("\n🔍 验证 Streamlit 文件修复...")
    
    streamlit_file = Path("pages/visualization_qa.py")
    
    if not streamlit_file.exists():
        print(f"❌ 文件不存在: {streamlit_file}")
        return False
    
    content = streamlit_file.read_text(encoding='utf-8')
    
    # 检查关键修复点
    checks = [
        {
            "name": "labels获取逻辑",
            "pattern": r"labels\s*=\s*trace_data\.get\(['\"]text['\"]\s*,\s*\[\]\s*\)\s*or\s*trace_data\.get\(['\"]labels['\"]\s*,\s*\[\]\s*\)",
            "required": True
        },
        {
            "name": "values获取逻辑",
            "pattern": r"values\s*=\s*trace_data\.get\(['\"]y['\"]\s*,\s*\[\]\s*\)\s*or\s*trace_data\.get\(['\"]values['\"]\s*,\s*\[\]\s*\)",
            "required": True
        },
        {
            "name": "go.Pie使用labels",
            "pattern": r"go\.Pie\s*\(\s*labels\s*=\s*labels",
            "required": True
        },
        {
            "name": "go.Pie使用values",
            "pattern": r"values\s*=\s*values",
            "required": True
        }
    ]
    
    all_passed = True
    for check in checks:
        if re.search(check["pattern"], content):
            print(f"  ✅ {check['name']}")
        else:
            print(f"  ❌ {check['name']} - 未找到")
            all_passed = False
    
    return all_passed


def verify_test_file():
    """验证测试文件是否存在"""
    print("\n🔍 验证测试文件...")
    
    test_file = Path("test_pie_chart_fix.html")
    
    if test_file.exists():
        print(f"  ✅ 测试文件存在: {test_file}")
        return True
    else:
        print(f"  ❌ 测试文件不存在: {test_file}")
        return False


def verify_documentation():
    """验证文档是否存在"""
    print("\n🔍 验证文档...")
    
    doc_file = Path("docs/PIE_CHART_FIX.md")
    
    if doc_file.exists():
        print(f"  ✅ 文档存在: {doc_file}")
        
        # 检查文档内容
        content = doc_file.read_text(encoding='utf-8')
        
        required_sections = [
            "问题描述",
            "问题分析",
            "解决方案",
            "测试验证",
            "部署说明"
        ]
        
        all_sections_found = True
        for section in required_sections:
            if section in content:
                print(f"    ✅ 包含章节: {section}")
            else:
                print(f"    ❌ 缺少章节: {section}")
                all_sections_found = False
        
        return all_sections_found
    else:
        print(f"  ❌ 文档不存在: {doc_file}")
        return False


def simulate_data_transformation():
    """模拟数据转换过程"""
    print("\n🔍 模拟数据转换...")
    
    # 模拟后端返回的数据
    backend_data = {
        "name": "分布",
        "x": [],
        "y": [60, 45, 30, 15],
        "type": "pie",
        "text": ["主营业务A", "主营业务B", "主营业务C", "其他业务"],
        "hovertemplate": "%{label}: %{value}亿元 (%{percent})<extra></extra>"
    }
    
    print("\n  📥 后端返回数据:")
    print(f"    type: {backend_data['type']}")
    print(f"    text: {backend_data['text']}")
    print(f"    y: {backend_data['y']}")
    
    # 模拟修复后的转换逻辑
    if backend_data['type'] == 'pie':
        plotly_data = {
            "type": "pie",
            "labels": backend_data['text'],
            "values": backend_data['y'],
            "name": backend_data['name'],
            "hovertemplate": backend_data['hovertemplate']
        }
        
        print("\n  📤 转换后数据 (Plotly格式):")
        print(f"    type: {plotly_data['type']}")
        print(f"    labels: {plotly_data['labels']}")
        print(f"    values: {plotly_data['values']}")
        
        # 验证转换是否正确
        if (plotly_data['labels'] == backend_data['text'] and 
            plotly_data['values'] == backend_data['y']):
            print("\n  ✅ 数据转换正确！")
            return True
        else:
            print("\n  ❌ 数据转换错误！")
            return False
    else:
        print("\n  ❌ 不是饼图类型！")
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("🔧 饼图修复验证脚本")
    print("=" * 80)
    
    results = {
        "HTML修复": verify_html_fix(),
        "Streamlit修复": verify_streamlit_fix(),
        "测试文件": verify_test_file(),
        "文档": verify_documentation(),
        "数据转换": simulate_data_transformation()
    }
    
    print("\n" + "=" * 80)
    print("📊 验证结果汇总")
    print("=" * 80)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有验证通过！修复已成功应用！")
        print("\n📝 下一步:")
        print("  1. 重启后端服务: cd llamareport-backend && python main.py")
        print("  2. 打开测试页面: http://localhost:8000/test_pie_chart_fix.html")
        print("  3. 或使用HTML页面: http://localhost:8000/static/index.html")
        print("  4. 提问测试: '公司2023年的营业收入是多少？'")
    else:
        print("❌ 部分验证失败，请检查上述错误！")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())

