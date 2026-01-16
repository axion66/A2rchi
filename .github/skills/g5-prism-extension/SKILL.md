---
name: g5-prism-extension
description: Guide for VS Code extension development for Prism. Use when working on Prism extension code, implementing tools, tree views, webviews, or extension APIs.
---

# G5 Prism Extension

This skill guides you through VS Code extension development for the Prism extension.

## When to Use This Skill

- Working on Prism extension code
- Implementing G5 MCP tools
- Creating tree views or webviews
- Adding extension commands
- Debugging extension issues

## Prism Architecture

```
prism/
├── src/
│   ├── extension.ts          # Entry point
│   ├── types.ts              # Shared types
│   ├── chat/                 # Chat participant
│   ├── components/           # Reusable components
│   ├── panels/               # Webview panels
│   ├── providers/            # Tree view providers
│   ├── services/             # Business logic
│   └── test/                 # Tests
├── specs/                    # G5 specs
├── media/                    # Icons, images
└── package.json              # Extension manifest
```

## Extension Lifecycle

### Activation

```typescript
// extension.ts
export async function activate(context: vscode.ExtensionContext) {
  // Initialize services
  const stateService = new StateService();
  const workflowService = new WorkflowService(stateService);
  
  // Register providers
  const workflowTreeProvider = new WorkflowTreeProvider(workflowService);
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('g5.workflows', workflowTreeProvider)
  );
  
  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('g5.newWorkflow', async () => {
      await workflowService.createWorkflow();
      workflowTreeProvider.refresh();
    })
  );
}

export function deactivate() {
  // Cleanup
}
```

### Deactivation

```typescript
export function deactivate() {
  // Dispose resources
  // Save state
  // Close connections
}
```

## Key Patterns

### Services

Encapsulate business logic in services:

```typescript
// services/StateService.ts
export class StateService {
  private db: Database;
  
  async getState(workspacePath: string): Promise<G5State> {
    const statePath = path.join(workspacePath, '.g5', 'state.sqlite');
    // Read and parse state
    return state;
  }
  
  async updateStatus(status: string): Promise<void> {
    // Update state
  }
}
```

### Tree View Providers

```typescript
// providers/WorkflowTreeProvider.ts
export class WorkflowTreeProvider implements vscode.TreeDataProvider<WorkflowItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<WorkflowItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  
  constructor(private workflowService: WorkflowService) {}
  
  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }
  
  getTreeItem(element: WorkflowItem): vscode.TreeItem {
    return element;
  }
  
  async getChildren(element?: WorkflowItem): Promise<WorkflowItem[]> {
    if (!element) {
      // Root level - list workflows
      const workflows = await this.workflowService.listWorkflows();
      return workflows.map(w => new WorkflowItem(w));
    }
    // Child level
    return element.getChildren();
  }
}
```

### Webview Panels

```typescript
// panels/HITLPanel.ts
export class HITLPanel {
  public static currentPanel: HITLPanel | undefined;
  private readonly _panel: vscode.WebviewPanel;
  private _disposables: vscode.Disposable[] = [];
  
  public static createOrShow(extensionUri: vscode.Uri) {
    const column = vscode.ViewColumn.Beside;
    
    if (HITLPanel.currentPanel) {
      HITLPanel.currentPanel._panel.reveal(column);
      return;
    }
    
    const panel = vscode.window.createWebviewPanel(
      'g5HITL',
      'HITL Dashboard',
      column,
      {
        enableScripts: true,
        localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'media')]
      }
    );
    
    HITLPanel.currentPanel = new HITLPanel(panel, extensionUri);
  }
  
  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
    this._panel = panel;
    this._panel.webview.html = this._getHtml(extensionUri);
    
    // Handle messages from webview
    this._panel.webview.onDidReceiveMessage(
      async message => {
        switch (message.type) {
          case 'approve':
            await this._handleApprove(message.decisionId);
            break;
        }
      },
      null,
      this._disposables
    );
    
    // Handle disposal
    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
  }
  
  private _getHtml(extensionUri: vscode.Uri): string {
    const stylesUri = this._panel.webview.asWebviewUri(
      vscode.Uri.joinPath(extensionUri, 'media', 'styles.css')
    );
    
    return `<!DOCTYPE html>
    <html>
    <head>
      <link href="${stylesUri}" rel="stylesheet">
    </head>
    <body>
      <div id="app"></div>
      <script>
        const vscode = acquireVsCodeApi();
        // UI logic
      </script>
    </body>
    </html>`;
  }
  
  public dispose() {
    HITLPanel.currentPanel = undefined;
    this._panel.dispose();
    this._disposables.forEach(d => d.dispose());
  }
}
```

### Commands

```typescript
// Register in extension.ts
context.subscriptions.push(
  vscode.commands.registerCommand('g5.advancePhase', async () => {
    const result = await workflowService.advancePhase();
    if (result.status === 'pending_approval') {
      HITLPanel.createOrShow(context.extensionUri);
    }
  })
);
```

### Configuration

```typescript
// Read settings
const config = vscode.workspace.getConfiguration('g5');
const autofix = config.get<boolean>('autofix', true);
const maxIterations = config.get<number>('maxIterations', 3);

// Watch for changes
context.subscriptions.push(
  vscode.workspace.onDidChangeConfiguration(e => {
    if (e.affectsConfiguration('g5')) {
      // Reload settings
    }
  })
);
```

## G5 Tool Integration

### MCP Client Setup

