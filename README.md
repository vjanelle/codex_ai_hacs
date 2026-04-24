# Codex AI for Home Assistant

Experimental Home Assistant custom integration that uses Codex-style ChatGPT
device authorization instead of an OpenAI API key.

The integration talks to the Codex ChatGPT backend with the OpenAI Python SDK:

- Base URL: `https://chatgpt.com/backend-api/codex`
- Auth: ChatGPT OAuth access token from device auth
- Account routing: `ChatGPT-Account-ID` header

## Features

- AI Tasks generate-data provider for `/config/ai-tasks`
- Assist conversation agent
- Image input attachments for AI Tasks
- Speech-to-text entity
- Text-to-speech entity
- Token refresh with one retry after authentication failure

## Not Included Yet

- Realtime voice conversation
- Image generation
- Full Home Assistant control/tool calling from Assist
- Extensive Home Assistant runtime tests

## Install With HACS

1. Open HACS.
2. Open the menu and choose **Custom repositories**.
3. Add repository:
   `https://github.com/vjanelle/codex_ai_hacs`
4. Select category: **Integration**.
5. Install **Codex AI**.
6. Restart Home Assistant.
7. Go to **Settings > Devices & services > Add integration**.
8. Search for **Codex AI**.

## Setup

During setup, Home Assistant starts a ChatGPT device authorization flow:

1. Open the displayed OpenAI verification URL.
2. Enter the displayed one-time code.
3. Submit the Home Assistant setup form after authorization completes.

No OpenAI API key is required.

## Defaults

- Main model: `gpt-5.5`
- Reasoning effort: `medium`
- STT model: `gpt-4o-mini-transcribe`
- TTS model: `gpt-4o-mini-tts`
- TTS voice: `marin`

These can be changed from the integration options.

## Status And Caveats

This is experimental and uses Codex's ChatGPT backend auth pattern, not the
standard OpenAI API-key path.

AI Tasks and Assist text use the Responses API path. STT/TTS use OpenAI SDK
audio endpoints against the Codex backend; those paths still need real
Home Assistant runtime validation.

## Development

Run local helper tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```
