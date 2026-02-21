"""
Subconscious — Web API (FastAPI)

REST API + WebSocket for the subconscious dashboard.
"""
import sys
import os
import json
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from subconscious.engine import SubconsciousEngine

# ─── Engine singleton ────────────────────────────────────────────────────────
engine: SubconsciousEngine = None  # type: ignore

def get_engine() -> SubconsciousEngine:
    global engine
    if engine is None:
        engine = SubconsciousEngine()
    return engine

def set_engine(ext_engine: SubconsciousEngine):
    """Dışarıdan engine inject et (start.py all modu için)."""
    global engine
    engine = ext_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start dream daemon on startup."""
    e = get_engine()
    e.start_dreaming(interval_seconds=300)
    yield
    e.stop_dreaming()


app = FastAPI(
    title="Subconscious API",
    version="0.3.0",
    description="🧠 AI Bilinçaltı Framework API",
    lifespan=lifespan,
)

# Serve static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ─── Models ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    show_subconscious: bool = True

class ChatResponse(BaseModel):
    response: str
    subconscious: Optional[dict] = None


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = get_engine().chat(req.message, show_subconscious=req.show_subconscious)
    return ChatResponse(**result)


@app.get("/api/stats")
async def stats():
    e = get_engine()
    return {
        "memory": e.get_memory_stats(),
        "associations": e.get_association_stats(),
        "emotions": e.get_emotional_trend(),
        "dream": e.get_dream_stats(),
    }


@app.get("/api/graph")
async def graph():
    return get_engine().associations.export_graph()


@app.get("/api/concepts")
async def concepts(limit: int = 20):
    return get_engine().get_active_concepts(limit)


@app.get("/api/concepts/{name}/related")
async def related(name: str, limit: int = 10):
    return get_engine().get_related_concepts(name, limit)


@app.get("/api/connections")
async def connections(limit: int = 10):
    return get_engine().discover_connections(limit)


@app.get("/api/memories")
async def memories(limit: int = 20):
    recent = get_engine().memory.recent(limit)
    return [m.to_dict() for m in recent]


@app.post("/api/dream")
async def dream_now():
    report = get_engine().dream_now(use_llm=True)
    return report.to_dict()


@app.get("/api/dream/thoughts")
async def dream_thoughts(limit: int = 10):
    return get_engine().get_dream_thoughts(limit)


# ─── WebSocket for real-time updates ─────────────────────────────────────────

connected_clients: list[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "chat":
                e = get_engine()
                result = e.chat(msg["message"], show_subconscious=True)
                await ws.send_json({
                    "type": "chat_response",
                    "data": result,
                })
                # Broadcast graph update to all clients
                graph_data = e.associations.export_graph()
                stats_data = {
                    "memory": e.get_memory_stats(),
                    "associations": e.get_association_stats(),
                    "emotions": e.get_emotional_trend(),
                    "dream": e.get_dream_stats(),
                }
                for client in connected_clients:
                    try:
                        await client.send_json({"type": "graph_update", "data": graph_data})
                        await client.send_json({"type": "stats_update", "data": stats_data})
                    except:
                        pass

            elif msg.get("type") == "dream":
                report = get_engine().dream_now(use_llm=True)
                await ws.send_json({
                    "type": "dream_report",
                    "data": report.to_dict(),
                })

    except WebSocketDisconnect:
        connected_clients.remove(ws)


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=3000, reload=True)
