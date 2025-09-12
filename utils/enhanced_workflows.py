"""
Enhanced LlamaIndex Workflows for Financial Document Processing
"""

import asyncio
from typing import Dict, Any, List, Optional, TypeVar, Generic
from llama_index.core.workflow import (
    Event, Context, Workflow, StartEvent, StopEvent, step
)
from llama_index.core import Document
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Event Types for Financial Document Workflow
@dataclass
class DocumentUploadedEvent(Event):
    """Event triggered when a document is uploaded"""
    file_path: str
    filename: str
    file_size: int

@dataclass 
class DocumentParsedEvent(Event):
    """Event triggered when document parsing is complete"""
    documents: List[Document]
    enhanced_content: Dict[str, Any]
    metadata: Dict[str, Any]
    filename: str

@dataclass
class TablesExtractedEvent(Event):
    """Event triggered when table extraction is complete"""
    tables: List[Dict[str, Any]]
    document_name: str
    extraction_stats: Dict[str, Any]

@dataclass
class FinancialAnalysisEvent(Event):
    """Event triggered when financial analysis is ready"""
    company_data: Dict[str, Any]
    financial_metrics: Dict[str, Any]
    document_name: str

@dataclass
class IndexBuiltEvent(Event):
    """Event triggered when RAG index is built"""
    index_id: str
    document_count: int
    success: bool

@dataclass
class WorkflowErrorEvent(Event):
    """Event triggered when an error occurs"""
    error_message: str
    error_type: str
    stage: str
    recoverable: bool

