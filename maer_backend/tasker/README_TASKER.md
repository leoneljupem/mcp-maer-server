# Tasker Integration for MAER 4.0

This folder contains Tasker profiles and AutoRemote integration configuration for MAER.

## Overview

**Tasker** is an Android automation tool that enables device-level task automation, context-aware triggers, and system integration. MAER integrates with Tasker to:

- Receive push notifications for procedural reminders
- Trigger automatic actions based on location, time, or system events
- Sync data between MAER web UI and Android devices
- Execute AutoRemote commands for inter-device communication

## Structure

- **profiles/** — Tasker profile configurations
- **tasks/** — Custom task definitions
- **autoremote/** — AutoRemote command mappings and handlers
- **exports/** — Tasker XML exports for backup and sharing

## AutoRemote Bridge

The AutoRemote integration allows MAER to send commands to Tasker across multiple devices:

```
MAER Web UI → AutoRemote API → Tasker Device → Device Actions
```

Supported commands:
- `reminder:*` — Display procedural reminder notifications
- `sync:*` — Trigger data synchronization
- `action:*` — Execute custom automation sequences

## Setup

1. Install Tasker and AutoRemote on target Android device
2. Configure AutoRemote API credentials in MAER backend
3. Import profile XML files into Tasker
4. Enable background service for notification handling

## Documentation

See `/maer_backend/config/tasker_config.json` for detailed configuration.
