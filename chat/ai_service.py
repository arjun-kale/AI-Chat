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
            # Try pdfplumber first (better text extraction)
            try:
                import pdfplumber
                text = ""
                with pdfplumber.open(file_path) as pdf:
                    print(f"PDF has {len(pdf.pages)} pages (using pdfplumber)")
                    for page_num, page in enumerate(pdf.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                text += f"\n--- Page {page_num + 1} ---\n"
                                text += page_text + "\n"
                                print(f"Extracted {len(page_text)} characters from page {page_num + 1}")
                        except Exception as page_error:
                            print(f"Error extracting page {page_num + 1}: {page_error}")
                            continue
                
                if text.strip():
                    print(f"Total extracted text length: {len(text)} characters (pdfplumber)")
                    return text
                else:
                    print("pdfplumber extracted no text, trying PyPDF2...")
            except ImportError:
                print("pdfplumber not available, using PyPDF2...")
            except Exception as e:
                print(f"pdfplumber failed: {e}, trying PyPDF2...")
            
            # Fallback to PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                print(f"PDF has {len(pdf_reader.pages)} pages (using PyPDF2)")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():  # Only add non-empty pages
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text + "\n"
                            print(f"Extracted {len(page_text)} characters from page {page_num + 1}")
                    except Exception as page_error:
                        print(f"Error extracting page {page_num + 1}: {page_error}")
                        continue
                
                print(f"Total extracted text length: {len(text)} characters (PyPDF2)")
                return text
                
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return ""

    def process_image(self, file_path: str) -> str:
        """Process image file and extract information"""
        try:
            from PIL import Image
            import os
            
            # Open and analyze the image
            with Image.open(file_path) as img:
                # Get basic image information
                width, height = img.size
                mode = img.mode
                format_name = img.format
                file_size = os.path.getsize(file_path)
                
                # Try to extract text using OCR
                extracted_text = ""
                try:
                    import pytesseract
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    extracted_text = pytesseract.image_to_string(img)
                    extracted_text = extracted_text.strip()
                except ImportError:
                    extracted_text = "OCR not available (pytesseract not installed)"
                except Exception as ocr_error:
                    extracted_text = f"OCR failed: {str(ocr_error)}"
                
                # Create a description of the image
                image_description = f"""
Image Analysis:
- Filename: {os.path.basename(file_path)}
- Dimensions: {width}x{height} pixels
- Color mode: {mode}
- Format: {format_name}
- File size: {file_size} bytes

Extracted Text:
{extracted_text if extracted_text else "No text found in image"}

Note: This is a visual image file. The AI can discuss the image based on its filename, metadata, and any extracted text content.
"""
                
                return image_description
                
        except Exception as e:
            print(f"Error processing image: {e}")
            return f"Image file: {os.path.basename(file_path)} (processing error: {str(e)})"

    def add_document_to_vectordb(self, content: str, document_id: str, conversation_id: str):
        """Add document content to vector database"""
        try:
            print(f"Adding document to vectordb: {document_id} for conversation: {conversation_id}")
            print(f"Content length: {len(content)} characters")
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(content)
            print(f"Split into {len(chunks)} chunks")
            
            # Create collection for this conversation
            collection_name = f"conversation_{conversation_id}"
            
            # Get or create collection
            try:
                collection = self.chroma_client.get_collection(collection_name)
                print(f"Using existing collection: {collection_name}")
            except:
                collection = self.chroma_client.create_collection(collection_name)
                print(f"Created new collection: {collection_name}")
            
            # Add chunks to collection
            for i, chunk in enumerate(chunks):
                collection.add(
                    documents=[chunk],
                    metadatas=[{"document_id": document_id, "chunk_index": i}],
                    ids=[f"{document_id}_{i}"]
                )
                print(f"Added chunk {i+1}/{len(chunks)}")
            
            print(f"Successfully added document {document_id} to vectordb")
                
        except Exception as e:
            print(f"Error adding document to vectordb: {e}")

    def get_conversation_context(self, conversation_id: str, query: str) -> str:
        """Retrieve relevant context from vector database"""
        try:
            collection_name = f"conversation_{conversation_id}"
            print(f"Looking for context in collection: {collection_name}")
            
            try:
                collection = self.chroma_client.get_collection(collection_name)
                print(f"Collection found, querying with: {query}")
                
                results = collection.query(
                    query_texts=[query],
                    n_results=5
                )
                
                print(f"Query results: {results}")
                
                if results['documents'] and results['documents'][0]:
                    context = "\n".join(results['documents'][0])
                    print(f"Retrieved context: {context[:200]}...")
                    return context
                else:
                    print("No documents found in results")
                    return ""
            except Exception as e:
                print(f"Error querying collection: {e}")
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
            For image files, you can discuss the filename, metadata, and general information about the image, but explain that you cannot see the actual visual content.
            When users ask about uploaded files, you have access to the content and can provide detailed information about them.
            Be helpful, accurate, and concise in your responses."""
            
            if context:
                system_prompt += f"\n\nRelevant context from uploaded documents:\n{context}"
            else:
                system_prompt += "\n\nNote: No specific document context was found for this query."
            
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
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while processing your request. Please try again."

    def create_conversation(self) -> str:
        """Create a new conversation session"""
        return str(uuid.uuid4())
