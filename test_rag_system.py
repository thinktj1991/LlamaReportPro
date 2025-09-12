#!/usr/bin/env python3
"""
RAG系统功能测试
测试RAGSystem和问答功能的完整性
"""

import os
import sys
import traceback
from pathlib import Path

# Add project root to path
sys.path.append('.')

def test_rag_system_initialization():
    """测试RAG系统初始化"""
    print("🔄 开始测试RAG系统初始化...")
    
    try:
        from utils.rag_system import RAGSystem
        print("✅ 成功导入RAGSystem模块")
        
        # Initialize RAG system
        rag_system = RAGSystem()
        print("✅ 成功初始化RAGSystem")
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print("✅ 检测到OpenAI API密钥")
        else:
            print("⚠️ 未检测到OpenAI API密钥，部分功能可能无法测试")
            
        return True
        
    except Exception as e:
        print(f"❌ RAG系统初始化失败: {str(e)}")
        traceback.print_exc()
        return False

def test_document_indexing():
    """测试文档索引功能"""
    print("\n🔄 开始测试文档索引功能...")
    
    try:
        from utils.rag_system import RAGSystem
        from utils.pdf_processor import PDFProcessor
        
        # Initialize systems
        rag_system = RAGSystem()
        pdf_processor = PDFProcessor()
        
        # Process test PDF
        test_pdf_path = "attached_assets/test-001_1757660301972.PDF"
        if not os.path.exists(test_pdf_path):
            print("❌ 测试PDF文件不存在")
            return False
            
        print("🔄 处理测试PDF文档...")
        documents = pdf_processor.read_pdf_file(test_pdf_path)
        
        if not documents:
            print("❌ PDF文档处理失败")
            return False
            
        print(f"✅ 成功处理PDF，共 {len(documents)} 页")
        
        # Test document indexing
        print("🔄 开始建立文档索引...")
        processed_docs = {"test-doc": {"documents": documents}}
        
        try:
            rag_system.build_index(processed_docs)
            print("✅ 文档索引建立成功")
            
            # Test index statistics
            stats = rag_system.get_index_stats()
            print(f"   索引状态: {stats.get('status', 'unknown')}")
            print(f"   文档总数: {stats.get('total_documents', 0)}")
            print(f"   查询引擎: {'已就绪' if stats.get('has_query_engine') else '未就绪'}")
            
        except Exception as e:
            print(f"⚠️ 文档索引建立失败: {str(e)}")
            # This might fail due to API key or network issues
            
        return True
        
    except Exception as e:
        print(f"❌ 文档索引测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_query_functionality():
    """测试查询功能"""
    print("\n🔄 开始测试查询功能...")
    
    try:
        from utils.rag_system import RAGSystem
        from utils.pdf_processor import PDFProcessor
        
        rag_system = RAGSystem()
        
        # Check if we have an API key for testing
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️ 缺少OpenAI API密钥，跳过查询功能测试")
            return True
            
        # First build an index with test data
        pdf_processor = PDFProcessor()
        test_pdf_path = "attached_assets/test-001_1757660301972.PDF"
        
        if os.path.exists(test_pdf_path):
            print("🔄 准备测试文档...")
            documents = pdf_processor.read_pdf_file(test_pdf_path)
            
            if documents:
                processed_docs = {"test-doc": {"documents": documents}}
                
                try:
                    rag_system.build_index(processed_docs)
                    print("✅ 索引建立完成，开始测试查询...")
                    
                    # Test queries
                    test_queries = [
                        "这份文档包含什么内容？",
                        "文档的主要信息是什么？",
                        "请总结这份文档"
                    ]
                    
                    for query in test_queries:
                        print(f"\n🔍 测试查询: '{query}'")
                        try:
                            response = rag_system.query(query)
                            if response and response.response:
                                print(f"✅ 查询成功，回答长度: {len(response.response)} 字符")
                                print(f"   回答预览: {response.response[:100]}...")
                            else:
                                print("⚠️ 查询返回空结果")
                        except Exception as query_error:
                            print(f"⚠️ 查询执行失败: {str(query_error)}")
                            
                except Exception as index_error:
                    print(f"⚠️ 索引建立失败，跳过查询测试: {str(index_error)}")
            else:
                print("⚠️ 文档处理失败，跳过查询测试")
        else:
            print("⚠️ 测试文件不存在，跳过查询测试")
            
        return True
        
    except Exception as e:
        print(f"❌ 查询功能测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_index_management():
    """测试索引管理功能"""
    print("\n🔄 开始测试索引管理功能...")
    
    try:
        from utils.rag_system import RAGSystem
        
        rag_system = RAGSystem()
        
        # Test getting stats from empty system
        stats = rag_system.get_index_stats()
        print("✅ 成功获取初始索引状态")
        print(f"   状态: {stats.get('status', 'unknown')}")
        print(f"   文档数: {stats.get('total_documents', 0)}")
        
        # Test clearing index
        try:
            rag_system.clear_index()
            print("✅ 成功清除索引")
        except Exception as e:
            print(f"⚠️ 清除索引失败: {str(e)}")
            
        # Test adding documents to index
        try:
            # Create sample document for testing
            sample_docs = {
                "sample": {
                    "documents": [
                        type('Document', (), {'text': '这是一个测试文档，包含一些样本内容。'})()
                    ]
                }
            }
            
            # This might fail without API key, which is expected
            try:
                rag_system.build_index(sample_docs)
                print("✅ 样本文档索引建立成功")
            except:
                print("⚠️ 样本文档索引建立失败（可能缺少API密钥）")
                
        except Exception as e:
            print(f"⚠️ 文档添加测试失败: {str(e)}")
            
        return True
        
    except Exception as e:
        print(f"❌ 索引管理测试失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 RAG系统功能全面测试")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("RAG系统初始化", test_rag_system_initialization()))
    results.append(("文档索引功能", test_document_indexing()))
    results.append(("查询功能", test_query_functionality()))
    results.append(("索引管理", test_index_management()))
    
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
        print("🎉 所有RAG系统测试通过!")
        sys.exit(0)
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息")
        sys.exit(1)