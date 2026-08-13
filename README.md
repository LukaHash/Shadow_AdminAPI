# Shadow Admin

> **Local Windows remote-control relay** — FastAPI service that turns a PC into a controllable host: keyboard/mouse injection, DXGI screen capture.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![WebSockets](https://img.shields.io/badge/WebSockets-JSON%20%2B%20PCM-7B61FF.svg)](https://fastapi.tiangolo.com/advanced/websockets/)
[![DXGI](https://img.shields.io/badge/Capture-DXGI%20%2B%20dxcam-orange.svg)](https://github.com/ra1nty/DXcam)
[![OpenCV](https://img.shields.io/badge/Video-OpenCV%20MJPEG-5C3EE8.svg)](https://opencv.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Local%20LAN%20tool-lightgrey.svg)]()

> **Not a public remote-desktop product.** This is a **LAN-only** personal/portfolio service. Do **not** expose it to the internet.

---

## Table of Contents

- [About](#about)
- [Security warning](#security-warning)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API](#api)
- [Command protocol](#command-protocol)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## About

**Shadow Admin** is a local FastAPI relay that lets you control a Windows PC from a phone or another machine on the same Wi-Fi network.

It is **not** a clone of Parsec / Moonlight / AnyDesk. Those products use GPU encoders and UDP/WebRTC. This project is a **backend systems** exercise: how to expose OS input, screen pixels, and speaker audio through HTTP and WebSockets, with explicit validation and a shared token.

The service has four independent channels:

| Channel | Transport | Payload |
|---------|-----------|---------|
| Commands (REST) | `POST /execute` | JSON `CommandRequest` |
| Commands (low-latency) | `WS /ws/execute` | JSON `CommandRequest` |
| Video | `GET /stream` | MJPEG (`multipart/x-mixed-replace`) |
| Audio | `WS /ws/audio` | raw PCM `int16` mono @ 48 kHz |

A browser demo client (`client.html`) is included so the backend can be used from a phone. The **learning and portfolio focus is the Python backend**, not the UI.

> **Why this project exists:** I wanted a real system on my own machine — not another CRUD tutorial. The interesting parts are protocol choice (HTTP vs WebSocket), non-blocking capture, DXGI/WASAPI interop, and an allowlisted input executor that will not blindly run arbitrary OS actions.

---

## Security warning

This process can **press keys, move the mouse, and stream your screen + system audio**.

- Bind only to a trusted LAN (`0.0.0.0:8000` is for Wi-Fi access from your phone, not for the public internet).
- Protect every route with `API_SECRET_KEY`.
- Never commit `.env`.
- Do not put this behind a port-forward, ngrok, or a public VPS unless you add TLS, real auth, and a threat model.
- Query-string tokens (`?token=...`) are used for `<img>` / WebSocket URLs because browsers cannot set custom headers there. Treat the token like a password and rotate it.

Unauthorized WebSocket clients are rejected with close code `1008`. HTTP clients get `401`.

---

## Features

| Feature | What it actually does |
|---------|------------------------|
| **REST command API** | `POST /execute` with Pydantic validation + `X-API-Key` |
| **WebSocket command channel** | Persistent JSON socket for key-down / mouse-move without HTTP overhead |
| **Allowlisted executor** | Only `press`, `type`, `up`, `down`, `click`, `move`, `scroll`, `mouse_up`, `mouse_down`, `hotkey` |
| **DirectInput injection** | `pydirectinput` for games / fullscreen apps; scan-code friendly vs layout-dependent `e.key` |
| **Normalized pointer** | Client sends `x,y` in `0..1`; server maps to current screen size |
| **DXGI screen capture** | `dxcam` reads frames from GPU desktop duplication (~55–67 FPS observed at reduced resolution) |
| **MJPEG stream** | OpenCV JPEG encode + `StreamingResponse` with `multipart/x-mixed-replace; boundary=frame` |
| **WASAPI loopback audio** | `soundcard` captures default speaker output, not a microphone |
| **Non-blocking audio read** | `asyncio.to_thread(rec.record, ...)` so capture does not freeze the event loop |
| **PCM over WebSocket** | `float32 [-1, 1]` → `int16` bytes the browser Web Audio API can schedule |
| **Token gate** | Shared secret from `.env`; header for HTTP, query param for WS / MJPEG |
| **Phone demo UI** | Fullscreen viewer, virtual keyboard (`e.code` map), mouse / loupe / scroll, audio toggle |

---

## Tech Stack

| Layer | Technology | Why this, not something else |
|-------|------------|------------------------------|
| **API** | **FastAPI + Uvicorn** | Native WebSockets, `StreamingResponse`, DI, OpenAPI for the REST part |
| **Validation** | **Pydantic v2** | Rejects malformed command payloads before they reach the OS |
| **Config** | **python-dotenv** | Secret stays out of source |
| **Keyboard / mouse** | **pydirectinput** | DirectInput path — works in many games where `SendInput` via pyautogui does not |
| **Scroll / hotkey** | **pyautogui** | `pydirectinput` has no reliable scroll/hotkey equivalent here |
| **Screen capture** | **dxcam (DXGI)** | Desktop Duplication API; `get_latest_frame()` instead of printing the whole desktop with PIL |
| **Encode** | **OpenCV** | Fast `cvtColor` + `resize` + `imencode('.jpg')` |
| **Audio capture** | **soundcard** | WASAPI loopback of the default render device |
| **Numeric / PCM** | **NumPy** | Vectorized `float32 → int16` conversion |
| **Demo client** | **HTML + JS** | Zero install on the phone; not the portfolio centerpiece |

Windows-only by design: DXGI and WASAPI loopback are not portable.

---

## Architecture

```text
  Phone / laptop browser
           |
           |  ws://host/ws/execute?token=...     JSON commands
           |  POST /execute  +  X-API-Key        same commands, HTTP
           |  GET  /stream?token=...             MJPEG frames
           |  ws://host/ws/audio?token=...       PCM int16 chunks
           v
     FastAPI  (app/app.py)
           |
     +-----+------+------------------+
     |            |                  |
  security     executor           stream / audio
  API key      allowcommand()     dxcam + cv2
               pydirectinput      soundcard loopback
               pyautogui          asyncio.to_thread
```

### 1. Control path

REST exists for debugging (Swagger, curl, Postman).  
WebSocket exists because a phone keyboard generates **dozens of events per second** (`down` / `up` / `move`). Opening a new HTTP request for each one adds latency and connection churn.

Flow:

1. Client sends JSON `{ "action", "parameter", "x", "y", "button" }`.
2. `CommandRequest` validates types.
3. `allowcommand()` checks the action against an explicit dict (no `eval`, no shell).
4. Keys are checked against `pydirectinput.KEYBOARD_MAPPING`.
5. Pointer actions convert normalized `x,y` to pixels with `pydirectinput.size()`.

### 2. Video path

1. `dxcam.create()` + `camera.start(...)` — DXGI Desktop Duplication.
2. `get_latest_frame()` — if the compositor has not produced a new frame, skip (`None`).
3. RGB → BGR (`cv2.cvtColor`) because OpenCV expects BGR.
4. Downscale (`cv2.resize`, nearest-neighbor) to cut encode cost and Wi-Fi bandwidth.
5. JPEG encode (`cv2.imencode`).
6. Yield a multipart part:

```http
--frame
Content-Type: image/jpeg

<jpeg bytes>
```

`StreamingResponse` sets `media_type="multipart/x-mixed-replace; boundary=frame"`. The browser `<img>` replaces the previous picture when the next part arrives. This is **MJPEG**, not a video codec.

Swagger `/docs` will spin forever on `/stream` — the response never ends. Open the URL in a browser or use the demo client.

### 3. Audio path

1. Resolve `soundcard.default_speaker()`.
2. Find the matching loopback device in `all_microphones(include_loopback=True)`.
3. Record `1024` frames @ `48000` Hz, mono.
4. `data` is `float32` in roughly `[-1.0, 1.0]`.
5. `(data * 32767).astype(np.int16).tobytes()` — classic PCM the Web Audio API understands.
6. `await websocket.send_bytes(...)`.

`rec.record()` is blocking, so it runs in `asyncio.to_thread(...)`. Without that, one audio client would stall command WebSockets and HTTP on the same event loop.

### 4. Auth split

| Surface | How the token is passed | Why |
|---------|-------------------------|-----|
| `POST /execute`, `/http-header-auth` | Header `X-API-Key` via `Depends(get_user_auth_token)` | Correct HTTP style |
| `/ws/execute`, `/ws/audio`, `/stream` | Query `?token=` | Browser `WebSocket` and `<img src>` cannot set custom headers |

---

## Requirements

- **Windows 10/11** (DXGI + WASAPI). Linux/macOS will not run capture/input as written.
- **Python 3.11+**
- A GPU/display stack that DXGI Desktop Duplication can attach to (normal desktop session; not a raw headless service without a desktop).
- Phone or second device on the **same LAN**
- Optional: Bluetooth keyboard — physical keys are mapped via JS `e.code`, so the host layout should stay English for letter injection

This project is **not Dockerized**. Screen capture, DirectInput, and WASAPI loopback need a real Windows desktop session. Putting that in a container is the wrong abstraction.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/<your-username>/Shadow-Admin.git
cd Shadow-Admin

# 2. Virtualenv
python -m venv .venv
.venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Secret
copy .env.example .env
# set API_SECRET_KEY to a long random string

# 5. Run (listens on all interfaces so a phone can connect)
python Fast_api.py
# equivalent:
# uvicorn app.app:app --host 0.0.0.0 --port 8000 --reload
```

Then, on the phone (same Wi-Fi):

1. Open `http://<pc-lan-ip>:8000/`
2. Paste the same `API_SECRET_KEY`
3. Connect — video, audio, keyboard, and mouse use that host + token

Health check:

```bash
curl http://127.0.0.1:8000/ping
# {"status":"online","service":"Shadow_Admin"}
```

REST example:

```bash
curl -X POST http://127.0.0.1:8000/execute ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: YOUR_SECRET" ^
  -d "{\"action\":\"press\",\"parameter\":\"enter\"}"
```

---

## Configuration

`.env`:

```env
API_SECRET_KEY=change-me-to-a-long-random-value
```

`.env.example` should contain only the key name, never a real secret.

| Variable | Required | Meaning |
|----------|----------|---------|
| `API_SECRET_KEY` | yes | Shared token for HTTP header and WS/stream query param |

Runtime constants (code, not env, today):

| Constant | Value | Where |
|----------|-------|--------|
| Bind host / port | `0.0.0.0:8000` | `Fast_api.py` |
| Audio sample rate | `48000` | `app.py` `/ws/audio` |
| Audio chunk | `1024` frames | `app.py` `/ws/audio` |
| Capture target FPS | `120` (producer) | `stream.py` |
| JPEG quality | `80` | `stream.py` |
| Resize factor | `0.75` | `stream.py` |
| `pydirectinput.PAUSE` | `0.00001` | `executor.py` |

---

## API

Interactive REST docs: `http://localhost:8000/docs`  
WebSockets and `/stream` are **not** testable in Swagger. Use the demo page, a browser, or a WS client.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | — | Serves `client.html` |
| `GET` | `/ping` | — | Liveness: service name + `online` |
| `GET` | `/http-header-auth` | `X-API-Key` | Token check helper |
| `POST` | `/execute` | `X-API-Key` | Run one command, return JSON |
| `WS` | `/ws/execute?token=` | query | Command loop (`receive_json` → executor → `send_json`) |
| `GET` | `/stream?token=` | query | Infinite MJPEG |
| `WS` | `/ws/audio?token=` | query | Infinite PCM binary frames |

### Command body

```json
{
  "action": "click",
  "parameter": null,
  "x": 0.5,
  "y": 0.5,
  "button": "left"
}
```

| Field | Type | Used by |
|-------|------|---------|
| `action` | `str` | all |
| `parameter` | `str \| float \| null` | `press`, `type`, `up`, `down`, `scroll`, `hotkey` |
| `x`, `y` | `float \| null` (`0..1`) | `click`, `move`, `mouse_down`, `mouse_up` |
| `button` | `str \| null` | `click`, `mouse_down`, `mouse_up` (default `"left"`) |

Success (REST):

```json
{ "status": "success", "message": "..." }
```

Unknown / invalid command → HTTP `400` (REST) or `{ "status": "error", "message": "..." }` (WS).

---

## Command protocol

| `action` | `parameter` | `x,y` | Effect |
|----------|-------------|-------|--------|
| `press` | key name | — | Tap a key (`pydirectinput.press`) |
| `down` / `up` | key name | — | Hold / release (needed for games and modifiers) |
| `type` | text | — | Type a string with a short interval |
| `hotkey` | `"ctrl+c"` | — | Chord via `pyautogui.hotkey` |
| `move` | — | yes | Move cursor to normalized point |
| `click` | — | yes | Click at point |
| `mouse_down` / `mouse_up` | — | yes | Drag building blocks |
| `scroll` | delta (`int`) | — | Wheel (`pyautogui.scroll`) |

Key names must exist in `pydirectinput.KEYBOARD_MAPPING` (`enter`, `esc`, `w`, `left`, …).  
The demo client maps `KeyboardEvent.code` (`KeyW`) → these names so a Russian layout on the phone does not send `"ц"` instead of `"w"`.

---

## Project Structure

```text
Shadow-Admin/
├── app/
│   ├── __init__.py
│   ├── app.py              # FastAPI routes: REST, WS commands, MJPEG, audio WS
│   ├── executor.py         # allowlisted OS input (pydirectinput / pyautogui)
│   ├── schemas.py          # CommandRequest / CommandResponse
│   ├── security.py         # X-API-Key dependency
│   └── stream.py           # dxcam capture + JPEG multipart generator
├── client.html             # Demo control surface (browser / phone)
├── Fast_api.py             # Uvicorn entrypoint, host 0.0.0.0
├── requirements.txt
├── .env.example
├── .gitignore              # must include .env, .venv, __pycache__
└── README.md
```

Layering:

- **`app.py`** — transport only (accept, auth, serialize).
- **`executor.py`** — the only module allowed to touch the OS input stack.
- **`stream.py`** — the only module allowed to touch DXGI.
- **`security.py`** — HTTP token check, reused via `Depends`.
- **`schemas.py`** — contract between client and executor.

---

## Limitations

Known, accepted, or still open:

- **LAN only.** Token auth is a shared secret, not a user system.
- **One DXGI producer.** `camera` / `running` are process globals; two `/stream` clients can race on start/stop.
- **MJPEG over TCP.** Typical result on a home Wi-Fi: playable video around 50–70 FPS at reduced resolution, not a 240 FPS game stream.
- **Audio is raw PCM.** No Opus, no clock recovery beyond a small client buffer (`~150 ms` start latency in the demo page).
- **`hotkey` / `scroll` still go through pyautogui.** Mixed input stacks can feel slightly different from `pydirectinput` keys.
- **Unicode typing is limited.** `pydirectinput.write` is not a full IME.
- **Browser steals some keys.** `Escape` often exits fullscreen and never reaches the host.
- **Query tokens leak into logs / history** more easily than headers. Fine on a home LAN; wrong on a shared network.
- **Reload + capture.** Uvicorn `--reload` plus DXGI/WASAPI native handles can leave a stuck camera after a crash; restart the process.

---

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| Phone cannot open the page | PC firewall, same Wi-Fi, server bound to `0.0.0.0` not `127.0.0.1` |
| `401` / WS close `1008` | `.env` loaded? Client token === `API_SECRET_KEY`? No extra spaces |
| Video is black / `/stream` dies | DXGI failed: run in a real desktop session; close other capture tools; restart process |
| `/docs` hangs on `/stream` | Expected — infinite stream. Use the demo `<img>` or a raw browser tab |
| Audio WS closes `1011` | No loopback device with the same name as `default_speaker()` |
| Audio present but choppy | Wi-Fi; keep the demo page in foreground; do not starve the event loop with heavy JPEG |
| Keys type the wrong letters | Host Windows layout should be EN; client must send `e.code` mappings, not `e.key` |
| Keys work in Notepad but not in a game | That is why `pydirectinput` is used; some anti-cheats still block injection |
| Clicks miss the target | Client must send normalized `0..1`, not CSS pixels; check letterboxing in fullscreen |
| High CPU | Lower JPEG quality / resize factor in `stream.py`; do not run 1.0 scale + quality 95 |

---

## License

Distributed under the **MIT License**. See `LICENSE` for details.

Use it on machines you own. Streaming someone else's desktop without consent is not a feature :]

---

