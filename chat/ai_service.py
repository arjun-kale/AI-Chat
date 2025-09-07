import os
import uuid
from typing import List, Optional
import chromadb
from chromadb.config import Settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory
from django.conf import settings
import PyPDF2
from PIL import Image
import io


class AIService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GEMINI_API_KEY
        )
        self.vectordb_path = settings.VECTORDB_PATH
        self.vectordb_path.mkdir(exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.vectordb_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    def process_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return ""

    def process_image(self, file_path: str) -> str:
        """Process image file - for now, return a placeholder"""
        try:
            # For now, we'll just return a basic description
            # In a real implementation, you might use OCR or vision models
            return f"Image file: {os.path.basename(file_path)}"
        except Exception as e:
            print(f"Error processing image: {e}")
            return ""

    def add_document_to_vectordb(self, content: str, document_id: str, conversation_id: str):
        """Add document content to vector database"""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(content)
            
            # Create collection for this conversation
            collection_name = f"conversation_{conversation_id}"
            
            # Get or create collection
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except:
                collection = self.chroma_client.create_collection(collection_name)
            
            # Add chunks to collection
            for i, chunk in enumerate(chunks):
                collection.add(
                    documents=[chunk],
                    metadatas=[{"document_id": document_id, "chunk_index": i}],
                    ids=[f"{document_id}_{i}"]
                )
                
        except Exception as e:
            print(f"Error adding document to vectordb: {e}")

    def get_conversation_context(self, conversation_id: str, query: str) -> str:
        """Retrieve relevant context from vector database"""
        try:
            collection_name = f"conversation_{conversation_id}"
            
            try:
                collection = self.chroma_client.get_collection(collection_name)
                results = collection.query(
                    query_texts=[query],
                    n_results=5
                )
                
                if results['documents'] and results['documents'][0]:
                    return "\n".join(results['documents'][0])
                return ""
            except:
                return ""
                
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""

    def generate_response(self, message: str, conversation_id: str, chat_history: List[dict] = None) -> str:
        """Generate AI response using Gemini"""
        try:
            # Get relevant context from documents
            context = self.get_conversation_context(conversation_id, message)
            
            # Prepare system message with context
            system_prompt = """You are a helpful AI assistant. You can help users with questions and provide information based on the context provided. 
            If you have access to uploaded documents, use that information to answer questions. 
            Be helpful, accurate, and concise in your responses."""
            
            if context:
                system_prompt += f"\n\nRelevant context from uploaded documents:\n{context}"
            
            # Prepare messages
            messages = [SystemMessage(content=system_prompt)]
            
            # Add chat history
            if chat_history:
                for msg in chat_history:
                    if msg['message_type'] == 'user':
                        messages.append(HumanMessage(content=msg['content']))
                    elif msg['message_type'] == 'assistant':
                        messages.append(AIMessage(content=msg['content']))
            
            # Add current user message
            messages.append(HumanMessage(content=message))
            
            # Generate response
            response = self.llm(messages)
            return response.content
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while processing your request. Please try again."

    def create_conversation(self) -> str:
        """Create a new conversation session"""
        return str(uuid.uuid4())
