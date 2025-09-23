"""
错误处理包装器
为SubQuestionQueryEngine和EntityExtractor添加更好的错误处理
"""

def safe_create_sub_question_engine(query_engine_tools, **kwargs):
    """安全创建SubQuestionQueryEngine"""
    try:
        from llama_index.core.query_engine import SubQuestionQueryEngine
        from llama_index.question_gen.openai import OpenAIQuestionGenerator
        
        # 尝试创建
        return SubQuestionQueryEngine.from_defaults(
            query_engine_tools=query_engine_tools,
            **kwargs
        )
    except ImportError as e:
        print(f"⚠️ SubQuestionQueryEngine依赖缺失: {e}")
        return None
    except Exception as e:
        print(f"⚠️ SubQuestionQueryEngine创建失败: {e}")
        return None

def safe_create_entity_extractor(llm=None, **kwargs):
    """安全创建EntityExtractor"""
    try:
        from llama_index.extractors.entity import EntityExtractor
        
        # 确保有llm参数
        if llm is None:
            from llama_index.core import Settings
            llm = Settings.llm
        
        return EntityExtractor(
            prediction_threshold=kwargs.get('prediction_threshold', 0.5),
            label_entities=kwargs.get('label_entities', False),
            device=kwargs.get('device', 'cpu'),
            llm=llm
        )
    except ImportError as e:
        print(f"⚠️ EntityExtractor依赖缺失: {e}")
        return None
    except Exception as e:
        print(f"⚠️ EntityExtractor创建失败: {e}")
        return None
