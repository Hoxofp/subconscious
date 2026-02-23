"use client";

import { useEffect, useState, useRef, FormEvent } from "react";
import * as d3 from "d3";
import { Sparkles, Terminal, ArrowRight, MessageSquare, Network, MessageCircle, Clock } from "lucide-react";

// Types
type WebMessage = {
  type: "chat_response" | "whisper" | "dream" | "graph_init" | "graph_update" | "session_created" | "session_history";
  content?: string;
  meta?: any;
  data?: any;
  session_id?: string;
};

type ChatSession = {
  id: string;
  title: string;
  date: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "whisper" | "dream";
  content: string;
  meta?: any;
  timestamp: string;
};

type ThoughtStreamItem = {
  id: string;
  text: string;
  type: "whisper" | "dream";
  time: string;
};

export default function Home() {
  // Navigation / View State
  const [currentTab, setCurrentTab] = useState<"chat" | "network">("chat");

  // WebSocket connection & State
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Application Data
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const [thoughts, setThoughts] = useState<ThoughtStreamItem[]>([]);
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] }>({
    nodes: [],
    edges: [],
  });
  const [stats, setStats] = useState("Connecting...");

  // Session State
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Fetch Sessions on Mount
  const fetchSessions = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/sessions");
      const data = await res.json();

      const formatted = data.sessions.map((s: any) => {
        const date = new Date(s.updated_at * 1000);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        let dateStr = "Geçen Hafta";
        if (date.toDateString() === today.toDateString()) {
          dateStr = "Bugün";
        } else if (date.toDateString() === yesterday.toDateString()) {
          dateStr = "Dün";
        }

        return {
          id: s.id,
          title: s.title,
          date: dateStr
        };
      });
      setSessions(formatted);
    } catch (e) {
      console.error("Failed to fetch sessions", e);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const loadSession = async (sessionId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/sessions/${sessionId}/messages`);
      const data = await res.json();

      const loadedMessages = data.messages.map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        meta: m.meta,
        timestamp: new Date(m.created_at * 1000).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" })
      }));

      setMessages(loadedMessages);
      setActiveSessionId(sessionId);
    } catch (e) {
      console.error("Failed to load session messages", e);
    }
  };

  // Refs for auto-scroll and d3
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const thoughtsBottomRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<any>(null);

  // Connection Management
  useEffect(() => {
    let socket: WebSocket;
    let reconnectTimer: NodeJS.Timeout;

    const connect = () => {
      // Connect directly to the backend on port 8000
      const wsUrl = `ws://localhost:8000/ws`;
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        setIsConnected(true);
        setStats("Subconscious active");
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "assistant",
            content: "Hello! I am your subconscious. While we talk, I'll continue to think, make connections, and develop intuitions in the background.\n\nWhat would you like to discuss?",
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
      };

      socket.onclose = () => {
        setIsConnected(false);
        setStats("Connection lost...");
        reconnectTimer = setTimeout(connect, 3000);
      };

      socket.onmessage = (event) => {
        try {
          const data: WebMessage = JSON.parse(event.data);
          handleWebMessage(data);
        } catch (e) {
          console.error("Error parsing message", e);
        }
      };

      setWs(socket);
    };

    connect();

    return () => {
      if (socket) socket.close();
      clearTimeout(reconnectTimer);
    };
  }, []);

  const handleWebMessage = (data: WebMessage) => {
    const time = new Date().toLocaleTimeString("tr-TR", {
      hour: "2-digit",
      minute: "2-digit",
    });
    const id = Date.now().toString() + Math.random().toString(36).substr(2, 5);

    switch (data.type) {
      case "chat_response":
        setIsTyping(false);
        setMessages((prev) => [
          ...prev,
          {
            id,
            role: "assistant",
            content: data.content || "",
            meta: data.meta,
            timestamp: time,
          },
        ]);
        break;
      case "whisper":
        setMessages((prev) => [
          ...prev,
          {
            id,
            role: "whisper",
            content: data.content || "",
            timestamp: time,
          },
        ]);
        setThoughts((prev) => {
          const newThoughts: ThoughtStreamItem[] = [
            ...prev,
            { id, text: data.content || "", type: "whisper", time },
          ];
          return newThoughts.slice(-20); // Keep last 20
        });
        break;
      case "dream":
        setMessages((prev) => [
          ...prev,
          {
            id,
            role: "dream",
            content: data.content || "",
            timestamp: time,
          },
        ]);
        setThoughts((prev) => {
          const newThoughts: ThoughtStreamItem[] = [
            ...prev,
            { id, text: data.content || "", type: "dream", time },
          ];
          return newThoughts.slice(-20);
        });
        break;
      case "graph_init":
      case "graph_update":
        if (data.data) {
          setGraphData(data.data);
          updateStatsFromData(data.data);
        }
        break;
      case "session_created":
        if (data.session_id && !activeSessionId) {
          setActiveSessionId(data.session_id);
          fetchSessions(); // Refresh list to show new session
        }
        break;
    }
  };

  const updateStatsFromData = (data: { nodes: any[]; edges: any[] }) => {
    const n = data.nodes?.length || 0;
    const e = data.edges?.length || 0;
    setStats(`Active · ${n} concepts · ${e} links`);
  };

  // Chat Actions
  const handleSendMessage = (e: FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !isConnected || !ws) return;

    const time = new Date().toLocaleTimeString();

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "user",
        content: inputMessage.trim(),
        timestamp: time,
      },
    ]);
    setIsTyping(true);

    ws.send(JSON.stringify({
      type: "chat",
      content: inputMessage.trim(),
      session_id: activeSessionId
    }));
    setInputMessage("");
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
    setMessages([
      {
        id: Date.now().toString(),
        role: "assistant",
        content: "Hello! I am your subconscious. While we talk, I'll continue to think, make connections, and develop intuitions in the background.\n\nWhat would you like to discuss?",
        timestamp: new Date().toLocaleTimeString(),
      }
    ]);
  };

  // Auto-scrolling
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    thoughtsBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thoughts]);

  // Add Graph Rendering
  useEffect(() => {
    if (currentTab !== "network") return; // Only render when visible to avoid 0x0 layout boxes
    if (!svgRef.current || !graphData.nodes.length) return;

    const svg = d3.select(svgRef.current);
    const rect = svgRef.current.parentElement?.getBoundingClientRect();
    const w = rect?.width || 340;
    const h = rect?.height || 280;

    svg.attr("viewBox", `0 0 ${w} ${h}`);

    if (!simulationRef.current) {
      svg.append("g").attr("class", "links");
      svg.append("g").attr("class", "nodes");

      simulationRef.current = d3
        .forceSimulation()
        // Strong weights pull closer (e.g. 1.0 weight = 40px, 0.1 weight = 160px)
        .force("link", d3.forceLink().id((d: any) => d.id).distance((d: any) => 120 - ((d.weight || 0.5) * 80)))
        // High repulsion to force unrelated clusters apart
        .force("charge", d3.forceManyBody().strength(-80))
        .force("center", d3.forceCenter(w / 2, h / 2))
        .force("collision", d3.forceCollide().radius(25));
    }

    const simulation = simulationRef.current;

    let nodes = [...graphData.nodes]
      .sort((a, b) => (b.importance || 0) - (a.importance || 0))
      .slice(0, 35);

    const nodeIds = new Set(nodes.map((n) => n.id));
    let links = [...graphData.edges]
      .filter((e) => nodeIds.has(e.source?.id || e.source) && nodeIds.has(e.target?.id || e.target))
      .slice(0, 60);

    // Links
    const link = svg
      .select(".links")
      .selectAll("line")
      .data(links, (d: any) => `${d.source?.id || d.source}-${d.target?.id || d.target}`);

    link.exit().remove();

    const linkEnter = link
      .enter()
      .append("line")
      .attr("class", "link")
      .attr("stroke", (d: any) => {
        // High weight (closely related) -> Bright Green
        if ((d.weight || 0) > 0.7) return "#00ea90";
        // Medium weight -> White/Gray
        if ((d.weight || 0) > 0.4) return "#888";
        // Weak weight (unrelated/distant) -> Dark red/gray
        return "#442222";
      })
      .attr("stroke-opacity", (d: any) => Math.max(0.2, d.weight || 0.5))
      .attr("stroke-dasharray", (d: any) => {
        // Unrelated/distant links get dashed lines
        return (d.weight || 0) < 0.4 ? "4,4" : "none";
      })
      .attr("stroke-width", (d: any) => Math.max(0.5, (d.weight || 0.5) * 2));

    const linkMerge = linkEnter.merge(link as any);

    // Nodes
    const node = svg.select(".nodes").selectAll(".node").data(nodes, (d: any) => d.id);
    node.exit().remove();

    const nodeEnter = node
      .enter()
      .append("g")
      .attr("class", "node")
      .call(
        d3
          .drag<any, any>()
          .on("start", (e, d) => {
            if (!e.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (e, d) => {
            d.fx = e.x;
            d.fy = e.y;
          })
          .on("end", (e, d) => {
            if (!e.active) simulation.alphaTarget(0);
          })
      );

    nodeEnter
      .append("circle")
      .attr("r", (d: any) => 3 + (d.importance || 0.5) * 8)
      .attr("fill", (d: any) => {
        // Calculate degree (number of links) to find isolated/unrelated concepts
        const degree = links.filter(l => l.source.id === d.id || l.target.id === d.id).length;

        if (d.is_recent) return "#00ea90";
        if (degree <= 1) return "#333333"; // Unrelated/isolated nodes are dark gray
        if (d.type === "event") return "#a855f7";
        if (d.type === "entity") return "#3b82f6";
        return "#ffffff";
      })
      .attr("opacity", (d: any) => {
        const degree = links.filter(l => l.source.id === d.id || l.target.id === d.id).length;
        // Make truly isolated concepts slightly faded
        return degree <= 1 && !d.is_recent ? 0.4 : (d.is_recent ? 1 : 0.8);
      })
      .attr("stroke", (d: any) => (d.is_recent ? "rgba(0, 234, 144, 0.4)" : "none"))
      .attr("stroke-width", 4);

    nodeEnter
      .append("text")
      .text((d: any) => d.id)
      .attr("font-size", (d: any) => 9 + (d.importance || 0.5) * 4)
      .attr("fill", (d: any) => {
        const degree = links.filter(l => l.source.id === d.id || l.target.id === d.id).length;
        return degree <= 1 && !d.is_recent ? "#555" : "#aaa";
      })
      .attr("dx", 12)
      .attr("dy", 4)
      .style("pointer-events", "none");

    const nodeMerge = nodeEnter.merge(node as any);

    // Keep the newly entered colors instead of overriding them on merge
    nodeMerge
      .select("circle")
      .attr("stroke", (d: any) => (d.is_recent ? "rgba(0, 234, 144, 0.4)" : "none"))
      .attr("opacity", (d: any) => {
        const degree = links.filter(l => l.source.id === d.id || l.target.id === d.id).length;
        return degree <= 1 && !d.is_recent ? 0.4 : (d.is_recent ? 1 : 0.8);
      });

    simulation.nodes(nodes).on("tick", () => {
      linkMerge
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      nodeMerge.attr("transform", (d: any) => {
        d.x = Math.max(8, Math.min(w - 8, d.x));
        d.y = Math.max(8, Math.min(h - 8, d.y));
        return `translate(${d.x},${d.y})`;
      });
    });

    simulation.force("link").links(links);
    simulation.alpha(0.3).restart();
  }, [graphData, currentTab]);

  // View: Subconscious Interface
  return (
    <div className="h-screen flex flex-col bg-[#090909] overflow-hidden font-sans selection:bg-[#00ea90]/30 selection:text-white">
      {/* Header */}
      <header className="h-16 shrink-0 border-b border-white/5 bg-black/40 backdrop-blur-xl flex items-center justify-between px-6 z-20">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#1a1a1a] to-[#2a2a2a] border border-white/10 flex items-center justify-center shadow-[0_0_15px_rgba(0,234,144,0.1)]">
              <Sparkles className="w-4 h-4 text-[#00ea90]" />
            </div>
            <h1 className="font-semibold tracking-tight text-white mr-4">Subconscious</h1>
          </div>

          {/* Tabs */}
          <div className="flex items-center bg-[#111] border border-white/5 rounded-lg p-1">
            <button
              onClick={() => setCurrentTab('chat')}
              className={`flex items-center gap-2 px-4 py-1.5 text-sm rounded-md transition-all ${currentTab === 'chat' ? 'bg-[#222] text-white shadow-sm' : 'text-neutral-500 hover:text-neutral-300'}`}
            >
              <MessageSquare className="w-4 h-4" />
              Chat
            </button>
            <button
              onClick={() => setCurrentTab('network')}
              className={`flex items-center gap-2 px-4 py-1.5 text-sm rounded-md transition-all ${currentTab === 'network' ? 'bg-[#222] text-white shadow-sm' : 'text-neutral-500 hover:text-neutral-300'}`}
            >
              <Network className="w-4 h-4" />
              Network
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-neutral-400">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#00ea90] shadow-[0_0_10px_rgba(0,234,144,0.5)] animate-pulse' : 'bg-red-500'}`} />
            {stats}
          </div>
        </div>
      </header>

      <div className="flex flex-1 min-h-0 relative">
        {/* Left Sidebar: Session History */}
        <aside className="w-[280px] shrink-0 border-r border-white/5 bg-[#0a0a0a] flex flex-col hidden md:flex">
          <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
            <span className="text-sm font-semibold text-neutral-300">Konuşmalar</span>
            <button className="text-[#00ea90] hover:text-white transition-colors">
              <MessageSquare className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-6">
            {/* Group: Bugün */}
            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-neutral-500 mb-2 px-2">Bugün</h3>
              <div className="space-y-1">
                {sessions.filter(s => s.date === "Bugün").map(s => (
                  <button key={s.id} className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-white/5 transition-colors group flex items-start gap-3">
                    <MessageCircle className="w-4 h-4 mt-0.5 text-neutral-500 group-hover:text-white transition-colors shrink-0" />
                    <span className="text-sm text-neutral-400 group-hover:text-neutral-200 truncate leading-snug">{s.title}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Group: Dün */}
            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-neutral-500 mb-2 px-2">Dün</h3>
              <div className="space-y-1">
                {sessions.filter(s => s.date === "Dün").map(s => (
                  <button key={s.id} className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-white/5 transition-colors group flex items-start gap-3">
                    <MessageCircle className="w-4 h-4 mt-0.5 text-neutral-500 group-hover:text-white transition-colors shrink-0" />
                    <span className="text-sm text-neutral-400 group-hover:text-neutral-200 truncate leading-snug">{s.title}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Group: Geçen Hafta */}
            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-neutral-500 mb-2 px-2">Geçen Hafta</h3>
              <div className="space-y-1">
                {sessions.filter(s => s.date === "Geçen Hafta").map(s => (
                  <button key={s.id} className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-white/5 transition-colors group flex items-start gap-3">
                    <Clock className="w-4 h-4 mt-0.5 text-neutral-500 group-hover:text-white transition-colors shrink-0" />
                    <span className="text-sm text-neutral-400 group-hover:text-neutral-200 truncate leading-snug">{s.title}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {currentTab === "chat" ? (
          <main className="flex-1 flex flex-col min-w-0 bg-[#090909]">
            {/* Main Chat Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8 pb-32">
              {messages.length === 0 && (
                <div className="h-full flex items-center justify-center text-neutral-500 font-mono text-sm opacity-50">
                  Awaiting connection...
                </div>
              )}

              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col max-w-3xl ${msg.role === "user" ? "ml-auto items-end" : "mr-auto items-start"
                    } ${msg.role === "whisper" || msg.role === "dream" ? "opacity-70 mx-auto items-center" : ""}`}
                >
                  {msg.role !== "whisper" && msg.role !== "dream" && (
                    <span className="text-xs font-mono uppercase tracking-wider text-neutral-500 mb-2 px-2">
                      {msg.role === 'user' ? 'You' : 'Subconscious'}
                    </span>
                  )}

                  <div
                    className={`
                      px-5 py-4 rounded-2xl text-sm leading-relaxed
                      ${msg.role === "user"
                        ? "bg-[#1a1a1a] border border-white/10 text-white rounded-tr-sm"
                        : msg.role === "assistant"
                          ? "bg-[#111] border border-[#222] text-gray-200 rounded-tl-sm"
                          : msg.role === "whisper"
                            ? "bg-transparent border border-[#00ea90]/20 text-[#00ea90] italic rounded-full px-6 py-2"
                            : "bg-transparent border border-[#4cc9f0]/20 text-[#4cc9f0] italic rounded-full px-6 py-2"
                      }
                    `}
                  >
                    <div dangerouslySetInnerHTML={{ __html: msg.content.replace(/\n/g, '<br/>') }} />

                    {/* Meta tags for assistant */}
                    {msg.role === "assistant" && msg.meta?.activated_concepts && (
                      <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-white/5">
                        {Object.keys(msg.meta.activated_concepts).slice(0, 5).map(c => (
                          <span key={c} className="text-[10px] font-mono px-2 py-1 rounded bg-white/5 text-neutral-400 border border-white/5">
                            {c}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex flex-col max-w-3xl mr-auto items-start">
                  <span className="text-xs font-mono uppercase tracking-wider text-neutral-500 mb-2 px-2">
                    Subconscious
                  </span>
                  <div className="px-5 py-4 rounded-2xl bg-[#111] border border-[#222] rounded-tl-sm flex items-center gap-1.5 h-12">
                    <div className="w-1.5 h-1.5 rounded-full bg-neutral-500 animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-neutral-500 animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-neutral-500 animate-bounce" />
                  </div>
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>

            <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[#090909] via-[#090909] to-transparent">
              <form
                onSubmit={handleSendMessage}
                className="max-w-4xl mx-auto relative group"
              >
                <div className="absolute inset-0 bg-[#00ea90]/5 rounded-xl blur-xl transition-opacity opacity-0 group-focus-within:opacity-100" />
                <div className="relative flex items-center gap-3 bg-[#111] border border-[#222] rounded-xl px-4 py-3 focus-within:border-[#00ea90]/50 focus-within:ring-1 focus-within:ring-[#00ea90]/50 transition-all shadow-2xl">
                  <Terminal className="w-5 h-5 text-neutral-500" />
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Interact with your subconscious..."
                    className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder:text-neutral-500"
                    disabled={!isConnected}
                  />
                  <button
                    type="submit"
                    disabled={!isConnected || !inputMessage.trim()}
                    className="w-8 h-8 rounded-lg bg-[#222] hover:bg-[#333] flex items-center justify-center text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed group/btn border border-white/5 hover:border-[#00ea90]/30"
                  >
                    <ArrowRight className="w-4 h-4 group-hover/btn:text-[#00ea90] transition-colors" />
                  </button>
                </div>
              </form>
            </div>
          </main>
        ) : (
          <main className="flex-1 flex flex-col md:flex-row min-w-0 bg-[#0c0c0c]">
            {/* Network Area */}
            <div className="flex-1 shrink-0 relative p-6 flex flex-col">
              <h3 className="text-xs font-mono uppercase tracking-wider text-neutral-500 mb-4 flex items-center gap-2 z-10">
                <div className="w-1.5 h-1.5 rounded-full bg-[#4cc9f0] animate-pulse" />
                Association Network
              </h3>
              <div className="flex-1 relative w-full rounded-xl bg-[#0f0f0f] border border-white/5 overflow-hidden shadow-inner">
                <div className="absolute inset-0 flex items-center justify-center text-xs text-neutral-500 font-mono flex-col gap-2">
                  <svg ref={svgRef} className="absolute inset-0 w-full h-full text-white" />
                </div>
              </div>
            </div>

            {/* Thoughts Stream is a sidebar inside the network tab */}
            <aside className="w-full md:w-[400px] shrink-0 border-l border-white/5 bg-[#0c0c0c] flex flex-col">
              <div className="flex-1 flex flex-col border-b border-white/5 p-6 min-h-0">
                <h3 className="text-xs font-mono uppercase tracking-wider text-neutral-500 mb-4 flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00ea90] animate-pulse" />
                  Background Streams
                </h3>
                <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                  {thoughts.length === 0 ? (
                    <div className="text-xs text-neutral-600 font-mono italic">Awaiting cognitive activity...</div>
                  ) : (
                    thoughts.map((t) => (
                      <div key={t.id} className="p-4 rounded-xl bg-[#141414] border-l-2 border-[#00ea90]/50 border-y border-r border-[#1a1a1a] shadow-md">
                        <div className="text-[10px] font-mono text-neutral-500 mb-2">{t.time}</div>
                        <div className="text-sm text-neutral-300 leading-relaxed">{t.text}</div>
                      </div>
                    ))
                  )}
                  <div ref={thoughtsBottomRef} />
                </div>
              </div>
            </aside>
          </main>
        )}
      </div>
    </div>
  );
}
