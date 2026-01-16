---
name: g5-prism-web-design
description: Guide for web UI design for Prism extension. Use when designing UI for Prism panels, using Figma for mockups, creating webviews, or working on frontend components.
---

# G5 Prism Web Design

This skill guides you through web UI design for the Prism VS Code extension.

## When to Use This Skill

- Designing Prism UI panels
- Creating Figma mockups
- Building webviews
- Working on dashboard components
- Styling Prism interfaces

## Prism UI Architecture

```
Prism Extension
├── Sidebar Panels
│   ├── Workflow Tree View
│   ├── Phase Indicator
│   └── Actions Panel
├── Webview Panels
│   ├── HITL Dashboard
│   ├── Views Panel
│   └── Spec Editor
├── Quick Picks
│   └── Phase transition dialogs
└── Status Bar
    └── Workflow status
```

## Design Workflow

### 1. Figma First

Before coding, design in Figma:

1. **Create wireframe** - Basic layout
2. **Add VS Code theming** - Use VS Code color tokens
3. **Review with stakeholders** - Get feedback
4. **Export assets** - Icons, images

### Figma Setup for VS Code

```
Frame sizes:
- Sidebar panel: 300px width (flexible height)
- Webview panel: 800x600px (default)
- Full editor: 1200x800px

Colors: Use VS Code theme variables (not hardcoded)
- Background: --vscode-editor-background
- Text: --vscode-editor-foreground
- Accent: --vscode-button-background
```

### 2. Component Design

Design components that match VS Code:

```html
<!-- Button matching VS Code style -->
<button class="vscode-button">
  <span class="codicon codicon-play"></span>
  Run Tests
</button>

<!-- Input matching VS Code -->
<input class="vscode-input" placeholder="Search..." />

<!-- Panel with VS Code styling -->
<div class="vscode-panel">
  <h3 class="vscode-panel-title">Workflow Status</h3>
  <div class="vscode-panel-content">
    ...
  </div>
</div>
```

### 3. Export to Webview

Figma → HTML/CSS → Webview

## VS Code Design System

### Theme Variables

Always use CSS variables for colors:

```css
.panel {
  background-color: var(--vscode-editor-background);
  color: var(--vscode-editor-foreground);
  border-color: var(--vscode-panel-border);
}

.button {
  background-color: var(--vscode-button-background);
  color: var(--vscode-button-foreground);
}

.button:hover {
  background-color: var(--vscode-button-hoverBackground);
}

.error {
  color: var(--vscode-errorForeground);
  background-color: var(--vscode-inputValidation-errorBackground);
}

.warning {
  color: var(--vscode-editorWarning-foreground);
}

.success {
  color: var(--vscode-terminal-ansiGreen);
}
```

### Common Theme Variables

| Variable | Use Case |
|----------|----------|
| `--vscode-editor-background` | Panel backgrounds |
| `--vscode-editor-foreground` | Text |
| `--vscode-button-background` | Primary buttons |
| `--vscode-button-secondaryBackground` | Secondary buttons |
| `--vscode-input-background` | Input fields |
| `--vscode-focusBorder` | Focus states |
| `--vscode-list-activeSelectionBackground` | Selected items |
| `--vscode-badge-background` | Badges/counters |

### Codicons

Use VS Code's built-in icons:

```html
<!-- Include codicons CSS -->
<link rel="stylesheet" href="${codiconsUri}">

<!-- Use icons -->
<span class="codicon codicon-check"></span>      <!-- Checkmark -->
<span class="codicon codicon-error"></span>      <!-- Error -->
<span class="codicon codicon-warning"></span>    <!-- Warning -->
<span class="codicon codicon-play"></span>       <!-- Play -->
<span class="codicon codicon-debug-start"></span><!-- Debug -->
<span class="codicon codicon-folder"></span>     <!-- Folder -->
<span class="codicon codicon-file"></span>       <!-- File -->
<span class="codicon codicon-sync"></span>       <!-- Sync/refresh -->
```

