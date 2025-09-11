import os
import json
from typing import List, Dict, Any, Optional
import streamlit as st
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response.pprint_utils import pprint_response
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import logging

# Configure logging
logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.index = None
        self.query_engine = None
        
        # Only setup if API key is available
        if self.openai_api_key:
            try:
                self._setup_llama_index()
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
            
            # Create query engine
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=5,
                response_mode="tree_summarize"
            )
            
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
