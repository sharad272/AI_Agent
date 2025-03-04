const vscode = require('vscode');

function activate(context) {
    let disposable = vscode.commands.registerCommand('aiagent.openInterface', () => {
        const panel = vscode.window.createWebviewPanel(
            'aiAgentInterface',
            'AI Agent Interface',
            vscode.ViewColumn.Two,
            {
                enableScripts: true
            }
        );

        panel.webview.html = getWebviewContent();

        panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'query':
                        // Handle query to backend
                        vscode.window.showInformationMessage(`Query received: ${message.text}`);
                        return;
                }
            },
            undefined,
            context.subscriptions
        );
    });

    context.subscriptions.push(disposable);
}

function getWebviewContent() {
    return `
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>AI Agent Interface</title>
                <style>
                    body {
                        padding: 20px;
                        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    }
                    .container {
                        display: flex;
                        flex-direction: column;
                        gap: 10px;
                    }
                    #queryInput {
                        padding: 10px;
                        border-radius: 4px;
                        border: 1px solid #ccc;
                    }
                    #response {
                        margin-top: 20px;
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        min-height: 100px;
                    }
                    button {
                        padding: 8px 16px;
                        background: #007acc;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    }
                    button:hover {
                        background: #005999;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>AI Agent Query Interface</h2>
                    <input type="text" id="queryInput" placeholder="Enter your query...">
                    <button onclick="sendQuery()">Send Query</button>
                    <div id="response"></div>
                </div>
                <script>
                    const vscode = acquireVsCodeApi();
                    
                    function sendQuery() {
                        const query = document.getElementById('queryInput').value;
                        vscode.postMessage({
                            command: 'query',
                            text: query
                        });
                    }
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
