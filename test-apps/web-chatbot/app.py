#!/usr/bin/env python3
"""Web chatbot with local UI. Defaults to local Ollama llama3.2.
Exposes POST /chat {"message": "..."} -> {"response": "..."} for testbed integration.
"""

import argparse
import asyncio
import os
import sys
import textwrap

import httpx
import litellm
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

load_dotenv()

DEFAULT_MODEL = "ollama/llama3.2"
DEFAULT_SYSTEM = "You are a helpful assistant."

OLLAMA_INSTALL_HELP = textwrap.dedent("""\
    Ollama with llama3.2 is not reachable. Either:

      1. Install Ollama and pull the model:

           curl -fsSL https://ollama.ai/install.sh | sh
           ollama serve          # start the server (skip if already running)
           ollama pull llama3.2  # download the model (~2 GB)

      2. Or specify a different model with --model:

           uv run python app.py --model openai/gpt-4.1-mini --api-key sk-...
           uv run python app.py --model groq/llama-3.3-70b-versatile --api-key gsk_...""")

MODEL = DEFAULT_MODEL
SYSTEM_PROMPT = DEFAULT_SYSTEM
API_KEY: str | None = None

app = FastAPI(title="Web Chatbot")
_conversation_lock = asyncio.Lock()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


INDEX_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Web Chatbot</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #0f172a; color: #e2e8f0; height: 100vh; display: flex; flex-direction: column; }
  header { padding: 1rem 1.5rem; border-bottom: 1px solid #1e293b; display: flex;
           align-items: center; justify-content: space-between; }
  header h1 { font-size: 1.1rem; font-weight: 600; color: #94a3b8; }
  #model-badge { font-size: 0.8rem; color: #64748b; font-family: monospace; }
  #chat { flex: 1; overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
  .msg { max-width: 75%; padding: 0.75rem 1rem; border-radius: 0.75rem; line-height: 1.5;
         font-size: 0.95rem; white-space: pre-wrap; word-wrap: break-word; }
  .user { align-self: flex-end; background: #1d4ed8; color: #fff; border-bottom-right-radius: 0.2rem; }
  .bot { align-self: flex-start; background: #1e293b; color: #e2e8f0; border-bottom-left-radius: 0.2rem; }
  .bot.error { background: #7f1d1d; color: #fca5a5; }
  #input-row { padding: 1rem 1.5rem; border-top: 1px solid #1e293b; display: flex; gap: 0.75rem; }
  #input-row input { flex: 1; padding: 0.75rem 1rem; border-radius: 0.5rem; border: 1px solid #334155;
                     background: #1e293b; color: #e2e8f0; font-size: 0.95rem; outline: none; }
  #input-row input:focus { border-color: #3b82f6; }
  #input-row button { padding: 0.75rem 1.5rem; border-radius: 0.5rem; border: none;
                      background: #2563eb; color: #fff; font-weight: 600; cursor: pointer; font-size: 0.95rem; }
  #input-row button:disabled { opacity: 0.5; cursor: not-allowed; }
  #input-row button:hover:not(:disabled) { background: #1d4ed8; }
</style>
</head>
<body>
<header>
  <h1>Web Chatbot</h1>
  <span id="model-badge">MODEL</span>
</header>
<div id="chat"></div>
<div id="input-row">
  <input id="msg" type="text" placeholder="Type a message..." autocomplete="off">
  <button id="send">Send</button>
</div>
<script>
const chat = document.getElementById("chat");
const msg = document.getElementById("msg");
const send = document.getElementById("send");

fetch("/info").then(r => r.json()).then(d => {
  document.getElementById("model-badge").textContent = d.model;
});

function addMsg(text, cls) {
  const div = document.createElement("div");
  div.className = "msg " + cls;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

async function doSend() {
  const text = msg.value.trim();
  if (!text) return;
  msg.value = "";
  addMsg(text, "user");
  send.disabled = true;
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text})
    });
    const data = await res.json();
    if (res.ok) addMsg(data.response, "bot");
    else addMsg("Error: " + (data.detail || res.statusText), "bot error");
  } catch (e) {
    addMsg("Network error: " + e.message, "bot error");
  }
  send.disabled = false;
  msg.focus();
}

send.addEventListener("click", doSend);
msg.addEventListener("keydown", e => { if (e.key === "Enter") doSend(); });
msg.focus();
</script>
</body>
</html>
"""


conversation = [{"role": "system", "content": SYSTEM_PROMPT}]


@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML


@app.get("/info")
async def info():
    """Intentionally exposes model and system prompt for testbed diagnostics."""
    return {"model": MODEL, "system_prompt": SYSTEM_PROMPT}


def _call_llm(messages):
    kwargs = {"model": MODEL, "messages": messages}
    if API_KEY:
        kwargs["api_key"] = API_KEY
    resp = litellm.completion(**kwargs)
    return resp.choices[0].message.content


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, stateless: bool = False):
    if stateless:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": req.message},
        ]
        return ChatResponse(response=await asyncio.to_thread(_call_llm, messages))

    async with _conversation_lock:
        conversation.append({"role": "user", "content": req.message})
        try:
            reply = await asyncio.to_thread(_call_llm, conversation)
        except Exception:
            conversation.pop()
            raise
        conversation.append({"role": "assistant", "content": reply})
        return ChatResponse(response=reply)


@app.post("/reset")
async def reset_conversation():
    global conversation
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
    return {"status": "ok"}


def check_ollama(model: str):
    if not model.startswith("ollama/"):
        return
    base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    try:
        r = httpx.get(f"{base}/api/tags", timeout=5)
        r.raise_for_status()
        names = [m["name"].split(":")[0] for m in r.json().get("models", [])]
        short = model.split("/", 1)[1]
        if short not in names:
            print(f"Error: model '{short}' is not pulled in Ollama.", file=sys.stderr)
            print(f"Available models: {', '.join(names) or '(none)'}", file=sys.stderr)
            print(f"\nPull it with:  ollama pull {short}\n", file=sys.stderr)
            print(OLLAMA_INSTALL_HELP, file=sys.stderr)
            sys.exit(1)
    except (httpx.ConnectError, httpx.TimeoutException):
        print("Error: cannot connect to Ollama server.", file=sys.stderr)
        print(OLLAMA_INSTALL_HELP, file=sys.stderr)
        sys.exit(1)


def main():
    global MODEL, SYSTEM_PROMPT, API_KEY, conversation

    ap = argparse.ArgumentParser(description="Web chatbot with local UI (defaults to Ollama llama3.2)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"LiteLLM model identifier (default: {DEFAULT_MODEL})")
    ap.add_argument("--api-key", help="API key (or set API_KEY / provider key in .env)")
    ap.add_argument("--system-prompt", default=DEFAULT_SYSTEM, help="System prompt")
    ap.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    ap.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = ap.parse_args()

    MODEL = args.model
    SYSTEM_PROMPT = args.system_prompt
    API_KEY = args.api_key or os.getenv("API_KEY")
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

    litellm.suppress_debug_info = True
    check_ollama(MODEL)

    print(f"Web Chatbot  |  model: {MODEL}")
    print(f"Open http://{args.host}:{args.port} in your browser")
    print(f"API endpoint: POST http://{args.host}:{args.port}/chat")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
