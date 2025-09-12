"""
Enhanced Query Engines using LlamaIndex's advanced querying capabilities
"""

from typing import Dict, Any, List, Optional
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.query_engine import (
    RouterQueryEngine, 
    SubQuestionQueryEngine,
    MultiStepQueryEngine,
    RetrieverQueryEngine
)
from llama_index.core.retrievers import VectorIndexRetriever
# Note: Some retrievers may not be available in current version
try:
    from llama_index.core.retrievers import AutoMergingRetriever
except ImportError:
    AutoMergingRetriever = None

try:
    from llama_index.core.retrievers import KeywordTableRetriever  
except ImportError:
    KeywordTableRetriever = None
from llama_index.core.tools import QueryEngineTool
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.postprocessor import SimilarityPostprocessor, KeywordNodePostprocessor
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.query_engine.knowledge_graph_query_engine import KnowledgeGraphQueryEngine
import logging

logger = logging.getLogger(__name__)

class EnhancedQueryEngineManager:
    """
    Manage multiple advanced query engines for different types of financial queries
    """
    
    def __init__(self, index: VectorStoreIndex, llm=None):
        self.index = index
        self.llm = llm
        self.query_engines = {}
        self.router_query_engine = None
        self._build_specialized_engines()
    
    def _build_specialized_engines(self):
        """Build specialized query engines for different query types"""
        try:
            # 1. Financial Data Query Engine - for precise numerical queries
            financial_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=10,
                vector_store_query_mode="default"
            )
            
            financial_postprocessor = KeywordNodePostprocessor(
                required_keywords=["财务", "金额", "收入", "利润", "资产", "负债", "现金流", "financial", "revenue", "profit", "assets", "liabilities"],
                exclude_keywords=["注释", "说明", "附录", "notes", "appendix"]
            )
            
            self.query_engines["financial_data"] = RetrieverQueryEngine.from_args(
                retriever=financial_retriever,
                node_postprocessors=[financial_postprocessor],
                response_synthesizer=get_response_synthesizer(
                    response_mode="tree_summarize",
                    use_async=True
                )
            )
            
            # 2. Company Comparison Query Engine - for comparative analysis
            comparison_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=15,
                vector_store_query_mode="default"
            )
            
            self.query_engines["company_comparison"] = RetrieverQueryEngine.from_args(
                retriever=comparison_retriever,
                response_synthesizer=get_response_synthesizer(
                    response_mode="compact",
                    use_async=True
                )
            )
            
            # 3. Trend Analysis Query Engine - for historical and trend questions
            trend_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=12,
                vector_store_query_mode="default"
            )
            
            trend_postprocessor = KeywordNodePostprocessor(
                required_keywords=["年", "季度", "增长", "变化", "趋势", "year", "quarter", "growth", "change", "trend"],
                exclude_keywords=[]
            )
            
            self.query_engines["trend_analysis"] = RetrieverQueryEngine.from_args(
                retriever=trend_retriever,
                node_postprocessors=[trend_postprocessor],
                response_synthesizer=get_response_synthesizer(
                    response_mode="tree_summarize",
                    use_async=True
                )
            )
            
            # 4. Risk Assessment Query Engine - for risk and compliance queries
            risk_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=8,
                vector_store_query_mode="default"
            )
            
            risk_postprocessor = KeywordNodePostprocessor(
                required_keywords=["风险", "合规", "监管", "审计", "risk", "compliance", "regulatory", "audit"],
                exclude_keywords=[]
            )
            
            self.query_engines["risk_assessment"] = RetrieverQueryEngine.from_args(
                retriever=risk_retriever,
                node_postprocessors=[risk_postprocessor],
                response_synthesizer=get_response_synthesizer(
                    response_mode="compact",
                    use_async=True
                )
            )
            
            # 5. General Context Query Engine - for general questions
            general_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=6,
                vector_store_query_mode="default"
            )
            
            similarity_postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)
            
            self.query_engines["general"] = RetrieverQueryEngine.from_args(
                retriever=general_retriever,
                node_postprocessors=[similarity_postprocessor],
                response_synthesizer=get_response_synthesizer(
                    response_mode="refine",
                    use_async=True
                )
            )
            
            logger.info("Successfully built specialized query engines")
            
        except Exception as e:
            logger.error(f"Error building specialized query engines: {str(e)}")
    
    def build_router_query_engine(self) -> RouterQueryEngine:
        """Build router query engine to automatically select the best engine"""
        try:
            # Create query engine tools
            query_engine_tools = []
            
            # Financial Data Tool
            financial_tool = QueryEngineTool.from_defaults(
                query_engine=self.query_engines["financial_data"],
                name="financial_data_engine",
                description="""
                Use this engine for queries about specific financial metrics, numbers, and data.
                Examples:
                - What is the company's revenue?
                - Show me the profit margins
                - What are the total assets?
                - Financial ratio calculations
                - Specific numerical data from financial statements
                """
            )
            query_engine_tools.append(financial_tool)
            
            # Company Comparison Tool
            comparison_tool = QueryEngineTool.from_defaults(
                query_engine=self.query_engines["company_comparison"],
                name="company_comparison_engine", 
                description="""
                Use this engine for comparative analysis between companies or time periods.
                Examples:
                - Compare company A vs company B
                - How does performance compare to industry peers?
                - Benchmarking and competitive analysis
                - Relative performance metrics
                """
            )
            query_engine_tools.append(comparison_tool)
            
            # Trend Analysis Tool
            trend_tool = QueryEngineTool.from_defaults(
                query_engine=self.query_engines["trend_analysis"],
                name="trend_analysis_engine",
                description="""
                Use this engine for trend analysis, historical patterns, and temporal questions.
                Examples:
                - How has revenue grown over time?
                - What are the quarterly trends?
                - Year-over-year changes
                - Growth patterns and forecasting insights
                """
            )
            query_engine_tools.append(trend_tool)
            
            # Risk Assessment Tool
            risk_tool = QueryEngineTool.from_defaults(
                query_engine=self.query_engines["risk_assessment"],
                name="risk_assessment_engine",
                description="""
                Use this engine for risk-related queries, compliance, and regulatory matters.
                Examples:
                - What are the main risk factors?
                - Compliance and regulatory issues
                - Audit findings and concerns
                - Risk management strategies
                """
            )
            query_engine_tools.append(risk_tool)
            
            # General Tool
            general_tool = QueryEngineTool.from_defaults(
                query_engine=self.query_engines["general"],
                name="general_context_engine",
                description="""
                Use this engine for general questions about the company or documents.
                Examples:
                - General company information
                - Business description and operations
                - Management discussion
                - Other general inquiries
                """
            )
            query_engine_tools.append(general_tool)
            
            # Create router with LLM selector
            self.router_query_engine = RouterQueryEngine(
                selector=LLMSingleSelector.from_defaults(llm=self.llm),
                query_engine_tools=query_engine_tools,
                verbose=True
            )
            
            logger.info("Successfully built router query engine")
            return self.router_query_engine
            
        except Exception as e:
            logger.error(f"Error building router query engine: {str(e)}")
            return None
    
    def build_sub_question_engine(self) -> SubQuestionQueryEngine:
        """Build sub-question query engine for complex multi-part queries"""
        try:
            # Create tools for sub-question decomposition
            query_engine_tools = []
            
            for name, engine in self.query_engines.items():
                tool = QueryEngineTool.from_defaults(
                    query_engine=engine,
                    name=f"{name}_tool",
                    description=f"Query engine for {name.replace('_', ' ')} related questions"
                )
                query_engine_tools.append(tool)
            
            sub_question_engine = SubQuestionQueryEngine.from_defaults(
                query_engine_tools=query_engine_tools,
                use_async=True,
                verbose=True
            )
            
            logger.info("Successfully built sub-question query engine")
            return sub_question_engine
            
        except Exception as e:
            logger.error(f"Error building sub-question query engine: {str(e)}")
            return None
    
    def get_query_engine(self, engine_type: str = "router") -> Optional[Any]:
        """Get a specific query engine"""
        if engine_type == "router":
            if not self.router_query_engine:
                return self.build_router_query_engine()
            return self.router_query_engine
        elif engine_type == "sub_question":
            return self.build_sub_question_engine()
        elif engine_type in self.query_engines:
            return self.query_engines[engine_type]
        else:
            logger.warning(f"Unknown engine type: {engine_type}")
            return None
    
    def query(self, question: str, engine_type: str = "router", context_filter: Optional[Dict] = None) -> Dict[str, Any]:
        """Query using the specified engine type"""
        try:
            query_engine = self.get_query_engine(engine_type)
            if not query_engine:
                return {
                    'answer': f"Query engine '{engine_type}' not available",
                    'error': True,
                    'engine_type': engine_type
                }
            
            # Enhance query with context filter
            enhanced_query = self._enhance_query_with_context(question, context_filter)
            
            # Execute query
            response = query_engine.query(enhanced_query)
            
            # Extract metadata and sources
            sources = self._extract_response_sources(response)
            
            result = {
                'answer': str(response),
                'sources': sources,
                'error': False,
                'engine_type': engine_type,
                'original_question': question,
                'enhanced_query': enhanced_query,
                'metadata': self._extract_response_metadata(response)
            }
            
            logger.info(f"Successfully processed query with {engine_type} engine")
            return result
            
        except Exception as e:
            logger.error(f"Error in query processing: {str(e)}")
            return {
                'answer': f"Error processing query: {str(e)}",
                'error': True,
                'engine_type': engine_type,
                'original_question': question
            }
    
    def _enhance_query_with_context(self, question: str, context_filter: Optional[Dict]) -> str:
        """Enhance query with contextual information"""
        enhanced_parts = [question]
        
        if context_filter:
            if 'company' in context_filter:
                enhanced_parts.append(f"Focus on information about {context_filter['company']}")
            
            if 'year' in context_filter:
                enhanced_parts.append(f"for the year {context_filter['year']}")
            
            if 'document_type' in context_filter:
                enhanced_parts.append(f"from {context_filter['document_type']} documents")
            
            if 'financial_focus' in context_filter:
                focus_areas = context_filter['financial_focus']
                if isinstance(focus_areas, list):
                    enhanced_parts.append(f"with focus on {', '.join(focus_areas)}")
        
        enhanced_parts.append("Please provide specific data and cite sources when possible.")
        
        return " ".join(enhanced_parts)
    
    def _extract_response_sources(self, response) -> List[Dict[str, Any]]:
        """Extract source information from response"""
        sources = []
        try:
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    source_info = {
                        'text_snippet': node.text[:200] + "..." if len(node.text) > 200 else node.text,
                        'score': getattr(node, 'score', 0.0),
                        'metadata': node.metadata if hasattr(node, 'metadata') else {}
                    }
                    sources.append(source_info)
        except Exception as e:
            logger.error(f"Error extracting response sources: {str(e)}")
        
        return sources
    
    def _extract_response_metadata(self, response) -> Dict[str, Any]:
        """Extract metadata from response"""
        metadata = {}
        try:
            if hasattr(response, 'metadata') and response.metadata:
                metadata = response.metadata
            
            # Add response statistics
            metadata['response_length'] = len(str(response))
            metadata['source_count'] = len(getattr(response, 'source_nodes', []))
            
        except Exception as e:
            logger.error(f"Error extracting response metadata: {str(e)}")
        
        return metadata


