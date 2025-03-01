# AI Code Assistant

An intelligent code assistant powered by Ollama and FAISS vector database that helps with code-related queries and file operations.

## Features

- Real-time file monitoring and context updating
- Code-aware query processing using vector similarity search
- File operations (create, edit, show, delete)
- Intelligent context management
- Integration with Ollama's Deepseek model

## Prerequisites

- Python 3.8+
- Ollama installed and running locally
- FAISS vector database
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd AI_Agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure Ollama is installed and running with the Deepseek model:
```bash
ollama pull deepseek-r1:1.5b
```

## Project Structure

```
AI_Agent/
├── main.py              # Main application entry point
├── models/
│   └── ollama_handler.py    # Ollama model integration
├── services/
│   └── query_service.py     # Query processing service
├── vectordb/
│   └── faiss_db.py         # FAISS vector database management
└── requirements.txt     # Project dependencies
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Enter your questions or commands when prompted. Examples:
   - "Show me the content of faiss_db.py"
   - "Fix the code in query_service.py"
   - "What does the OllamaHandler class do?"

3. Type 'quit' to exit the application.

## Features in Detail

### Code-Related Queries
- The system automatically detects if a query is code-related
- Utilizes FAISS for semantic search of relevant code context
- Provides file-specific responses with relevant code snippets

### File Operations
- Show file content
- Fix code issues
- Create new files
- Edit existing files
- Delete files

### Context Management
- Real-time file monitoring
- Automatic context updates on file changes
- Efficient vector similarity search

## Configuration

The system uses default configurations for:
- Ollama model: deepseek-r1:1.5b
- FAISS vector dimension: 384
- File monitoring: recursive directory watching

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.