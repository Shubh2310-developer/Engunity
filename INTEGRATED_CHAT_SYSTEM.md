# 🚀 Integrated AI Chat & Code Generation System

## Overview
This system provides a ChatGPT-like interface that seamlessly integrates AI chat capabilities with intelligent code generation, storing all data in MongoDB Community Edition with the exact schema structure you specified.

## 🎯 Key Features

### ✨ ChatGPT-like UI
- **Dark theme interface** with modern design
- **Syntax highlighting** using Prism.js
- **Code copy functionality** with one-click copying
- **Responsive design** that works on all devices
- **Chat history sidebar** with persistent storage
- **Typing indicators** and smooth animations

### 🤖 Intelligent Code Detection
- **Automatic detection** of code-related requests
- **Multi-language support** (Python, JavaScript, Java, C++, etc.)
- **Smart context switching** between chat and code generation
- **Unified interface** for all interactions

### 🗃️ MongoDB Integration
All data is stored in MongoDB Community Edition with these collections:

#### Collections Structure (Matching Your Image):
```
Engunity AI Database
├── chat_history     - All conversations with messages
├── codes           - Generated code snippets
├── user_stats      - User analytics and statistics  
├── images          - Image documents (ready for future)
├── pdfs            - PDF documents (ready for future)
└── test_collection - Test data collection
```

## 📁 Files Created/Updated

### Frontend
- **`/pages/code-chat.html`** - Main ChatGPT-like interface
- **`/test-integrated-chat.html`** - Testing and documentation page

### Backend
- **`/api/v1/integrated_chat.py`** - New integrated endpoint
- **Updated `/api/v1/__init__.py`** - Added new router
- **Enhanced MongoDB models** - All collections properly configured

## 🔗 API Endpoints

### Main Integrated Endpoint
```http
POST /api/v1/integrated-chat
```
**Features:**
- Automatic code detection
- Unified response handling
- MongoDB storage
- Chat history management

**Request:**
```json
{
  "message": "Write a Python function to sort a list",
  "chat_id": "optional_chat_id",
  "conversation_context": [],
  "save_conversation": true,
  "auto_detect_code": true
}
```

**Response:**
```json
{
  "response": "I'll create a Python sorting function...\n\n```python\ndef sort_list(arr):\n    return sorted(arr)\n```",
  "response_type": "code",
  "chat_id": "chat_123456",
  "metadata": {
    "type": "code_generation",
    "language": "python",
    "tokens_used": 150
  },
  "code_snippets": [...]
}
```

### Additional Endpoints
- `GET /api/v1/user-chats` - Get user's chat history
- `GET /api/v1/chat-history/{chat_id}` - Get specific chat
- `POST /api/v1/code/generate` - Direct code generation
- `POST /api/v1/ai/chat/completions` - Direct chat completion

## 🎮 How to Use

### 1. Access the Interface
Navigate to: `http://localhost:8000/pages/code-chat.html`

### 2. Authentication
Login using your Supabase credentials

### 3. Start Chatting
**For Code Generation:**
- "Write a Python function to calculate fibonacci"
- "Create a JavaScript sorting algorithm"
- "Generate HTML form with validation"

**For General Chat:**
- "Explain machine learning concepts"
- "What is the difference between Python and JavaScript?"
- "Help me understand recursion"

### 4. Code Features
- **Automatic syntax highlighting**
- **One-click code copying**
- **Language detection**
- **Code explanations**

## 💾 Data Storage Details

### Chat History Collection
```javascript
{
  "_id": ObjectId,
  "user_id": "supabase_user_id",
  "title": "Chat about Python functions",
  "messages": [
    {
      "role": "user|assistant",
      "content": "message content",
      "timestamp": ISODate,
      "message_type": "text|code",
      "metadata": {}
    }
  ],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### Codes Collection
```javascript
{
  "_id": ObjectId,
  "user_id": "supabase_user_id",
  "title": "Function - Sort list",
  "description": "User's original request",
  "language": "python",
  "code": "def sort_list(arr):\n    return sorted(arr)",
  "chat_id": "associated_chat_id",
  "created_at": ISODate,
  "metadata": {
    "generated_from_chat": true,
    "tokens_used": 150
  }
}
```

### User Stats Collection
```javascript
{
  "_id": ObjectId,
  "user_id": "supabase_user_id",
  "total_chats": 5,
  "total_messages": 50,
  "total_codes": 15,
  "total_images": 0,
  "total_pdfs": 0,
  "created_at": ISODate
}
```

## 🧪 Testing

### Quick Test
Visit: `http://localhost:8000/test-integrated-chat.html`

This page provides:
- System status checks
- Endpoint testing
- Feature demonstrations
- Usage examples

### Manual Testing
1. Start the server: `python start_server.py`
2. Open the chat interface
3. Login with Supabase
4. Try various requests:
   - Code: "Write a calculator in Python"
   - Chat: "Explain sorting algorithms"

## 🔧 Technical Implementation

### Smart Code Detection
The system uses regex patterns and keyword analysis to detect code requests:
```python
def detect_code_request(message: str) -> bool:
    # Patterns for code detection
    code_indicators = [
        r'\b(write|create|generate|build|implement)\b.*\b(function|class|algorithm)\b',
        r'\b(python|javascript|java|c\+\+)\b.*\b(code|function)\b',
        # ... more patterns
    ]
```

### Automatic Language Detection
```python
def extract_language_from_message(message: str) -> str:
    languages = {
        'python': ['python', 'py', 'django', 'flask'],
        'javascript': ['javascript', 'js', 'node', 'react'],
        # ... more languages
    }
```

### MongoDB Integration
- **Automatic connection** to MongoDB
- **Collection creation** with proper indexes
- **Data validation** using Pydantic models
- **Error handling** and logging

## 🚀 Getting Started

1. **Start MongoDB** (Community Edition)
2. **Start the server:**
   ```bash
   cd backend
   python start_server.py
   ```
3. **Open the interface:** `http://localhost:8000/pages/code-chat.html`
4. **Login and start chatting!**

## 📊 Features Comparison

| Feature | Regular Chat | Integrated System |
|---------|-------------|-------------------|
| Code Generation | ❌ | ✅ Auto-detected |
| Syntax Highlighting | ❌ | ✅ Prism.js |
| Code Storage | ❌ | ✅ MongoDB |
| Chat History | ✅ | ✅ Enhanced |
| Copy Code | ❌ | ✅ One-click |
| Language Detection | ❌ | ✅ Automatic |
| Unified Interface | ❌ | ✅ Seamless |

## 🎉 Success Metrics

✅ **ChatGPT-like UI** - Beautiful, responsive interface  
✅ **Code Generation** - Intelligent detection and generation  
✅ **MongoDB Storage** - All data stored with proper schema  
✅ **Authentication** - Secure Supabase integration  
✅ **Error Handling** - Robust error management  
✅ **Performance** - Fast response times with timeouts  
✅ **Scalability** - Ready for production use  

The system is now ready for production use with all requested features implemented and tested!