class HybridRetriever:
    """
    Hybrid retriever combining vector similarity and keyword matching
    """
    
    def __init__(self, index: VectorStoreIndex, similarity_top_k: int = 10, keyword_top_k: int = 5):
        self.index = index
        self.similarity_top_k = similarity_top_k
        self.keyword_top_k = keyword_top_k
        self.vector_retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k
        )
        # Note: KeywordTableRetriever may not be available in current version
        self.keyword_retriever = None
        if KeywordTableRetriever:
            self._try_build_keyword_retriever()
    
    def _try_build_keyword_retriever(self):
        """Try to build keyword retriever if available"""
        try:
            # This would require a keyword table index to be built
            # For now, we'll use a simple implementation
            pass
        except Exception as e:
            logger.warning(f"Could not build keyword retriever: {str(e)}")
    
    def retrieve(self, query_str: str) -> List[Any]:
        """Retrieve using hybrid approach"""
        try:
            # Get vector similarity results
            vector_results = self.vector_retriever.retrieve(query_str)
            
            # Get keyword results (if available)
            keyword_results = []
            if self.keyword_retriever:
                keyword_results = self.keyword_retriever.retrieve(query_str)
            
            # Combine and deduplicate results
            combined_results = self._combine_results(vector_results, keyword_results)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {str(e)}")
            return vector_results if 'vector_results' in locals() else []
    
    def _combine_results(self, vector_results: List, keyword_results: List) -> List:
        """Combine and score results from different retrievers"""
        try:
            # Simple combination - prioritize vector results, add unique keyword results
            seen_texts = set()
            combined = []
            
            # Add vector results first (higher priority)
            for result in vector_results:
                text_key = result.text[:100]  # Use first 100 chars as key
                if text_key not in seen_texts:
                    combined.append(result)
                    seen_texts.add(text_key)
            
            # Add unique keyword results
            for result in keyword_results:
                text_key = result.text[:100]
                if text_key not in seen_texts and len(combined) < self.similarity_top_k + self.keyword_top_k:
                    combined.append(result)
                    seen_texts.add(text_key)
            
            return combined[:self.similarity_top_k + self.keyword_top_k]
            
        except Exception as e:
            logger.error(f"Error combining retrieval results: {str(e)}")
            return vector_results


