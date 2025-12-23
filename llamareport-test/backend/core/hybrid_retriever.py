"""
Hybrid Retriever - 混合检索器
基于语义相似度 × 指标加权 × 年份过滤的财务数据检索系统
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.retrievers import VectorIndexRetriever
import chromadb

logger = logging.getLogger(__name__)

class HybridRetrievalScorer:
    """混合检索评分器"""
    
    def __init__(self):
        # 权重配置
        self.weights = {
            'semantic_similarity': 0.6,  # 语义相似度权重
            'metric_matching': 0.3,      # 指标匹配度权重
            'year_consistency': 0.1      # 年份一致性权重
        }
        
        # 财务指标关键词库
        self.financial_metrics = [
            '净利润', 'ROE', 'ROA', '负债率', '资产负债率', '流动比率',
            '营业收入', '营业利润', '毛利率', '净利率', '资产周转率',
            '现金流', '股东权益', '总资产', '总负债', '每股收益',
            '净资产', '流动资产', '非流动资产', '流动负债', '非流动负债',
            '营业成本', '销售费用', '管理费用', '财务费用', '研发费用'
        ]
        
        # 财务指标同义词
        self.financial_synonyms = {
            '净利润': ['净利润', '盈余', '收益', 'Profit', 'Earnings', '净利'],
            'ROE': ['ROE', '净资产收益率', '权益回报率', 'Return on Equity'],
            '营业收入': ['营业收入', '营收', '收入', 'Revenue', 'Sales'],
            '资产': ['资产', 'Assets', '总资产', '净资产'],
            '负债': ['负债', 'Liabilities', '总负债', '债务']
        }
    
    def calculate_comprehensive_score(self, 
                                    query: str, 
                                    document: Document, 
                                    semantic_score: float) -> Dict[str, Any]:
        """
        计算综合评分，财务报表文档会获得额外加分
        """
        """计算综合评分"""
        
        # 1. 语义相似度 (sim_score)
        sim_score = semantic_score
        
        # 2. 指标匹配度 (metric_score)
        metric_score = self._calculate_metric_score(query, document)
        
        # 3. 年份一致性 (year_score)
        year_score = self._calculate_year_score(query, document)
        
        # 4. 财务报表加分（如果文档是财务报表，给予额外权重）
        financial_statement_bonus = 0.0
        if document.metadata.get('is_financial_statement', False):
            financial_statement_bonus = 0.2  # 财务报表额外加分20%
            # 如果查询包含财务报表相关关键词，额外加分
            query_lower = query.lower()
            statement_type = document.metadata.get('financial_statement_type', '')
            if statement_type:
                type_keywords = {
                    '利润表': ['利润', '收入', '成本', 'profit', 'revenue', 'income'],
                    '资产负债表': ['资产', '负债', '权益', 'asset', 'liability', 'equity'],
                    '现金流量表': ['现金流', '现金', 'cash flow', 'cash']
                }
                if statement_type in type_keywords:
                    for keyword in type_keywords[statement_type]:
                        if keyword in query_lower:
                            financial_statement_bonus = 0.3  # 匹配时额外加分30%
                            break
        
        # 5. 计算综合评分（财务报表会获得额外加分）
        base_score = (
            sim_score * self.weights['semantic_similarity'] +
            metric_score * self.weights['metric_matching'] +
            year_score * self.weights['year_consistency']
        )
        
        # 应用财务报表加分（但不超过1.0）
        comprehensive_score = min(1.0, base_score + financial_statement_bonus)
        
        return {
            'comprehensive_score': comprehensive_score,
            'sim_score': sim_score,
            'metric_score': metric_score,
            'year_score': year_score,
            'financial_statement_bonus': financial_statement_bonus,
            'weights': self.weights
        }
    
    def _calculate_metric_score(self, query: str, document: Document) -> float:
        """计算指标匹配度"""
        query_lower = query.lower()
        doc_text = document.text.lower()
        
        # 检查查询中的财务指标
        query_metrics = [metric for metric in self.financial_metrics 
                        if metric in query_lower]
        
        if not query_metrics:
            return 0.5  # 中性分数
        
        # 检查文档中是否包含这些指标
        matched_metrics = [metric for metric in query_metrics 
                          if metric in doc_text]
        
        # 计算匹配度
        base_score = len(matched_metrics) / len(query_metrics)
        
        # 额外加分：如果文档是表格类型且包含财务指标
        if document.metadata.get('doc_type') == 'table' and matched_metrics:
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def _calculate_year_score(self, query: str, document: Document) -> float:
        """计算年份一致性"""
        # 从查询中提取年份
        query_years = self._extract_years_from_text(query)
        
        if not query_years:
            return 0.0
        
        # 从文档元数据中获取年份
        doc_year = document.metadata.get('year')
        if not doc_year:
            return 0.0
        
        # 检查年份匹配
        if str(doc_year) in query_years:
            return 1.0
        else:
            return 0.0
    
    def _extract_years_from_text(self, text: str) -> List[str]:
        """从文本中提取年份信息"""
        patterns = [
            r'(\d{4})-(\d{4})年',  # 2020-2022年
            r'(\d{4})年',          # 2023年
            r'(\d{4})到(\d{4})',   # 2020到2022
            r'(\d{4})至(\d{4})',   # 2020至2022
            r'近(\d)年',           # 近三年
        ]
        
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:  # 年份范围
                        start_year, end_year = match
                        years.extend(range(int(start_year), int(end_year) + 1))
                    elif len(match) == 1:  # 近N年
                        n_years = int(match[0])
                        current_year = datetime.now().year
                        years.extend(range(current_year - n_years + 1, current_year + 1))
                else:
                    years.append(int(match))
        
        return [str(year) for year in sorted(set(years))]

class QueryExpansion:
    """查询扩展器"""
    
    def __init__(self):
        self.financial_synonyms = {
            '净利润': ['净利润', '盈余', '收益', 'Profit', 'Earnings', '净利'],
            'ROE': ['ROE', '净资产收益率', '权益回报率', 'Return on Equity'],
            '营业收入': ['营业收入', '营收', '收入', 'Revenue', 'Sales'],
            '资产': ['资产', 'Assets', '总资产', '净资产'],
            '负债': ['负债', 'Liabilities', '总负债', '债务'],
            '现金流': ['现金流', '现金流量', 'Cash Flow', '经营现金流'],
            '毛利率': ['毛利率', 'Gross Margin', '毛利润率'],
            '净利率': ['净利率', 'Net Margin', '净利润率']
        }
    
    def expand_query(self, query: str) -> str:
        """扩展查询词"""
        expanded_terms = []
        
        for term, synonyms in self.financial_synonyms.items():
            if term in query:
                expanded_terms.extend(synonyms)
        
        if expanded_terms:
            return f"{query} {' '.join(expanded_terms)}"
        
        return query

class HybridRetriever:
    """混合检索器"""
    
    def __init__(self, storage_dir: str = "./storage"):
        self.storage_dir = storage_dir
        self.scorer = HybridRetrievalScorer()
        self.query_expander = QueryExpansion()
        
        # 双通道索引
        self.text_index = None
        self.table_index = None
        
        # ChromaDB客户端
        self.chroma_client = None
        self.text_collection = None
        self.table_collection = None
        
        # 初始化ChromaDB
        self._setup_chroma()
    
    def _setup_chroma(self):
        """设置ChromaDB"""
        try:
            chroma_persist_dir = f"{self.storage_dir}/chroma_hybrid"
            
            self.chroma_client = chromadb.PersistentClient(path=chroma_persist_dir)
            
            # 创建两个集合
            try:
                self.text_collection = self.chroma_client.get_collection("text_index")
            except:
                self.text_collection = self.chroma_client.create_collection("text_index")
            
            try:
                self.table_collection = self.chroma_client.get_collection("table_index")
            except:
                self.table_collection = self.chroma_client.create_collection("table_index")
            
            logger.info("✅ Hybrid Retriever ChromaDB初始化成功")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB初始化失败: {str(e)}")
    
    def build_hybrid_index(self, processed_documents: Dict, extracted_tables: Dict) -> bool:
        """构建混合检索索引"""
        try:
            logger.info("🚀 开始构建Hybrid Retriever索引")
            
            # 1. 构建文本索引
            text_documents = []
            for doc_name, doc_data in processed_documents.items():
                for doc in doc_data['documents']:
                    doc.metadata.update({
                        'doc_type': 'text',
                        'channel': 'text_index',
                        'source_file': doc_name
                    })
                    text_documents.append(doc)
            
            if text_documents:
                text_vector_store = ChromaVectorStore(chroma_collection=self.text_collection)
                text_storage_context = StorageContext.from_defaults(vector_store=text_vector_store)
                self.text_index = VectorStoreIndex.from_documents(
                    text_documents,
                    storage_context=text_storage_context
                )
                logger.info(f"✅ 文本索引构建完成: {len(text_documents)}个文档")
            
            # 2. 构建表格索引
            table_documents = []
            for doc_name, tables in extracted_tables.items():
                for table in tables:
                    table_text = self._table_to_text(table)
                    table_doc = Document(
                        text=table_text,
                        metadata={
                            'doc_type': 'table',
                            'channel': 'table_index',
                            'indicator': table.get('summary', ''),
                            'year': self._extract_year_from_table(table),
                            'source': f"{doc_name}_page_{table['page_number']}",
                            'table_id': table['table_id'],
                            'is_financial': table.get('is_financial', False)
                        }
                    )
                    table_documents.append(table_doc)
            
            if table_documents:
                table_vector_store = ChromaVectorStore(chroma_collection=self.table_collection)
                table_storage_context = StorageContext.from_defaults(vector_store=table_vector_store)
                self.table_index = VectorStoreIndex.from_documents(
                    table_documents,
                    storage_context=table_storage_context
                )
                logger.info(f"✅ 表格索引构建完成: {len(table_documents)}个文档")
            
            logger.info("✅ Hybrid Retriever索引构建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 构建混合索引失败: {str(e)}")
            return False
    
    def load_existing_index(self) -> bool:
        """从现有的ChromaDB集合加载Hybrid Retriever索引"""
        try:
            logger.info("🔄 开始加载Hybrid Retriever索引...")
            
            # 检查集合是否有数据
            text_count = self.text_collection.count() if self.text_collection else 0
            table_count = self.table_collection.count() if self.table_collection else 0
            
            logger.info(f"📊 文本集合: {text_count} 个向量")
            logger.info(f"📊 表格集合: {table_count} 个向量")
            
            if text_count == 0 and table_count == 0:
                logger.warning("⚠️ Hybrid Retriever集合为空，无法加载索引")
                return False
            
            # 加载文本索引
            if text_count > 0:
                try:
                    from llama_index.vector_stores.chroma import ChromaVectorStore
                    from llama_index.core import StorageContext
                    
                    text_vector_store = ChromaVectorStore(chroma_collection=self.text_collection)
                    text_storage_context = StorageContext.from_defaults(vector_store=text_vector_store)
                    self.text_index = VectorStoreIndex.from_vector_store(text_vector_store)
                    logger.info(f"✅ 文本索引加载成功: {text_count} 个向量")
                except Exception as e:
                    logger.warning(f"⚠️ 文本索引加载失败: {str(e)}")
                    self.text_index = None
            
            # 加载表格索引
            if table_count > 0:
                try:
                    from llama_index.vector_stores.chroma import ChromaVectorStore
                    from llama_index.core import StorageContext
                    
                    table_vector_store = ChromaVectorStore(chroma_collection=self.table_collection)
                    table_storage_context = StorageContext.from_defaults(vector_store=table_vector_store)
                    self.table_index = VectorStoreIndex.from_vector_store(table_vector_store)
                    logger.info(f"✅ 表格索引加载成功: {table_count} 个向量")
                except Exception as e:
                    logger.warning(f"⚠️ 表格索引加载失败: {str(e)}")
                    self.table_index = None
            
            # 至少有一个索引加载成功就算成功
            if self.text_index or self.table_index:
                logger.info("✅ Hybrid Retriever索引加载完成")
                return True
            else:
                logger.warning("⚠️ Hybrid Retriever索引加载失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 加载Hybrid Retriever索引失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False
    
    def retrieve(self, query: str, top_k: int = 10, 
                strategy: str = 'auto') -> List[Dict[str, Any]]:
        """混合检索"""
        try:
            # 1. 查询扩展
            expanded_query = self.query_expander.expand_query(query)
            
            # 2. 确定检索策略
            if strategy == 'auto':
                strategy = self._determine_retrieval_strategy(query)
            
            # 3. 执行检索
            if strategy == 'text_first':
                results = self._retrieve_text_first(expanded_query, top_k)
            elif strategy == 'table_first':
                results = self._retrieve_table_first(expanded_query, top_k)
            else:  # hybrid
                results = self._retrieve_hybrid(expanded_query, top_k)
            
            # 4. 综合评分和排序
            scored_results = []
            for result in results:
                score_result = self.scorer.calculate_comprehensive_score(
                    query, result['document'], result['semantic_score']
                )
                
                scored_results.append({
                    'document': result['document'],
                    'semantic_score': result['semantic_score'],
                    'comprehensive_score': score_result['comprehensive_score'],
                    'sim_score': score_result['sim_score'],
                    'metric_score': score_result['metric_score'],
                    'year_score': score_result['year_score'],
                    'strategy': strategy
                })
            
            # 5. 按综合评分排序
            scored_results.sort(key=lambda x: x['comprehensive_score'], reverse=True)
            
            # 6. 返回Top-K结果
            return scored_results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ 混合检索失败: {str(e)}")
            return []
    
    def _determine_retrieval_strategy(self, query: str) -> str:
        """确定检索策略"""
        # 明确的财务指标关键词（应该优先检索表格）
        financial_indicator_keywords = [
            '营业收入', '营收', '收入', '净利润', '利润', '资产', '负债', '现金流',
            'ROE', 'ROA', '毛利率', '净利率', '总资产', '净资产', '股东权益',
            '营业成本', '销售费用', '管理费用', '财务费用'
        ]
        
        # 数值类关键词
        numeric_keywords = ['增长率', '变化幅度', '同比', '环比', '数据', '数值', '金额', '比例', '趋势']
        
        # 语义分析类关键词  
        semantic_keywords = ['表现如何', '趋势说明', '分析', '评价', '情况', '概述']
        
        # 如果查询包含明确的财务指标，优先使用表格检索
        if any(keyword in query for keyword in financial_indicator_keywords):
            logger.info(f"📊 检测到财务指标关键词，使用表格优先检索策略")
            return 'table_first'  # 表格优先
        elif any(keyword in query for keyword in numeric_keywords):
            return 'table_first'  # 表格优先
        elif any(keyword in query for keyword in semantic_keywords):
            return 'text_first'   # 文本优先
        else:
            return 'hybrid'       # 混合检索
    
    def _retrieve_text_first(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """文本优先检索"""
        results = []
        
        if self.text_index:
            retriever = VectorIndexRetriever(index=self.text_index, similarity_top_k=top_k)
            nodes = retriever.retrieve(query)
            
            for node in nodes:
                results.append({
                    'document': node,
                    'semantic_score': getattr(node, 'score', 0.0)
                })
        
        return results
    
    def _retrieve_table_first(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """表格优先检索"""
        results = []
        
        if self.table_index:
            retriever = VectorIndexRetriever(index=self.table_index, similarity_top_k=top_k)
            nodes = retriever.retrieve(query)
            
            for node in nodes:
                results.append({
                    'document': node,
                    'semantic_score': getattr(node, 'score', 0.0)
                })
        
        return results
    
    def _retrieve_hybrid(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """混合检索"""
        results = []
        
        # 文本检索
        if self.text_index:
            text_retriever = VectorIndexRetriever(index=self.text_index, similarity_top_k=top_k//2)
            text_nodes = text_retriever.retrieve(query)
            
            for node in text_nodes:
                results.append({
                    'document': node,
                    'semantic_score': getattr(node, 'score', 0.0)
                })
        
        # 表格检索
        if self.table_index:
            table_retriever = VectorIndexRetriever(index=self.table_index, similarity_top_k=top_k//2)
            table_nodes = table_retriever.retrieve(query)
            
            for node in table_nodes:
                results.append({
                    'document': node,
                    'semantic_score': getattr(node, 'score', 0.0)
                })
        
        return results
    
    def _table_to_text(self, table: Dict[str, Any]) -> str:
        """将表格转换为文本表示"""
        try:
            text_parts = []
            
            # 添加表格基本信息
            text_parts.append(f"📊 表格数据 - {table['table_id']}")
            text_parts.append(f"📄 来源页码: 第{table['page_number']}页")
            
            if table.get('is_financial'):
                text_parts.append("💰 类型: 财务数据表格")
            
            if table.get('summary'):
                text_parts.append(f"📝 表格摘要: {table['summary']}")
            
            # 添加表格数据
            if 'table_data' in table:
                table_data = table['table_data']
                columns = table_data['columns']
                data_rows = table_data['data']
                
                # 生成Markdown表格
                text_parts.append("\n**表格内容：**\n")
                
                # 表头
                header = "| " + " | ".join([str(col) for col in columns]) + " |"
                text_parts.append(header)
                
                # 分隔线
                separator = "|" + "|".join(["---" for _ in columns]) + "|"
                text_parts.append(separator)
                
                # 数据行
                max_rows = min(len(data_rows), 30)
                for row in data_rows[:max_rows]:
                    row_str = "| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |"
                    text_parts.append(row_str)
                
                if len(data_rows) > max_rows:
                    text_parts.append(f"\n... (表格共有 {len(data_rows)} 行数据)")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"表格转文本失败: {str(e)}")
            return f"表格 {table.get('table_id', 'unknown')}"
    
    def _extract_year_from_table(self, table: Dict[str, Any]) -> Optional[int]:
        """从表格中提取年份"""
        try:
            # 从表格摘要中提取年份
            summary = table.get('summary', '')
            year_match = re.search(r'(\d{4})', summary)
            if year_match:
                return int(year_match.group(1))
            
            # 从表格数据中提取年份
            if 'table_data' in table:
                table_data = table['table_data']
                for row in table_data.get('data', []):
                    for cell in row:
                        if isinstance(cell, str):
                            year_match = re.search(r'(\d{4})', cell)
                            if year_match:
                                year = int(year_match.group(1))
                                if 2000 <= year <= 2030:  # 合理的年份范围
                                    return year
            
            return None
            
        except Exception as e:
            logger.error(f"提取年份失败: {str(e)}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        stats = {
            'text_index_ready': self.text_index is not None,
            'table_index_ready': self.table_index is not None,
            'text_collection_count': self.text_collection.count() if self.text_collection else 0,
            'table_collection_count': self.table_collection.count() if self.table_collection else 0,
            'weights': self.scorer.weights,
            'financial_metrics_count': len(self.scorer.financial_metrics)
        }
        
        return stats
