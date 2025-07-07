import json
import os
import threading
from urllib.parse import urlencode

import pyaudio
from dotenv import load_dotenv
from websocket import ABNF, WebSocketApp

load_dotenv()

# config for api
API_KEY = os.getenv("ALCHEMY_API_KEY")
PARAMS = {
    "sample_rate": 16000,
    "format_turns": True,
    "endpointing": 5
}
WS_URL = "wss://streaming.assemblyai.com/v3/ws?" + urlencode(PARAMS)

# Audio settings
RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = int(0.05 * RATE)  # 50 ms

# Sync primitives
_done = threading.Event()
_result = {"text": ""}


def _on_open(ws):
    def _stream():
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True, frames_per_buffer=CHUNK)
        try:
            while not _done.is_set():
                data = stream.read(CHUNK, exception_on_overflow=False)
                ws.send(data, ABNF.OPCODE_BINARY)
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
    threading.Thread(target=_stream, daemon=True).start()


def _on_message(ws, message):
    obj = json.loads(message)
    if obj.get("type") == "Turn" and obj.get("turn_is_formatted"):
        _result["text"] = obj.get("transcript", "")
        _done.set()
        ws.close()


def _on_error(ws, err):
    print("WebSocket error:", err)
    _done.set()


def _on_close(ws, code, reason):
    _done.set()


def transcribe_user_question(timeout: float = 10.0) -> str:
    _done.clear()
    _result["text"] = ""

    ws = WebSocketApp(
        WS_URL,
        header=[f"Authorization: {API_KEY}"],
        on_open=_on_open,
        on_message=_on_message,
        on_error=_on_error,
        on_close=_on_close,
    )

    # run WS in background
    thread = threading.Thread(target=ws.run_forever, daemon=True)
    thread.start()

    # wait for result or timeout (max 60 seconds to be safe)
    try:
        _done.wait(timeout=min(timeout, 60.0))  # cap timeout to avoid OverflowError
    except OverflowError:
        print("Invalid timeout value. Using 10 seconds fallback.")
        _done.wait(timeout=10.0)

    return _result["text"] or "No speech detected"
