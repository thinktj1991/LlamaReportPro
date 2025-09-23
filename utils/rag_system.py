import os
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
from enum import Enum
import streamlit as st
from llama_index.core import VectorStoreIndex, Document, Settings, StorageContext, load_index_from_storage
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response.pprint_utils import pprint_response
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import logging

# 结构化输出相关导入
from pydantic import BaseModel, Field, validator
from llama_index.core.llms import ChatMessage

# 第二阶段增强功能导入
from utils.enhanced_query_engines import (
    EnhancedQueryEngineManager,
    QueryEngineFactory,
    EnhancedQueryResult,
    QueryType,
    SynthesisStrategy,
    EvaluationMetrics
)

# Configure logging
logger = logging.getLogger(__name__)

# ==================== 结构化输出模型定义 ====================

class AnalysisType(str, Enum):
    """分析类型枚举"""
    FINANCIAL_METRICS = "financial_metrics"
    RISK_ASSESSMENT = "risk_assessment"
    GROWTH_ANALYSIS = "growth_analysis"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    GENERAL_INQUIRY = "general_inquiry"

class ConfidenceLevel(str, Enum):
    """置信度等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class FinancialMetrics(BaseModel):
    """财务指标"""
    revenue: Optional[float] = Field(description="营业收入（万元）", default=None)
    net_income: Optional[float] = Field(description="净利润（万元）", default=None)
    total_assets: Optional[float] = Field(description="总资产（万元）", default=None)
    total_equity: Optional[float] = Field(description="股东权益（万元）", default=None)
    revenue_growth_rate: Optional[float] = Field(description="营收增长率（%）", default=None)
    profit_margin: Optional[float] = Field(description="净利润率（%）", default=None)
    roe: Optional[float] = Field(description="净资产收益率（%）", default=None)
    debt_to_equity: Optional[float] = Field(description="资产负债率（%）", default=None)

    @validator('revenue_growth_rate', 'profit_margin', 'roe', 'debt_to_equity')
    def validate_percentage(cls, v):
        if v is not None and (v < -100 or v > 1000):
            raise ValueError('百分比数值超出合理范围')
        return v

class RiskFactor(BaseModel):
    """风险因素"""
    category: str = Field(description="风险类别")
    description: str = Field(description="风险描述")
    severity: str = Field(description="严重程度：高/中/低")
    impact: str = Field(description="影响说明")

class EvidenceSource(BaseModel):
    """证据来源"""
    page_number: Optional[int] = Field(description="页码", default=None)
    section: Optional[str] = Field(description="章节", default=None)
    quote: str = Field(description="原文引用")
    relevance_score: float = Field(description="相关性评分", ge=0.0, le=1.0)

class StructuredAnalysisResponse(BaseModel):
    """结构化分析响应"""
    company_name: str = Field(description="公司名称")
    fiscal_year: Optional[int] = Field(description="财年", default=None)
    analysis_type: AnalysisType = Field(description="分析类型")

    # 核心分析内容
    summary: str = Field(description="分析摘要")
    key_findings: List[str] = Field(description="关键发现")

    # 财务数据（如适用）
    financial_metrics: Optional[FinancialMetrics] = Field(description="财务指标", default=None)

    # 风险评估（如适用）
    risk_factors: List[RiskFactor] = Field(description="风险因素", default_factory=list)

    # 证据支撑
    evidence_sources: List[EvidenceSource] = Field(description="证据来源", default_factory=list)

    # 元数据
    confidence_level: ConfidenceLevel = Field(description="整体置信度")
    analysis_date: datetime = Field(description="分析日期", default_factory=datetime.now)
    limitations: List[str] = Field(description="分析局限性", default_factory=list)

    @validator('fiscal_year')
    def validate_fiscal_year(cls, v):
        if v is not None and (v < 1900 or v > 2030):
            raise ValueError('财年超出合理范围')
        return v

class RAGSystem:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.index = None
        self.query_engine = None
        self.persist_dir = "./storage/rag_data"

        # 第二阶段增强功能
        self.enhanced_manager = None
        self.enable_phase2_features = True  # 启用第二阶段功能
        self.evaluation_enabled = True      # 启用评估功能

        # 第三阶段增强功能
        self.phase3_manager = None
        self.enable_phase3_features = True  # 启用第三阶段功能

        # 第四阶段增强功能
        self.phase4_manager = None
        self.enable_phase4_features = True  # 启用第四阶段功能

        # Only setup if API key is available
        if self.openai_api_key:
            try:
                self._setup_llama_index()
                # Try to load existing index
                self._load_existing_index()
            except Exception as e:
                logger.error(f"Error setting up LlamaIndex: {str(e)}")
        else:
            logger.warning("OpenAI API key not found, RAG system will be limited")

    def _setup_llama_index(self):
        """
        Setup LlamaIndex with OpenAI configurations
        """
        try:
            if not self.openai_api_key:
                raise ValueError("OpenAI API key is required")

            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            Settings.llm = OpenAI(
                model="gpt-4o",  # Using gpt-4o which is more stable
                api_key=self.openai_api_key,
                temperature=0.1
            )

            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-large",
                api_key=self.openai_api_key
            )

            logger.info("LlamaIndex settings configured successfully")

        except Exception as e:
            logger.error(f"Error setting up LlamaIndex: {str(e)}")
            # Don't raise the error, just log it

    def _load_existing_index(self):
        """
        Try to load existing persisted index on startup
        """
        try:
            if Path(self.persist_dir).exists():
                logger.info(f"Found existing storage directory: {self.persist_dir}")

                # Check if storage contains valid index files
                storage_files = list(Path(self.persist_dir).glob("*"))
                if storage_files:
                    logger.info(f"Found {len(storage_files)} storage files, attempting to load index...")

                    # Load the storage context
                    storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)

                    # Load the index
                    self.index = load_index_from_storage(storage_context)

                    # Create enhanced query engine (hybrid + rerank if available)
                    self._build_query_engine()

                    logger.info("✅ Successfully loaded existing RAG index from storage")
                    return True
                else:
                    logger.info("Storage directory exists but is empty")
            else:
                logger.info("No existing storage directory found")

        except Exception as e:
            logger.warning(f"⚠️ Failed to load existing index: {str(e)}")
            # Reset index and query_engine if loading failed
            self.index = None
            self.query_engine = None

        return False

    def _build_query_engine(self):
        """
        第二阶段增强：构建增强查询引擎，支持路由、子问题、评估
        """
        try:
            # 第二阶段：构建增强查询引擎管理器
            if self.enable_phase2_features:
                try:
                    self.enhanced_manager = EnhancedQueryEngineManager(
                        index=self.index,
                        llm=Settings.llm,
                        enable_evaluation=self.evaluation_enabled
                    )
                    logger.info("✅ 第二阶段增强查询引擎管理器构建成功")
                except Exception as e:
                    logger.warning(f"⚠️ 第二阶段增强功能初始化失败，降级到第一阶段: {e}")
                    self.enhanced_manager = None
                    self.enable_phase2_features = False

            # 第三阶段：Chat Engines, Workflows, Agents
            if self.enable_phase3_features:
                try:
                    from utils.phase3_enhancements import create_phase3_manager
                    self.phase3_manager = create_phase3_manager(self.index, Settings.llm)
                    logger.info("✅ 第三阶段增强功能初始化成功")
                except Exception as e:
                    logger.warning(f"⚠️ 第三阶段增强功能初始化失败: {e}")
                    self.phase3_manager = None
                    self.enable_phase3_features = False

            # 第四阶段：多模态、高级存储、元数据提取、知识图谱、高级提示工程
            if self.enable_phase4_features:
                try:
                    from utils.phase4_enhancements import create_phase4_manager
                    self.phase4_manager = create_phase4_manager(self.index, Settings.llm)
                    logger.info("✅ 第四阶段增强功能初始化成功")
                except Exception as e:
                    logger.warning(f"⚠️ 第四阶段增强功能初始化失败: {e}")
                    self.phase4_manager = None
                    self.enable_phase4_features = False

            # 第一阶段：混合检索 + 重排序（保持向后兼容）
            # 1) Vector retriever (always available)
            vector_retriever = self.index.as_retriever(similarity_top_k=15)
            fusion_retriever = None

            # 2) Try BM25 sparse retriever (no extra persistence required)
            bm25_retriever = None
            try:
                from llama_index.retrievers.bm25 import BM25Retriever
                bm25_retriever = BM25Retriever.from_defaults(
                    docstore=self.index.docstore, similarity_top_k=15
                )
            except ImportError:
                # 如果BM25包不可用，跳过BM25检索
                logger.info("BM25Retriever not available, using vector retrieval only")
                bm25_retriever = None
            except Exception as e:
                logger.warning(f"Failed to initialize BM25Retriever: {e}")
                bm25_retriever = None

            # 3) Try QueryFusionRetriever (dense + sparse)
            try:
                from llama_index.core.retrievers import QueryFusionRetriever
                if bm25_retriever:
                    fusion_retriever = QueryFusionRetriever(
                        [vector_retriever, bm25_retriever],
                        similarity_top_k=10,
                        num_queries=1,
                        mode="reciprocal_rerank",
                        use_async=True,
                    )
            except Exception:
                fusion_retriever = None

            retriever = fusion_retriever or vector_retriever

            # 4) Optional LLM-based reranker
            node_postprocessors = []
            try:
                from llama_index.core.postprocessor import LLMRerank
                llm_rerank = LLMRerank(top_n=5)
                node_postprocessors = [llm_rerank]
            except Exception:
                node_postprocessors = []

            # 5) Assemble RetrieverQueryEngine with a robust synthesizer
            from llama_index.core.response_synthesizers import get_response_synthesizer
            from llama_index.core.query_engine import RetrieverQueryEngine

            self.query_engine = RetrieverQueryEngine.from_args(
                retriever=retriever,
                node_postprocessors=node_postprocessors if node_postprocessors else None,
                response_synthesizer=get_response_synthesizer(
                    response_mode="tree_summarize",
                    use_async=True,
                ),
            )

        except Exception as e:
            # final fallback: basic query engine
            try:
                self.query_engine = self.index.as_query_engine(
                    similarity_top_k=5,
                    response_mode="tree_summarize",
                )
            except Exception:
                self.query_engine = None
            logger.warning(f"Falling back to basic query engine due to: {e}")

    def build_index(self, processed_documents: Dict[str, Any], extracted_tables: Dict[str, List[Dict]]) -> bool:
        """
        Build vector store index from processed documents and tables
        """
        try:
            all_documents = []

            # Process text documents
            for doc_name, doc_data in processed_documents.items():
                if 'documents' in doc_data:
                    for doc in doc_data['documents']:
                        # Add metadata
                        doc.metadata.update({
                            'source_file': doc_name,
                            'document_type': 'text_content'
                        })

                        # Add company info if available
                        if 'company_info' in doc_data:
                            doc.metadata.update(doc_data['company_info'])

                        all_documents.append(doc)

            # Process extracted tables
            for doc_name, tables in extracted_tables.items():
                for table in tables:
                    # Convert table to text representation
                    table_text = self._table_to_text(table)

                    table_doc = Document(
                        text=table_text,
                        metadata={
                            'source_file': doc_name,
                            'document_type': 'table_data',
                            'table_id': table['table_id'],
                            'page_number': table['page_number'],
                            'is_financial': table['is_financial'],
                            'importance_score': table['importance_score'],
                            'table_summary': table['summary']
                        }
                    )

                    all_documents.append(table_doc)

            if not all_documents:
                logger.warning("No documents to index")
                return False

            # Build the index
            self.index = VectorStoreIndex.from_documents(all_documents)

            # Persist the index to disk
            try:
                os.makedirs(self.persist_dir, exist_ok=True)
                self.index.storage_context.persist(persist_dir=self.persist_dir)
                logger.info(f"✅ RAG index persisted to: {self.persist_dir}")
            except Exception as e:
                logger.error(f"❌ Failed to persist index: {str(e)}")

            # Create enhanced query engine (hybrid + rerank if available)
            self._build_query_engine()

            logger.info(f"Successfully built index with {len(all_documents)} documents")
            return True

        except Exception as e:
            logger.error(f"Error building index: {str(e)}")
            return False

    def _table_to_text(self, table: Dict) -> str:
        """
        Convert table data to text representation for indexing
        """
        try:
            df = table['dataframe']

            # Create a comprehensive text representation
            text_parts = []

            # Add table metadata
            text_parts.append(f"Table from page {table['page_number']}")
            text_parts.append(f"Table ID: {table['table_id']}")
            text_parts.append(f"Summary: {table['summary']}")

            if table['is_financial']:
                text_parts.append("This is a financial data table.")

            # Add column information
            text_parts.append(f"Columns: {', '.join(df.columns)}")

            # Add table content in a readable format
            text_parts.append("Table content:")

            # Convert DataFrame to string with better formatting
            table_str = df.to_string(index=False, max_rows=20)
            text_parts.append(table_str)

            # Add summary statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                text_parts.append("Numeric data summary:")
                for col in numeric_cols:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        text_parts.append(f"{col}: min={col_data.min()}, max={col_data.max()}, mean={col_data.mean():.2f}")

            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error converting table to text: {str(e)}")
            return f"Table {table.get('table_id', 'unknown')} - content unavailable"

    def query(self, question: str, context_filter: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Query the RAG system with a question
        """
        try:
            if not self.query_engine:
                return {
                    'answer': "RAG system not initialized. Please process documents first.",
                    'sources': [],
                    'error': True
                }

            # Enhanced query with context
            enhanced_query = self._enhance_query(question, context_filter)

            # Perform the query
            response = self.query_engine.query(enhanced_query)

            # Extract source information
            sources = self._extract_sources(response)

            result = {
                'answer': str(response),
                'sources': sources,
                'error': False,
                'original_question': question,
                'enhanced_query': enhanced_query
            }

            logger.info(f"Successfully processed query: {question[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Error processing query '{question}': {str(e)}")
            return {
                'answer': f"Error processing query: {str(e)}",
                'sources': [],
                'error': True
            }

    def _enhance_query(self, question: str, context_filter: Optional[Dict] = None) -> str:
        """
        Enhance the query with additional context
        """
        enhanced_parts = [question]

        if context_filter:
            if 'company' in context_filter:
                enhanced_parts.append(f"Focus on information about {context_filter['company']}")

            if 'year' in context_filter:
                enhanced_parts.append(f"for the year {context_filter['year']}")

            if 'document_type' in context_filter:
                enhanced_parts.append(f"from {context_filter['document_type']} documents")

        enhanced_parts.append("Please provide specific data and cite sources when possible.")

        return " ".join(enhanced_parts)

    def _extract_sources(self, response) -> List[Dict]:
        """
        Extract source information from the response
        """
        sources = []

        try:
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    source_info = {
                        'content_preview': node.text[:200] + "..." if len(node.text) > 200 else node.text,
                        'score': getattr(node, 'score', 0.0),
                        'metadata': node.metadata
                    }
                    sources.append(source_info)
        except Exception as e:
            logger.error(f"Error extracting sources: {str(e)}")

        return sources

    def get_similar_content(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Get similar content without generating an answer
        """
        try:
            if not self.index:
                return []

            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=top_k
            )

            nodes = retriever.retrieve(query)

            similar_content = []
            for node in nodes:
                content = {
                    'text': node.text,
                    'score': getattr(node, 'score', 0.0),
                    'metadata': node.metadata
                }
                similar_content.append(content)

            return similar_content

        except Exception as e:
            logger.error(f"Error getting similar content: {str(e)}")
            return []

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current index
        """
        if not self.index:
            return {'status': 'No index built'}

        try:
            # Get basic stats
            stats = {
                'status': 'Active',
                'total_documents': len(self.index.docstore.docs),
                'has_query_engine': self.query_engine is not None
            }

            # Count document types
            doc_types = {}
            for doc_id, doc in self.index.docstore.docs.items():
                doc_type = doc.metadata.get('document_type', 'unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

            stats['document_types'] = doc_types

            return stats

        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {'status': 'Error', 'error': str(e)}

    def query_structured(self, query: str, analysis_type: Optional[AnalysisType] = None) -> Union[StructuredAnalysisResponse, Dict[str, Any]]:
        """
        执行结构化查询，返回Pydantic结构化结果

        Args:
            query: 查询问题
            analysis_type: 分析类型，如果不指定则自动推断

        Returns:
            StructuredAnalysisResponse对象或错误信息字典
        """
        if not self.query_engine:
            return {
                "error": "查询引擎未初始化",
                "details": "请先构建索引",
                "query": query
            }

        try:
            # 1. 先用常规查询引擎检索相关内容
            response = self.query_engine.query(query)

            if not response or not response.response:
                return {
                    "error": "检索失败",
                    "details": "未找到相关内容",
                    "query": query
                }

            # 2. 提取证据来源
            evidence_sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for i, node in enumerate(response.source_nodes[:5]):  # 最多5个证据
                    # 确保相关性评分在0-1范围内
                    raw_score = getattr(node, 'score', 0.8)
                    normalized_score = min(1.0, max(0.0, raw_score / 10.0 if raw_score > 1.0 else raw_score))

                    evidence = EvidenceSource(
                        quote=node.text[:200] + "..." if len(node.text) > 200 else node.text,
                        relevance_score=normalized_score,
                        section=getattr(node.metadata, 'section', None) if hasattr(node, 'metadata') else None,
                        page_number=getattr(node.metadata, 'page_number', None) if hasattr(node, 'metadata') else None
                    )
                    evidence_sources.append(evidence)

            # 3. 自动推断分析类型（如果未指定）
            if not analysis_type:
                analysis_type = self._infer_analysis_type(query)

            # 4. 构建结构化提示
            structured_prompt = self._build_structured_prompt(
                query=query,
                context=response.response,
                analysis_type=analysis_type,
                evidence_sources=evidence_sources
            )

            # 5. 使用LLM进行结构化输出
            try:
                # 尝试使用函数调用（如果支持）
                messages = [
                    ChatMessage(
                        role="system",
                        content="你是一个专业的财务分析师。请基于提供的信息进行结构化分析。"
                    ),
                    ChatMessage(
                        role="user",
                        content=structured_prompt
                    )
                ]

                # 获取LLM实例
                llm = Settings.llm
                if hasattr(llm, 'structured_predict'):
                    structured_response = llm.structured_predict(
                        StructuredAnalysisResponse,
                        messages
                    )
                else:
                    # 降级到输出解析器
                    from llama_index.core.output_parsers import PydanticOutputParser
                    parser = PydanticOutputParser(StructuredAnalysisResponse)

                    prompt_with_format = f"{structured_prompt}\n\n{parser.format}"
                    completion = llm.complete(prompt_with_format)
                    structured_response = parser.parse(completion.text)

                # 6. 补充证据来源
                structured_response.evidence_sources = evidence_sources

                return structured_response

            except Exception as e:
                logger.warning(f"结构化输出失败，返回基础分析: {e}")

                # 降级：返回基础结构化响应
                return StructuredAnalysisResponse(
                    company_name="未识别",
                    analysis_type=analysis_type,
                    summary=response.response[:500] + "..." if len(response.response) > 500 else response.response,
                    key_findings=[response.response[:200] + "..." if len(response.response) > 200 else response.response],
                    evidence_sources=evidence_sources,
                    confidence_level=ConfidenceLevel.LOW,
                    limitations=["结构化解析失败，返回基础分析结果"]
                )

        except Exception as e:
            logger.error(f"结构化查询失败: {e}")
            return {
                "error": "结构化查询失败",
                "details": str(e),
                "query": query
            }
    def _infer_analysis_type(self, query: str) -> AnalysisType:
        """
        根据查询内容推断分析类型
        """
        query_lower = query.lower()

        # 财务指标关键词
        financial_keywords = ['营收', '收入', '利润', '资产', '负债', '现金流', '毛利率', '净利率',
                             'roe', 'roa', '财务', '业绩', '盈利', '亏损', '增长率']

        # 风险评估关键词
        risk_keywords = ['风险', '威胁', '挑战', '不确定性', '危机', '问题', '困难', '障碍']

        # 增长分析关键词
        growth_keywords = ['增长', '发展', '扩张', '趋势', '前景', '预测', '未来', '战略']

        # 竞争分析关键词
        competitive_keywords = ['竞争', '对手', '市场份额', '优势', '劣势', '比较', '行业地位']

        # 计算匹配度
        financial_score = sum(1 for keyword in financial_keywords if keyword in query_lower)
        risk_score = sum(1 for keyword in risk_keywords if keyword in query_lower)
        growth_score = sum(1 for keyword in growth_keywords if keyword in query_lower)
        competitive_score = sum(1 for keyword in competitive_keywords if keyword in query_lower)

        # 返回得分最高的类型
        scores = {
            AnalysisType.FINANCIAL_METRICS: financial_score,
            AnalysisType.RISK_ASSESSMENT: risk_score,
            AnalysisType.GROWTH_ANALYSIS: growth_score,
            AnalysisType.COMPETITIVE_ANALYSIS: competitive_score
        }

        max_type = max(scores, key=scores.get)
        return max_type if scores[max_type] > 0 else AnalysisType.GENERAL_INQUIRY

    def _build_structured_prompt(self, query: str, context: str, analysis_type: AnalysisType,
                                evidence_sources: List[EvidenceSource]) -> str:
        """
        构建结构化分析提示
        """
        base_prompt = f"""
请基于以下上下文信息，对查询进行专业的财务分析，并以结构化格式返回结果。

查询问题：{query}

分析类型：{analysis_type.value}

上下文信息：
{context}

分析要求：
1. 提取公司名称和财年（如果可识别）
2. 提供清晰的分析摘要
3. 列出3-5个关键发现
"""

        # 根据分析类型添加特定要求
        if analysis_type == AnalysisType.FINANCIAL_METRICS:
            base_prompt += """
4. 提取具体的财务指标数据（营收、净利润、资产、负债等）
5. 计算相关财务比率（如净利率、ROE、资产负债率等）
6. 评估财务表现和趋势
"""
        elif analysis_type == AnalysisType.RISK_ASSESSMENT:
            base_prompt += """
4. 识别主要风险因素，按类别分类
5. 评估每个风险的严重程度（高/中/低）
6. 分析风险对公司的潜在影响
"""
        elif analysis_type == AnalysisType.GROWTH_ANALYSIS:
            base_prompt += """
4. 分析历史增长趋势
5. 识别增长驱动因素
6. 评估未来增长潜力和挑战
"""
        elif analysis_type == AnalysisType.COMPETITIVE_ANALYSIS:
            base_prompt += """
4. 分析市场地位和竞争优势
5. 识别主要竞争对手和威胁
6. 评估行业趋势和公司应对策略
"""

        base_prompt += """
7. 评估分析的置信度（高/中/低）
8. 说明分析的局限性
9. 确保所有数据都有明确的来源引用

请确保分析客观、准确，并基于提供的证据进行推理。
"""

        return base_prompt
    # ==================== 第二阶段增强查询方法 ====================

    async def query_enhanced(self, query: str, use_router: bool = True,
                           use_sub_questions: bool = False,
                           enable_evaluation: bool = True) -> EnhancedQueryResult:
        """
        第二阶段增强查询方法

        Args:
            query: 查询问题
            use_router: 是否使用智能路由
            use_sub_questions: 是否使用子问题分解
            enable_evaluation: 是否启用评估

        Returns:
            EnhancedQueryResult: 增强查询结果
        """
        if not self.enhanced_manager:
            # 降级到基础查询
            logger.warning("⚠️ 增强查询管理器不可用，降级到基础查询")
            basic_response = self.query(query)
            return EnhancedQueryResult(
                query=query,
                query_type=QueryType.DETAILED_SEARCH,
                synthesis_strategy=SynthesisStrategy.COMPACT,
                answer=basic_response.get('answer', '查询失败'),
                sources=basic_response.get('sources', []),
                processing_time=0.0
            )

        try:
            result = await self.enhanced_manager.query_enhanced(
                query=query,
                use_router=use_router,
                use_sub_questions=use_sub_questions,
                enable_evaluation=enable_evaluation
            )
            return result
        except Exception as e:
            logger.error(f"❌ 增强查询失败: {e}")
            # 降级到基础查询
            basic_response = self.query(query)
            return EnhancedQueryResult(
                query=query,
                query_type=QueryType.DETAILED_SEARCH,
                synthesis_strategy=SynthesisStrategy.COMPACT,
                answer=basic_response.get('answer', f'查询失败: {str(e)}'),
                sources=basic_response.get('sources', []),
                processing_time=0.0
            )

    def query_with_router(self, query: str) -> Dict[str, Any]:
        """
        使用路由引擎查询
        """
        if not self.enhanced_manager or not self.enhanced_manager.router_query_engine:
            logger.warning("⚠️ 路由引擎不可用，降级到基础查询")
            return self.query(query)

        try:
            response = self.enhanced_manager.router_query_engine.query(query)
            sources = self.enhanced_manager._extract_sources(response)

            return {
                'answer': str(response),
                'sources': sources,
                'query_type': 'router',
                'engine_used': 'router_query_engine'
            }
        except Exception as e:
            logger.error(f"❌ 路由查询失败: {e}")
            return self.query(query)

    def query_with_sub_questions(self, query: str) -> Dict[str, Any]:
        """
        使用子问题分解查询
        """
        if not self.enhanced_manager or not self.enhanced_manager.sub_question_engine:
            logger.warning("⚠️ 子问题引擎不可用，降级到基础查询")
            return self.query(query)

        try:
            response = self.enhanced_manager.sub_question_engine.query(query)
            sources = self.enhanced_manager._extract_sources(response)

            # 提取子问题信息
            sub_questions = []
            sub_answers = []
            if hasattr(response, 'metadata') and response.metadata:
                sub_questions = response.metadata.get('sub_questions', [])
                sub_answers = response.metadata.get('sub_answers', [])

            return {
                'answer': str(response),
                'sources': sources,
                'sub_questions': sub_questions,
                'sub_answers': sub_answers,
                'query_type': 'sub_question',
                'engine_used': 'sub_question_engine'
            }
        except Exception as e:
            logger.error(f"❌ 子问题查询失败: {e}")
            return self.query(query)

    async def batch_query_enhanced(self, queries: List[str]) -> List[EnhancedQueryResult]:
        """
        批量增强查询
        """
        if not self.enhanced_manager:
            logger.warning("⚠️ 增强查询管理器不可用")
            results = []
            for query in queries:
                basic_response = self.query(query)
                result = EnhancedQueryResult(
                    query=query,
                    query_type=QueryType.DETAILED_SEARCH,
                    synthesis_strategy=SynthesisStrategy.COMPACT,
                    answer=basic_response.get('answer', '查询失败'),
                    sources=basic_response.get('sources', []),
                    processing_time=0.0
                )
                results.append(result)
            return results

    # ==================== 第三阶段增强方法 ====================

    def create_chat_session(self, mode: str = "context", **kwargs) -> Optional[str]:
        """创建聊天会话"""
        if not self.phase3_manager:
            logger.warning("⚠️ 第三阶段功能未启用，无法创建聊天会话")
            return None

        try:
            from utils.phase3_enhancements import ChatMode
            chat_mode = ChatMode(mode) if mode in ChatMode.__members__.values() else ChatMode.CONTEXT
            return self.phase3_manager.create_chat_session(mode=chat_mode, **kwargs)
        except Exception as e:
            logger.error(f"❌ 创建聊天会话失败: {e}")
            return None

    def chat(self, session_id: str, message: str) -> Dict[str, Any]:
        """聊天"""
        if not self.phase3_manager:
            return {"error": "第三阶段功能未启用"}

        return self.phase3_manager.chat(session_id, message)

    def stream_chat(self, session_id: str, message: str):
        """流式聊天"""
        if not self.phase3_manager:
            yield "错误: 第三阶段功能未启用"
            return

        yield from self.phase3_manager.stream_chat(session_id, message)

    async def run_workflow(self, query: str) -> Dict[str, Any]:
        """运行工作流"""
        if not self.phase3_manager:
            return {"error": "第三阶段功能未启用"}

        try:
            result = await self.phase3_manager.run_analysis_workflow(query)
            if result is None:
                return {"error": "工作流返回空结果"}

            return {
                'workflow_id': result.workflow_id,
                'status': result.status.value if hasattr(result.status, 'value') else str(result.status),
                'result': result.result,
                'execution_time': result.execution_time,
                'error': result.error
            }
        except Exception as e:
            logger.error(f"❌ 工作流运行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    async def run_agent(self, query: str) -> Dict[str, Any]:
        """运行智能代理"""
        if not self.phase3_manager:
            return {"error": "第三阶段功能未启用"}

        return await self.phase3_manager.run_agent_query(query)

    async def analyze_multimodal(self, image_path: str, text_query: str) -> Dict[str, Any]:
        """多模态分析"""
        if not self.phase3_manager:
            return {"error": "第三阶段功能未启用"}

        return await self.phase3_manager.analyze_multimodal(image_path, text_query)

    def get_phase3_capabilities(self) -> Dict[str, bool]:
        """获取第三阶段功能能力"""
        if not self.phase3_manager:
            return {
                'chat_engines': False,
                'workflows': False,
                'agents': False,
                'multimodal': False,
                'streaming': False,
                'memory_management': False
            }

        return self.phase3_manager.get_capabilities()

    def get_phase3_stats(self) -> Dict[str, Any]:
        """获取第三阶段统计信息"""
        if not self.phase3_manager:
            return {"error": "第三阶段功能未启用"}

        return self.phase3_manager.get_stats()

    def get_chat_sessions(self) -> List[Dict[str, Any]]:
        """获取聊天会话列表"""
        if not self.phase3_manager:
            return []

        sessions = self.phase3_manager.chat_manager.get_active_sessions()
        return [
            {
                'session_id': session.session_id,
                'chat_mode': session.chat_mode.value,
                'created_at': session.created_at.isoformat(),
                'last_active': session.last_active.isoformat(),
                'message_count': session.message_count
            }
            for session in sessions
        ]

    def close_chat_session(self, session_id: str) -> bool:
        """关闭聊天会话"""
        if not self.phase3_manager:
            return False

        return self.phase3_manager.chat_manager.close_session(session_id)

    # ==================== 第四阶段增强方法 ====================

    def create_multimodal_index(self, data_path: str) -> bool:
        """创建多模态索引"""
        if not self.phase4_manager:
            logger.warning("⚠️ 第四阶段功能未启用，无法创建多模态索引")
            return False

        return self.phase4_manager.create_multimodal_index(data_path)

    def analyze_multimodal_content(self, query: str, include_images: bool = True) -> Dict[str, Any]:
        """分析多模态内容"""
        if not self.phase4_manager:
            return {"error": "第四阶段功能未启用"}

        return self.phase4_manager.analyze_multimodal_content(query, include_images)

    def create_knowledge_graph(self, documents: List[Any] = None) -> bool:
        """创建知识图谱"""
        if not self.phase4_manager:
            logger.warning("⚠️ 第四阶段功能未启用，无法创建知识图谱")
            return False

        return self.phase4_manager.create_knowledge_graph(documents)

    def query_knowledge_graph(self, query: str, mode: str = "hybrid") -> Dict[str, Any]:
        """查询知识图谱"""
        if not self.phase4_manager:
            return {"error": "第四阶段功能未启用"}

        return self.phase4_manager.query_knowledge_graph(query, mode)

    def render_financial_analysis_prompt(self, company_name: str, period: str,
                                       financial_data: str) -> str:
        """渲染财务分析提示"""
        if not self.phase4_manager:
            return f"基于以下财务数据，请进行专业的财务分析：\n\n公司名称：{company_name}\n分析期间：{period}\n\n财务数据：\n{financial_data}"

        return self.phase4_manager.render_financial_analysis_prompt(company_name, period, financial_data)

    def render_risk_assessment_prompt(self, company_background: str, **kwargs) -> str:
        """渲染风险评估提示"""
        if not self.phase4_manager:
            return f"请对以下公司进行全面的风险评估：\n\n公司背景：\n{company_background}"

        return self.phase4_manager.render_risk_assessment_prompt(company_background, **kwargs)

    def switch_storage_backend(self, backend: str, persist_dir: str = "./storage") -> bool:
        """切换存储后端"""
        if not self.phase4_manager:
            logger.warning("⚠️ 第四阶段功能未启用，无法切换存储后端")
            return False

        try:
            from utils.phase4_enhancements import StorageBackend
            backend_enum = StorageBackend(backend)
            return self.phase4_manager.switch_storage_backend(backend_enum, persist_dir)
        except ValueError:
            logger.error(f"❌ 不支持的存储后端: {backend}")
            return False

    def get_phase4_capabilities(self) -> Dict[str, Any]:
        """获取第四阶段功能能力"""
        if not self.phase4_manager:
            return {
                'multimodal': {'supports_images': False, 'supports_text': True, 'image_formats': []},
                'storage': {'available_backends': ['simple'], 'current_backend': 'simple'},
                'metadata_extraction': {'available_extractors': []},
                'knowledge_graph': {'supports_kg': False},
                'prompt_engineering': {'supports_jinja': False, 'available_templates': []}
            }

        return self.phase4_manager.get_capabilities()

    def get_phase4_stats(self) -> Dict[str, Any]:
        """获取第四阶段统计信息"""
        if not self.phase4_manager:
            return {"error": "第四阶段功能未启用"}

        return self.phase4_manager.get_stats()

    def get_storage_capabilities(self) -> Dict[str, Any]:
        """获取存储能力"""
        if not self.phase4_manager:
            return {"simple": {"backend_type": "simple", "supports_metadata_filtering": True}}

        return self.phase4_manager.get_storage_capabilities()

    def get_enhanced_stats(self) -> Dict[str, Any]:
        """
        获取增强功能统计信息
        """
        if not self.enhanced_manager:
            return {
                'phase2_enabled': False,
                'enhanced_manager_available': False
            }

        stats = self.enhanced_manager.get_engine_stats()
        stats.update({
            'phase2_enabled': self.enable_phase2_features,
            'enhanced_manager_available': True,
            'evaluation_enabled': self.evaluation_enabled
        })

        return stats

    def get_available_query_modes(self) -> List[str]:
        """
        获取可用的查询模式
        """
        modes = ['basic', 'structured']  # 第一阶段功能

        if self.enhanced_manager:
            if self.enhanced_manager.router_query_engine:
                modes.append('router')
            if self.enhanced_manager.sub_question_engine:
                modes.append('sub_question')
            modes.append('enhanced')
            modes.append('batch_enhanced')

        return modes