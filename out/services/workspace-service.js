"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.WorkspaceService = void 0;
const vscode = __importStar(require("vscode"));
class WorkspaceService {
    constructor() {
        // Watch for file changes in workspace
        this.fileWatcher = vscode.workspace.createFileSystemWatcher('**/*.{js,py,ts,json,html,css}', false, // Don't ignore creates
        false, // Don't ignore changes
        false // Don't ignore deletes
        );
        // Setup file watchers
        this.setupWatchers();
    }
    static getInstance() {
        if (!WorkspaceService.instance) {
            WorkspaceService.instance = new WorkspaceService();
        }
        return WorkspaceService.instance;
    }
    setupWatchers() {
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
    async handleFileChange(document) {
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
    async getOpenFiles() {
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
    dispose() {
        this.fileWatcher.dispose();
    }
}
exports.WorkspaceService = WorkspaceService;
//# sourceMappingURL=workspace-service.js.map