"""
🧠 Subconscious Web Server — v2 (Gerçek AI Bilinçaltı)

Her whisper LLM tarafından üretilir. Template yok.
Insight'lar gelecek cevapları etkiler.
"""
import asyncio
import json
import random
import re
import sys
import os
import time
import threading
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subconscious import Subconscious
from subconscious.adapters import OllamaAdapter
from microsubconscious.layer import SubconsciousLayer

# ─── Initialize ──────────────────────────────────────────────────

app = FastAPI(title="🧠 Subconscious")

# Core systems
try:
    adapter = OllamaAdapter("llama3.1:8b")
    mind = Subconscious(adapter=adapter)
    print("✅ Ollama adapter connected")
except Exception as e:
    print(f"⚠️ Ollama unavailable ({e}), running without LLM")
    adapter = None
    mind = Subconscious()

micro_layer = SubconsciousLayer(capacity=256)

# Connected WebSocket clients
connected_clients: list[WebSocket] = []

# ─── Conversation State ─────────────────────────────────────────

conversation_history: list[dict] = []     # {"role": "user"/"assistant", "content": "..."}
extracted_topics: list[str] = []          # LLM-extracted real topics
background_insights: list[str] = []       # LLM-generated background insights
recent_concepts: list[str] = []          # For graph visualization
whisper_history: list[dict] = []


# ─── LLM Helper ─────────────────────────────────────────────────

from typing import Optional

def _llm_generate(prompt: str, system: str = "", max_retries: int = 2) -> Optional[str]:
    """Call LLM and return response text, or None on failure."""
    if adapter is None:
        return None
    for _ in range(max_retries):
        try:
            resp = adapter.generate(prompt=prompt, system=system)
            if resp and resp.strip():
                return resp.strip()
        except Exception as e:
            print(f"LLM error: {e}")
    return None


def _extract_topics_llm(text: str) -> list[str]:
    """LLM ile metinden gerçek kavramları/konuları çıkar."""
    prompt = (
        f"Aşağıdaki metindeki ana kavramları/konuları çıkar. "
        f"Sadece anlamlı kavramları ver (isim, terim, konu başlığı). "
        f"Gramer ekleri veya bağlaçlar OLMAMALI. "
        f"Virgülle ayırarak, maksimum 5 kavram yaz. Başka hiçbir şey yazma.\n\n"
        f"Metin: {text}\n\n"
        f"Kavramlar:"
    )
    result = _llm_generate(prompt, system="Sen bir kavram çıkarma asistanısın. Sadece kavramları virgülle listele, başka bir şey yazma.")
    if result:
        # Parse comma-separated topics and clean
        topics = [t.strip().lower().strip('"\'.-*') for t in result.split(",")]
        topics = [t for t in topics if 2 < len(t) < 40 and not t.isdigit()]
        return topics[:5]

    # Fallback: basic regex with strict filtering
    return _extract_topics_regex(text)


def _extract_topics_regex(text: str) -> list[str]:
    """Fallback: regex kavram çıkarma (daha iyi filtreli)."""
    # Turkish suffixed forms to strip (common endings)
    SUFFIX_PATTERNS = [
        r'(ların|lerin|ları|leri|ında|inde|ınca|ince)$',
        r'(ıyla|iyle|ının|inin|ıdır|idir|ması|mesi)$',
        r'(arak|erek|ığını|iğini|ılır|ilir|ınır|inir)$',
        r'(deki|daki|teki|taki)$',
    ]

    words = re.findall(r'\b\w+\b', text.lower())
    # Strip Turkish suffixes
    stemmed = []
    for w in words:
        for pat in SUFFIX_PATTERNS:
            w = re.sub(pat, '', w)
        if len(w) >= 4:
            stemmed.append(w)

    # Filter stop words and short words
    from subconscious.core.mind import STOP_WORDS
    concepts = [w for w in stemmed if w not in STOP_WORDS and not w.isdigit()]

    seen = set()
    unique = []
    for c in concepts:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique[:8]


# ─── WebSocket broadcast ─────────────────────────────────────────

async def broadcast(data: dict):
    """Send data to all connected clients."""
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


# ─── Background Thinking Thread ─────────────────────────────────

