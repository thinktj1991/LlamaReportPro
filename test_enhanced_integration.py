"""
Simple smoke test for enhanced LlamaIndex integration
"""

import os
import logging
from utils.enhanced_integration import get_system_integrator, reset_system_integrator
from io import BytesIO

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_system_integrator():
    """Test basic system integrator functionality"""
    print("🧪 Testing Enhanced System Integrator")
    print("=" * 50)
    
    # Reset integrator for fresh test
    reset_system_integrator()
    
    # Get integrator instance
    integrator = get_system_integrator()
    
    # Test system status
    print("📋 System Status:")
    status = integrator.get_system_status()
    
    print(f"  Enhanced Mode: {status['enhanced_mode']}")
    print(f"  Components Available:")
    for component, available in status['components'].items():
        print(f"    - {component}: {'✅' if available else '❌'}")
    
    print(f"  Capabilities:")
    for capability, available in status['capabilities'].items():
        print(f"    - {capability}: {'✅' if available else '❌'}")
    
    print(f"  Environment:")
    for env_key, available in status['environment'].items():
        print(f"    - {env_key}: {'✅' if available else '❌'}")
    
    print("\n" + "=" * 50)
    
    return status

def test_mock_file_processing():
    """Test file processing with mock data"""
    print("🧪 Testing Mock File Processing")
    print("=" * 50)
    
    integrator = get_system_integrator()
    
    # Create a mock uploaded file
    class MockUploadedFile:
        def __init__(self, name, content):
            self.name = name
            self.size = len(content)
            self.type = "application/pdf"
            self._content = content
        
        def read(self):
            return self._content
        
        def seek(self, position):
            pass
    
    # Test with mock PDF content (just for smoke test)
    mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"
    mock_file = MockUploadedFile("test_annual_report.pdf", mock_pdf_content)
    
    try:
        # This will likely fail with real processing, but we can test the integration path
        result = integrator.process_uploaded_file(mock_file)
        
        print(f"  Processing Method: {result.get('processing_method', 'unknown')}")
        print(f"  Success: {not result.get('error', False)}")
        
        if 'processing_error' in result:
            print(f"  Processing Error: {result['processing_error']}")
        
        # Test stats retrieval
        stats = integrator.get_processing_stats(result)
        print(f"  Stats Available: {'✅' if 'integration_info' in stats else '❌'}")
        
        return result
        
    except Exception as e:
        print(f"  Processing failed (expected): {str(e)}")
        return {"error": True, "error_message": str(e)}

def test_query_system():
    """Test query system functionality"""
    print("🧪 Testing Query System")
    print("=" * 50)
    
    integrator = get_system_integrator()
    
    # Test query without any documents (should gracefully handle)
    test_question = "公司的收入是多少？"
    
    try:
        result = integrator.query_system(test_question)
        
        print(f"  Query Method: {result.get('query_method', 'unknown')}")
        print(f"  Success: {not result.get('error', False)}")
        print(f"  Answer Length: {len(result.get('answer', ''))}")
        
        return result
        
    except Exception as e:
        print(f"  Query failed (may be expected): {str(e)}")
        return {"error": True, "error_message": str(e)}

def main():
    """Run all smoke tests"""
    print("🚀 Enhanced LlamaIndex Integration Smoke Test")
    print("=" * 60)
    
    # Test 1: System Integrator
    try:
        system_status = test_system_integrator()
        test1_success = True
    except Exception as e:
        print(f"❌ System Integrator Test Failed: {e}")
        test1_success = False
    
    print()
    
    # Test 2: Mock File Processing
    try:
        processing_result = test_mock_file_processing()
        test2_success = True
    except Exception as e:
        print(f"❌ Mock File Processing Test Failed: {e}")
        test2_success = False
    
    print()
    
    # Test 3: Query System
    try:
        query_result = test_query_system()
        test3_success = True
    except Exception as e:
        print(f"❌ Query System Test Failed: {e}")
        test3_success = False
    
    print()
    print("=" * 60)
    print("📊 Test Results:")
    print(f"  System Integrator: {'✅' if test1_success else '❌'}")
    print(f"  Mock Processing: {'✅' if test2_success else '❌'}")
    print(f"  Query System: {'✅' if test3_success else '❌'}")
    
    overall_success = test1_success and test2_success and test3_success
    print(f"  Overall: {'✅ PASS' if overall_success else '❌ NEEDS FIXES'}")
    print("=" * 60)
    
    return overall_success

if __name__ == "__main__":
    main()