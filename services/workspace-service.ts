import * as vscode from 'vscode';

export class WorkspaceService {
    private static instance: WorkspaceService;
    private fileWatcher: vscode.FileSystemWatcher;

    private constructor() {
        // Watch for file changes in workspace
        this.fileWatcher = vscode.workspace.createFileSystemWatcher(
            '**/*.{js,py,ts,json,html,css}',
            false, // Don't ignore creates
            false, // Don't ignore changes
            false  // Don't ignore deletes
        );

        // Setup file watchers
        this.setupWatchers();
    }

    public static getInstance(): WorkspaceService {
        if (!WorkspaceService.instance) {
            WorkspaceService.instance = new WorkspaceService();
        }
        return WorkspaceService.instance;
    }

    private setupWatchers() {
        // Watch for file changes
        this.fileWatcher.onDidChange(async (uri) => {
            const document = await vscode.workspace.openTextDocument(uri);
            this.handleFileChange(document);
        });

        // Watch for new files
        this.fileWatcher.onDidCreate(async (uri) => {
            const document = await vscode.workspace.openTextDocument(uri);
            this.handleFileChange(document);
        });
    }

    private async handleFileChange(document: vscode.TextDocument) {
        // Only process if it's a text document
        if (document.uri.scheme === 'file') {
            return {
                filePath: document.uri.fsPath,
                content: document.getText(),
                language: document.languageId
            };
        }
        return null;
    }

    public async getOpenFiles(): Promise<any[]> {
        const openFiles = [];
        
        // Get all open text documents
        for (const document of vscode.workspace.textDocuments) {
            if (document.uri.scheme === 'file') {
                openFiles.push({
                    filePath: document.uri.fsPath,
                    content: document.getText(),
                    language: document.languageId
                });
            }
        }
        
        return openFiles;
    }

    public dispose() {
        this.fileWatcher.dispose();
    }
} 