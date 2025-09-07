# AI Chat Assistant

A Basic AI chat application built with Django, LangChain, VectorDB, and Gemini AI. Users can interact with an AI assistant and upload PDF or image files to get AI-powered responses.

## Features

- 🤖 AI-powered chat using Google Gemini
- 📄 PDF document processing and analysis
- 🖼️ Image file support
- 🔍 Vector database for document search and retrieval
- 💬 Persistent conversation history
- 📱 Responsive web interface
- 🚀 Real-time chat experience

## Tech Stack


- **Backend**: Django 4.2.7
- **AI/ML**: LangChain, Google Gemini, Langchain_community 
- **Vector Database**: ChromaDB
- **Frontend**: HTML, CSS, JavaScript
- **File Processing**: PyPDF2, Pillow

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-Chat

   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Open your browser**
   Navigate to `http://127.0.0.1:8000`

## Getting a Gemini API Key

1. Go to #Google AI Studio
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Add it to your `.env` file

## Usage

### Starting a Chat
1. Open the application in your browser
2. Type a message in the input field
3. Press Enter or click the send button
4. The AI will respond based on the conversation context

### Uploading Files
1. Click the "Upload File" button or drag and drop files
2. Supported formats: PDF, JPG, PNG, GIF, BMP
3. Once uploaded, you can ask questions about the document content
4. The AI will use the document content to provide relevant answers

### Features
- **New Chat**: Start a fresh conversation
- **File Upload**: Upload documents for AI analysis
- **Persistent Sessions**: Your conversation history is saved
- **Responsive Design**: Works on desktop and mobile devices

## API Endpoints

- `GET /` - Main chat interface
- `POST /api/conversations/start/` - Start a new conversation
- `GET /api/conversations/<session_id>/` - Get conversation details
- `POST /api/chat/` - Send a message
- `POST /api/upload/` - Upload a file
- `GET /api/conversations/` - List all conversations
- `DELETE /api/conversations/<session_id>/delete/` - Delete a conversation

## Project Structure

```
aichat/
├── aichat/                 # Django project settings
├── chat/                   # Main chat application
│   ├── models.py          # Database models
│   ├── views.py           # API views
│   ├── serializers.py     # API serializers
│   ├── ai_service.py      # AI integration service
│   └── urls.py            # URL patterns
├── templates/             # HTML templates
├── static/                # CSS and JavaScript files
├── media/                 # Uploaded files
├── vectordb/              # Vector database storage
└── requirements.txt       # Python dependencies
```

## Configuration

The application can be configured through Django settings:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `VECTORDB_PATH`: Path to store the vector database
- `MEDIA_ROOT`: Directory for uploaded files
- `DEBUG`: Enable/disable debug mode

## Troubleshooting

### Common Issues

1. **API Key Error**: Make sure your Gemini API key is correctly set in the `.env` file
2. **File Upload Issues**: Check file permissions and ensure the media directory exists
3. **Vector DB Issues**: Ensure the vectordb directory is writable
4. **CORS Issues**: Make sure CORS settings are properly configured for your domain


## License

This project is licensed under the MIT License.