[Full icon list](https://microsoft.github.io/vscode-codicons/dist/codicon.html)

## Prism Components

### Phase Indicator

```html
<div class="phase-indicator">
  <div class="phase phase-complete">
    <span class="phase-number">1</span>
    <span class="phase-name">Intent</span>
  </div>
  <div class="phase phase-current">
    <span class="phase-number">2</span>
    <span class="phase-name">Spec</span>
  </div>
  <div class="phase phase-pending">
    <span class="phase-number">3</span>
    <span class="phase-name">Code</span>
  </div>
  <div class="phase phase-pending">
    <span class="phase-number">4</span>
    <span class="phase-name">Verify</span>
  </div>
</div>
```

```css
.phase-indicator {
  display: flex;
  gap: 8px;
}

.phase {
  padding: 8px 12px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.phase-complete {
  background: var(--vscode-terminal-ansiGreen);
  opacity: 0.7;
}

.phase-current {
  background: var(--vscode-button-background);
  color: var(--vscode-button-foreground);
}

.phase-pending {
  background: var(--vscode-input-background);
  opacity: 0.5;
}
```

### HITL Decision Card

```html
<div class="hitl-card">
  <div class="hitl-header">
    <span class="codicon codicon-bell"></span>
    <span class="hitl-title">Approval Required</span>
  </div>
  <div class="hitl-body">
    <p class="hitl-description">Advance to Phase 3 (Code)?</p>
    <p class="hitl-rationale">Design doc complete with 5 specs identified</p>
  </div>
  <div class="hitl-actions">
    <button class="vscode-button primary">
      <span class="codicon codicon-check"></span> Approve
    </button>
    <button class="vscode-button secondary">
      <span class="codicon codicon-x"></span> Reject
    </button>
  </div>
</div>
```

### Workflow Tree Item

```html
<div class="tree-item tree-item-expanded">
  <span class="tree-icon codicon codicon-chevron-down"></span>
  <span class="tree-icon codicon codicon-folder"></span>
  <span class="tree-label">g5-agent-skills</span>
  <span class="tree-badge">Phase 3</span>
</div>
```

## Webview Structure

### Basic Webview HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" 
        content="default-src 'none'; style-src ${cspSource}; script-src ${cspSource};">
  <link href="${stylesUri}" rel="stylesheet">
  <link href="${codiconsUri}" rel="stylesheet">
  <title>Prism Panel</title>
</head>
<body>
  <div id="app">
    <!-- Content here -->
  </div>
  <script src="${scriptUri}"></script>
</body>
</html>
```

### Message Passing

```typescript
// In webview
const vscode = acquireVsCodeApi();

// Send message to extension
vscode.postMessage({
  type: 'approve',
  decisionId: 'hitl_123'
});

// Receive message from extension
window.addEventListener('message', event => {
  const message = event.data;
  switch (message.type) {
    case 'update':
      updateUI(message.data);
      break;
  }
});
```

## Accessibility

### Keyboard Navigation

```css
/* Visible focus indicators */
:focus {
  outline: 2px solid var(--vscode-focusBorder);
  outline-offset: 2px;
}

/* Skip to main content */
.skip-link {
  position: absolute;
  top: -100px;
}
.skip-link:focus {
  top: 0;
}
```

### ARIA Labels

```html
<button aria-label="Approve phase transition">
  <span class="codicon codicon-check"></span>
</button>

<div role="status" aria-live="polite">
  Phase 2 complete
</div>
```

### Color Contrast

Use VS Code theme variables - they're designed for accessibility.

## Responsive Design

```css
/* Sidebar panel (narrow) */
@media (max-width: 300px) {
  .phase-indicator {
    flex-direction: column;
  }
}

/* Full editor panel */
@media (min-width: 600px) {
  .dashboard {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
```

## Common Mistakes

1. **Hardcoded colors** - Always use theme variables
2. **Missing dark mode** - Theme variables handle this
3. **No focus styles** - Accessibility requirement
4. **Custom fonts** - Use VS Code's default fonts
5. **Ignoring CSP** - Webviews have Content Security Policy

## Design Checklist

- [ ] Figma mockup created
- [ ] Uses VS Code theme variables
- [ ] Uses codicons for icons
- [ ] Keyboard accessible
- [ ] Works in light and dark themes
- [ ] Responsive to panel size
- [ ] CSP-compliant
- [ ] Message passing implemented

> 💡 **Related skills**: 
> - [g5-prism-extension](../g5-prism-extension/SKILL.md) for implementation
> - [g5-viewgen](../g5-viewgen/SKILL.md) for views panel design