```typescript
// services/MCPService.ts
import { Client } from '@modelcontextprotocol/sdk/client/index.js';

export class MCPService {
  private client: Client;
  
  async connect() {
    this.client = new Client({
      name: 'prism',
      version: '1.0.0'
    });
    
    const transport = new StdioClientTransport({
      command: 'python',
      args: ['-m', 'src.g5.mcp']
    });
    
    await this.client.connect(transport);
  }
  
  async callTool(name: string, args: Record<string, unknown>) {
    return await this.client.callTool({ name, arguments: args });
  }
}
```

### Tool Calls

```typescript
// Get phase context
const context = await mcpService.callTool('g5_getPhaseContext', {});

// Update status
await mcpService.callTool('g5_updateStatus', {
  status: 'Creating skill files'
});

// Advance phase
const result = await mcpService.callTool('g5_advancePhase', {
  rationale: 'All skills created'
});
```

## Testing

### Unit Tests

```typescript
// test/services/StateService.test.ts
import * as assert from 'assert';
import { StateService } from '../../src/services/StateService';

suite('StateService Tests', () => {
  let service: StateService;
  
  setup(() => {
    service = new StateService();
  });
  
  test('getState returns valid state', async () => {
    const state = await service.getState('/test/workspace');
    assert.ok(state);
    assert.ok(state.current_phase >= 1 && state.current_phase <= 4);
  });
});
```

### Integration Tests

```typescript
// test/integration/workflow.test.ts
import * as vscode from 'vscode';

suite('Workflow Integration Tests', () => {
  test('Create workflow command works', async () => {
    await vscode.commands.executeCommand('g5.newWorkflow', {
      name: 'test-workflow'
    });
    
    // Verify workflow was created
    const workflows = await vscode.commands.executeCommand('g5.listWorkflows');
    assert.ok(workflows.some(w => w.name === 'test-workflow'));
  });
});
```

### Running Tests

```bash
# Compile and run tests
npm run test

# Run specific test file
npm run test -- --grep "StateService"
```

## Package.json Manifest

### Contribution Points

```json
{
  "contributes": {
    "commands": [
      {
        "command": "g5.newWorkflow",
        "title": "New Workflow",
        "category": "G5",
        "icon": "$(add)"
      }
    ],
    "views": {
      "g5": [
        {
          "id": "g5.workflows",
          "name": "Workflows"
        }
      ]
    },
    "viewsContainers": {
      "activitybar": [
        {
          "id": "g5",
          "title": "G5",
          "icon": "media/g5.svg"
        }
      ]
    },
    "menus": {
      "view/title": [
        {
          "command": "g5.newWorkflow",
          "when": "view == g5.workflows",
          "group": "navigation"
        }
      ]
    },
    "configuration": {
      "title": "G5",
      "properties": {
        "g5.autofix": {
          "type": "boolean",
          "default": true,
          "description": "Automatically fix test failures"
        }
      }
    }
  }
}
```

### Activation Events

```json
{
  "activationEvents": [
    "workspaceContains:.g5/state.sqlite",
    "onCommand:g5.newWorkflow",
    "onView:g5.workflows"
  ]
}
```

## Error Handling

```typescript
// Wrap in try-catch with user feedback
try {
  await workflowService.advancePhase();
} catch (error) {
  if (error instanceof GateError) {
    vscode.window.showWarningMessage(`Gate check failed: ${error.message}`);
  } else {
    vscode.window.showErrorMessage(`Error: ${error.message}`);
    console.error(error);
  }
}
```

## Debugging

### Launch Configuration

```json
// .vscode/launch.json
{
  "configurations": [
    {
      "name": "Run Extension",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}/src/prism",
        "${workspaceFolder}/test-workspace"
      ],
      "outFiles": ["${workspaceFolder}/src/prism/out/**/*.js"]
    },
    {
      "name": "Extension Tests",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}/src/prism",
        "--extensionTestsPath=${workspaceFolder}/src/prism/out/test/suite/index"
      ]
    }
  ]
}
```

### Debug Logging

```typescript
// Create output channel
const outputChannel = vscode.window.createOutputChannel('G5');

// Log messages
outputChannel.appendLine(`[INFO] Phase advanced to ${phase}`);
outputChannel.appendLine(`[ERROR] ${error.message}`);

// Show to user
outputChannel.show();
```

## Common Mistakes

1. **Not disposing subscriptions** - Memory leaks
2. **Blocking the extension host** - Use async/await
3. **Missing activation events** - Extension won't activate
4. **Hardcoded paths** - Use `vscode.Uri.joinPath`
5. **Missing error handling** - Silent failures

## Extension Development Checklist

- [ ] Services encapsulate business logic
- [ ] Commands registered in package.json
- [ ] Views declared in contribution points
- [ ] Activation events specified
- [ ] Subscriptions disposed on deactivation
- [ ] Errors shown to user
- [ ] Tests written and passing

## File Structure for New Features

When adding a new feature:

1. **Type definitions** in `types.ts`
2. **Service** in `services/`
3. **Provider** in `providers/` (for views)
4. **Panel** in `panels/` (for webviews)
5. **Commands** registered in `extension.ts`
6. **Spec** in `specs/`
7. **Tests** in `test/`

> 💡 **Related skills**: 
> - [g5-prism-web-design](../g5-prism-web-design/SKILL.md) for UI design
> - [g5-codegen](../g5-codegen/SKILL.md) for implementation patterns
> - [g5-testgen](../g5-testgen/SKILL.md) for writing tests
