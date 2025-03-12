# Jarvis Code Assistant

An intelligent VSCode extension powered by Ollama and FAISS vector database that provides real-time code understanding and assistance.

## Features

- **Smart Context Understanding**: Uses FAISS vector DB for efficient code context search
- **Real-time Streaming**: Provides streaming responses for better interaction
- **File Monitoring**: Automatically tracks and indexes workspace files
- **Memory Context**: Maintains conversation history for contextual responses
- **Multi-language Support**: Works with Python, JavaScript, TypeScript, HTML, CSS, and more
- **Error Handling**: Robust error handling across all operations

## Prerequisites

- Python 3.8+
- VSCode 1.60.0+
- Ollama with deepseek-r1:1.5b model
- Node.js and npm

## Project Structure

```
jarvis-code-assistant/
├── services/
│   ├── vscode_bridge.py     # Bridge between VSCode and Python
│   ├── query_service.py     # Query processing and context management
│   └── workspace-service.ts # Workspace file management
├── models/
│   └── ollama_handler.py    # Ollama model integration
├── vectordb/
│   └── faiss_db.py         # Vector database implementation
├── extension.js            # VSCode extension main file
├── main.py                # Python backend entry point
└── package.json           # Extension manifest
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt

2. Install Ollama and pull the model:
```bash
ollama pull deepseek-r1:1.5b
```

## Usage

Run the application:
```bash
python main.py
```

### Query Examples

1. Code Explanation:
```
Enter your question: Explain how the FAISS indexing works in this project
```

2. Error Fixing:
```
Enter your question: Fix the error in file_reader.py
```

3. Code Understanding:
```
Enter your question: How does the file monitoring system work?
```

## Key Components

### FAISSManager (faiss_db.py)
- Manages document embeddings
- Performs similarity search
- Handles index creation and updates

### FileReader (file_reader.py)
- Manages file operations
- Handles file type validation
- Maintains file content cache

### OllamaHandler (ollama_handler.py)
- Interfaces with Ollama model
- Processes different query types
- Handles response formatting

### Main Application (main.py)
- Implements file change monitoring
- Manages user interactions
- Coordinates system components

## Error Handling

The system includes comprehensive error handling for:
- File operations
- Model interactions
- Vector database operations
- Context updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License
