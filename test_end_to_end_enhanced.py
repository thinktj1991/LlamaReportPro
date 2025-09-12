"""
End-to-end test for enhanced LlamaIndex features with real PDF processing
"""

import os
import tempfile
import logging
from io import BytesIO
from utils.enhanced_integration import get_system_integrator, reset_system_integrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_pdf():
    """Create a simple PDF for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        
        # Create PDF with sample content
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, "测试年报 - Test Annual Report")
        
        # Add some financial table-like content
        p.setFont("Helvetica", 12)
        p.drawString(100, 700, "财务数据 Financial Data:")
        
        # Simple table structure
        y = 670
        table_data = [
            ["项目 Item", "2023年", "2024年"],
            ["营业收入 Revenue", "100,000", "120,000"], 
            ["净利润 Net Income", "15,000", "18,000"],
            ["总资产 Total Assets", "500,000", "580,000"],
            ["负债总计 Total Liabilities", "200,000", "220,000"]
        ]
        
        for row in table_data:
            x = 100
            for cell in row:
                p.drawString(x, y, cell)
                x += 150
            y -= 20
        
        # Add more content
        p.drawString(100, 500, "公司简介 Company Overview:")
        p.drawString(100, 480, "本公司是一家领先的技术公司，专注于AI和数据分析。")
        p.drawString(100, 460, "This company is a leading technology firm specializing in AI and data analytics.")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        logger.warning("reportlab not available, using minimal PDF")
        # Create minimal PDF content
        return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Test Annual Report) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
299
%%EOF"""

class MockStreamlitFile:
    """Mock Streamlit uploaded file for testing"""
    
    def __init__(self, name: str, content: bytes):
        self.name = name
        self.size = len(content)
        self.type = "application/pdf"
        self._content = content
    
    def read(self):
        return self._content
    
    def seek(self, position):
        pass
    
    def getvalue(self):
        return self._content

def test_enhanced_processing_end_to_end():
    """Test complete enhanced processing pipeline"""
    print("🧪 End-to-End Enhanced Processing Test")
    print("=" * 50)
    
    # Reset integrator for clean test
    reset_system_integrator()
    
    # Create sample PDF
    print("📄 Creating sample PDF...")
    pdf_content = create_sample_pdf()
    mock_file = MockStreamlitFile("test_annual_report.pdf", pdf_content)
    print(f"   Created PDF: {len(pdf_content)} bytes")
    
    # Get integrator
    integrator = get_system_integrator()
    system_status = integrator.get_system_status()
    
    print(f"\n🔍 System Status:")
    print(f"   Enhanced Mode: {system_status['enhanced_mode']}")
    print(f"   LlamaParse Available: {system_status['capabilities']['llamaparse_processing']}")
    print(f"   API Key Available: {system_status['environment']['llamaparse_key_available']}")
    
    # Test PDF processing
    print(f"\n⚙️ Processing PDF...")
    try:
        result = integrator.process_uploaded_file(mock_file)
        
        print(f"   Processing Method: {result.get('processing_method', 'unknown')}")
        print(f"   Success: {not result.get('error', False)}")
        
        if result.get('error'):
            print(f"   Error: {result.get('error_message', 'Unknown error')}")
        else:
            print(f"   Document Count: {len(result.get('documents', []))}")
            
            # Check if enhanced content exists
            if 'enhanced_content' in result:
                print(f"   Enhanced Content: Available")
                enhanced = result['enhanced_content']
                print(f"   Pages Processed: {len(enhanced.get('pages', []))}")
                print(f"   Tables Found: {sum(len(p.get('tables', [])) for p in enhanced.get('pages', []))}")
            else:
                print(f"   Enhanced Content: Not available (using legacy)")
        
        # Test processing statistics
        stats = integrator.get_processing_stats(result)
        if 'integration_info' in stats:
            integration_info = stats['integration_info']
            print(f"\n📊 Integration Statistics:")
            print(f"   Enhanced Mode: {integration_info['enhanced_mode']}")
            print(f"   Processing Method: {integration_info['processing_method']}")
            print(f"   Components Available: {integration_info['components_available']}")
        
        return result
        
    except Exception as e:
        print(f"   Processing failed: {str(e)}")
        return {"error": True, "error_message": str(e)}

def test_rag_integration():
    """Test RAG index building with enhanced features"""
    print(f"\n🤖 Testing RAG Integration...")
    
    integrator = get_system_integrator()
    
    # Test with empty data (should handle gracefully)
    empty_docs = {}
    empty_tables = {}
    
    try:
        success = integrator.build_enhanced_rag_index(empty_docs, empty_tables)
        print(f"   RAG Index Build: {'Success' if success else 'Failed'}")
        
        # Test query system
        test_question = "公司的收入是多少？"
        query_result = integrator.query_system(test_question)
        
        print(f"   Query Method: {query_result.get('query_method', 'unknown')}")
        print(f"   Query Success: {not query_result.get('error', False)}")
        print(f"   Answer Length: {len(query_result.get('answer', ''))}")
        
        return query_result
        
    except Exception as e:
        print(f"   RAG Integration failed: {str(e)}")
        return {"error": True, "error_message": str(e)}

def test_environment_configuration():
    """Test environment configuration and secrets"""
    print(f"\n🔑 Testing Environment Configuration...")
    
    # Check for Replit Secrets
    api_key = os.getenv('LLAMA_CLOUD_API_KEY')
    enhanced_flag = os.getenv('USE_ENHANCED_LLAMAINDEX', 'false')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"   LLAMA_CLOUD_API_KEY: {'Set' if api_key else 'Missing'}")
    print(f"   USE_ENHANCED_LLAMAINDEX: {enhanced_flag}")
    print(f"   OPENAI_API_KEY: {'Set' if openai_key else 'Missing'}")
    
    if not api_key:
        print(f"   💡 To enable enhanced features, set LLAMA_CLOUD_API_KEY in Replit Secrets")
    
    if not openai_key:
        print(f"   ⚠️  OpenAI API key missing - some features may not work")

def main():
    """Run complete end-to-end test"""
    print("🚀 Enhanced LlamaIndex End-to-End Test")
    print("=" * 60)
    
    # Test 1: Environment Configuration
    try:
        test_environment_configuration()
        env_test_success = True
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        env_test_success = False
    
    # Test 2: Enhanced Processing
    try:
        processing_result = test_enhanced_processing_end_to_end()
        processing_success = not processing_result.get('error', False)
    except Exception as e:
        print(f"❌ Processing test failed: {e}")
        processing_success = False
    
    # Test 3: RAG Integration  
    try:
        rag_result = test_rag_integration()
        rag_success = not rag_result.get('error', False)
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        rag_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Environment Configuration: {'✅' if env_test_success else '❌'}")
    print(f"   Enhanced Processing: {'✅' if processing_success else '❌'}")
    print(f"   RAG Integration: {'✅' if rag_success else '❌'}")
    
    overall_success = env_test_success and processing_success and rag_success
    print(f"   Overall Result: {'✅ ALL PASS' if overall_success else '⚠️  PARTIAL SUCCESS'}")
    
    if not overall_success:
        print(f"\n💡 Next Steps:")
        if not env_test_success:
            print(f"   - Set API keys in Replit Secrets")
        if not processing_success:
            print(f"   - Check enhanced processing configuration")
        if not rag_success:
            print(f"   - Verify RAG system integration")
    
    print("=" * 60)
    return overall_success

if __name__ == "__main__":
    main()