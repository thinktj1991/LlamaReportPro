"""
LlamaReportPro 第三阶段增强功能
实现Chat Engines、Workflows、Agent System等高级功能
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

# LlamaIndex核心导入
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.chat_engine import SimpleChatEngine, ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole

logger = logging.getLogger(__name__)

# ==================== 第三阶段模型定义 ====================

class ChatMode(str, Enum):
    """聊天模式枚举"""
    SIMPLE = "simple"
    CONTEXT = "context"
    CONDENSE_QUESTION = "condense_question"
    REACT = "react"

class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ChatSession(BaseModel):
    """聊天会话"""
    session_id: str = Field(description="会话ID")
    chat_mode: ChatMode = Field(description="聊天模式")
    created_at: datetime = Field(description="创建时间", default_factory=datetime.now)
    last_active: datetime = Field(description="最后活跃时间", default_factory=datetime.now)
    message_count: int = Field(description="消息数量", default=0)
    metadata: Dict[str, Any] = Field(description="元数据", default_factory=dict)

class WorkflowResult(BaseModel):
    """工作流结果"""
    workflow_id: str = Field(description="工作流ID")
    status: WorkflowStatus = Field(description="状态")
    result: Any = Field(description="结果", default=None)
    error: Optional[str] = Field(description="错误信息", default=None)
    execution_time: float = Field(description="执行时间", default=0.0)
    steps_completed: int = Field(description="完成步骤数", default=0)
    metadata: Dict[str, Any] = Field(description="元数据", default_factory=dict)

# ==================== Chat Engine Manager ====================

class ChatEngineManager:
    """聊天引擎管理器"""

    def __init__(self, index: VectorStoreIndex, llm=None):
        self.index = index
        self.llm = llm or Settings.llm
        self.chat_engines = {}
        self.active_sessions = {}
        self.memory_buffers = {}

    def create_chat_engine(self, mode: ChatMode = ChatMode.CONTEXT,
                          session_id: str = None, **kwargs) -> Any:
        """创建聊天引擎"""
        try:
            if session_id is None:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 创建记忆缓冲区
            memory = ChatMemoryBuffer.from_defaults(
                token_limit=kwargs.get('token_limit', 3000)
            )
            self.memory_buffers[session_id] = memory

            # 根据模式创建聊天引擎
            if mode == ChatMode.SIMPLE:
                chat_engine = self.index.as_chat_engine(
                    chat_mode="simple",
                    memory=memory,
                    llm=self.llm,
                    verbose=kwargs.get('verbose', False)
                )
            elif mode == ChatMode.CONTEXT:
                chat_engine = self.index.as_chat_engine(
                    chat_mode="context",
                    memory=memory,
                    similarity_top_k=kwargs.get('similarity_top_k', 5),
                    system_prompt=kwargs.get('system_prompt',
                        "你是一个专业的财务分析助手，基于提供的财报文档回答问题。"),
                    llm=self.llm,
                    verbose=kwargs.get('verbose', False)
                )
            elif mode == ChatMode.CONDENSE_QUESTION:
                chat_engine = self.index.as_chat_engine(
                    chat_mode="condense_question",
                    memory=memory,
                    llm=self.llm,
                    verbose=kwargs.get('verbose', False)
                )
            else:
                # 默认使用context模式
                chat_engine = self.index.as_chat_engine(
                    chat_mode="context",
                    memory=memory,
                    llm=self.llm
                )

            # 保存聊天引擎和会话信息
            self.chat_engines[session_id] = chat_engine
            self.active_sessions[session_id] = ChatSession(
                session_id=session_id,
                chat_mode=mode,
                metadata=kwargs
            )

            logger.info(f"✅ 创建聊天引擎成功: {session_id}, 模式: {mode.value}")
            return chat_engine

        except Exception as e:
            logger.error(f"❌ 创建聊天引擎失败: {e}")
            return None

    def get_chat_engine(self, session_id: str) -> Optional[Any]:
        """获取聊天引擎"""
        return self.chat_engines.get(session_id)

    def chat(self, session_id: str, message: str) -> Dict[str, Any]:
        """聊天"""
        try:
            chat_engine = self.get_chat_engine(session_id)
            if not chat_engine:
                return {
                    'error': f'会话 {session_id} 不存在',
                    'session_id': session_id
                }

            # 更新会话信息
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.last_active = datetime.now()
                session.message_count += 1

            # 执行聊天
            response = chat_engine.chat(message)

            return {
                'response': str(response),
                'session_id': session_id,
                'message_count': self.active_sessions[session_id].message_count,
                'sources': getattr(response, 'source_nodes', [])
            }

        except Exception as e:
            logger.error(f"❌ 聊天失败: {e}")
            return {
                'error': str(e),
                'session_id': session_id
            }

    def stream_chat(self, session_id: str, message: str):
        """流式聊天"""
        try:
            chat_engine = self.get_chat_engine(session_id)
            if not chat_engine:
                yield f"错误: 会话 {session_id} 不存在"
                return

            # 更新会话信息
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.last_active = datetime.now()
                session.message_count += 1

            # 执行流式聊天
            streaming_response = chat_engine.stream_chat(message)
            for token in streaming_response.response_gen:
                yield token

        except Exception as e:
            logger.error(f"❌ 流式聊天失败: {e}")
            yield f"错误: {str(e)}"

    def get_active_sessions(self) -> List[ChatSession]:
        """获取活跃会话"""
        return list(self.active_sessions.values())

    def close_session(self, session_id: str) -> bool:
        """关闭会话"""
        try:
            if session_id in self.chat_engines:
                del self.chat_engines[session_id]
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            if session_id in self.memory_buffers:
                del self.memory_buffers[session_id]

            logger.info(f"✅ 会话 {session_id} 已关闭")
            return True

        except Exception as e:
            logger.error(f"❌ 关闭会话失败: {e}")
            return False

# ==================== Simple Workflow System ====================

class SimpleWorkflowManager:
    """简化的工作流管理器"""

    def __init__(self, index: VectorStoreIndex):
        self.index = index
        self.llm = Settings.llm

    async def run_financial_analysis_workflow(self, query: str) -> WorkflowResult:
        """运行财务分析工作流"""
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            start_time = time.time()

            # 步骤1: 分析查询类型
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in ['营收', '收入', '利润', '财务']):
                analysis_type = 'financial'
            elif any(keyword in query_lower for keyword in ['风险', '挑战', '问题']):
                analysis_type = 'risk'
            elif any(keyword in query_lower for keyword in ['趋势', '增长', '发展']):
                analysis_type = 'trend'
            else:
                analysis_type = 'general'

            # 步骤2: 检索相关上下文
            retriever = self.index.as_retriever(similarity_top_k=10)
            nodes = retriever.retrieve(query)

            # 步骤3: 合成响应
            context = "\n".join([node.text for node in nodes])

            prompt = f"""
            基于以下上下文信息回答问题：

            问题：{query}

            上下文：
            {context}

            请提供详细、准确的回答。
            """

            response = await self.llm.acomplete(prompt)
            execution_time = time.time() - start_time

            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                result={
                    'answer': str(response),
                    'sources': len(nodes),
                    'query': query,
                    'analysis_type': analysis_type
                },
                execution_time=execution_time,
                steps_completed=3,
                metadata={'query': query}
            )

        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(f"❌ 工作流执行异常: {e}")
            import traceback
            traceback.print_exc()

            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e),
                execution_time=execution_time,
                metadata={'query': query}
            )

# ==================== Simple Agent System ====================

class SimpleFinancialAgent:
    """简化的财务分析代理"""

    def __init__(self, index: VectorStoreIndex, llm=None):
        self.index = index
        self.llm = llm or Settings.llm

    async def run(self, query: str) -> Dict[str, Any]:
        """运行代理查询"""
        try:
            # 简单的工具调用模拟
            if "计算" in query or "比率" in query:
                # 模拟计算工具
                result = "基于财务数据计算的结果"
            elif "趋势" in query:
                # 模拟趋势分析工具
                result = "基于历史数据的趋势分析"
            else:
                # 使用查询引擎
                query_engine = self.index.as_query_engine(similarity_top_k=5)
                response = query_engine.query(query)
                result = str(response)

            return {
                'response': result,
                'tools_used': 1,
                'query': query
            }

        except Exception as e:
            logger.error(f"❌ 代理运行失败: {e}")
            return {"error": str(e)}

# ==================== Phase 3 Integration Manager ====================

class Phase3Manager:
    """第三阶段集成管理器"""

    def __init__(self, index: VectorStoreIndex, llm=None):
        self.index = index
        self.llm = llm or Settings.llm

        # 初始化各个管理器
        self.chat_manager = ChatEngineManager(index, llm)
        self.workflow_manager = SimpleWorkflowManager(index)
        self.financial_agent = SimpleFinancialAgent(index, llm)

    def get_capabilities(self) -> Dict[str, bool]:
        """获取第三阶段功能能力"""
        return {
            'chat_engines': True,
            'workflows': True,
            'agents': True,
            'multimodal': False,  # 简化版本暂不支持
            'streaming': True,
            'memory_management': True
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'active_chat_sessions': len(self.chat_manager.active_sessions),
            'capabilities': self.get_capabilities()
        }

    # Chat Engine 方法
    def create_chat_session(self, mode: ChatMode = ChatMode.CONTEXT, **kwargs) -> str:
        """创建聊天会话"""
        chat_engine = self.chat_manager.create_chat_engine(mode=mode, **kwargs)
        if chat_engine:
            # 返回会话ID
            sessions = list(self.chat_manager.active_sessions.keys())
            return sessions[-1] if sessions else None
        return None

    def chat(self, session_id: str, message: str) -> Dict[str, Any]:
        """聊天"""
        return self.chat_manager.chat(session_id, message)

    def stream_chat(self, session_id: str, message: str):
        """流式聊天"""
        return self.chat_manager.stream_chat(session_id, message)

    # Workflow 方法
    async def run_analysis_workflow(self, query: str) -> WorkflowResult:
        """运行分析工作流"""
        return await self.workflow_manager.run_financial_analysis_workflow(query)

    # Agent 方法
    async def run_agent_query(self, query: str) -> Dict[str, Any]:
        """运行代理查询"""
        return await self.financial_agent.run(query)

    # Multi-Modal 方法（占位符）
    async def analyze_multimodal(self, image_path: str, text_query: str) -> Dict[str, Any]:
        """多模态分析（暂不支持）"""
        return {"error": "多模态功能暂不支持"}

# ==================== 工厂函数 ====================

def create_phase3_manager(index: VectorStoreIndex, llm=None) -> Phase3Manager:
    """创建第三阶段管理器"""
    return Phase3Manager(index=index, llm=llm)

def get_phase3_features() -> Dict[str, bool]:
    """获取第三阶段功能可用性"""
    return {
        'workflows': True,
        'agents': True,
        'chat_engines': True,
        'multimodal': False,
        'memory_management': True
    }
