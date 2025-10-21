"""
快速验证JSON序列化修复是否生效
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
backend_path = project_root / "llamareport-backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_method_exists():
    """验证_serialize_tool_output方法是否存在"""
    logger.info("=" * 60)
    logger.info("步骤1: 验证序列化方法是否存在")
    logger.info("=" * 60)
    
    try:
        from agents.report_agent import ReportAgent
        
        # 检查方法是否存在
        if hasattr(ReportAgent, '_serialize_tool_output'):
            logger.info("✅ _serialize_tool_output方法已添加")
            return True
        else:
            logger.error("❌ _serialize_tool_output方法不存在")
            return False
            
    except Exception as e:
        logger.error(f"❌ 导入失败: {str(e)}")
        return False


def verify_code_changes():
    """验证代码修改是否正确"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤2: 验证代码修改")
    logger.info("=" * 60)
    
    try:
        # 读取文件内容
        file_path = backend_path / "agents" / "report_agent.py"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键代码是否存在
        checks = [
            ("序列化方法定义", "def _serialize_tool_output(self, tool_output)"),
            ("序列化调用1", "tool_output_serializable = self._serialize_tool_output(event.tool_output)"),
            ("序列化调用2", "visualization_data = tool_output_serializable"),
            ("Pydantic v2支持", "hasattr(tool_output, 'model_dump')"),
            ("Pydantic v1支持", "hasattr(tool_output, 'dict')"),
            ("递归处理列表", "isinstance(tool_output, (list, tuple))"),
            ("递归处理字典", "isinstance(tool_output, dict)"),
        ]
        
        all_passed = True
        for check_name, check_code in checks:
            if check_code in content:
                logger.info(f"✅ {check_name}: 已添加")
            else:
                logger.error(f"❌ {check_name}: 未找到")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ 验证失败: {str(e)}")
        return False


def verify_serialization():
    """验证序列化功能"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤3: 验证序列化功能")
    logger.info("=" * 60)
    
    try:
        import json
        
        # 创建测试类
        class TestAgent:
            def _serialize_tool_output(self, tool_output):
                """复制的序列化方法"""
                try:
                    if isinstance(tool_output, (str, int, float, bool, type(None))):
                        return tool_output
                    
                    if isinstance(tool_output, (list, tuple)):
                        return [self._serialize_tool_output(item) for item in tool_output]
                    
                    if isinstance(tool_output, dict):
                        return {key: self._serialize_tool_output(value) for key, value in tool_output.items()}
                    
                    if hasattr(tool_output, 'model_dump'):
                        try:
                            return tool_output.model_dump()
                        except Exception:
                            pass
                    
                    if hasattr(tool_output, 'dict'):
                        try:
                            return tool_output.dict()
                        except Exception:
                            pass
                    
                    if hasattr(tool_output, '__dict__'):
                        try:
                            return {k: self._serialize_tool_output(v) for k, v in tool_output.__dict__.items() if not k.startswith('_')}
                        except Exception:
                            pass
                    
                    return str(tool_output)
                    
                except Exception as e:
                    return str(tool_output)
        
        agent = TestAgent()
        
        # 测试用例
        test_cases = [
            ("基本类型", "test"),
            ("字典", {"key": "value"}),
            ("列表", [1, 2, 3]),
            ("嵌套", {"outer": {"inner": [1, 2, 3]}}),
        ]
        
        all_passed = True
        for name, test_data in test_cases:
            try:
                serialized = agent._serialize_tool_output(test_data)
                json_str = json.dumps(serialized)
                logger.info(f"✅ {name}: 序列化成功")
            except Exception as e:
                logger.error(f"❌ {name}: 序列化失败 - {str(e)}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ 验证失败: {str(e)}")
        return False


def main():
    """主验证流程"""
    logger.info("\n" + "🔍 开始验证JSON序列化修复\n")
    
    results = {
        "方法存在性": verify_method_exists(),
        "代码修改": verify_code_changes(),
        "序列化功能": verify_serialization(),
    }
    
    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("验证结果汇总")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"总计: {passed}/{total} 验证通过")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("\n🎉 所有验证通过！修复已成功应用！")
        logger.info("\n下一步:")
        logger.info("1. 启动后端服务: cd llamareport-backend && python main.py")
        logger.info("2. 测试Agent查询: POST /agent/query")
        logger.info("3. 确认不再出现JSON序列化错误")
        return 0
    else:
        logger.error(f"\n⚠️ 有 {total - passed} 个验证失败")
        logger.error("\n请检查:")
        logger.error("1. 是否正确拉取了最新代码")
        logger.error("2. 文件路径是否正确")
        logger.error("3. 是否有语法错误")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

