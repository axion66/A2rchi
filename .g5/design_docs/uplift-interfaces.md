# Design Doc: Uplift Interfaces Module

## Overview
Extract G5 specs from the `src/interfaces/` module - user-facing interfaces for A2rchi including chat app, grader app, and platform integrations.

## Goals
- Document Flask-based web applications (chat, grader)
- Spec the platform integration wrappers (Piazza, Mattermost)
- Spec the Redmine-Mailbox integration
- Document utility classes and rendering components

## Non-Goals
- Changing any existing functionality
- Adding new interfaces or integrations

## Module Structure

```
src/interfaces/
├── __init__.py
├── mattermost.py           # MattermostAIWrapper, Mattermost
├── piazza.py               # PiazzaAIWrapper, Piazza
├── chat_app/
│   ├── app.py              # ChatWrapper, AnswerRenderer, Flask app
│   ├── utils.py            # collapse_assistant_sequences
│   └── document_utils.py   # File hashing, upload handling
├── grader_app/
│   └── app.py              # GradingWrapper, ImageToTextWrapper, Flask app
└── redmine_mailer_integration/
    ├── mailbox.py          # Mailbox class
    ├── redmine.py          # RedmineAIWrapper, Redmine class
    └── utils/              # Email utilities
```

## Spec Plan

### 1. Chat App (`interfaces/chat-app.spec.md`)
- `AnswerRenderer` - Markdown rendering with code highlighting
- `ChatWrapper` - Main chat functionality wrapper
- `ConversationAccessError` - Custom exception
- Flask routes and endpoints

### 2. Chat App Utilities (`interfaces/chat-utils.spec.md`)
- `collapse_assistant_sequences` - History collapsing
- File hashing utilities (`simple_hash`, `file_hash`)
- Document upload utilities
- Account management functions

### 3. Grader App (`interfaces/grader-app.spec.md`)
- `ImageToTextWrapper` - Image processing wrapper
- `GradingWrapper` - Grading pipeline wrapper
- Flask routes and endpoints

### 4. Platform Integrations (`interfaces/integrations.spec.md`)
- `PiazzaAIWrapper` - Piazza question answering
- `Piazza` - Piazza feed processing
- `MattermostAIWrapper` - Mattermost message handling
- `Mattermost` - Mattermost feed processing

### 5. Redmine-Mailbox (`interfaces/redmine-mailbox.spec.md`)
- `Mailbox` - IMAP mailbox management
- `RedmineAIWrapper` - Redmine ticket answering
- `Redmine` - Redmine API integration

## Success Criteria
- All public classes and methods have specs
- Flask route contracts documented
- Integration authentication flows documented
- Error handling patterns captured
