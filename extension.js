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

    initialize() {
        if (this.pythonProcess) {
            log('Python process already running');
            return;
        }

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
            log('Python process started successfully');

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

    async processQuery(query) {
        log(`Processing query: "${query.substring(0, 50)}..."`);
        
        return new Promise((resolve, reject) => {
            try {
                log('Sending query to Python process');
                
                let buffer = '';
                let isAnswer = false;
                let currentResponse = '';
                
                const outputHandler = (data) => {
                    const output = data.toString();
                    if (output.includes('Answer:')) {
                        isAnswer = true;
                        const answerPart = output.split('Answer:')[1];
                        if (answerPart) {
                            currentResponse = answerPart;
                            this.emit('stream', currentResponse);
                        }
                    } 
                    else if (isAnswer && output.trim()) {
                        currentResponse = output;
                        this.emit('stream', currentResponse);
                    }
                };
                
                this.pythonProcess.stdout.on('data', outputHandler);
                
                // Send query to Python process
                this.pythonProcess.stdin.write(
                    JSON.stringify({
                        command: 'query',
                        text: query
                    }) + '\n'
                );
                
            } catch (error) {
                reject(error);
            }
        });
    }
}

function activate(context) {
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
                    await bridge.initialize();

                    // Wait for ready signal before creating webview
                    await new Promise((resolve, reject) => {
                        const initHandler = (data) => {
                            const output = data.toString();
                            if (output.includes("Ready! Waiting for queries...")) {
                                bridge.pythonProcess.stdout.removeListener('data', initHandler);
                                resolve();
                            }
                            if (output.includes("Processing file:")) {
                                progress.report({ message: output });
                            }
                        };
                        
                        bridge.pythonProcess.stdout.on('data', initHandler);
                        setTimeout(() => reject(new Error('Initialization timeout')), 60000);
                    });

                } catch (error) {
                    throw error;
                }
            });

            // Only create webview after successful initialization
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
                                if (bridge && bridge.pythonProcess) {
                                    bridge.pythonProcess.stdin.write(message.text + '\n');
                                    log(`Sent query to Python: ${message.text}`);
                                } else {
                                    throw new Error('Python process not initialized');
                                }
                            } catch (error) {
                                log(`Error sending query: ${error.message}`, 'error');
                                panel.webview.postMessage({
                                    type: 'error',
                                    content: error.message
                                });
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
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline';">
                <title>Jarvis Code Assistant</title>
                <style>
                    body {
                        padding: 15px;
                        color: var(--vscode-editor-foreground);
                        font-family: var(--vscode-font-family);
                    }
                    #main {
                        display: flex;
                        flex-direction: column;
                        height: 100vh;
                    }
                    .status-bar {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin-bottom: 15px;
                        padding: 8px;
                        background: var(--vscode-editor-background);
                        border: 1px solid var(--vscode-input-border);
                        border-radius: 4px;
                    }
                    .status-indicator {
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #4CAF50;
                    }
                    .status-text {
                        color: var(--vscode-editor-foreground);
                        font-size: 12px;
                    }
                    #response {
                        flex: 1;
                        border: 1px solid var(--vscode-input-border);
                        padding: 10px;
                        margin-bottom: 10px;
                        overflow-y: auto;
                        white-space: pre-wrap;
                        background: var(--vscode-editor-background);
                    }
                    .input-container {
                        display: flex;
                        gap: 8px;
                    }
                    #queryInput {
                        flex: 1;
                        padding: 8px;
                        min-height: 60px;
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        border: 1px solid var(--vscode-input-border);
                    }
                    button {
                        padding: 0 16px;
                        background: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border: none;
                    }
                    .loading {
                        position: fixed;
                        bottom: 80px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: var(--vscode-editor-background);
                        padding: 6px 12px;
                        border-radius: 4px;
                        border: 1px solid var(--vscode-input-border);
                        display: none;
                    }
                </style>
            </head>
            <body>
                <div id="main">
                    <div class="status-bar">
                        <div class="status-indicator"></div>
                        <span class="status-text">Jarvis is initializing...</span>
                    </div>
                    <div id="response"></div>
                    <div class="input-container">
                        <textarea id="queryInput" placeholder="Ask Jarvis about your code..." disabled></textarea>
                        <button onclick="sendQuery()" disabled>Ask Jarvis</button>
                    </div>
                    <div class="loading">Jarvis is thinking...</div>
                </div>

                <script>
                    const vscode = acquireVsCodeApi();
                    const responseEl = document.getElementById('response');
                    const inputEl = document.getElementById('queryInput');
                    const buttonEl = document.querySelector('button');
                    const statusText = document.querySelector('.status-text');
                    const statusIndicator = document.querySelector('.status-indicator');
                    const loadingEl = document.querySelector('.loading');
                    let isResponding = false;

                    function sendQuery() {
                        const text = inputEl.value.trim();
                        if (!text || isResponding) return;
                        
                        isResponding = true;
                        inputEl.disabled = true;
                        buttonEl.disabled = true;
                        loadingEl.style.display = 'block';

                        responseEl.textContent += '> ' + text + '\\n\\n';
                        
                        vscode.postMessage({ command: 'query', text });
                        inputEl.value = '';
                        responseEl.scrollTop = responseEl.scrollHeight;
                    }

                    window.addEventListener('message', event => {
                        const message = event.data;
                        switch (message.type) {
                            case 'ready':
                                statusText.textContent = 'Jarvis is Connected';
                                statusIndicator.style.background = '#4CAF50';
                                inputEl.disabled = false;
                                buttonEl.disabled = false;
                                break;
                            case 'stream':
                                responseEl.textContent += message.content;
                                responseEl.scrollTop = responseEl.scrollHeight;
                                break;
                            case 'streamComplete':
                                loadingEl.style.display = 'none';
                                responseEl.textContent += '\\n\\n';
                                isResponding = false;
                                inputEl.disabled = false;
                                buttonEl.disabled = false;
                                break;
                            case 'error':
                                loadingEl.style.display = 'none';
                                responseEl.textContent = 'Error: ' + message.content + '\\n\\n';
                                statusText.textContent = 'Jarvis encountered an error';
                                statusIndicator.style.background = '#f44336';
                                isResponding = false;
                                inputEl.disabled = false;
                                buttonEl.disabled = false;
                                break;
                        }
                    });

                    inputEl.addEventListener('keydown', e => {
                        if (e.key === 'Enter' && !e.shiftKey && !isResponding) {
                            e.preventDefault();
                            sendQuery();
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
