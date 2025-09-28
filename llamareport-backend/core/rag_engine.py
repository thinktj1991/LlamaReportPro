"""
简化的RAG引擎
专注于文档索引构建和智能问答
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb

logger = logging.getLogger(__name__)

class RAGEngine:
    """简化的RAG引擎"""
    
    def __init__(self, storage_dir: str = "./storage", collection_name: str = "documents"):
        self.storage_dir = Path(storage_dir)
        self.collection_name = collection_name
        self.index = None
        self.query_engine = None
        self.chroma_client = None
        self.chroma_collection = None
        
        # 确保存储目录存在
        self.storage_dir.mkdir(exist_ok=True)
        
        # 设置LlamaIndex
        self.llama_index_ready = self._setup_llama_index()

        # 初始化ChromaDB
        if self.llama_index_ready:
            self._setup_chroma()
        else:
            logger.warning("⚠️ 跳过ChromaDB初始化 - LlamaIndex未就绪")
    
    def _setup_llama_index(self):
        """设置LlamaIndex配置"""
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.warning("⚠️ OPENAI_API_KEY未设置，RAG功能将受限")
                return False

            # 设置LLM
            Settings.llm = OpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=openai_api_key,
                temperature=0.1
            )

            # 设置嵌入模型
            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=openai_api_key
            )

            logger.info("✅ LlamaIndex配置成功")
            return True

        except Exception as e:
            logger.error(f"❌ LlamaIndex配置失败: {str(e)}")
            return False
    
    def _setup_chroma(self):
        """设置ChromaDB"""
        try:
            # 使用持久化客户端
            chroma_persist_dir = self.storage_dir / "chroma"
            chroma_persist_dir.mkdir(exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(path=str(chroma_persist_dir))
            
            # 尝试获取现有集合，如果不存在则创建
            try:
                self.chroma_collection = self.chroma_client.get_collection(self.collection_name)
                logger.info(f"✅ 加载现有ChromaDB集合: {self.collection_name}")
            except:
                self.chroma_collection = self.chroma_client.create_collection(self.collection_name)
                logger.info(f"✅ 创建新的ChromaDB集合: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB设置失败: {str(e)}")
            raise

    def load_existing_index(self) -> bool:
        """从现有的ChromaDB集合加载索引"""
        try:
            if not self.llama_index_ready:
                logger.error("❌ LlamaIndex未就绪，无法加载索引")
                return False

            if not self.chroma_collection:
                logger.error("❌ ChromaDB集合未初始化")
                return False

            # 检查集合是否有数据
            collection_count = self.chroma_collection.count()
            if collection_count == 0:
                logger.warning("⚠️ ChromaDB集合为空，无法加载索引")
                return False

            # 创建向量存储
            from llama_index.vector_stores.chroma import ChromaVectorStore
            from llama_index.core import StorageContext

            vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)

            # 从向量存储加载索引
            self.index = VectorStoreIndex.from_vector_store(vector_store)

            # 创建查询引擎
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=5,
                response_mode="tree_summarize"
            )

            logger.info(f"✅ 成功从ChromaDB加载索引，包含 {collection_count} 个向量")
            return True

        except Exception as e:
            logger.error(f"❌ 加载索引失败: {str(e)}")
            return False
    
    def build_index(self, processed_documents: Dict[str, Any], extracted_tables: Dict[str, List[Dict]] = None) -> bool:
        """
        构建向量索引

        Args:
            processed_documents: 处理过的文档
            extracted_tables: 提取的表格（可选）

        Returns:
            是否成功构建索引
        """
        if not self.llama_index_ready:
            logger.error("❌ LlamaIndex未就绪，无法构建索引")
            return False

        try:
            all_documents = []
            
            # 处理文本文档
            for doc_name, doc_data in processed_documents.items():
                if 'documents' in doc_data:
                    for doc in doc_data['documents']:
                        # 添加元数据
                        doc.metadata.update({
                            'source_file': doc_name,
                            'document_type': 'text_content'
                        })
                        all_documents.append(doc)
            
            # 处理表格数据
            if extracted_tables:
                for doc_name, tables in extracted_tables.items():
                    for table in tables:
                        # 将表格转换为文本
                        table_text = self._table_to_text(table)
                        
                        table_doc = Document(
                            text=table_text,
                            metadata={
                                'source_file': doc_name,
                                'document_type': 'table_data',
                                'table_id': table['table_id'],
                                'page_number': table['page_number'],
                                'is_financial': table.get('is_financial', False),
                                'importance_score': table.get('importance_score', 0.0)
                            }
                        )
                        all_documents.append(table_doc)
            
            if not all_documents:
                logger.warning("没有文档可以索引")
                return False
            
            # 创建向量存储
            vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
            
            # 创建存储上下文
            storage_context = StorageContext.from_defaults(
                docstore=SimpleDocumentStore(),
                index_store=SimpleIndexStore(),
                vector_store=vector_store
            )
            
            # 构建索引
            self.index = VectorStoreIndex.from_documents(
                all_documents,
                storage_context=storage_context
            )
            
            # 创建查询引擎
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=5,
                response_mode="tree_summarize"
            )
            
            logger.info(f"✅ 成功构建索引，包含 {len(all_documents)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"❌ 构建索引失败: {str(e)}")
            return False
    
    def _table_to_text(self, table: Dict[str, Any]) -> str:
        """将表格转换为文本表示"""
        try:
            text_parts = []
            
            # 添加表格基本信息
            text_parts.append(f"表格ID: {table['table_id']}")
            text_parts.append(f"页码: {table['page_number']}")
            
            if table.get('summary'):
                text_parts.append(f"摘要: {table['summary']}")
            
            # 添加表格数据
            if 'table_data' in table:
                table_data = table['table_data']
                # 转换为字符串表示
                text_parts.append("表格内容:")
                text_parts.append(f"列名: {', '.join(table_data['columns'])}")

                # 添加前几行数据
                for i, row in enumerate(table_data['data'][:10]):  # 只显示前10行
                    row_str = " | ".join([str(cell) for cell in row])
                    text_parts.append(f"行{i+1}: {row_str}")

                if len(table_data['data']) > 10:
                    text_parts.append(f"... (共{len(table_data['data'])}行)")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"表格转文本失败: {str(e)}")
            return f"表格 {table.get('table_id', 'unknown')}"
    
    def query(self, question: str, context_filter: Optional[Dict] = None) -> Dict[str, Any]:
        """
        查询RAG系统

        Args:
            question: 查询问题
            context_filter: 上下文过滤器（可选）

        Returns:
            查询结果
        """
        try:
            if not self.llama_index_ready:
                return {
                    'answer': "RAG系统未就绪，请检查OPENAI_API_KEY配置。",
                    'sources': [],
                    'error': True
                }

            if not self.query_engine:
                # 尝试从现有的ChromaDB集合加载索引
                if not self.load_existing_index():
                    return {
                        'answer': "RAG系统未初始化，请先处理文档。",
                        'sources': [],
                        'error': True
                    }
            
            # 增强查询
            enhanced_query = self._enhance_query(question, context_filter)
            
            # 执行查询
            response = self.query_engine.query(enhanced_query)
            
            # 提取来源信息
            sources = self._extract_sources(response)
            
            result = {
                'answer': str(response),
                'sources': sources,
                'error': False,
                'original_question': question,
                'enhanced_query': enhanced_query
            }
            
            logger.info(f"✅ 查询成功: {question[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌ 查询失败: {str(e)}")
            return {
                'answer': f"查询失败: {str(e)}",
                'sources': [],
                'error': True
            }
    
    def _enhance_query(self, question: str, context_filter: Optional[Dict] = None) -> str:
        """增强查询"""
        enhanced_parts = [question]
        
        if context_filter:
            if 'company' in context_filter:
                enhanced_parts.append(f"关注 {context_filter['company']} 的信息")
            
            if 'year' in context_filter:
                enhanced_parts.append(f"针对 {context_filter['year']} 年")
            
            if 'document_type' in context_filter:
                enhanced_parts.append(f"来自 {context_filter['document_type']} 文档")
        
        enhanced_parts.append("请提供具体数据并尽可能引用来源。")
        
        return " ".join(enhanced_parts)
    
    def _extract_sources(self, response) -> List[Dict[str, Any]]:
        """提取来源信息"""
        sources = []
        
        try:
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    source_info = {
                        'text': node.text[:200] + "..." if len(node.text) > 200 else node.text,
                        'metadata': node.metadata,
                        'score': getattr(node, 'score', 0.0)
                    }
                    sources.append(source_info)
        except Exception as e:
            logger.warning(f"提取来源信息失败: {str(e)}")
        
        return sources
    
    def get_similar_content(self, query: str, top_k: int = 5) -> List[Dict]:
        """获取相似内容"""
        try:
            if not self.index:
                return []
            
            retriever = self.index.as_retriever(similarity_top_k=top_k)
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
            logger.error(f"获取相似内容失败: {str(e)}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        try:
            if not self.index:
                return {'status': 'not_initialized'}
            
            # 获取文档数量
            doc_count = len(self.index.docstore.docs)
            
            # 获取集合信息
            collection_count = self.chroma_collection.count() if self.chroma_collection else 0
            
            return {
                'status': 'ready',
                'document_count': doc_count,
                'vector_count': collection_count,
                'storage_dir': str(self.storage_dir),
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            logger.error(f"获取索引统计失败: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def clear_index(self) -> bool:
        """清空索引"""
        try:
            # 删除ChromaDB集合
            if self.chroma_collection:
                self.chroma_client.delete_collection(self.collection_name)
                self.chroma_collection = self.chroma_client.create_collection(self.collection_name)
            
            # 重置索引
            self.index = None
            self.query_engine = None
            
            logger.info("✅ 索引已清空")
            return True
            
        except Exception as e:
            logger.error(f"❌ 清空索引失败: {str(e)}")
            return False
