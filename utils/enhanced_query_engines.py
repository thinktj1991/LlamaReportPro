from .safe_config import should_disable_sub_question_engine
"""
Enhanced Query Engines using LlamaIndex's advanced querying capabilities
第二阶段增强：路由引擎、子问题引擎、合成策略、评估系统
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
import asyncio

from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.query_engine import (
    RouterQueryEngine,
    SubQuestionQueryEngine,
    MultiStepQueryEngine,
    RetrieverQueryEngine
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.tools import QueryEngineTool
from llama_index.core.selectors import LLMSingleSelector, PydanticSingleSelector
from llama_index.core.postprocessor import SimilarityPostprocessor, KeywordNodePostprocessor
from llama_index.core.response_synthesizers import get_response_synthesizer, ResponseMode
from llama_index.core.llms import ChatMessage
from llama_index.core.schema import QueryBundle

# 评估相关导入
try:
    from llama_index.core.evaluation import (
        FaithfulnessEvaluator,
        RelevancyEvaluator,
        CorrectnessEvaluator,
        SemanticSimilarityEvaluator
    )
    EVALUATION_AVAILABLE = True
except ImportError:
    EVALUATION_AVAILABLE = False

# 结构化输出相关
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

# ==================== 第二阶段增强模型定义 ====================

class QueryType(str, Enum):
    """查询类型枚举"""
    FINANCIAL_DATA = "financial_data"
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"
    SUMMARY = "summary"
    DETAILED_SEARCH = "detailed_search"
    CROSS_SECTION = "cross_section"

class SynthesisStrategy(str, Enum):
    """合成策略枚举"""
    COMPACT = "compact"
    REFINE = "refine"
    TREE_SUMMARIZE = "tree_summarize"
    SIMPLE_SUMMARIZE = "simple_summarize"

class EvaluationMetrics(BaseModel):
    """评估指标"""
    faithfulness: Optional[float] = Field(description="忠实性评分", default=None)
    relevancy: Optional[float] = Field(description="相关性评分", default=None)
    correctness: Optional[float] = Field(description="正确性评分", default=None)
    semantic_similarity: Optional[float] = Field(description="语义相似性评分", default=None)
    response_time: Optional[float] = Field(description="响应时间(秒)", default=None)
    token_usage: Optional[int] = Field(description="Token使用量", default=None)

class EnhancedQueryResult(BaseModel):
    """增强查询结果"""
    query: str = Field(description="原始查询")
    query_type: QueryType = Field(description="查询类型")
    synthesis_strategy: SynthesisStrategy = Field(description="使用的合成策略")
    answer: str = Field(description="答案")
    sub_questions: List[str] = Field(description="子问题列表", default_factory=list)
    sub_answers: List[str] = Field(description="子问题答案", default_factory=list)
    sources: List[Dict[str, Any]] = Field(description="来源信息", default_factory=list)
    evaluation_metrics: Optional[EvaluationMetrics] = Field(description="评估指标", default=None)
    processing_time: float = Field(description="处理时间", default=0.0)
    timestamp: datetime = Field(description="时间戳", default_factory=datetime.now)

class EnhancedQueryEngineManager:
    """
    第二阶段增强：管理多种高级查询引擎，支持路由、子问题、评估
    """

    def __init__(self, index: VectorStoreIndex, llm=None, enable_evaluation=True):
        self.index = index
        self.llm = llm or Settings.llm
        self.enable_evaluation = enable_evaluation and EVALUATION_AVAILABLE

        # 查询引擎存储
        self.query_engines = {}
        self.router_query_engine = None
        self.sub_question_engine = None

        # 评估器
        self.evaluators = {}

        # 构建所有引擎
        self._build_specialized_engines()
        self._build_router_engine()
        self._build_sub_question_engine()
        if self.enable_evaluation:
            self._build_evaluators()

    def _build_specialized_engines(self):
        """构建专门的查询引擎，支持不同的合成策略"""
        try:
            # 1. 财务数据查询引擎 - 精确数值查询，使用compact策略
            financial_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=10
            )
            self.query_engines['financial_data'] = RetrieverQueryEngine.from_args(
                retriever=financial_retriever,
                response_synthesizer=get_response_synthesizer(
                    response_mode=ResponseMode.COMPACT,
                    use_async=True
                ),
                node_postprocessors=[
                    SimilarityPostprocessor(similarity_cutoff=0.7),
                    KeywordNodePostprocessor(keywords=["营收", "利润", "资产", "负债", "现金流"])
                ]
            )

            # 2. 趋势分析引擎 - 时间序列分析，使用tree_summarize策略
            trend_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=15
            )
            self.query_engines['trend_analysis'] = RetrieverQueryEngine.from_args(
                retriever=trend_retriever,
                response_synthesizer=get_response_synthesizer(
                    response_mode=ResponseMode.TREE_SUMMARIZE,
                    use_async=True
                ),
                node_postprocessors=[
                    KeywordNodePostprocessor(keywords=["增长", "下降", "趋势", "变化", "同比", "环比"])
                ]
            )

            # 3. 对比分析引擎 - 多维度对比，使用refine策略
            comparison_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=20
            )
            self.query_engines['comparison'] = RetrieverQueryEngine.from_args(
                retriever=comparison_retriever,
                response_synthesizer=get_response_synthesizer(
                    response_mode=ResponseMode.REFINE,
                    use_async=True
                ),
                node_postprocessors=[
                    KeywordNodePostprocessor(keywords=["对比", "比较", "差异", "相似", "优于", "低于"])
                ]
            )

            # 4. 摘要引擎 - 高层次概述，使用simple_summarize策略
            summary_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=25
            )
            self.query_engines['summary'] = RetrieverQueryEngine.from_args(
                retriever=summary_retriever,
                response_synthesizer=get_response_synthesizer(
                    response_mode=ResponseMode.SIMPLE_SUMMARIZE,
                    use_async=True
                )
            )

            # 5. 详细搜索引擎 - 深度检索，使用compact策略
            detailed_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=30
            )
            self.query_engines['detailed_search'] = RetrieverQueryEngine.from_args(
                retriever=detailed_retriever,
                response_synthesizer=get_response_synthesizer(
                    response_mode=ResponseMode.COMPACT,
                    use_async=True
                ),
                node_postprocessors=[
                    SimilarityPostprocessor(similarity_cutoff=0.6)
                ]
            )

            logger.info("✅ 成功构建5个专门查询引擎")

        except Exception as e:
            logger.error(f"❌ 构建专门查询引擎失败: {e}")
            # 降级：构建基础引擎
            basic_retriever = VectorIndexRetriever(index=self.index, similarity_top_k=10)
            self.query_engines['basic'] = RetrieverQueryEngine.from_args(
                retriever=basic_retriever,
                response_synthesizer=get_response_synthesizer(response_mode=ResponseMode.COMPACT)
            )
    def _build_router_engine(self):
        """构建路由查询引擎"""
        try:
            # 创建查询引擎工具
            tools = []

            # 财务数据工具
            if 'financial_data' in self.query_engines:
                financial_tool = QueryEngineTool.from_defaults(
                    query_engine=self.query_engines['financial_data'],
                    description="用于精确的财务数据查询，如营收、利润、资产负债等具体数值。适合回答'公司营收是多少'、'净利润增长率'等问题。"
                )
                tools.append(financial_tool)

            # 趋势分析工具
            if 'trend_analysis' in self.query_engines:
                trend_tool = QueryEngineTool.from_defaults(
                    query_engine=self.query_engines['trend_analysis'],
                    description="用于趋势分析和时间序列分析，识别增长模式、周期性变化等。适合回答'增长趋势如何'、'业绩变化'等问题。"
                )
                tools.append(trend_tool)

            # 对比分析工具
            if 'comparison' in self.query_engines:
                comparison_tool = QueryEngineTool.from_defaults(
                    query_engine=self.query_engines['comparison'],
                    description="用于多维度对比分析，比较不同时期、不同指标或不同方面。适合回答'与去年相比'、'优势劣势对比'等问题。"
                )
                tools.append(comparison_tool)

            # 摘要工具
            if 'summary' in self.query_engines:
                summary_tool = QueryEngineTool.from_defaults(
                    query_engine=self.query_engines['summary'],
                    description="用于生成高层次摘要和概述，提供整体情况。适合回答'公司整体情况'、'业务概况'等问题。"
                )
                tools.append(summary_tool)

            # 详细搜索工具
            if 'detailed_search' in self.query_engines:
                detailed_tool = QueryEngineTool.from_defaults(
                    query_engine=self.query_engines['detailed_search'],
                    description="用于深度详细搜索，获取全面信息。适合回答复杂的、需要详细信息的问题。"
                )
                tools.append(detailed_tool)

            # 构建路由器
            if tools:
                self.router_query_engine = RouterQueryEngine(
                    selector=PydanticSingleSelector.from_defaults(llm=self.llm),
                    query_engine_tools=tools,
                    verbose=True
                )
                logger.info(f"✅ 成功构建路由查询引擎，包含{len(tools)}个工具")
            else:
                logger.warning("⚠️ 无可用工具，跳过路由引擎构建")

        except Exception as e:
            logger.error(f"❌ 构建路由查询引擎失败: {e}")
            self.router_query_engine = None

    def _build_sub_question_engine(self):
        """构建子问题查询引擎"""
        if should_disable_sub_question_engine():
            logger.info("⚠️ 子问题查询引擎已禁用（安全模式）")
            self.sub_question_engine = None
            return
        """构建子问题查询引擎"""
        try:
            # 首先检查question_gen是否可用
            try:
                from llama_index.question_gen.openai import OpenAIQuestionGenerator
                question_gen_available = True
            except ImportError:
                question_gen_available = False
                logger.error("❌ 构建子问题查询引擎失败: `llama-index-question-gen-openai` package cannot be found. Please install it by using `pip install `llama-index-question-gen-openai`")
                self.sub_question_engine = None
                return

            # 使用最佳的查询引擎作为基础
            base_engine = (
                self.query_engines.get('detailed_search') or
                self.query_engines.get('financial_data') or
                list(self.query_engines.values())[0] if self.query_engines else None
            )

            if base_engine and question_gen_available:
                # 创建question generator
                question_gen = OpenAIQuestionGenerator.from_defaults(llm=self.llm)

                self.sub_question_engine = SubQuestionQueryEngine.from_defaults(
                    query_engine_tools=[
                        QueryEngineTool.from_defaults(
                            query_engine=base_engine,
                            description="用于回答财务年报相关的各种问题"
                        )
                    ],
                    question_gen=question_gen,
                    llm=self.llm,
                    verbose=True
                )
                logger.info("✅ 成功构建子问题查询引擎")
            else:
                if not base_engine:
                    logger.warning("⚠️ 无基础查询引擎，跳过子问题引擎构建")
                self.sub_question_engine = None

        except Exception as e:
            logger.error(f"❌ 构建子问题查询引擎失败: {e}")
            self.sub_question_engine = None

    def _build_evaluators(self):
        """构建评估器"""
        if not EVALUATION_AVAILABLE:
            logger.warning("⚠️ 评估模块不可用，跳过评估器构建")
            return

        try:
            # 忠实性评估器
            self.evaluators['faithfulness'] = FaithfulnessEvaluator(llm=self.llm)

            # 相关性评估器
            self.evaluators['relevancy'] = RelevancyEvaluator(llm=self.llm)

            # 正确性评估器（需要参考答案）
            self.evaluators['correctness'] = CorrectnessEvaluator(llm=self.llm)

            # 语义相似性评估器
            self.evaluators['semantic_similarity'] = SemanticSimilarityEvaluator()

            logger.info("✅ 成功构建评估器")

        except Exception as e:
            logger.error(f"❌ 构建评估器失败: {e}")
            self.evaluators = {}

    def _infer_query_type(self, query: str) -> QueryType:
        """推断查询类型"""
        query_lower = query.lower()

        # 财务数据关键词
        financial_keywords = ['营收', '收入', '利润', '资产', '负债', '现金流', '毛利率', '净利率',
                             'roe', 'roa', '财务指标', '数据', '金额', '元']

        # 趋势分析关键词
        trend_keywords = ['增长', '下降', '趋势', '变化', '同比', '环比', '发展', '走势', '波动']

        # 对比分析关键词
        comparison_keywords = ['对比', '比较', '差异', '相似', '优于', '低于', '超过', '不如', '与']

        # 摘要关键词
        summary_keywords = ['概况', '总体', '整体', '概述', '简介', '情况', '状况', '总结']

        # 跨章节关键词
        cross_section_keywords = ['各', '分别', '不同', '多个', '全面', '综合', '各项', '整个']

        # 计算匹配度
        financial_score = sum(1 for keyword in financial_keywords if keyword in query_lower)
        trend_score = sum(1 for keyword in trend_keywords if keyword in query_lower)
        comparison_score = sum(1 for keyword in comparison_keywords if keyword in query_lower)
        summary_score = sum(1 for keyword in summary_keywords if keyword in query_lower)
        cross_section_score = sum(1 for keyword in cross_section_keywords if keyword in query_lower)

        # 返回得分最高的类型
        scores = {
            QueryType.FINANCIAL_DATA: financial_score,
            QueryType.TREND_ANALYSIS: trend_score,
            QueryType.COMPARISON: comparison_score,
            QueryType.SUMMARY: summary_score,
            QueryType.CROSS_SECTION: cross_section_score
        }

        max_type = max(scores, key=scores.get)
        return max_type if scores[max_type] > 0 else QueryType.DETAILED_SEARCH

    def _get_synthesis_strategy(self, query_type: QueryType) -> SynthesisStrategy:
        """根据查询类型获取最佳合成策略"""
        strategy_mapping = {
            QueryType.FINANCIAL_DATA: SynthesisStrategy.COMPACT,
            QueryType.TREND_ANALYSIS: SynthesisStrategy.TREE_SUMMARIZE,
            QueryType.COMPARISON: SynthesisStrategy.REFINE,
            QueryType.SUMMARY: SynthesisStrategy.SIMPLE_SUMMARIZE,
            QueryType.DETAILED_SEARCH: SynthesisStrategy.COMPACT,
            QueryType.CROSS_SECTION: SynthesisStrategy.TREE_SUMMARIZE
        }
        return strategy_mapping.get(query_type, SynthesisStrategy.COMPACT)

    async def _evaluate_response(self, query: str, response: str, contexts: List[str]) -> EvaluationMetrics:
        """评估响应质量"""
        if not self.enable_evaluation or not self.evaluators:
            return EvaluationMetrics()

        metrics = EvaluationMetrics()

        try:
            # 忠实性评估
            if 'faithfulness' in self.evaluators and contexts:
                faithfulness_result = await self.evaluators['faithfulness'].aevaluate(
                    query=query,
                    response=response,
                    contexts=contexts
                )
                metrics.faithfulness = faithfulness_result.score

            # 相关性评估
            if 'relevancy' in self.evaluators:
                relevancy_result = await self.evaluators['relevancy'].aevaluate(
                    query=query,
                    response=response,
                    contexts=contexts
                )
                metrics.relevancy = relevancy_result.score

        except Exception as e:
            logger.warning(f"⚠️ 评估过程中出现错误: {e}")

        return metrics

    async def query_enhanced(self, query: str, use_router: bool = True, use_sub_questions: bool = False,
                           enable_evaluation: bool = True) -> EnhancedQueryResult:
        """
        第二阶段增强查询方法

        Args:
            query: 查询问题
            use_router: 是否使用路由引擎
            use_sub_questions: 是否使用子问题分解
            enable_evaluation: 是否启用评估

        Returns:
            EnhancedQueryResult: 增强查询结果
        """
        import time
        start_time = time.time()

        # 推断查询类型
        query_type = self._infer_query_type(query)
        synthesis_strategy = self._get_synthesis_strategy(query_type)

        try:
            # 选择查询引擎
            if use_sub_questions and self.sub_question_engine:
                # 使用子问题引擎
                response = await self._query_with_sub_questions(query)
                sub_questions = getattr(response, 'sub_questions', [])
                sub_answers = getattr(response, 'sub_answers', [])
            elif use_router and self.router_query_engine:
                # 使用路由引擎
                response = self.router_query_engine.query(query)
                sub_questions = []
                sub_answers = []
            else:
                # 使用专门引擎
                engine_key = self._get_engine_key(query_type)
                engine = self.query_engines.get(engine_key, list(self.query_engines.values())[0])
                response = engine.query(query)
                sub_questions = []
                sub_answers = []

            # 提取响应信息
            answer = str(response)
            sources = self._extract_sources(response)
            contexts = [source.get('text', '') for source in sources]

            # 评估响应质量
            evaluation_metrics = None
            if enable_evaluation and self.enable_evaluation:
                evaluation_metrics = await self._evaluate_response(query, answer, contexts)

            # 计算处理时间
            processing_time = time.time() - start_time

            # 构建结果
            result = EnhancedQueryResult(
                query=query,
                query_type=query_type,
                synthesis_strategy=synthesis_strategy,
                answer=answer,
                sub_questions=sub_questions,
                sub_answers=sub_answers,
                sources=sources,
                evaluation_metrics=evaluation_metrics,
                processing_time=processing_time
            )

            logger.info(f"✅ 增强查询完成: {query_type.value}, 耗时: {processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"❌ 增强查询失败: {e}")
            # 降级到基础查询
            return await self._fallback_query(query, start_time)

    async def _query_with_sub_questions(self, query: str):
        """使用子问题引擎查询"""
        try:
            response = self.sub_question_engine.query(query)
            return response
        except Exception as e:
            logger.error(f"❌ 子问题查询失败: {e}")
            # 降级到基础引擎
            basic_engine = list(self.query_engines.values())[0] if self.query_engines else None
            if basic_engine:
                return basic_engine.query(query)
            else:
                raise e

    def _get_engine_key(self, query_type: QueryType) -> str:
        """根据查询类型获取引擎键"""
        mapping = {
            QueryType.FINANCIAL_DATA: 'financial_data',
            QueryType.TREND_ANALYSIS: 'trend_analysis',
            QueryType.COMPARISON: 'comparison',
            QueryType.SUMMARY: 'summary',
            QueryType.DETAILED_SEARCH: 'detailed_search',
            QueryType.CROSS_SECTION: 'detailed_search'
        }
        return mapping.get(query_type, 'detailed_search')

    def _extract_sources(self, response) -> List[Dict[str, Any]]:
        """提取来源信息"""
        sources = []
        try:
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for i, node in enumerate(response.source_nodes):
                    source = {
                        'id': i,
                        'text': node.text[:300] + "..." if len(node.text) > 300 else node.text,
                        'score': getattr(node, 'score', 0.0),
                        'metadata': getattr(node, 'metadata', {})
                    }
                    sources.append(source)
        except Exception as e:
            logger.warning(f"⚠️ 提取来源信息失败: {e}")

        return sources

    async def _fallback_query(self, query: str, start_time: float) -> EnhancedQueryResult:
        """降级查询"""
        try:
            # 使用第一个可用的引擎
            engine = list(self.query_engines.values())[0] if self.query_engines else None
            if engine:
                response = engine.query(query)
                answer = str(response)
                sources = self._extract_sources(response)
            else:
                answer = "抱歉，查询引擎不可用。"
                sources = []

            processing_time = time.time() - start_time

            return EnhancedQueryResult(
                query=query,
                query_type=QueryType.DETAILED_SEARCH,
                synthesis_strategy=SynthesisStrategy.COMPACT,
                answer=answer,
                sources=sources,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"❌ 降级查询也失败: {e}")
            processing_time = time.time() - start_time

            return EnhancedQueryResult(
                query=query,
                query_type=QueryType.DETAILED_SEARCH,
                synthesis_strategy=SynthesisStrategy.COMPACT,
                answer=f"查询失败: {str(e)}",
                sources=[],
                processing_time=processing_time
            )

    def get_available_engines(self) -> Dict[str, str]:
        """获取可用的查询引擎列表"""
        engines = {}
        if self.query_engines:
            for key in self.query_engines.keys():
                engines[key] = f"专门的{key}查询引擎"

        if self.router_query_engine:
            engines['router'] = "智能路由查询引擎"

        if self.sub_question_engine:
            engines['sub_question'] = "子问题分解查询引擎"

        return engines

    def get_engine_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            'specialized_engines': len(self.query_engines),
            'router_available': self.router_query_engine is not None,
            'sub_question_available': self.sub_question_engine is not None,
            'evaluation_available': self.enable_evaluation,
            'evaluators_count': len(self.evaluators)
        }

    async def batch_query(self, queries: List[str], use_router: bool = True) -> List[EnhancedQueryResult]:
        """批量查询"""
        results = []
        for query in queries:
            try:
                result = await self.query_enhanced(query, use_router=use_router)
                results.append(result)
            except Exception as e:
                logger.error(f"❌ 批量查询中的单个查询失败: {e}")
                # 添加错误结果
                error_result = EnhancedQueryResult(
                    query=query,
                    query_type=QueryType.DETAILED_SEARCH,
                    synthesis_strategy=SynthesisStrategy.COMPACT,
                    answer=f"查询失败: {str(e)}",
                    sources=[],
                    processing_time=0.0
                )
                results.append(error_result)

        return results

# ==================== 第二阶段增强工具函数 ====================

class QueryEngineFactory:
    """查询引擎工厂类"""

    @staticmethod
    def create_enhanced_manager(index: VectorStoreIndex, llm=None, enable_evaluation: bool = True) -> EnhancedQueryEngineManager:
        """创建增强查询引擎管理器"""
        return EnhancedQueryEngineManager(index=index, llm=llm, enable_evaluation=enable_evaluation)

    @staticmethod
    def create_router_only(index: VectorStoreIndex, llm=None) -> Optional[RouterQueryEngine]:
        """仅创建路由引擎"""
        try:
            manager = EnhancedQueryEngineManager(index=index, llm=llm, enable_evaluation=False)
            return manager.router_query_engine
        except Exception as e:
            logger.error(f"❌ 创建路由引擎失败: {e}")
            return None

    @staticmethod
    def create_sub_question_only(index: VectorStoreIndex, llm=None) -> Optional[SubQuestionQueryEngine]:
        """仅创建子问题引擎"""
        try:
            manager = EnhancedQueryEngineManager(index=index, llm=llm, enable_evaluation=False)
            return manager.sub_question_engine
        except Exception as e:
            logger.error(f"❌ 创建子问题引擎失败: {e}")
            return None

def create_evaluation_suite(llm=None) -> Dict[str, Any]:
    """创建评估套件"""
    if not EVALUATION_AVAILABLE:
        logger.warning("⚠️ 评估模块不可用")
        return {}

    try:
        evaluators = {
            'faithfulness': FaithfulnessEvaluator(llm=llm),
            'relevancy': RelevancyEvaluator(llm=llm),
            'correctness': CorrectnessEvaluator(llm=llm),
            'semantic_similarity': SemanticSimilarityEvaluator()
        }
        logger.info("✅ 成功创建评估套件")
        return evaluators
    except Exception as e:
        logger.error(f"❌ 创建评估套件失败: {e}")
        return {}

# ==================== 向后兼容性保持 ====================

class HybridRetriever:
    """向后兼容的混合检索器类"""

    def __init__(self, index: VectorStoreIndex):
        self.index = index
        logger.warning("⚠️ HybridRetriever已弃用，请使用EnhancedQueryEngineManager")

    def retrieve(self, query: str) -> List[Any]:
        """基础检索方法"""
        try:
            retriever = VectorIndexRetriever(index=self.index, similarity_top_k=10)
            return retriever.retrieve(query)
        except Exception as e:
            logger.error(f"❌ HybridRetriever检索失败: {e}")
            return []

# ==================== 向后兼容的旧类保持 ====================

class ContextualQueryProcessor:
    """向后兼容的上下文查询处理器"""

    def __init__(self, enhanced_manager: EnhancedQueryEngineManager):
        self.enhanced_manager = enhanced_manager
        logger.warning("⚠️ ContextualQueryProcessor已弃用，请直接使用EnhancedQueryEngineManager")

    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理查询并返回结果"""
        try:
            result = await self.enhanced_manager.query_enhanced(query)
            return {
                'answer': result.answer,
                'sources': result.sources,
                'query_type': result.query_type.value,
                'processing_time': result.processing_time
            }
        except Exception as e:
            logger.error(f"❌ 上下文查询处理失败: {e}")
            return {
                'answer': f"查询失败: {str(e)}",
                'sources': [],
                'query_type': 'error',
                'processing_time': 0.0
            }