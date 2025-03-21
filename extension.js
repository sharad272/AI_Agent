const vscode = require('vscode');
const fetch = require('node-fetch');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Ollama API handler - Simplified to just handle prompts
class OllamaHandler {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
}

// Process the streaming response
async function processStreamingResponse(stream, panel) {
    const reader = stream.getReader();
    let accumulatedResponse = '';
    const textDecoder = new TextDecoder();

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = textDecoder.decode(value, { stream: true });
            const lines = text.split('\n').filter(line => line.trim());

            for (const line of lines) {
                try {
                    const parsed = JSON.parse(line);
                    if (parsed.response) {
                        accumulatedResponse += parsed.response;
                        panel.webview.postMessage({
                            type: 'stream',
                            content: parsed.response
                        });
                    }
                } catch (e) {
                    console.error('Failed to parse line:', e);
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
    return accumulatedResponse;
}

// Add logging utility
function log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = `[AI Code Assistant] ${timestamp}`;
    switch(type) {
        case 'error':
            console.error(`${prefix} ERROR: ${message}`);
            break;
        case 'warn':
            console.warn(`${prefix} WARN: ${message}`);
            break;
        default:
            console.log(`${prefix} INFO: ${message}`);
    }
}

// Simplified PythonBridge class - only handles initialization and queries
class PythonBridge {
    constructor() {
        this.pythonProcess = null;
        log('PythonBridge initialized');
    }

    async initialize() {
        if (this.pythonProcess) {
            log('Python process already running');
            return;
        }

        // Get all open text editors
        const openFiles = await this.getOpenFiles();
        log(`Found ${openFiles.length} open files`);

        const scriptPath = path.join(__dirname, 'main.py');
        log(`Starting Python process with script: ${scriptPath}`);
        
        try {
            this.pythonProcess = spawn('py', [scriptPath], {
                stdio: ['pipe', 'pipe', 'pipe'],
                env: { 
                    ...process.env, 
                    PYTHONUNBUFFERED: '1'
                }
            });

            // Send initial files to Python process for embedding
            this.pythonProcess.stdin.write(
                JSON.stringify({
                    command: 'initialize',
                    files: openFiles.map(file => ({
                        filePath: file.filePath,
                        content: file.content,
                        language: file.language
                    }))
                }) + '\n'
            );

            log(`Sent ${openFiles.length} files for initialization`);
            
            // Handle stdout
            this.pythonProcess.stdout.on('data', (data) => {
                const output = data.toString().trim();
                if (output) {
                    log(`[Python] ${output}`);
                }
            });

            // Handle errors
            this.pythonProcess.on('error', (err) => {
                log(`Failed to start Python process: ${err.message}`, 'error');
            });

            this.pythonProcess.stderr.on('data', (data) => {
                const error = data.toString().trim();
                if (error) {
                    log(`[Python Error] ${error}`, 'error');
                }
            });

        } catch (error) {
            log(`Failed to start Python process: ${error.message}`, 'error');
            throw error;
        }
    }

    async getOpenFiles() {
        const openFiles = [];
        
        try {
            // Get files from workspace
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (workspaceFolders) {
                for (const folder of workspaceFolders) {
                    const files = await vscode.workspace.findFiles(
                        new vscode.RelativePattern(folder, '**/*.{js,ts,py,java,cpp,jsx,tsx}'),
                        '**/node_modules/**'
                    );
                    
                    for (const file of files) {
                        try {
                            const document = await vscode.workspace.openTextDocument(file);
                            if (this.isValidDocument(document)) {
                                openFiles.push({
                                    filePath: document.uri.fsPath,
                                    content: document.getText(),
                                    language: document.languageId
                                });
                            }
                        } catch (err) {
                            log(`Error reading file ${file.fsPath}: ${err.message}`, 'error');
                        }
                    }
                }
            }

            // Also get currently open editors
            vscode.window.visibleTextEditors.forEach(editor => {
                if (this.isValidDocument(editor.document) && 
                    !openFiles.some(f => f.filePath === editor.document.uri.fsPath)) {
                    openFiles.push({
                        filePath: editor.document.uri.fsPath,
                        content: editor.document.getText(),
                        language: editor.document.languageId
                    });
                }
            });

            log(`Found ${openFiles.length} valid files`);
            return openFiles;
        } catch (error) {
            log(`Error getting open files: ${error.message}`, 'error');
            return [];
        }
    }

    isValidDocument(document) {
        return document.uri.scheme === 'file' && 
               !document.fileName.includes('node_modules') &&
               !document.fileName.includes('.git');
    }

    setupResponseHandler(panel) {
        if (!this.pythonProcess) return;

        let isStreaming = false;

        this.pythonProcess.stdout.on('data', (data) => {
            const output = data.toString();
            
            // Skip thinking messages
            if (output.includes('<think>')) {
                return;
            }

            // Handle streaming response
            if (output.startsWith('Answer:')) {
                isStreaming = true;
                const content = output.replace('Answer:', '');
                panel.webview.postMessage({
                    type: 'stream',
                    content: content
                });
                return;
            }

            // Continue streaming if we're in streaming mode - send raw output
            if (isStreaming && output) {
                panel.webview.postMessage({
                    type: 'stream',
                    content: output
                });
            }
        });
    }

    async processQuery(query) {
        if (!this.pythonProcess) {
            throw new Error('Python process not initialized');
        }

        try {
            this.pythonProcess.stdin.write(
                JSON.stringify({
            command: 'query',
            text: query
                }) + '\n'
            );
            log(`Sent query to Python: ${query}`);
    } catch (error) {
            log(`Error sending query: ${error.message}`, 'error');
            throw error;
        }
    }
}

async function activate(context) {
    log('Activating extension');
    let disposable = vscode.commands.registerCommand('aiagent.openJarvis', async () => {
        let bridge;

        try {
            // First initialize backend with progress
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Jarvis Code Assistant",
                cancellable: false
            }, async (progress) => {
                try {
                    progress.report({ message: "Starting Python backend..." });
                    bridge = new PythonBridge();
                    
                    // Initialize with progress updates
                    await bridge.initialize();

                    // Get open files and generate embeddings
                    const openFiles = await bridge.getOpenFiles();
                    progress.report({ message: `Indexing ${openFiles.length} files...` });
                    
                    // Send files for embedding and wait for indexing to complete
                    await new Promise((resolve) => {
                        bridge.pythonProcess.stdin.write(
                            JSON.stringify({
                                command: 'initialize',
                                files: openFiles.map(file => ({
                                    filePath: file.filePath,
                                    content: file.content,
                                    language: file.language
                                }))
                            }) + '\n'
                        );
                        
                        // Wait for "ready" message from Python
                        bridge.pythonProcess.stdout.on('data', (data) => {
                            if (data.toString().includes("AI Assistant ready!")) {
                                resolve();
                            }
                        });
                    });
                    
                    progress.report({ message: "Initialization complete" });

                } catch (error) {
                    throw error;
                }
            });

            // Only create webview after indexing is complete
            const panel = vscode.window.createWebviewPanel(
                'jarvisInterface',
                'Jarvis Code Assistant',
                vscode.ViewColumn.Two,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true
                }
            );

            // Set up webview content
            panel.webview.html = getWebviewContent();

            // Set up response handler
            bridge.setupResponseHandler(panel);
            panel.bridge = bridge;

            // Handle messages from webview
            panel.webview.onDidReceiveMessage(
                async message => {
                    switch (message.command) {
                        case 'query':
                            try {
                                // Disable input while processing
                                panel.webview.postMessage({ type: 'processing' });
                                
                                await bridge.processQuery(message.text);
                                
                                // Re-enable input after response
                                panel.webview.postMessage({ type: 'streamComplete' });
                            } catch (error) {
                                log(`Error processing query: ${error.message}`, 'error');
                                panel.webview.postMessage({
                                    type: 'error',
                                    content: error.message
                                });
                                // Re-enable input on error
                                panel.webview.postMessage({ type: 'streamComplete' });
                            }
                            return;
                    }
                },
                undefined,
                context.subscriptions
            );

            // Handle panel disposal
            panel.onDidDispose(() => {
                if (bridge && bridge.pythonProcess) {
                    bridge.pythonProcess.kill();
                }
            }, null, context.subscriptions);

            // After successful initialization
            panel.webview.postMessage({ type: 'ready' });

        } catch (error) {
            log(`Failed to initialize: ${error.message}`, 'error');
            vscode.window.showErrorMessage(`Failed to initialize AI Code Assistant: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
    log('Extension activated successfully');
}

function getWebviewContent() {
    return `
        <!DOCTYPE html>
        <html>
            <head>
                <style>
                    body {
                        padding: 10px;
                        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        background-color: var(--vscode-editor-background);
                        color: var(--vscode-editor-foreground);
                        margin: 0;
                        padding: 15px;
                        height: 100vh;
                        display: flex;
                        flex-direction: column;
                    }
                    
                    .status-bar {
                        padding: 8px 12px;
                        background-color: var(--vscode-statusBar-background);
                        color: var(--vscode-statusBar-foreground);
                        margin-bottom: 15px;
                        display: flex;
                        align-items: center;
                        border-radius: 4px;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
                    }
                    
                    .status-bar .status-icon {
                        margin-right: 8px;
                        color: #44cc44;
                        animation: pulse 2s infinite;
                    }
                    
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.7; }
                        100% { opacity: 1; }
                    }
                    
                    #messages {
                        margin-bottom: 15px;
                        white-space: pre-wrap;
                        flex: 1;
                        overflow-y: auto;
                        padding-right: 5px;
                    }
                    
                    #messages::-webkit-scrollbar {
                        width: 6px;
                    }
                    
                    #messages::-webkit-scrollbar-thumb {
                        background-color: rgba(100, 100, 100, 0.5);
                        border-radius: 3px;
                    }
                    
                    .message {
                        margin-bottom: 15px;
                        animation: fadeIn 0.3s ease-in-out;
                        line-height: 1.5;
                    }
                    
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(5px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    
                    .user {
                        color: #4a9eff;
                        padding: 8px 12px;
                        border-radius: 5px;
                        background-color: rgba(74, 158, 255, 0.1);
                        border-left: 3px solid #4a9eff;
                    }
                    
                    .assistant {
                        color: #ffffff;
                        padding: 8px 12px;
                        border-radius: 5px;
                        background-color: rgba(255, 255, 255, 0.05);
                        border-left: 3px solid #888;
                    }
                    
                    .thinking {
                        color: orange;
                        font-style: italic;
                        padding: 8px 12px;
                        border-radius: 5px;
                        background-color: rgba(255, 165, 0, 0.1);
                        border-left: 3px solid orange;
                    }
                    
                    .input-container {
                        display: flex;
                        align-items: center;
                        background-color: var(--vscode-input-background);
                        border: 1px solid var(--vscode-input-border);
                        border-radius: 5px;
                        padding: 5px;
                        margin-top: 5px;
                    }
                    
                    #userInput {
                        flex: 1;
                        padding: 8px;
                        background-color: transparent;
                        color: var(--vscode-input-foreground);
                        border: none;
                        outline: none;
                        font-size: 14px;
                    }
                    
                    .send-button {
                        background-color: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border: none;
                        border-radius: 3px;
                        padding: 6px 12px;
                        cursor: pointer;
                        margin-left: 5px;
                        transition: background-color 0.2s;
                    }
                    
                    .send-button:hover {
                        background-color: var(--vscode-button-hoverBackground);
                    }
                    
                    .send-button:disabled {
                        opacity: 0.6;
                        cursor: not-allowed;
                    }
                    
                    code {
                        font-family: 'Courier New', monospace;
                        background-color: rgba(255, 255, 255, 0.1);
                        padding: 2px 4px;
                        border-radius: 3px;
                    }
                    
                    pre {
                        background-color: var(--vscode-editor-background);
                        border: 1px solid var(--vscode-editorWidget-border);
                        border-radius: 4px;
                        padding: 10px;
                        overflow-x: auto;
                        margin: 10px 0;
                    }
                </style>
            </head>
            <body>
                <div class="status-bar">
                    <span class="status-icon">●</span> Jarvis is Connected
                </div>
                <div id="messages"></div>
                <div class="input-container">
                    <input type="text" id="userInput" placeholder="Ask Jarvis something..." />
                    <button id="sendButton" class="send-button">Send</button>
                </div>
                
                <script>
                    const vscode = acquireVsCodeApi();
                    const messagesDiv = document.getElementById('messages');
                    const userInput = document.getElementById('userInput');
                    const sendButton = document.getElementById('sendButton');
                    
                    // Function to send user query
                    function sendQuery() {
                        const userMessage = userInput.value.trim();
                        if (userMessage && !userInput.disabled) {
                            // Add user message with proper class
                            messagesDiv.innerHTML += '<div class="message user">You: ' + userMessage + '</div>';
                            
                            // Create a placeholder for the assistant response
                            messagesDiv.innerHTML += '<div class="message assistant" id="currentResponse">Assistant: </div>';
                            
                            // Send to backend
                            vscode.postMessage({ command: 'query', text: userMessage });
                            
                            // Clear input and disable it
                            userInput.value = '';
                            userInput.disabled = true;
                            sendButton.disabled = true;
                            
                            // Scroll to the bottom
                            scrollToBottom();
                        }
                    }
                    
                    // Function to handle code blocks in responses
                    function formatResponse(text) {
                        // Replace backtick code blocks with HTML
                        let formatted = text.replace(/\`\`\`([a-zA-Z]*)([\s\S]*?)\`\`\`/g, function(match, language, code) {
                            return '<pre><code class="language-' + language + '">' + code + '</code></pre>';
                        });
                        
                        // Replace inline code
                        formatted = formatted.replace(/\`([^\`]+)\`/g, '<code>$1</code>');
                        
                        return formatted;
                    }
                    
                    // Function to scroll to bottom of messages
                    function scrollToBottom() {
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    }
                    
                    // Event listener for Enter key
                    userInput.addEventListener('keyup', (e) => {
                        if (e.key === 'Enter') {
                            sendQuery();
                        }
                    });
                    
                    // Event listener for Send button
                    sendButton.addEventListener('click', sendQuery);
                    
                    // Set focus on input field
                    userInput.focus();
                    
                    // Listen for messages from extension
                    window.addEventListener('message', event => {
                        const message = event.data;
                        const currentResponse = document.getElementById('currentResponse');
                        
                        switch (message.type) {
                            case 'processing':
                                // Ensure input is disabled during processing
                                userInput.disabled = true;
                                sendButton.disabled = true;
                                break;
                                
                            case 'thinking':
                                // Handle thinking content (orange text)
                                if (!document.getElementById('currentThinking')) {
                                    messagesDiv.innerHTML += '<div class="message thinking" id="currentThinking">Thinking: ' + message.content + '</div>';
                                } else {
                                    const thinkingEl = document.getElementById('currentThinking');
                                    thinkingEl.innerHTML = 'Thinking: ' + thinkingEl.innerHTML.substring(9) + message.content;
                                }
                                
                                // Scroll to the bottom
                                scrollToBottom();
                                break;
                                
                            case 'thinkingComplete':
                                // Remove thinking ID but keep the element visible
                                const thinkingEl = document.getElementById('currentThinking');
                                if (thinkingEl) {
                                    thinkingEl.removeAttribute('id');
                                }
                                
                                // Create a new element for the actual response (below the thinking content)
                                messagesDiv.innerHTML += '<div class="message assistant" id="currentResponse">Assistant: </div>';
                                
                                // Scroll to the bottom
                                scrollToBottom();
                                break;
                                
                            case 'stream':
                                // Make sure we have a response element
                                if (!currentResponse) {
                                    // If thinking has happened but no response element exists yet,
                                    // add it after the thinking content
                                    messagesDiv.innerHTML += '<div class="message assistant" id="currentResponse">Assistant: </div>';
                                }
                                
                                // Format and append the new content
                                const formattedContent = formatResponse(message.content);
                                currentResponse.innerHTML = 'Assistant: ' + currentResponse.innerHTML.substring(11) + formattedContent;
                                
                                // Scroll to the bottom
                                scrollToBottom();
                                break;
                                
                            case 'streamComplete':
                                // Re-enable input after streaming is complete
                                userInput.disabled = false;
                                sendButton.disabled = false;
                                
                                // Remove the ID from the current response so new responses get their own element
                                if (currentResponse) {
                                    currentResponse.removeAttribute('id');
                                }
                                
                                // Focus the input field
                                userInput.focus();
                                break;
                                
                            case 'error':
                                // Handle errors
                                if (!currentResponse) {
                                    messagesDiv.innerHTML += '<div class="message assistant" id="currentResponse">Assistant: </div>';
                                }
                                
                                currentResponse.innerHTML = 'Assistant: <span style="color: #ff6b6b;">Error: ' + message.content + '</span>';
                                currentResponse.removeAttribute('id');
                                userInput.disabled = false;
                                sendButton.disabled = false;
                                userInput.focus();
                                break;
                                
                            case 'ready':
                                // Focus the input when the panel is ready
                                userInput.focus();
                                break;
                        }
                    });
                </script>
            </body>
        </html>
    `;
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
}
