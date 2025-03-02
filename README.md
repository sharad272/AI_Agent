# AI Code Assistant

An intelligent code assistant powered by Ollama and FAISS vector database that provides code understanding, querying, and analysis capabilities.

## Features

- **Vector Similarity Search**: Uses FAISS for efficient code context search
- **File Management**: Reads and processes multiple file types (.py, .js, .ts, .java, .cpp, .json, .md, .txt)
- **Real-time Monitoring**: Watches for file changes and updates context automatically
- **Intelligent Response**: Uses Ollama's Deepseek model for code understanding
- **Error Handling**: Robust error handling across file operations and model interactions

## Prerequisites

- Python 3.8+
- Ollama with deepseek-r1:1.5b model
- Required Python packages (see requirements.txt)

## Project Structure

```
AI_Agent/
├── models/
│   └── ollama_handler.py    # Manages Ollama model interactions
├── utils/
│   └── file_reader.py       # Handles file operations and monitoring
├── vectordb/
│   └── faiss_db.py         # FAISS vector database implementation
├── main.py                  # Application entry point
└── requirements.txt         # Project dependencies
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

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