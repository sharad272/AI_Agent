# Jarvis Code Assistant

An intelligent VSCode extension powered by Ollama and FAISS vector database that provides real-time code understanding and assistance.

## Features

- **Smart Context Understanding**: Uses FAISS vector DB for efficient code context search
- **Real-time Streaming**: Provides streaming responses for better interaction
- **File Monitoring**: Automatically tracks and indexes workspace files
- **Memory Context**: Maintains conversation history for contextual responses
- **Multi-language Support**: Works with Python, JavaScript, TypeScript, HTML, CSS, and more
- **Error Handling**: Robust error handling across all operations
- **Configuration Management**: Flexible configuration through environment variables
- **TypeScript Integration**: Full TypeScript support for better type safety
- **Cross-Python Compatibility**: Support for multiple Python versions (3.8+)

## Prerequisites

- Python 3.8+ (compatible with 3.9, 3.10, and 3.11)
- VSCode 1.60.0+
- Ollama with deepseek-r1:1.5b model
- Node.js 14+ and npm 6+

## Project Structure

```
jarvis-code-assistant/
├── config/
│   ├── config.py          # Configuration management
│   └── .env.template      # Environment variables template
├── models/
│   └── ollama_handler.py  # Ollama model integration
├── services/
│   ├── vscode_bridge.py   # Bridge between VSCode and Python
│   ├── query_service.py   # Query processing and context management
│   └── workspace-service.ts # Workspace file management
├── utils/
│   └── file_reader.py     # File operations and validation
├── vectordb/
│   └── faiss_db.py        # Vector database implementation
├── resources/             # Static resources
├── tracking-folder/       # File change tracking
├── .vscode/              # VSCode specific configurations
├── extension.js          # VSCode extension main file
├── main.py              # Python backend entry point
├── package.json         # Extension manifest
├── tsconfig.json        # TypeScript configuration
└── requirements.txt     # Python dependencies with flexible versioning
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jarvis-code-assistant.git
cd jarvis-code-assistant
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

The requirements.txt file includes:
- Flexible version constraints for better compatibility across Python versions
- Option for CPU-only installation (see commented lines in requirements.txt)
- Clearly categorized dependencies for different functionalities

3. Install Node.js dependencies:
```bash
npm install
```

4. Install Ollama and pull the model:
```bash
ollama pull deepseek-r1:1.5b
```

5. Set up environment variables:
```bash
cp .env.template .env
# Edit .env with your configuration
```

## Python Compatibility

The extension is designed to work with multiple Python versions:
- Fully compatible with Python 3.8, 3.9, 3.10, and 3.11
- Dependencies are versioned to ensure compatibility
- For users with specific environment constraints:
  - CPU-only option available in requirements.txt
  - M1/M2 Mac compatibility notes in documentation

## Usage

1. Start the Python backend:
```bash
python main.py
```

2. In VSCode:
   - Press `F5` to start debugging
   - Use the command palette (Ctrl+Shift+P) and type "Jarvis" to see available commands

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

### Configuration Management (config/)
- `config.py`: Handles application configuration
- `.env.template`: Template for environment variables

### Models (models/)
- `ollama_handler.py`: Interfaces with Ollama model
- Processes different query types
- Handles response formatting

### Services (services/)
- `vscode_bridge.py`: Communication between VSCode and Python
- `query_service.py`: Query processing and context management
- `workspace-service.ts`: TypeScript implementation of workspace management

### Utils (utils/)
- `file_reader.py`: File operations and validation
- Handles file type checking
- Manages file content caching

### Vector Database (vectordb/)
- `faiss_db.py`: FAISS vector database implementation
- Manages document embeddings
- Performs similarity search
- Handles index creation and updates

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
- Configuration errors
- TypeScript compilation errors
- Python version compatibility issues

## Development

1. TypeScript Development:
```bash
npm run build    # Build TypeScript files
npm run watch    # Watch for changes
```

2. Python Development:
```bash
python -m pytest tests/  # Run tests
```

3. Environment Setup:
```bash
# For development with specific Python versions
python3.9 -m venv venv39
source venv39/bin/activate  # On Windows: venv39\Scripts\activate
pip install -r requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - See LICENSE file for details
