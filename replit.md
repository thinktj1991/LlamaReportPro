# Annual Report Analysis System

## Overview

This is a comprehensive Streamlit-based web application designed for analyzing annual reports and financial documents using AI-powered tools. The system combines LlamaIndex for document processing and RAG (Retrieval-Augmented Generation) capabilities with advanced table extraction and data visualization features. Users can upload PDF documents, extract financial data, perform comparative analysis across companies, and interact with their documents through an intelligent Q&A system.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit with multi-page navigation
- **Page Structure**: Modular design with separate pages for upload, analysis, Q&A, and comparison
- **State Management**: Session-based state management for document persistence and user workflow
- **UI Components**: Wide layout with sidebar navigation and tabbed interfaces for organized content presentation

### Backend Architecture
- **Document Processing**: LlamaIndex integration for PDF reading and text extraction with pdfplumber for detailed content analysis
- **Data Processing**: Pandas-based table extraction and financial metrics calculation
- **AI Integration**: OpenAI GPT-5 model for language processing with text-embedding-3-large for vector embeddings
- **RAG System**: Vector store index for intelligent document querying and retrieval

### Data Storage Solutions
- **Session Storage**: In-memory storage using Streamlit session state for processed documents, extracted tables, and company data
- **Temporary Files**: File-based temporary storage for uploaded PDF processing
- **Vector Index**: LlamaIndex vector store for document embeddings and search capabilities

### Authentication and Authorization
- **API Key Management**: Environment variable-based OpenAI API key configuration
- **No User Authentication**: Single-user application model without user management system

### Core Processing Pipeline
- **PDF Processing**: Multi-stage extraction using both LlamaIndex and pdfplumber for comprehensive content analysis
- **Table Extraction**: Intelligent financial table identification and processing with keyword-based filtering
- **Company Analysis**: Automated company information extraction and financial metrics calculation
- **Visualization**: Plotly-based interactive charts and graphs for data presentation

## External Dependencies

### AI and ML Services
- **OpenAI API**: GPT-5 for language processing and text-embedding-3-large for document embeddings
- **LlamaIndex**: Document indexing, vector storage, and RAG system implementation

### Data Processing Libraries
- **Pandas**: Data manipulation and table processing
- **NumPy**: Numerical computations and data analysis
- **pdfplumber**: Advanced PDF content extraction and table detection

### Visualization and UI
- **Streamlit**: Web application framework and user interface
- **Plotly**: Interactive data visualization and charting
- **Plotly Express**: Simplified plotting interface for quick visualizations

### File Processing
- **PDFReader (LlamaIndex)**: Primary PDF document processing
- **Pathlib**: File system path management
- **Tempfile**: Temporary file handling for uploads

### Development and Monitoring
- **Logging**: Python standard logging for application monitoring and debugging
- **JSON**: Data serialization for configuration and data exchange

### Configuration Management
- **Environment Variables**: API key and configuration management through OS environment
- **Default Fallbacks**: Built-in fallback values for missing configurations