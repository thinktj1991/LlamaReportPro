from .safe_config import should_disable_entity_extractor
"""
LlamaReportPro 第四阶段增强功能
实现多模态支持、高级存储系统、元数据提取、知识图谱等高级功能
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field

# LlamaIndex核心导入
from llama_index.core import VectorStoreIndex, Settings, StorageContext, SimpleDirectoryReader
from llama_index.core.indices import MultiModalVectorStoreIndex
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.storage.chat_store import SimpleChatStore

logger = logging.getLogger(__name__)

# ==================== 第四阶段模型定义 ====================

class StorageBackend(str, Enum):
    """存储后端类型"""
    SIMPLE = "simple"
    CHROMA = "chroma"
    QDRANT = "qdrant"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"

class MultiModalType(str, Enum):
    """多模态类型"""
    TEXT_ONLY = "text_only"
    IMAGE_TEXT = "image_text"
    MIXED = "mixed"

class MetadataExtractorType(str, Enum):
    """元数据提取器类型"""
    SUMMARY = "summary"
    TITLE = "title"
    QUESTIONS = "questions"
    ENTITIES = "entities"

class MultiModalCapability(BaseModel):
    """多模态能力"""
    supports_images: bool = Field(description="支持图像", default=False)
    supports_text: bool = Field(description="支持文本", default=True)
    image_formats: List[str] = Field(description="支持的图像格式", default_factory=lambda: [])
    max_image_size: Optional[int] = Field(description="最大图像尺寸", default=None)

class StorageCapability(BaseModel):
    """存储能力"""
    backend_type: StorageBackend = Field(description="存储后端类型")
    supports_metadata_filtering: bool = Field(description="支持元数据过滤", default=False)
    supports_hybrid_search: bool = Field(description="支持混合搜索", default=False)
    supports_async: bool = Field(description="支持异步", default=False)
    supports_persistence: bool = Field(description="支持持久化", default=True)

# ==================== 多模态管理器 ====================

class MultiModalManager:
    """多模态管理器"""

    def __init__(self, storage_context: Optional[StorageContext] = None):
        self.storage_context = storage_context or StorageContext.from_defaults()
        self.multimodal_index = None
        self.capabilities = MultiModalCapability()

        # 检查多模态依赖
        self._check_multimodal_dependencies()

    def _check_multimodal_dependencies(self):
        """检查多模态依赖"""
        try:
            # 检查OpenAI多模态LLM
            from llama_index.multi_modal_llms.openai import OpenAIMultiModal
            self.capabilities.supports_images = True
            self.capabilities.image_formats = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
            self.capabilities.max_image_size = 20 * 1024 * 1024  # 20MB
            logger.info("✅ 多模态LLM支持已启用")
        except ImportError:
            logger.warning("⚠️ 多模态LLM依赖未安装，仅支持文本模式")

    def create_multimodal_index(self, documents: List[Any]) -> Optional[MultiModalVectorStoreIndex]:
        """创建多模态索引"""
        try:
            if not self.capabilities.supports_images:
                logger.warning("⚠️ 多模态功能未启用，创建标准向量索引")
                return VectorStoreIndex.from_documents(
                    documents, storage_context=self.storage_context
                )

            # 创建多模态索引
            self.multimodal_index = MultiModalVectorStoreIndex.from_documents(
                documents, storage_context=self.storage_context
            )

            logger.info(f"✅ 多模态索引创建成功，文档数量: {len(documents)}")
            return self.multimodal_index

        except Exception as e:
            logger.error(f"❌ 多模态索引创建失败: {e}")
            # 降级到标准向量索引
            return VectorStoreIndex.from_documents(
                documents, storage_context=self.storage_context
            )

    def load_multimodal_documents(self, data_path: str) -> List[Any]:
        """加载多模态文档"""
        try:
            # 使用SimpleDirectoryReader加载文档
            reader = SimpleDirectoryReader(
                input_dir=data_path,
                recursive=True,
                required_exts=[".txt", ".pdf", ".docx", ".jpg", ".jpeg", ".png", ".gif"]
            )
            documents = reader.load_data()

            # 分类文档类型
            text_docs = []
            image_docs = []

            for doc in documents:
                if hasattr(doc, 'metadata') and doc.metadata.get('file_type'):
                    file_type = doc.metadata['file_type'].lower()
                    if file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                        image_docs.append(doc)
                    else:
                        text_docs.append(doc)
                else:
                    text_docs.append(doc)

            logger.info(f"✅ 文档加载完成 - 文本: {len(text_docs)}, 图像: {len(image_docs)}")
            return documents

        except Exception as e:
            logger.error(f"❌ 多模态文档加载失败: {e}")
            return []

    def create_multimodal_query_engine(self, similarity_top_k: int = 3,
                                     image_similarity_top_k: int = 3):
        """创建多模态查询引擎"""
        try:
            if not self.multimodal_index:
                raise ValueError("多模态索引未创建")

            if self.capabilities.supports_images:
                # 尝试创建多模态查询引擎
                try:
                    from llama_index.multi_modal_llms.openai import OpenAIMultiModal

                    openai_mm_llm = OpenAIMultiModal(
                        model="gpt-4-vision-preview",
                        max_new_tokens=1000
                    )

                    query_engine = self.multimodal_index.as_query_engine(
                        multi_modal_llm=openai_mm_llm,
                        similarity_top_k=similarity_top_k,
                        image_similarity_top_k=image_similarity_top_k
                    )

                    logger.info("✅ 多模态查询引擎创建成功")
                    return query_engine

                except Exception as e:
                    logger.warning(f"⚠️ 多模态查询引擎创建失败，使用标准查询引擎: {e}")

            # 降级到标准查询引擎
            return self.multimodal_index.as_query_engine(similarity_top_k=similarity_top_k)

        except Exception as e:
            logger.error(f"❌ 查询引擎创建失败: {e}")
            return None

    def analyze_multimodal_content(self, query: str, include_images: bool = True) -> Dict[str, Any]:
        """分析多模态内容"""
        try:
            query_engine = self.create_multimodal_query_engine()
            if not query_engine:
                return {"error": "查询引擎创建失败"}

            start_time = time.time()
            response = query_engine.query(query)
            execution_time = time.time() - start_time

            # 分析响应中的多模态内容
            result = {
                "response": str(response),
                "execution_time": execution_time,
                "multimodal_type": MultiModalType.TEXT_ONLY.value,
                "sources": []
            }

            # 检查是否有图像来源
            if hasattr(response, 'source_nodes') and response.source_nodes:
                image_sources = 0
                text_sources = 0

                for node in response.source_nodes:
                    if hasattr(node, 'metadata') and node.metadata:
                        file_type = node.metadata.get('file_type', '').lower()
                        if file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                            image_sources += 1
                        else:
                            text_sources += 1
                    else:
                        text_sources += 1

                result["sources"] = {
                    "text_sources": text_sources,
                    "image_sources": image_sources,
                    "total_sources": len(response.source_nodes)
                }

                if image_sources > 0 and text_sources > 0:
                    result["multimodal_type"] = MultiModalType.MIXED.value
                elif image_sources > 0:
                    result["multimodal_type"] = MultiModalType.IMAGE_TEXT.value

            return result

        except Exception as e:
            logger.error(f"❌ 多模态内容分析失败: {e}")
            return {"error": str(e)}

# ==================== 高级存储管理器 ====================

class AdvancedStorageManager:
    """高级存储管理器"""

    def __init__(self):
        self.available_backends = {}
        self.current_backend = StorageBackend.SIMPLE
        self.storage_context = None

        # 检查可用的存储后端
        self._check_storage_backends()

    def _check_storage_backends(self):
        """检查可用的存储后端"""
        # 简单存储（总是可用）
        self.available_backends[StorageBackend.SIMPLE] = StorageCapability(
            backend_type=StorageBackend.SIMPLE,
            supports_metadata_filtering=True,
            supports_hybrid_search=False,
            supports_async=False,
            supports_persistence=True
        )

        # 检查Chroma
        try:
            import chromadb
            self.available_backends[StorageBackend.CHROMA] = StorageCapability(
                backend_type=StorageBackend.CHROMA,
                supports_metadata_filtering=True,
                supports_hybrid_search=False,
                supports_async=False,
                supports_persistence=True
            )
            logger.info("✅ Chroma存储后端可用")
        except ImportError:
            logger.info("ℹ️ Chroma存储后端不可用")

        # 检查Qdrant
        try:
            import qdrant_client
            self.available_backends[StorageBackend.QDRANT] = StorageCapability(
                backend_type=StorageBackend.QDRANT,
                supports_metadata_filtering=True,
                supports_hybrid_search=True,
                supports_async=True,
                supports_persistence=True
            )
            logger.info("✅ Qdrant存储后端可用")
        except ImportError:
            logger.info("ℹ️ Qdrant存储后端不可用")

        # 检查Pinecone
        try:
            import pinecone
            self.available_backends[StorageBackend.PINECONE] = StorageCapability(
                backend_type=StorageBackend.PINECONE,
                supports_metadata_filtering=True,
                supports_hybrid_search=True,
                supports_async=False,
                supports_persistence=True
            )
            logger.info("✅ Pinecone存储后端可用")
        except ImportError:
            logger.info("ℹ️ Pinecone存储后端不可用")

    def create_storage_context(self, backend: StorageBackend = StorageBackend.SIMPLE,
                             persist_dir: str = "./storage") -> StorageContext:
        """创建存储上下文"""
        try:
            if backend not in self.available_backends:
                logger.warning(f"⚠️ 存储后端 {backend.value} 不可用，使用简单存储")
                backend = StorageBackend.SIMPLE

            self.current_backend = backend

            if backend == StorageBackend.SIMPLE:
                # 简单存储
                vector_store = SimpleVectorStore()
                docstore = SimpleDocumentStore()
                index_store = SimpleIndexStore()

                self.storage_context = StorageContext.from_defaults(
                    vector_store=vector_store,
                    docstore=docstore,
                    index_store=index_store
                )

            elif backend == StorageBackend.CHROMA:
                # Chroma存储
                import chromadb
                from llama_index.vector_stores.chroma import ChromaVectorStore

                chroma_client = chromadb.PersistentClient(path=persist_dir)
                chroma_collection = chroma_client.get_or_create_collection("llamareportpro")
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

                self.storage_context = StorageContext.from_defaults(
                    vector_store=vector_store
                )

            elif backend == StorageBackend.QDRANT:
                # Qdrant存储
                import qdrant_client
                from llama_index.vector_stores.qdrant import QdrantVectorStore

                client = qdrant_client.QdrantClient(path=persist_dir)
                vector_store = QdrantVectorStore(
                    client=client,
                    collection_name="llamareportpro"
                )

                self.storage_context = StorageContext.from_defaults(
                    vector_store=vector_store
                )

            logger.info(f"✅ 存储上下文创建成功: {backend.value}")
            return self.storage_context

        except Exception as e:
            logger.error(f"❌ 存储上下文创建失败: {e}")
            # 降级到简单存储（避免递归）
            if backend != StorageBackend.SIMPLE:
                return self.create_storage_context(StorageBackend.SIMPLE, persist_dir)
            else:
                # 如果简单存储也失败，返回默认存储上下文
                return StorageContext.from_defaults()

    def get_storage_capabilities(self) -> Dict[str, StorageCapability]:
        """获取存储能力"""
        return {backend.value: capability for backend, capability in self.available_backends.items()}

    def persist_storage(self, persist_dir: str = "./storage"):
        """持久化存储"""
        try:
            if self.storage_context:
                self.storage_context.persist(persist_dir=persist_dir)
                logger.info(f"✅ 存储持久化成功: {persist_dir}")
                return True
        except Exception as e:
            logger.error(f"❌ 存储持久化失败: {e}")
        return False

# ==================== 元数据提取管理器 ====================

class MetadataExtractorManager:
    """元数据提取管理器"""

    def __init__(self, llm=None):
        self.llm = llm or Settings.llm
        self.extractors = {}
        self._initialize_extractors()

    def _initialize_extractors(self):
        """初始化提取器"""
        try:
            # 尝试导入核心元数据提取器
            from llama_index.core.extractors import (
                SummaryExtractor,
                QuestionsAnsweredExtractor,
                TitleExtractor
            )

            # 尝试导入实体提取器（需要单独的包）
            try:
                from llama_index.extractors.entity import EntityExtractor
                entity_extractor_available = True
            except ImportError:
                entity_extractor_available = False
                print("⚠️ EntityExtractor需要安装: pip install llama-index-extractors-entity")

            # 摘要提取器
            self.extractors[MetadataExtractorType.SUMMARY] = SummaryExtractor(
                summaries=["prev", "self", "next"],
                llm=self.llm
            )

            # 问题提取器
            self.extractors[MetadataExtractorType.QUESTIONS] = QuestionsAnsweredExtractor(
                questions=3,
                llm=self.llm
            )

            # 标题提取器
            self.extractors[MetadataExtractorType.TITLE] = TitleExtractor(
                llm=self.llm
            )

            # 实体提取器（如果可用）
            if entity_extractor_available and not should_disable_entity_extractor():
                try:
                    self.extractors[MetadataExtractorType.ENTITIES] = EntityExtractor(
                        prediction_threshold=0.5,
                        label_entities=False,
                        device="cpu",
                        llm=self.llm
                    )
                except Exception as e:
                    print(f"⚠️ 实体提取器初始化失败: {e}")
                    entity_extractor_available = False

            if not entity_extractor_available:
                print("⚠️ 实体提取器不可用，跳过初始化")

            logger.info("✅ 元数据提取器初始化成功")

        except ImportError as e:
            logger.warning(f"⚠️ 元数据提取器依赖未安装: {e}")
        except Exception as e:
            logger.error(f"❌ 元数据提取器初始化失败: {e}")

    def extract_metadata(self, documents: List[Any],
                        extractor_types: List[MetadataExtractorType] = None) -> List[Any]:
        """提取元数据"""
        try:
            if not extractor_types:
                extractor_types = list(self.extractors.keys())

            # 构建提取器列表
            active_extractors = []
            for extractor_type in extractor_types:
                if extractor_type in self.extractors:
                    active_extractors.append(self.extractors[extractor_type])

            if not active_extractors:
                logger.warning("⚠️ 没有可用的元数据提取器")
                return documents

            # 应用提取器
            from llama_index.core.ingestion import IngestionPipeline

            pipeline = IngestionPipeline(
                transformations=active_extractors
            )

            enhanced_documents = pipeline.run(documents=documents)

            logger.info(f"✅ 元数据提取完成，处理文档数: {len(enhanced_documents)}")
            return enhanced_documents

        except Exception as e:
            logger.error(f"❌ 元数据提取失败: {e}")
            return documents

    def get_available_extractors(self) -> List[str]:
        """获取可用的提取器"""
        return [extractor_type.value for extractor_type in self.extractors.keys()]

# ==================== 知识图谱管理器 ====================

class KnowledgeGraphManager:
    """知识图谱管理器"""

    def __init__(self, llm=None):
        self.llm = llm or Settings.llm
        self.kg_index = None
        self.graph_store = None
        self.supports_kg = False

        # 检查知识图谱依赖
        self._check_kg_dependencies()

    def _check_kg_dependencies(self):
        """检查知识图谱依赖"""
        try:
            from llama_index.core.indices import KnowledgeGraphIndex
            from llama_index.graph_stores.simple import SimpleGraphStore
            self.supports_kg = True
            logger.info("✅ 知识图谱支持已启用")
        except ImportError:
            logger.warning("⚠️ 知识图谱依赖未安装")

    def create_knowledge_graph(self, documents: List[Any],
                             storage_context: Optional[StorageContext] = None) -> Optional[Any]:
        """创建知识图谱"""
        try:
            if not self.supports_kg:
                logger.warning("⚠️ 知识图谱功能未启用")
                return None

            from llama_index.core.indices import KnowledgeGraphIndex
            from llama_index.graph_stores.simple import SimpleGraphStore

            # 创建图存储
            if not storage_context:
                self.graph_store = SimpleGraphStore()
                storage_context = StorageContext.from_defaults(graph_store=self.graph_store)

            # 创建知识图谱索引
            self.kg_index = KnowledgeGraphIndex.from_documents(
                documents,
                storage_context=storage_context,
                llm=self.llm,
                max_triplets_per_chunk=10,
                include_embeddings=True
            )

            logger.info(f"✅ 知识图谱创建成功，文档数量: {len(documents)}")
            return self.kg_index

        except Exception as e:
            logger.error(f"❌ 知识图谱创建失败: {e}")
            return None

    def query_knowledge_graph(self, query: str, mode: str = "hybrid") -> Dict[str, Any]:
        """查询知识图谱"""
        try:
            if not self.kg_index:
                return {"error": "知识图谱未创建"}

            start_time = time.time()

            # 创建查询引擎
            query_engine = self.kg_index.as_query_engine(
                include_text=True,
                response_mode="tree_summarize",
                embedding_mode=mode
            )

            response = query_engine.query(query)
            execution_time = time.time() - start_time

            # 提取图谱信息
            graph_info = {
                "response": str(response),
                "execution_time": execution_time,
                "query_mode": mode,
                "triplets": [],
                "entities": []
            }

            # 尝试获取图谱三元组
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    if hasattr(node, 'metadata') and 'triplets' in node.metadata:
                        graph_info["triplets"].extend(node.metadata['triplets'])

            return graph_info

        except Exception as e:
            logger.error(f"❌ 知识图谱查询失败: {e}")
            return {"error": str(e)}

    def get_graph_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        try:
            if not self.graph_store:
                return {"error": "图存储未初始化"}

            # 获取图谱统计
            stats = {
                "total_triplets": 0,
                "unique_entities": 0,
                "unique_relations": 0
            }

            # 简单图存储的统计
            if hasattr(self.graph_store, 'graph_dict'):
                graph_dict = self.graph_store.graph_dict
                stats["total_triplets"] = len(graph_dict)

                entities = set()
                relations = set()

                for triplet in graph_dict.values():
                    if isinstance(triplet, tuple) and len(triplet) >= 3:
                        entities.add(triplet[0])  # 主体
                        entities.add(triplet[2])  # 客体
                        relations.add(triplet[1])  # 关系

                stats["unique_entities"] = len(entities)
                stats["unique_relations"] = len(relations)

            return stats

        except Exception as e:
            logger.error(f"❌ 图谱统计获取失败: {e}")
            return {"error": str(e)}

# ==================== 高级提示工程管理器 ====================

class AdvancedPromptManager:
    """高级提示工程管理器"""

    def __init__(self):
        self.templates = {}
        self.supports_jinja = False

        # 检查Jinja2支持
        self._check_jinja_support()
        self._initialize_templates()

    def _check_jinja_support(self):
        """检查Jinja2支持"""
        try:
            import jinja2
            self.supports_jinja = True
            logger.info("✅ Jinja2模板支持已启用")
        except ImportError:
            logger.warning("⚠️ Jinja2未安装，使用基础模板")

    def _initialize_templates(self):
        """初始化模板"""
        # 财务分析模板
        self.templates["financial_analysis"] = {
            "template": """