class BackgroundThinker:
    """
    Gerçek bilinçaltı — LLM kullanarak arka planda düşünür.
    Template string YOK. Her düşünce LLM tarafından üretilir.
    Insight'lar sonraki cevapları etkiler.
    """

    def __init__(self):
        self._running = False
        self._loop = None
        self._thread = None
        self._last_dream = time.time()
        self._last_whisper = 0
        self._whisper_count = 0

    def start(self, loop):
        self._running = True
        self._loop = loop
        self._thread = threading.Thread(target=self._think_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _think_loop(self):
        """Main thinking loop — runs every 45-90 seconds."""
        while self._running:
            try:
                # Wait 45-90 seconds between thoughts (not 8-15!)
                time.sleep(random.uniform(45, 90))
                if not self._running:
                    break

                # Only think if we have conversation context
                if not conversation_history or not extracted_topics:
                    continue

                # Rate limit: max 1 whisper per 40 seconds
                if time.time() - self._last_whisper < 40:
                    continue

                thought = self._generate_real_thought()
                if thought:
                    self._last_whisper = time.time()
                    self._whisper_count += 1

                    # Store insight for future responses
                    background_insights.append(thought["insight"])
                    # Keep last 10 insights
                    while len(background_insights) > 10:
                        background_insights.pop(0)

                    # Broadcast to clients
                    if self._loop and connected_clients:
                        asyncio.run_coroutine_threadsafe(
                            broadcast(thought), self._loop
                        )

                # Dream cycle every 3 minutes
                if time.time() - self._last_dream > 180:
                    self._run_dream()
                    self._last_dream = time.time()

            except Exception as e:
                print(f"Background thinker error: {e}")

    def _generate_real_thought(self) -> Optional[dict]:
        """LLM ile gerçek bir bilinçaltı düşüncesi üret."""
        if adapter is None:
            return None

        # Build context from conversation
        recent_msgs = conversation_history[-6:]
        conv_summary = "\n".join([
            f"{'Kullanıcı' if m['role']=='user' else 'AI'}: {m['content'][:200]}"
            for m in recent_msgs
        ])

        topics_str = ", ".join(extracted_topics[:10])

        # Previous insights context
        prev_insights = ""
        if background_insights:
            prev_insights = f"\nÖnceki bilinçaltı düşüncelerim: {'; '.join(background_insights[-3:])}"

        prompt = (
            f"Sen bir AI'ın bilinçaltısın. Konuşma bağlamına bakarak, "
            f"tartışılan konular arasında şaşırtıcı, derin veya beklenmedik bir bağlantı kur.\n\n"
            f"Tartışılan konular: {topics_str}\n"
            f"Son konuşma:\n{conv_summary}\n"
            f"{prev_insights}\n\n"
            f"ÖNEMLİ KURALLAR:\n"
            f"- Sadece 1-2 cümle yaz, kısa ve öz ol\n"
            f"- Gerçek bir içgörü sun, boş bağlantı kurma\n"
            f"- Farklı disiplinlerden (biyoloji, matematik, felsefe, bilgisayar) bağlantı kur\n"
            f"- 'İlginç...' veya 'Hmm...' gibi dolgu kelimelerle BAŞLAMA\n"
            f"- Doğrudan içgörüyü yaz\n\n"
            f"Bilinçaltı düşüncen:"
        )

        system = (
            "Sen bir AI'ın bilinçaltı katmanısın. Görevin konuşma bağlamından "
            "beklenmedik ama gerçek bağlantılar kurmak. Kısa, öz, derin."
        )

        result = _llm_generate(prompt, system=system)
        if not result or len(result) < 10:
            return None

        # Clean up the response
        insight = result.strip().strip('"').strip("'")
        # Skip if too generic or too long
        if len(insight) > 300 or len(insight) < 15:
            return None

        whisper = {
            "type": "whisper",
            "content": f"💭 {insight}",
            "insight": insight,
            "topics": extracted_topics[:5],
            "timestamp": time.time(),
        }
        whisper_history.append(whisper)
        return whisper

    def _run_dream(self):
        """Background dream cycle — consolidation."""
        try:
            report = mind.dream()
            dream_msg = {
                "type": "dream",
                "content": f"🌙 Bellek konsolidasyonu: {report.new_connections} yeni bağlantı, "
                           f"{report.patterns_found} örüntü keşfedildi",
                "timestamp": time.time(),
            }
            if self._loop and connected_clients:
                asyncio.run_coroutine_threadsafe(
                    broadcast(dream_msg), self._loop
                )
        except Exception:
            pass


thinker = BackgroundThinker()


# ─── API Endpoints ───────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    loop = asyncio.get_event_loop()
    thinker.start(loop)
    print("🧠 Background thinker started")


@app.on_event("shutdown")
async def shutdown():
    thinker.stop()


@app.get("/")
async def index():
    return {"status": "Subconscious AI Backend Operational"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)

    # Send current graph state
    try:
        graph_data = _get_graph_data()
        await ws.send_json({"type": "graph_init", "data": graph_data})
    except Exception:
        pass

    try:
        while True:
            data = await ws.receive_json()

            if data.get("type") == "chat":
                message = data.get("content", "")
                response = await _process_chat(message)
                await ws.send_json(response)

                # Send updated graph
                graph_data = _get_graph_data()
                await broadcast({"type": "graph_update", "data": graph_data})

    except WebSocketDisconnect:
        connected_clients.remove(ws)


async def _process_chat(message: str) -> dict:
    """Full subconscious pipeline for a chat message."""
    global recent_concepts, extracted_topics

    # 1. Store conversation
    conversation_history.append({"role": "user", "content": message})

    # 2. Extract real topics via LLM (not just words)
    topics = _extract_topics_llm(message)
    extracted_topics = list(dict.fromkeys(topics + extracted_topics))[:20]
    recent_concepts = extracted_topics[:15]

    # 3. microsubconscious layer — Thought DAG processing
    micro_result = micro_layer.process(message)

    # 4. Build extra context from background insights
    insight_context = ""
    if background_insights:
        insight_context = (
            "\n\nBilinçaltı düşüncelerim (bunları yanıtına doğal şekilde entegre et):\n"
            + "\n".join(f"- {ins}" for ins in background_insights[-5:])
        )

    # 5. subconscious.think() — memory + graph + creativity
    #    Inject background insights into the thinking process
    think_result = mind.think(
        message + insight_context,
        include_creative=True,
        n_creative=2,
    )

    # 6. Store response in conversation history
    conversation_history.append({"role": "assistant", "content": think_result.response})

    # Keep conversation history manageable
    while len(conversation_history) > 20:
        conversation_history.pop(0)

    # 7. Extract topics from response too
    resp_topics = _extract_topics_llm(think_result.response)
    extracted_topics = list(dict.fromkeys(extracted_topics + resp_topics))[:25]

    # 8. microsubconscious absorb
    micro_layer.absorb(think_result.response)

    # 9. Build response
    return {
        "type": "chat_response",
        "content": think_result.response,
        "meta": {
            "activated_concepts": dict(list(think_result.activated_concepts.items())[:8]),
            "creative_sparks": [
                {"strategy": s.strategy.value, "idea": s.idea[:150]}
                for s in think_result.creative_sparks
            ],
            "topics": topics,
            "insights_used": len(background_insights),
            "recalled_count": len(think_result.recalled_memories),
            "thoughts_in_dag": micro_result.get("total_thoughts", 0),
        },
    }


def _get_graph_data() -> dict:
    """Get cognitive graph as D3.js compatible data."""
    graph = mind.graph
    nodes = []
    edges = []

    for node_id in graph._graph.nodes:
        data = graph._graph.nodes[node_id]
        nodes.append({
            "id": node_id,
            "type": data.get("node_type", "concept"),
            "activation": data.get("activation", 0.5),
            "importance": data.get("importance", 0.5),
            "domain": data.get("domain", ""),
            "is_recent": node_id in [c.lower() for c in recent_concepts[:10]],
        })

    for u, v, key, data in graph._graph.edges(keys=True, data=True):
        edges.append({
            "source": u,
            "target": v,
            "weight": data.get("weight", 0.5),
            "type": data.get("edge_type", "related"),
        })

    return {"nodes": nodes, "edges": edges}


@app.get("/api/stats")
async def get_stats():
    return JSONResponse({
        "mind": mind.stats(),
        "micro_layer": micro_layer.stats(),
        "whispers": len(whisper_history),
        "insights": background_insights[-5:],
        "topics": extracted_topics[:10],
    })


# ─── Run ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("🧠 Starting Subconscious Web Server...")
    print("   Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
