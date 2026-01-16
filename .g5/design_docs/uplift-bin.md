# Design Doc: Uplift Bin Module

## Overview
Extract G5 specs from the `src/bin/` module - service entry point scripts for running A2rchi services.

## Goals
- Document all service entry points
- Spec the common service initialization patterns
- Document the benchmarking service

## Non-Goals
- Changing any existing functionality
- Adding new services

## Module Structure

```
src/bin/
├── __init__.py
├── service_chat.py          # Chat Flask app entry point
├── service_grader.py        # Grader Flask app entry point
├── service_piazza.py        # Piazza polling service
├── service_mattermost.py    # Mattermost polling service
├── service_mailbox.py       # IMAP mailbox polling service
├── service_redmine.py       # Redmine polling service
├── service_benchmark.py     # Benchmarking/evaluation service
├── service_create_account.py # Account creation utility
└── service_uploader.py      # Document uploader service
```

## Spec Plan

### 1. Services (`bin/services.spec.md`)
All service entry points follow common patterns:
- Load secrets into environment
- Setup logging
- Initialize service class
- Run polling loop or start Flask app

## Success Criteria
- All service entry points documented
- Common initialization patterns captured
- Required secrets and config documented