基于以下财务数据，请进行专业的财务分析：

公司信息：
- 公司名称：{{ company_name }}
- 分析期间：{{ period }}

财务数据：
{{ financial_data }}

请从以下角度进行分析：
1. 盈利能力分析
2. 偿债能力分析
3. 营运能力分析
4. 发展能力分析

分析要求：
- 提供具体的财务指标计算
- 给出专业的解读和建议
- 识别潜在的风险点
""",
            "variables": ["company_name", "period", "financial_data"]
        }

        # 风险评估模板
        self.templates["risk_assessment"] = {
            "template": """
请对以下公司进行全面的风险评估：

公司背景：
{{ company_background }}

评估维度：
1. 财务风险：{{ financial_risks }}
2. 市场风险：{{ market_risks }}
3. 运营风险：{{ operational_risks }}
4. 合规风险：{{ compliance_risks }}

请提供：
- 风险等级评定（高/中/低）
- 具体风险描述
- 风险缓解建议
""",
            "variables": ["company_background", "financial_risks", "market_risks", "operational_risks", "compliance_risks"]
        }

    def render_template(self, template_name: str, **kwargs) -> str:
        """渲染模板"""
        try:
            if template_name not in self.templates:
                raise ValueError(f"模板 {template_name} 不存在")

            template_info = self.templates[template_name]
            template_str = template_info["template"]

            if self.supports_jinja:
                import jinja2
                template = jinja2.Template(template_str)
                return template.render(**kwargs)
            else:
                # 简单字符串替换
                for key, value in kwargs.items():
                    template_str = template_str.replace(f"{{{{ {key} }}}}", str(value))
                return template_str

        except Exception as e:
            logger.error(f"❌ 模板渲染失败: {e}")
            return template_str

    def add_template(self, name: str, template: str, variables: List[str]):
        """添加模板"""
        self.templates[name] = {
            "template": template,
            "variables": variables
        }
        logger.info(f"✅ 模板 {name} 添加成功")

    def get_available_templates(self) -> Dict[str, List[str]]:
        """获取可用模板"""
        return {name: info["variables"] for name, info in self.templates.items()}

# ==================== 第四阶段集成管理器 ====================

class Phase4Manager:
    """第四阶段集成管理器"""

    def __init__(self, index: VectorStoreIndex, llm=None):
        self.index = index
        self.llm = llm or Settings.llm

        # 初始化各个管理器
        self.multimodal_manager = MultiModalManager()
        self.storage_manager = AdvancedStorageManager()
        self.metadata_manager = MetadataExtractorManager(llm)
        self.kg_manager = KnowledgeGraphManager(llm)
        self.prompt_manager = AdvancedPromptManager()

        # 增强索引
        self.enhanced_index = None
        self._initialize_enhanced_features()

    def _initialize_enhanced_features(self):
        """初始化增强功能"""
        try:
            # 创建高级存储上下文
            storage_context = self.storage_manager.create_storage_context()

            # 如果有多模态支持，创建多模态索引
            if self.multimodal_manager.capabilities.supports_images:
                # 这里可以重新构建多模态索引
                pass

            logger.info("✅ 第四阶段增强功能初始化完成")

        except Exception as e:
            logger.error(f"❌ 第四阶段增强功能初始化失败: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """获取第四阶段功能能力"""
        return {
            'multimodal': {
                'supports_images': self.multimodal_manager.capabilities.supports_images,
                'supports_text': self.multimodal_manager.capabilities.supports_text,
                'image_formats': self.multimodal_manager.capabilities.image_formats
            },
            'storage': {
                'available_backends': list(self.storage_manager.available_backends.keys()),
                'current_backend': self.storage_manager.current_backend.value
            },
            'metadata_extraction': {
                'available_extractors': self.metadata_manager.get_available_extractors()
            },
            'knowledge_graph': {
                'supports_kg': self.kg_manager.supports_kg
            },
            'prompt_engineering': {
                'supports_jinja': self.prompt_manager.supports_jinja,
                'available_templates': list(self.prompt_manager.templates.keys())
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'multimodal_index_created': self.multimodal_manager.multimodal_index is not None,
            'storage_backend': self.storage_manager.current_backend.value,
            'kg_index_created': self.kg_manager.kg_index is not None,
            'available_templates': len(self.prompt_manager.templates)
        }

        # 添加知识图谱统计
        if self.kg_manager.kg_index:
            kg_stats = self.kg_manager.get_graph_statistics()
            if 'error' not in kg_stats:
                stats.update(kg_stats)

        return stats

    # 多模态方法
    def create_multimodal_index(self, data_path: str) -> bool:
        """创建多模态索引"""
        try:
            documents = self.multimodal_manager.load_multimodal_documents(data_path)
            if not documents:
                return False

            # 提取元数据
            enhanced_documents = self.metadata_manager.extract_metadata(documents)

            # 创建多模态索引
            self.enhanced_index = self.multimodal_manager.create_multimodal_index(enhanced_documents)

            return self.enhanced_index is not None

        except Exception as e:
            logger.error(f"❌ 多模态索引创建失败: {e}")
            return False

    def analyze_multimodal_content(self, query: str, include_images: bool = True) -> Dict[str, Any]:
        """分析多模态内容"""
        return self.multimodal_manager.analyze_multimodal_content(query, include_images)

    # 知识图谱方法
    def create_knowledge_graph(self, documents: List[Any] = None) -> bool:
        """创建知识图谱"""
        try:
            if documents is None:
                # 使用现有索引的文档
                if hasattr(self.index, 'docstore') and self.index.docstore:
                    documents = list(self.index.docstore.docs.values())
                else:
                    logger.warning("⚠️ 没有可用的文档创建知识图谱")
                    return False

            # 提取元数据
            enhanced_documents = self.metadata_manager.extract_metadata(documents)

            # 创建知识图谱
            kg_index = self.kg_manager.create_knowledge_graph(enhanced_documents)

            return kg_index is not None

        except Exception as e:
            logger.error(f"❌ 知识图谱创建失败: {e}")
            return False

    def query_knowledge_graph(self, query: str, mode: str = "hybrid") -> Dict[str, Any]:
        """查询知识图谱"""
        return self.kg_manager.query_knowledge_graph(query, mode)

    # 高级提示工程方法
    def render_financial_analysis_prompt(self, company_name: str, period: str,
                                       financial_data: str) -> str:
        """渲染财务分析提示"""
        return self.prompt_manager.render_template(
            "financial_analysis",
            company_name=company_name,
            period=period,
            financial_data=financial_data
        )

    def render_risk_assessment_prompt(self, company_background: str,
                                    financial_risks: str = "",
                                    market_risks: str = "",
                                    operational_risks: str = "",
                                    compliance_risks: str = "") -> str:
        """渲染风险评估提示"""
        return self.prompt_manager.render_template(
            "risk_assessment",
            company_background=company_background,
            financial_risks=financial_risks,
            market_risks=market_risks,
            operational_risks=operational_risks,
            compliance_risks=compliance_risks
        )

    # 存储管理方法
    def switch_storage_backend(self, backend: StorageBackend, persist_dir: str = "./storage") -> bool:
        """切换存储后端"""
        try:
            new_context = self.storage_manager.create_storage_context(backend, persist_dir)
            if new_context:
                # 这里可以迁移现有数据到新的存储后端
                logger.info(f"✅ 存储后端切换成功: {backend.value}")
                return True
        except Exception as e:
            logger.error(f"❌ 存储后端切换失败: {e}")
        return False

    def get_storage_capabilities(self) -> Dict[str, Any]:
        """获取存储能力"""
        return self.storage_manager.get_storage_capabilities()

# ==================== 工厂函数 ====================

def create_phase4_manager(index: VectorStoreIndex, llm=None) -> Phase4Manager:
    """创建第四阶段管理器"""
    return Phase4Manager(index=index, llm=llm)

def get_phase4_features() -> Dict[str, bool]:
    """获取第四阶段功能可用性"""
    # 检查各种依赖
    features = {
        'multimodal': False,
        'advanced_storage': True,  # 基础存储总是可用
        'metadata_extraction': False,
        'knowledge_graph': False,
        'prompt_engineering': True  # 基础模板总是可用
    }

    # 检查多模态支持
    try:
        from llama_index.multi_modal_llms.openai import OpenAIMultiModal
        features['multimodal'] = True
    except ImportError:
        pass

    # 检查元数据提取
    try:
        from llama_index.core.extractors import SummaryExtractor
        features['metadata_extraction'] = True
    except ImportError:
        pass

    # 检查知识图谱
    try:
        from llama_index.core.indices import KnowledgeGraphIndex
        features['knowledge_graph'] = True
    except ImportError:
        pass

    return features