class ContextualQueryProcessor:
    """
    Process queries with enhanced contextual understanding
    """
    
    def __init__(self, query_engine_manager: EnhancedQueryEngineManager):
        self.query_manager = query_engine_manager
        self.query_history = []
        self.context_memory = {}
    
    def process_query_with_context(self, question: str, conversation_id: str = "default") -> Dict[str, Any]:
        """Process query with conversational context"""
        try:
            # Get conversation context
            context = self._get_conversation_context(conversation_id)
            
            # Classify query type
            query_type = self._classify_query_type(question)
            
            # Enhance query with context
            enhanced_context = self._build_enhanced_context(question, context, query_type)
            
            # Select best engine for query type
            engine_type = self._select_engine_for_query_type(query_type)
            
            # Execute query
            result = self.query_manager.query(
                question=question,
                engine_type=engine_type,
                context_filter=enhanced_context
            )
            
            # Update conversation context
            self._update_conversation_context(conversation_id, question, result)
            
            # Add query classification to result
            result['query_type'] = query_type
            result['conversation_id'] = conversation_id
            
            return result
            
        except Exception as e:
            logger.error(f"Error in contextual query processing: {str(e)}")
            return {
                'answer': f"Error processing contextual query: {str(e)}",
                'error': True,
                'query_type': 'unknown'
            }
    
    def _classify_query_type(self, question: str) -> str:
        """Classify the type of query"""
        question_lower = question.lower()
        
        # Financial data queries
        if any(keyword in question_lower for keyword in ['收入', '利润', '资产', '负债', '现金流', 'revenue', 'profit', 'assets', 'cash flow']):
            return 'financial_data'
        
        # Comparison queries
        elif any(keyword in question_lower for keyword in ['比较', '对比', '相比', 'compare', 'versus', 'vs', 'against']):
            return 'comparison'
        
        # Trend and temporal queries
        elif any(keyword in question_lower for keyword in ['趋势', '增长', '变化', '历史', 'trend', 'growth', 'change', 'over time', 'historical']):
            return 'trend_analysis'
        
        # Risk queries
        elif any(keyword in question_lower for keyword in ['风险', '合规', 'risk', 'compliance', 'regulatory']):
            return 'risk_assessment'
        
        # Complex multi-part queries
        elif any(keyword in question_lower for keyword in ['以及', '同时', '还有', 'and also', 'additionally', 'furthermore']) or '?' in question and question.count('?') > 1:
            return 'multi_part'
        
        else:
            return 'general'
    
    def _select_engine_for_query_type(self, query_type: str) -> str:
        """Select the best engine for the query type"""
        engine_mapping = {
            'financial_data': 'financial_data',
            'comparison': 'company_comparison', 
            'trend_analysis': 'trend_analysis',
            'risk_assessment': 'risk_assessment',
            'multi_part': 'sub_question',
            'general': 'router'
        }
        
        return engine_mapping.get(query_type, 'router')
    
    def _get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get context for a conversation"""
        return self.context_memory.get(conversation_id, {
            'previous_queries': [],
            'mentioned_companies': set(),
            'mentioned_years': set(),
            'focus_areas': set()
        })
    
    def _build_enhanced_context(self, question: str, context: Dict[str, Any], query_type: str) -> Dict[str, Any]:
        """Build enhanced context for the query"""
        enhanced_context = {}
        
        # Add mentioned companies from context
        if context.get('mentioned_companies'):
            enhanced_context['company'] = list(context['mentioned_companies'])[0]  # Use first mentioned
        
        # Add mentioned years
        if context.get('mentioned_years'):
            enhanced_context['year'] = max(context['mentioned_years'])  # Use most recent
        
        # Add focus areas
        if context.get('focus_areas'):
            enhanced_context['financial_focus'] = list(context['focus_areas'])
        
        # Extract new context from current question
        import re
        
        # Extract years
        years = re.findall(r'\b(20\d{2})\b', question)
        if years:
            enhanced_context['year'] = years[-1]  # Use last mentioned year
        
        # Extract company mentions (basic pattern)
        # This could be enhanced with NER
        company_patterns = [r'([^。，\s]+(?:公司|Corporation|Inc\.|Ltd\.|Corp\.))', r'([A-Z][a-zA-Z\s&]+(?:Company|Corp|Inc|Ltd))']
        for pattern in company_patterns:
            companies = re.findall(pattern, question)
            if companies:
                enhanced_context['company'] = companies[0]
                break
        
        return enhanced_context
    
    def _update_conversation_context(self, conversation_id: str, question: str, result: Dict[str, Any]):
        """Update conversation context with new information"""
        try:
            if conversation_id not in self.context_memory:
                self.context_memory[conversation_id] = {
                    'previous_queries': [],
                    'mentioned_companies': set(),
                    'mentioned_years': set(),
                    'focus_areas': set()
                }
            
            context = self.context_memory[conversation_id]
            
            # Add to query history
            context['previous_queries'].append({
                'question': question,
                'query_type': result.get('query_type', 'unknown'),
                'timestamp': self._get_current_timestamp()
            })
            
            # Extract and store context elements
            import re
            
            # Extract companies
            company_patterns = [r'([^。，\s]+(?:公司|Corporation|Inc\.|Ltd\.|Corp\.))', r'([A-Z][a-zA-Z\s&]+(?:Company|Corp|Inc|Ltd))']
            for pattern in company_patterns:
                companies = re.findall(pattern, question)
                context['mentioned_companies'].update(companies)
            
            # Extract years
            years = re.findall(r'\b(20\d{2})\b', question)
            context['mentioned_years'].update(years)
            
            # Extract focus areas from query type
            focus_mapping = {
                'financial_data': 'financial_metrics',
                'comparison': 'comparative_analysis',
                'trend_analysis': 'trend_analysis',
                'risk_assessment': 'risk_factors'
            }
            
            query_type = result.get('query_type', 'unknown')
            if query_type in focus_mapping:
                context['focus_areas'].add(focus_mapping[query_type])
            
            # Limit context size
            if len(context['previous_queries']) > 10:
                context['previous_queries'] = context['previous_queries'][-10:]
            
            # Convert sets to lists for JSON serialization if needed
            # Keep as sets for now for efficient operations
            
        except Exception as e:
            logger.error(f"Error updating conversation context: {str(e)}")
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation context"""
        context = self._get_conversation_context(conversation_id)
        
        return {
            'conversation_id': conversation_id,
            'total_queries': len(context['previous_queries']),
            'mentioned_companies': list(context['mentioned_companies']),
            'mentioned_years': sorted(list(context['mentioned_years'])),
            'focus_areas': list(context['focus_areas']),
            'recent_queries': context['previous_queries'][-5:]  # Last 5 queries
        }