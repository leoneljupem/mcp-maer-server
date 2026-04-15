# WhatsApp Business API Integration for MAER 4.0

This folder contains webhook handlers and automated responder logic for WhatsApp Business API integration with MAER.

## Overview

The WhatsApp integration enables MAER to:

- Receive procedural status updates via WhatsApp messages
- Send automated notifications about procedure milestones
- Handle user queries through conversational bot responder
- Maintain message history and logs

## Structure

- **webhooks/** — HTTP endpoint handlers for incoming messages
- **responders/** — Chatbot logic and automated reply rules
- **templates/** — WhatsApp message templates (multipart, buttons, etc)
- **logs/** — Message history and delivery tracking

## Message Flow

```
WhatsApp Business API
        ↓
  webhook handler
        ↓
  message parser & router
        ↓
  responder bot or MAER action
        ↓
  API response & logging
```

## Supported Interactions

- **Status queries** — "¿Qué etapa va de mi trámite?" (What stage is my procedure at?)
- **Document submission** — File attachments and confirmations
- **Notifications** — Automated alerts on procedure stage changes
- **Help/Support** — Direct user queries to support queue

## Setup

1. Register business account with WhatsApp Business API provider
2. Configure webhook URL in MAER backend settings
3. Add message templates for procedure notifications
4. Test webhook connectivity and message flow

## Configuration

See `/maer_backend/config/whatsapp_config.json` for API credentials and webhook configuration.
