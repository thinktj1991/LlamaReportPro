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
from llama_index.llms.deepseek import DeepSeek
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb

# 导入Hybrid Retriever
from .hybrid_retriever import HybridRetriever

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
        
        # 初始化Hybrid Retriever
        self.hybrid_retriever = HybridRetriever(storage_dir=str(self.storage_dir))
        self.use_hybrid_retriever = True  # 默认启用混合检索
    
    def _setup_llama_index(self):
        """设置LlamaIndex配置"""
        try:
            # 获取 API Keys
            openai_api_key = os.getenv("OPENAI_API_KEY")
            deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

            if not openai_api_key:
                logger.warning("⚠️ OPENAI_API_KEY未设置，Embedding功能将受限")
                return False

            if not deepseek_api_key:
                logger.warning("⚠️ DEEPSEEK_API_KEY未设置，对话功能将受限")
                return False

            # 设置LLM - 使用 DeepSeek 专用集成
            deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

            Settings.llm = DeepSeek(
                model=deepseek_model,
                api_key=deepseek_api_key,
                temperature=0.1
            )

            logger.info(f"✅ DeepSeek LLM配置成功 - 模型: {deepseek_model}")

            # 设置嵌入模型 - 继续使用 OpenAI
            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=openai_api_key
            )

            logger.info("✅ OpenAI Embedding配置成功")
            logger.info("✅ LlamaIndex配置成功 (DeepSeek LLM + OpenAI Embedding)")
            return True

        except Exception as e:
            logger.error(f"❌ LlamaIndex配置失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
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

            # 创建查询引擎 - 优化配置
            from llama_index.core.prompts import PromptTemplate

            # 自定义系统提示词，强调使用表格数据
            qa_prompt_tmpl = (
                "你是一个专业的财务分析助手。下面是从文档中检索到的相关内容：\n\n"
                "{context_str}\n\n"
                "请仔细阅读上述内容，特别注意其中的表格数据。如果内容中包含Markdown格式的表格，"
                "请务必分析表格中的具体数值。\n\n"
                "用户问题：{query_str}\n\n"
                "回答要求：\n"
                "1. 必须基于检索到的具体数据回答，特别是表格中的数值\n"
                "2. 如果找到相关数据，请引用具体数字和来源\n"
                "3. 如果数据不足，明确说明缺少哪些信息\n"
                "4. 对于趋势分析，需要对比不同时期的数据\n\n"
                "请提供详细、准确的回答："
            )
            qa_prompt = PromptTemplate(qa_prompt_tmpl)

            self.query_engine = self.index.as_query_engine(
                similarity_top_k=10,  # 增加检索数量
                response_mode="compact",  # 使用compact模式保留更多细节
                text_qa_template=qa_prompt,
                verbose=True
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
            
            # 🔍 打印索引构建开始信息
            print("\n" + "=" * 80)
            print("🚀 开始构建RAG索引")
            print("=" * 80)
            
            # 处理文本文档
            print("📄 处理文本文档:")
            text_doc_count = 0
            for doc_name, doc_data in processed_documents.items():
                if 'documents' in doc_data:
                    print(f"  - {doc_name}: {len(doc_data['documents'])}个文档片段")
                    for doc in doc_data['documents']:
                        # 添加元数据
                        doc.metadata.update({
                            'source_file': doc_name,
                            'document_type': 'text_content'
                        })
                        all_documents.append(doc)
                        text_doc_count += 1
            
            print(f"  📊 文本文档总数: {text_doc_count}")
            
            # 处理表格数据
            table_doc_count = 0
            if extracted_tables:
                print("\n📊 处理表格数据:")
                for doc_name, tables in extracted_tables.items():
                    print(f"  - {doc_name}: {len(tables)}个表格")
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
                        table_doc_count += 1
                        
                        # 打印表格转换示例（前2个）
                        if table_doc_count <= 2:
                            print(f"    📋 表格{table_doc_count}: {table['table_id']}")
                            print(f"       - 财务表格: {'是' if table.get('is_financial', False) else '否'}")
                            print(f"       - 重要性: {table.get('importance_score', 0.0):.2f}")
                            print(f"       - 文本长度: {len(table_text)}字符")
                
                print(f"  📊 表格文档总数: {table_doc_count}")
            else:
                print("\n📊 表格数据: 无")
            
            if not all_documents:
                logger.warning("没有文档可以索引")
                return False
            
            print(f"\n📈 索引统计:")
            print(f"  - 总文档数: {len(all_documents)}")
            print(f"  - 文本文档: {text_doc_count}")
            print(f"  - 表格文档: {table_doc_count}")
            
            # 创建向量存储
            print(f"\n🔧 创建向量存储...")
            vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
            
            # 创建存储上下文
            print(f"🔧 创建存储上下文...")
            storage_context = StorageContext.from_defaults(
                docstore=SimpleDocumentStore(),
                index_store=SimpleIndexStore(),
                vector_store=vector_store
            )
            
            # 构建索引
            print(f"🔧 构建向量索引...")
            self.index = VectorStoreIndex.from_documents(
                all_documents,
                storage_context=storage_context
            )
            
            # 创建查询引擎 - 优化配置
            print(f"🔧 创建查询引擎...")
            from llama_index.core.prompts import PromptTemplate

            # 自定义系统提示词，强调使用表格数据
            qa_prompt_tmpl = (
                "你是一个专业的财务分析助手。下面是从文档中检索到的相关内容：\n\n"
                "{context_str}\n\n"
                "请仔细阅读上述内容，特别注意其中的表格数据。如果内容中包含Markdown格式的表格，"
                "请务必分析表格中的具体数值。\n\n"
                "用户问题：{query_str}\n\n"
                "回答要求：\n"
                "1. 必须基于检索到的具体数据回答，特别是表格中的数值\n"
                "2. 如果找到相关数据，请引用具体数字和来源\n"
                "3. 如果数据不足，明确说明缺少哪些信息\n"
                "4. 对于趋势分析，需要对比不同时期的数据\n\n"
                "请提供详细、准确的回答："
            )
            qa_prompt = PromptTemplate(qa_prompt_tmpl)

            self.query_engine = self.index.as_query_engine(
                similarity_top_k=10,  # 增加检索数量
                response_mode="compact",  # 使用compact模式保留更多细节
                text_qa_template=qa_prompt,
                verbose=True
            )
            
            # 🔍 打印索引构建完成信息
            print(f"\n✅ 索引构建完成!")
            print(f"  - 文档总数: {len(all_documents)}")
            print(f"  - 向量存储: ChromaDB")
            print(f"  - 集合名称: {self.collection_name}")
            print(f"  - 检索数量: 10")
            print(f"  - 响应模式: compact")
            print("=" * 80)
            
            # 构建Hybrid Retriever索引
            if self.use_hybrid_retriever:
                print("🚀 构建Hybrid Retriever索引...")
                hybrid_success = self.hybrid_retriever.build_hybrid_index(
                    processed_documents, extracted_tables
                )
                if hybrid_success:
                    print("✅ Hybrid Retriever索引构建成功")
                    hybrid_stats = self.hybrid_retriever.get_stats()
                    print(f"  - 文本索引: {hybrid_stats['text_collection_count']}个文档")
                    print(f"  - 表格索引: {hybrid_stats['table_collection_count']}个文档")
                    print(f"  - 财务指标: {hybrid_stats['financial_metrics_count']}个")
                else:
                    print("❌ Hybrid Retriever索引构建失败")
            
            logger.info(f"✅ 成功构建索引，包含 {len(all_documents)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"❌ 构建索引失败: {str(e)}")
            return False
    
    def _table_to_text(self, table: Dict[str, Any]) -> str:
        """将表格转换为文本表示 - 优化版本，生成更易于LLM理解的格式"""
        try:
            text_parts = []

            # 添加表格基本信息和上下文
            text_parts.append("=" * 80)
            text_parts.append(f"📊 表格数据 - {table['table_id']}")
            text_parts.append(f"📄 来源页码: 第{table['page_number']}页")

            # 标注表格类型
            if table.get('is_financial'):
                text_parts.append("💰 类型: 财务数据表格")

            if table.get('summary'):
                text_parts.append(f"📝 表格摘要: {table['summary']}")

            text_parts.append("=" * 80)

            # 添加表格数据 - 使用Markdown表格格式
            if 'table_data' in table:
                table_data = table['table_data']
                columns = table_data['columns']
                data_rows = table_data['data']

                # 生成Markdown表格
                text_parts.append("\n**表格内容（Markdown格式）：**\n")

                # 表头
                header = "| " + " | ".join([str(col) for col in columns]) + " |"
                text_parts.append(header)

                # 分隔线
                separator = "|" + "|".join(["---" for _ in columns]) + "|"
                text_parts.append(separator)

                # 数据行 - 显示所有行或最多30行
                max_rows = min(len(data_rows), 30)
                for i, row in enumerate(data_rows[:max_rows]):
                    row_str = "| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |"
                    text_parts.append(row_str)

                if len(data_rows) > max_rows:
                    text_parts.append(f"\n... (表格共有 {len(data_rows)} 行数据，以上显示前 {max_rows} 行)")
                else:
                    text_parts.append(f"\n(表格共有 {len(data_rows)} 行数据)")

                # 添加数据统计信息
                text_parts.append(f"\n**表格维度**: {len(data_rows)} 行 × {len(columns)} 列")

                # 对于财务表格，添加特别提示
                if table.get('is_financial'):
                    text_parts.append("\n⚠️ **重要提示**: 这是财务数据表格，包含具体的数值信息。请仔细分析表格中的数据来回答问题。")

            text_parts.append("=" * 80 + "\n")

            result_text = "\n".join(text_parts)
            
            # 🔍 打印表格转换信息（仅前2个表格）
            if hasattr(self, '_table_count'):
                self._table_count += 1
            else:
                self._table_count = 1
                
            if self._table_count <= 2:
                print(f"    🔄 表格转换: {table['table_id']}")
                print(f"       - 原始数据: {len(table.get('table_data', {}).get('data', []))}行")
                print(f"       - 转换后长度: {len(result_text)}字符")
                print(f"       - 包含Markdown: {'是' if '|' in result_text else '否'}")

            return result_text

        except Exception as e:
            logger.error(f"表格转文本失败: {str(e)}")
            return f"表格 {table.get('table_id', 'unknown')} (转换失败: {str(e)})"
    
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
            # 🔍 打印查询开始信息
            print("\n" + "=" * 80)
            print("🔍 开始RAG查询")
            print("=" * 80)
            print(f"📝 原始问题: {question}")
            
            if not self.llama_index_ready:
                print("❌ RAG系统未就绪")
                return {
                    'answer': "RAG系统未就绪，请检查OPENAI_API_KEY配置。",
                    'sources': [],
                    'error': True
                }

            if not self.query_engine:
                print("🔄 尝试加载现有索引...")
                # 尝试从现有的ChromaDB集合加载索引
                if not self.load_existing_index():
                    print("❌ 无法加载现有索引")
                    return {
                        'answer': "RAG系统未初始化，请先处理文档。",
                        'sources': [],
                        'error': True
                    }
                print("✅ 成功加载现有索引")
            
            # 增强查询
            print("🔧 增强查询...")
            enhanced_query = self._enhance_query(question, context_filter)
            print(f"📝 增强后查询: {enhanced_query[:200]}...")
            
            # 执行查询
            if self.use_hybrid_retriever and self.hybrid_retriever.text_index and self.hybrid_retriever.table_index:
                print("🔍 使用Hybrid Retriever执行混合检索...")
                # 使用Hybrid Retriever进行检索
                hybrid_results = self.hybrid_retriever.retrieve(question, top_k=10)
                
                if hybrid_results:
                    print(f"📊 Hybrid Retriever检索结果:")
                    print(f"  - 检索到文档: {len(hybrid_results)}个")
                    print(f"  - 平均综合评分: {sum(r['comprehensive_score'] for r in hybrid_results)/len(hybrid_results):.3f}")
                    print(f"  - 策略: {hybrid_results[0]['strategy']}")
                    
                    # 构建上下文
                    context = "\n\n".join([r['document'].text for r in hybrid_results])
                    
                    # 使用LLM生成回答
                    response = self.query_engine.query(enhanced_query)
                    
                    # 提取来源信息
                    sources = []
                    for result in hybrid_results:
                        sources.append({
                            'text': result['document'].text[:200] + "..." if len(result['document'].text) > 200 else result['document'].text,
                            'metadata': result['document'].metadata,
                            'score': result['comprehensive_score'],
                            'sim_score': result['sim_score'],
                            'metric_score': result['metric_score'],
                            'year_score': result['year_score']
                        })
                else:
                    print("⚠️ Hybrid Retriever未找到结果，回退到传统检索")
                    response = self.query_engine.query(enhanced_query)
                    sources = self._extract_sources(response)
            else:
                print("🔍 执行传统向量检索和LLM生成...")
                response = self.query_engine.query(enhanced_query)
                
                # 提取来源信息
                print("📚 提取来源信息...")
                sources = self._extract_sources(response)
            
            result = {
                'answer': str(response),
                'sources': sources,
                'error': False,
                'original_question': question,
                'enhanced_query': enhanced_query
            }
            
            # 🔍 打印查询结果信息
            print(f"\n✅ 查询完成!")
            print(f"  - 检索到来源: {len(sources)}个")
            print(f"  - 回答长度: {len(str(response))}字符")
            print(f"  - 来源类型: {[s.get('metadata', {}).get('document_type', 'unknown') for s in sources[:3]]}")
            print("=" * 80)
            
            logger.info(f"✅ 查询成功: {question[:50]}...")
            return result
            
        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")
            logger.error(f"❌ 查询失败: {str(e)}")
            return {
                'answer': f"查询失败: {str(e)}",
                'sources': [],
                'error': True
            }
    
    def _enhance_query(self, question: str, context_filter: Optional[Dict] = None) -> str:
        """增强查询 - 优化版本，确保LLM使用检索到的数据"""
        enhanced_parts = []

        # 添加明确的指令
        enhanced_parts.append("【重要指令】请仔细阅读下面检索到的文档内容，特别是表格数据，并基于这些具体数据来回答问题。")
        enhanced_parts.append("如果检索到的内容中包含表格，请务必分析表格中的数值数据。")
        enhanced_parts.append("")

        # 添加原始问题
        enhanced_parts.append(f"【用户问题】{question}")
        enhanced_parts.append("")

        # 添加上下文过滤
        if context_filter:
            enhanced_parts.append("【查询条件】")
            if 'company' in context_filter:
                enhanced_parts.append(f"- 公司: {context_filter['company']}")

            if 'year' in context_filter:
                enhanced_parts.append(f"- 年份: {context_filter['year']} 年")

            if 'document_type' in context_filter:
                enhanced_parts.append(f"- 文档类型: {context_filter['document_type']}")

            enhanced_parts.append("")

        # 添加回答要求
        enhanced_parts.append("【回答要求】")
        enhanced_parts.append("1. 必须使用检索到的具体数据（特别是表格中的数值）")
        enhanced_parts.append("2. 如果数据不足，明确说明缺少哪些信息")
        enhanced_parts.append("3. 提供数据来源（页码、表格ID等）")
        enhanced_parts.append("4. 对于趋势分析，需要对比不同时期的数据")

        return "\n".join(enhanced_parts)
    
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
