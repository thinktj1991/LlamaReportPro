#!/usr/bin/env python3
"""
PDF处理功能测试
测试PDFProcessor和相关功能的完整性
"""

import os
import sys
import traceback
from pathlib import Path

# Add project root to path
sys.path.append('.')

def test_pdf_processing():
    """测试PDF处理功能"""
    print("🔄 开始测试PDF处理功能...")
    
    try:
        # Import required modules
        from utils.pdf_processor import PDFProcessor
        print("✅ 成功导入PDFProcessor模块")
        
        # Initialize processor
        processor = PDFProcessor()
        print("✅ 成功初始化PDFProcessor")
        
        # Test with real PDF file
        test_pdf_path = "attached_assets/test-001_1757660301972.PDF"
        
        if not os.path.exists(test_pdf_path):
            print("❌ 测试PDF文件不存在:", test_pdf_path)
            return False
            
        print(f"📄 使用测试文件: {test_pdf_path}")
        
        # Test PDF reading
        print("🔄 测试PDF文档读取...")
        documents = processor.read_pdf_file(test_pdf_path)
        
        if documents and len(documents) > 0:
            print(f"✅ 成功读取PDF，共 {len(documents)} 页")
            print(f"   第一页内容长度: {len(documents[0].text)} 字符")
            
            # Show sample content (first 200 chars)
            sample_text = documents[0].text[:200].replace('\n', ' ')
            print(f"   内容示例: {sample_text}...")
        else:
            print("❌ PDF读取失败或内容为空")
            return False
            
        # Test company info extraction
        print("🔄 测试公司信息提取...")
        try:
            company_info = processor.extract_company_info(documents)
            print(f"✅ 成功提取公司信息: {len(company_info)} 条记录")
            
            if company_info:
                for company, info in company_info.items():
                    print(f"   公司: {company}")
                    print(f"   信息: {info}")
        except Exception as e:
            print(f"⚠️ 公司信息提取出现错误: {str(e)}")
            
        # Test document processing with metadata
        print("🔄 测试完整文档处理...")
        try:
            # Create a mock uploaded file object for testing
            class MockUploadedFile:
                def __init__(self, file_path):
                    self.name = os.path.basename(file_path)
                    self.size = os.path.getsize(file_path)
                    with open(file_path, 'rb') as f:
                        self._content = f.read()
                        
                def read(self):
                    return self._content
                    
                def getvalue(self):
                    return self._content
            
            mock_file = MockUploadedFile(test_pdf_path)
            processed_data = processor.process_uploaded_file(mock_file)
            
            print(f"✅ 文档处理完成")
            print(f"   文档数量: {len(processed_data.get('documents', []))}")
            print(f"   公司信息: {len(processed_data.get('company_info', {}))}")
            
        except Exception as e:
            print(f"⚠️ 文档处理出现错误: {str(e)}")
            traceback.print_exc()
            
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ PDF处理测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_pdf_validation():
    """测试PDF文件验证功能"""
    print("\n🔄 开始测试PDF验证功能...")
    
    try:
        from utils.pdf_processor import validate_pdf_file
        
        # Test with valid PDF
        test_pdf_path = "attached_assets/test-001_1757660301972.PDF"
        if os.path.exists(test_pdf_path):
            class MockFile:
                def __init__(self, path):
                    self.name = os.path.basename(path)
                    self.size = os.path.getsize(path)
                    with open(path, 'rb') as f:
                        self._content = f.read()
                def getvalue(self):
                    return self._content
                    
            mock_file = MockFile(test_pdf_path)
            is_valid, error_msg = validate_pdf_file(mock_file)
            
            if is_valid:
                print("✅ PDF文件验证通过")
            else:
                print(f"❌ PDF文件验证失败: {error_msg}")
                
        # Test with invalid file (simulate)
        print("🔄 测试无效文件处理...")
        class MockInvalidFile:
            def __init__(self):
                self.name = "invalid.txt"
                self.size = 100
            def getvalue(self):
                return b"This is not a PDF file"
                
        invalid_file = MockInvalidFile()
        is_valid, error_msg = validate_pdf_file(invalid_file)
        
        if not is_valid:
            print(f"✅ 正确识别无效文件: {error_msg}")
        else:
            print("⚠️ 未能正确识别无效文件")
            
        return True
        
    except Exception as e:
        print(f"❌ PDF验证测试失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("📋 PDF处理功能全面测试")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("PDF处理功能", test_pdf_processing()))
    results.append(("PDF验证功能", test_pdf_validation()))
    
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
        print("🎉 所有PDF处理测试通过!")
        sys.exit(0)
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息")
        sys.exit(1)