# Workflow State Management
class ProcessingStage(Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    TABLE_EXTRACTION = "table_extraction"
    FINANCIAL_ANALYSIS = "financial_analysis"
    INDEX_BUILDING = "index_building"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowState:
    """Centralized workflow state"""
    current_stage: ProcessingStage
    document_name: str
    progress_percentage: int
    processed_documents: Dict[str, Any]
    extracted_tables: Dict[str, Any]
    company_data: Dict[str, Any]
    errors: List[str]
    start_time: float
    last_update_time: float

# Main Financial Document Processing Workflow
class FinancialDocumentWorkflow(Workflow):
    """
    Enhanced workflow for processing financial documents with event-driven architecture
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enhanced_pdf_processor = None
        self.table_extractor = None
        self.rag_system = None
        self.financial_calculator = None
        
    async def initialize_processors(self, context: Context):
        """Initialize all required processors"""
        try:
            if not self.enhanced_pdf_processor:
                from utils.enhanced_pdf_processor import EnhancedPDFProcessor
                self.enhanced_pdf_processor = EnhancedPDFProcessor(use_premium_parse=True)
                
            if not self.table_extractor:
                from utils.table_extractor import TableExtractor
                self.table_extractor = TableExtractor()
                
            if not self.rag_system:
                from utils.rag_system import RAGSystem
                self.rag_system = RAGSystem()
                
            if not self.financial_calculator:
                from utils.financial_calculator import FinancialCalculator
                self.financial_calculator = FinancialCalculator()
                
            logger.info("All processors initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize processors: {str(e)}")
            return False

    @step
    async def handle_document_upload(
        self, context: Context, ev: StartEvent
    ) -> DocumentUploadedEvent:
        """Handle initial document upload and validation"""
        try:
            # Initialize workflow state
            import time
            workflow_state = WorkflowState(
                current_stage=ProcessingStage.UPLOADED,
                document_name=ev.file_name,
                progress_percentage=10,
                processed_documents={},
                extracted_tables={},
                company_data={},
                errors=[],
                start_time=time.time(),
                last_update_time=time.time()
            )
            
            context.data["workflow_state"] = workflow_state
            context.data["uploaded_file"] = ev.uploaded_file
            
            logger.info(f"Document upload initiated: {ev.file_name}")
            
            return DocumentUploadedEvent(
                file_path=ev.file_path,
                filename=ev.file_name,
                file_size=ev.file_size
            )
            
        except Exception as e:
            logger.error(f"Error in document upload stage: {str(e)}")
            return WorkflowErrorEvent(
                error_message=str(e),
                error_type="upload_error",
                stage="document_upload",
                recoverable=False
            )

    @step
    async def parse_document(
        self, context: Context, ev: DocumentUploadedEvent
    ) -> DocumentParsedEvent | WorkflowErrorEvent:
        """Parse document using enhanced PDF processor"""
        try:
            # Initialize processors
            initialized = await self.initialize_processors(context)
            if not initialized:
                raise Exception("Failed to initialize processors")
            
            # Update workflow state
            workflow_state = context.data["workflow_state"]
            workflow_state.current_stage = ProcessingStage.PARSING
            workflow_state.progress_percentage = 25
            
            uploaded_file = context.data["uploaded_file"]
            
            logger.info(f"Starting document parsing: {ev.filename}")
            
            # Process with enhanced PDF processor
            processed_result = await self.enhanced_pdf_processor.process_uploaded_file_async(uploaded_file)
            
            # Update context
            context.data["processed_result"] = processed_result
            workflow_state.processed_documents[ev.filename] = processed_result
            workflow_state.progress_percentage = 40
            
            logger.info(f"Document parsing completed: {ev.filename}")
            
            return DocumentParsedEvent(
                documents=processed_result['documents'],
                enhanced_content=processed_result['enhanced_content'],
                metadata=processed_result['metadata'],
                filename=ev.filename
            )
            
        except Exception as e:
            logger.error(f"Error in document parsing stage: {str(e)}")
            return WorkflowErrorEvent(
                error_message=str(e),
                error_type="parsing_error",
                stage="document_parsing",
                recoverable=True
            )

    @step
    async def extract_tables(
        self, context: Context, ev: DocumentParsedEvent
    ) -> TablesExtractedEvent | WorkflowErrorEvent:
        """Extract and analyze tables from parsed documents"""
        try:
            workflow_state = context.data["workflow_state"]
            workflow_state.current_stage = ProcessingStage.TABLE_EXTRACTION
            workflow_state.progress_percentage = 55
            
            logger.info(f"Starting table extraction: {ev.filename}")
            
            # Extract tables using enhanced table extractor
            processed_documents = {ev.filename: context.data["processed_result"]}
            extracted_tables = self.table_extractor.extract_and_process_tables(processed_documents)
            
            # Store in context
            context.data["extracted_tables"] = extracted_tables
            workflow_state.extracted_tables = extracted_tables
            workflow_state.progress_percentage = 70
            
            # Calculate extraction statistics
            extraction_stats = {
                'total_tables': sum(len(tables) for tables in extracted_tables.values()),
                'financial_tables': sum(
                    1 for tables in extracted_tables.values() 
                    for table in tables if table.get('is_financial', False)
                ),
                'high_confidence_tables': sum(
                    1 for tables in extracted_tables.values()
                    for table in tables if table.get('importance_score', 0) > 0.7
                )
            }
            
            logger.info(f"Table extraction completed: {ev.filename}, {extraction_stats['total_tables']} tables found")
            
            return TablesExtractedEvent(
                tables=extracted_tables.get(ev.filename, []),
                document_name=ev.filename,
                extraction_stats=extraction_stats
            )
            
        except Exception as e:
            logger.error(f"Error in table extraction stage: {str(e)}")
            return WorkflowErrorEvent(
                error_message=str(e),
                error_type="table_extraction_error",
                stage="table_extraction",
                recoverable=True
            )

    @step
    async def perform_financial_analysis(
        self, context: Context, ev: TablesExtractedEvent
    ) -> FinancialAnalysisEvent | WorkflowErrorEvent:
        """Perform financial analysis on extracted data"""
        try:
            workflow_state = context.data["workflow_state"]
            workflow_state.current_stage = ProcessingStage.FINANCIAL_ANALYSIS
            workflow_state.progress_percentage = 80
            
            logger.info(f"Starting financial analysis: {ev.document_name}")
            
            # Process financial data
            tables = ev.tables
            financial_metrics = {}
            
            # Extract financial metrics from tables
            for table in tables:
                if table.get('is_financial', False):
                    df = table['dataframe']
                    table_type = table.get('table_type', 'unknown')
                    
                    # Extract metrics based on table type
                    if table_type == 'income_statement':
                        metrics = self._extract_income_statement_metrics(df)
                        financial_metrics.update(metrics)
                    elif table_type == 'balance_sheet':
                        metrics = self._extract_balance_sheet_metrics(df)
                        financial_metrics.update(metrics)
                    elif table_type == 'cash_flow':
                        metrics = self._extract_cash_flow_metrics(df)
                        financial_metrics.update(metrics)
            
            # Create company data structure
            company_data = {
                'company_name': context.data["processed_result"]['metadata']['company_info'].get('company_name', 'Unknown'),
                'year': context.data["processed_result"]['metadata']['company_info'].get('year', 'Unknown'),
                'financial_metrics': financial_metrics,
                'tables': tables,
                'document_metadata': context.data["processed_result"]['metadata']
            }
            
            # Store in context
            context.data["company_data"] = company_data
            workflow_state.company_data[ev.document_name] = company_data
            workflow_state.progress_percentage = 90
            
            logger.info(f"Financial analysis completed: {ev.document_name}")
            
            return FinancialAnalysisEvent(
                company_data=company_data,
                financial_metrics=financial_metrics,
                document_name=ev.document_name
            )
            
        except Exception as e:
            logger.error(f"Error in financial analysis stage: {str(e)}")
            return WorkflowErrorEvent(
                error_message=str(e),
                error_type="financial_analysis_error",
                stage="financial_analysis",
                recoverable=True
            )

    @step
    async def build_rag_index(
        self, context: Context, ev: FinancialAnalysisEvent
    ) -> IndexBuiltEvent | WorkflowErrorEvent:
        """Build RAG index for intelligent querying"""
        try:
            workflow_state = context.data["workflow_state"]
            workflow_state.current_stage = ProcessingStage.INDEX_BUILDING
            workflow_state.progress_percentage = 95
            
            logger.info(f"Building RAG index: {ev.document_name}")
            
            # Build RAG index
            processed_documents = workflow_state.processed_documents
            extracted_tables = workflow_state.extracted_tables
            
            index_built = self.rag_system.build_index(processed_documents, extracted_tables)
            
            if index_built:
                workflow_state.current_stage = ProcessingStage.COMPLETED
                workflow_state.progress_percentage = 100
                
                logger.info(f"RAG index built successfully: {ev.document_name}")
                
                return IndexBuiltEvent(
                    index_id=f"index_{ev.document_name}",
                    document_count=len(processed_documents),
                    success=True
                )
            else:
                raise Exception("Failed to build RAG index")
            
        except Exception as e:
            logger.error(f"Error in RAG index building stage: {str(e)}")
            return WorkflowErrorEvent(
                error_message=str(e),
                error_type="index_building_error",
                stage="index_building",
                recoverable=True
            )

    @step
    async def handle_completion(
        self, context: Context, ev: IndexBuiltEvent
    ) -> StopEvent:
        """Handle workflow completion"""
        try:
            workflow_state = context.data["workflow_state"]
            
            import time
            total_time = time.time() - workflow_state.start_time
            
            completion_summary = {
                'status': 'completed',
                'total_processing_time': total_time,
                'processed_documents': len(workflow_state.processed_documents),
                'extracted_tables': sum(len(tables) for tables in workflow_state.extracted_tables.values()),
                'companies_analyzed': len(workflow_state.company_data),
                'final_stage': workflow_state.current_stage.value,
                'workflow_state': workflow_state
            }
            
            logger.info(f"Workflow completed successfully in {total_time:.2f} seconds")
            
            return StopEvent(result=completion_summary)
            
        except Exception as e:
            logger.error(f"Error in completion stage: {str(e)}")
            return StopEvent(result={'status': 'completed_with_errors', 'error': str(e)})

    @step
    async def handle_error(
        self, context: Context, ev: WorkflowErrorEvent
    ) -> StopEvent:
        """Handle workflow errors"""
        try:
            workflow_state = context.data.get("workflow_state")
            if workflow_state:
                workflow_state.current_stage = ProcessingStage.FAILED
                workflow_state.errors.append(f"{ev.stage}: {ev.error_message}")
            
            error_summary = {
                'status': 'failed',
                'error_type': ev.error_type,
                'error_message': ev.error_message,
                'failed_stage': ev.stage,
                'recoverable': ev.recoverable,
                'workflow_state': workflow_state
            }
            
            logger.error(f"Workflow failed at stage {ev.stage}: {ev.error_message}")
            
            return StopEvent(result=error_summary)
            
        except Exception as e:
            logger.error(f"Error in error handling: {str(e)}")
            return StopEvent(result={'status': 'critical_failure', 'error': str(e)})

    def _extract_income_statement_metrics(self, df) -> Dict[str, Any]:
        """Extract metrics from income statement"""
        metrics = {}
        try:
            # Look for common income statement items
            for col in df.columns:
                col_lower = str(col).lower()
                if '营业收入' in col_lower or 'revenue' in col_lower:
                    values = df[col].dropna()
                    if len(values) > 0:
                        metrics['revenue'] = self._extract_numeric_value(values.iloc[-1])
                elif '净利润' in col_lower or 'net income' in col_lower:
                    values = df[col].dropna()
                    if len(values) > 0:
                        metrics['net_income'] = self._extract_numeric_value(values.iloc[-1])
        except Exception as e:
            logger.error(f"Error extracting income statement metrics: {str(e)}")
        return metrics

    def _extract_balance_sheet_metrics(self, df) -> Dict[str, Any]:
        """Extract metrics from balance sheet"""
        metrics = {}
        try:
            for col in df.columns:
                col_lower = str(col).lower()
                if '总资产' in col_lower or 'total assets' in col_lower:
                    values = df[col].dropna()
                    if len(values) > 0:
                        metrics['total_assets'] = self._extract_numeric_value(values.iloc[-1])
                elif '股东权益' in col_lower or 'shareholders equity' in col_lower:
                    values = df[col].dropna()
                    if len(values) > 0:
                        metrics['shareholders_equity'] = self._extract_numeric_value(values.iloc[-1])
        except Exception as e:
            logger.error(f"Error extracting balance sheet metrics: {str(e)}")
        return metrics

    def _extract_cash_flow_metrics(self, df) -> Dict[str, Any]:
        """Extract metrics from cash flow statement"""
        metrics = {}
        try:
            for col in df.columns:
                col_lower = str(col).lower()
                if '经营活动现金流' in col_lower or 'operating cash flow' in col_lower:
                    values = df[col].dropna()
                    if len(values) > 0:
                        metrics['operating_cash_flow'] = self._extract_numeric_value(values.iloc[-1])
        except Exception as e:
            logger.error(f"Error extracting cash flow metrics: {str(e)}")
        return metrics

    def _extract_numeric_value(self, value) -> Optional[float]:
        """Extract numeric value from text"""
        try:
            import re
            # Remove currency symbols and common text
            cleaned = re.sub(r'[¥$€£,\s万亿千百十元人民币]', '', str(value))
            cleaned = re.sub(r'[^\d.-]', '', cleaned)
            if cleaned:
                return float(cleaned)
        except:
            pass
        return None


# Parallel Multi-Document Workflow
class ParallelDocumentWorkflow(Workflow):
    """
    Workflow for processing multiple documents in parallel
    """
    
    @step
    async def process_multiple_documents(
        self, context: Context, ev: StartEvent
    ) -> StopEvent:
        """Process multiple documents concurrently"""
        try:
            uploaded_files = ev.uploaded_files
            
            # Create individual workflows for each document
            workflows = []
            for uploaded_file in uploaded_files:
                workflow = FinancialDocumentWorkflow()
                workflows.append(workflow)
            
            # Process all documents in parallel
            tasks = []
            for i, workflow in enumerate(workflows):
                start_event = StartEvent(
                    uploaded_file=uploaded_files[i],
                    file_name=uploaded_files[i].name,
                    file_path=f"/tmp/{uploaded_files[i].name}",
                    file_size=len(uploaded_files[i].getvalue())
                )
                task = workflow.run(start_event)
                tasks.append(task)
            
            # Wait for all workflows to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            successful_results = []
            failed_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_results.append({
                        'filename': uploaded_files[i].name,
                        'error': str(result)
                    })
                else:
                    successful_results.append({
                        'filename': uploaded_files[i].name,
                        'result': result
                    })
            
            summary = {
                'total_documents': len(uploaded_files),
                'successful': len(successful_results),
                'failed': len(failed_results),
                'successful_results': successful_results,
                'failed_results': failed_results
            }
            
            logger.info(f"Parallel processing completed: {summary['successful']}/{summary['total_documents']} successful")
            
            return StopEvent(result=summary)
            
        except Exception as e:
            logger.error(f"Error in parallel document processing: {str(e)}")
            return StopEvent(result={'status': 'parallel_processing_failed', 'error': str(e)})


# Workflow Management Utilities
class WorkflowManager:
    """
    Manage and monitor financial document workflows
    """
    
    def __init__(self):
        self.active_workflows: Dict[str, Workflow] = {}
        self.workflow_states: Dict[str, WorkflowState] = {}
    
    async def start_document_processing(self, uploaded_file, workflow_id: str = None) -> str:
        """Start a new document processing workflow"""
        if workflow_id is None:
            import uuid
            workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
        
        workflow = FinancialDocumentWorkflow()
        self.active_workflows[workflow_id] = workflow
        
        start_event = StartEvent(
            uploaded_file=uploaded_file,
            file_name=uploaded_file.name,
            file_path=f"/tmp/{uploaded_file.name}",
            file_size=len(uploaded_file.getvalue())
        )
        
        # Start workflow asynchronously
        task = asyncio.create_task(workflow.run(start_event))
        
        logger.info(f"Started workflow {workflow_id} for {uploaded_file.name}")
        return workflow_id
    
    async def start_parallel_processing(self, uploaded_files: List, workflow_id: str = None) -> str:
        """Start parallel processing of multiple documents"""
        if workflow_id is None:
            import uuid
            workflow_id = f"parallel_workflow_{uuid.uuid4().hex[:8]}"
        
        workflow = ParallelDocumentWorkflow()
        self.active_workflows[workflow_id] = workflow
        
        start_event = StartEvent(uploaded_files=uploaded_files)
        
        # Start workflow asynchronously
        task = asyncio.create_task(workflow.run(start_event))
        
        logger.info(f"Started parallel workflow {workflow_id} for {len(uploaded_files)} documents")
        return workflow_id
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a workflow"""
        if workflow_id not in self.workflow_states:
            return None
            
        state = self.workflow_states[workflow_id]
        return {
            'workflow_id': workflow_id,
            'current_stage': state.current_stage.value,
            'progress_percentage': state.progress_percentage,
            'document_name': state.document_name,
            'errors': state.errors,
            'start_time': state.start_time,
            'last_update_time': state.last_update_time
        }
    
    def list_active_workflows(self) -> List[str]:
        """List all active workflow IDs"""
        return list(self.active_workflows.keys())
    
    async def wait_for_completion(self, workflow_id: str, timeout: float = 300.0) -> Dict[str, Any]:
        """Wait for a workflow to complete with timeout"""
        if workflow_id not in self.active_workflows:
            return {'error': f'Workflow {workflow_id} not found'}
        
        try:
            workflow = self.active_workflows[workflow_id]
            result = await asyncio.wait_for(workflow, timeout=timeout)
            
            # Clean up completed workflow
            del self.active_workflows[workflow_id]
            if workflow_id in self.workflow_states:
                del self.workflow_states[workflow_id]
            
            return result
            
        except asyncio.TimeoutError:
            return {'error': f'Workflow {workflow_id} timed out after {timeout} seconds'}
        except Exception as e:
            return {'error': f'Workflow {workflow_id} failed: {str(e)}'}