"""
简化配置 - 禁用有问题的功能
"""

# 禁用EntityExtractor和SubQuestionQueryEngine的标志
DISABLE_ENTITY_EXTRACTOR = True
DISABLE_SUB_QUESTION_ENGINE = True

def should_disable_entity_extractor():
    """检查是否应该禁用EntityExtractor"""
    return DISABLE_ENTITY_EXTRACTOR

def should_disable_sub_question_engine():
    """检查是否应该禁用SubQuestionQueryEngine"""
    return DISABLE_SUB_QUESTION_ENGINE

def get_safe_config():
    """获取安全配置"""
    return {
        "entity_extractor_enabled": not DISABLE_ENTITY_EXTRACTOR,
        "sub_question_engine_enabled": not DISABLE_SUB_QUESTION_ENGINE,
        "use_fallback_mode": True
    }
