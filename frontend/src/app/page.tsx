"use client";

import { useEffect, useState, useRef, FormEvent } from "react";
import * as d3 from "d3";
import { Sparkles, Terminal, ArrowRight } from "lucide-react";

// Types
type WebMessage = {
  type: "chat_response" | "whisper" | "dream" | "graph_init" | "graph_update";
  content?: string;
  meta?: any;
  data?: any;
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
  const [hasJoined, setHasJoined] = useState(false);

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

  // Refs for auto-scroll and d3
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const thoughtsBottomRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<any>(null);

  // Connection Management
  useEffect(() => {
    if (!hasJoined) return;

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
  }, [hasJoined]);

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

    ws.send(JSON.stringify({ type: "chat", content: inputMessage.trim() }));
    setInputMessage("");
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
        .force("link", d3.forceLink().id((d: any) => d.id).distance(40))
        .force("charge", d3.forceManyBody().strength(-30))
        .force("center", d3.forceCenter(w / 2, h / 2))
        .force("collision", d3.forceCollide().radius(15));
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
      .attr("stroke", "#333")
      .attr("stroke-opacity", 0.4)
      .attr("stroke-width", (d: any) => Math.max(0.5, (d.weight || 0.5) * 1.5));

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
            d.fx = null;
            d.fy = null;
          })
      );

    nodeEnter
      .append("circle")
      .attr("r", (d: any) => 3 + (d.importance || 0.5) * 4)
      .attr("fill", (d: any) => (d.is_recent ? "#00ea90" : d.domain ? "#4cc9f0" : "#222"))
      .attr("stroke", (d: any) => (d.is_recent ? "#00ea90" : "#333"))
      .attr("stroke-width", 1.5)
      .attr("opacity", (d: any) => 0.5 + (d.activation || 0.5) * 0.5);

    nodeEnter
      .append("text")
      .attr("dx", 8)
      .attr("dy", 3)
      .attr("font-size", "9px")
      .attr("fill", "#666")
      .style("font-family", "monospace")
      .style("pointer-events", "none")
      .text((d: any) => (d.id.length > 12 ? d.id.slice(0, 12) + "…" : d.id));

    const nodeMerge = nodeEnter.merge(node as any);

    nodeMerge
      .select("circle")
      .attr("fill", (d: any) => (d.is_recent ? "#00ea90" : d.domain ? "#4cc9f0" : "#222"))
      .attr("opacity", (d: any) => 0.5 + (d.activation || 0.5) * 0.5);

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
  }, [graphData]);

  // View: Landing Page
  if (!hasJoined) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden bg-black selection:bg-[#00ea90]/30 selection:text-white">
        {/* HackerRank-style Top Nav Mock */}
        <nav className="absolute top-0 w-full flex items-center justify-between p-6 px-8 z-10 glass-nav border-b border-white/5 bg-black/40 backdrop-blur-xl">
          <div className="flex items-center gap-2">
            <span className="font-bold text-xl tracking-tight text-white flex items-center gap-1.5">
              HackerRank<div className="w-4 h-4 bg-[#00ea90]" />
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-neutral-400 font-medium tracking-wide">
            <span className="hover:text-white transition-colors cursor-pointer">Products</span>
            <span className="hover:text-white transition-colors cursor-pointer">Solutions</span>
            <span className="hover:text-white transition-colors cursor-pointer">Resources</span>
            <span className="hover:text-white transition-colors cursor-pointer">Pricing</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-neutral-400 hover:text-white transition-colors cursor-pointer hidden md:flex items-center gap-1.5">
              For Developers <ArrowRight className="w-4 h-4" />
            </span>
            <button className="text-sm font-medium bg-[#1e1e1e] hover:bg-[#2a2a2a] text-white px-5 py-2 rounded-md transition-all border border-white/5 hidden sm:block">
              Request Demo
            </button>
            <button
              onClick={() => setHasJoined(true)}
              className="text-sm font-medium bg-[#00ea90] hover:bg-[#00c97b] text-black px-5 py-2 rounded-md transition-transform active:scale-95 shadow-[0_0_20px_rgba(0,234,144,0.3)] hover:shadow-[0_0_30px_rgba(0,234,144,0.5)]"
            >
              Sign Up
            </button>
          </div>
        </nav>

        {/* Ambient Glows */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-[#00ea90] opacity-[0.03] blur-[120px] rounded-full pointer-events-none" />

        {/* Main Content */}
        <div className="z-10 flex flex-col items-center text-center max-w-4xl mt-12">
          <h1 className="text-6xl md:text-8xl font-medium tracking-tight text-neutral-300 leading-[1.1] mb-6">
            The future<br />
            of development<br />
            is <span className="text-white flex items-center justify-center gap-2 relative inline-flex">
              <Sparkles className="w-12 h-12 text-[#00ea90] shrink-0" strokeWidth={1.5} />
              human + AI
            </span>
          </h1>

          <p className="text-lg md:text-xl text-neutral-400 max-w-2xl mb-12 font-light leading-relaxed">
            We help you map the skills you need, track the skills you have, and close your gaps to thrive in a GenAI world.
          </p>

          <button
            onClick={() => setHasJoined(true)}
            className="group relative px-8 py-4 bg-black border border-[#333] hover:border-[#00ea90]/50 rounded-lg text-white font-medium text-lg transition-all duration-300 hover:shadow-[0_0_40px_rgba(0,234,144,0.15)] flex items-center gap-3 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[#00ea90]/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
            Join The Community
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </main>
    );
  }

  // View: Subconscious Interface
  return (
    <div className="h-screen flex flex-col bg-[#090909] overflow-hidden font-sans selection:bg-[#00ea90]/30 selection:text-white">
      {/* Header */}
      <header className="h-16 shrink-0 border-b border-white/5 bg-black/40 backdrop-blur-xl flex items-center justify-between px-6 z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#1a1a1a] to-[#2a2a2a] border border-white/10 flex items-center justify-center shadow-[0_0_15px_rgba(0,234,144,0.1)]">
            <Sparkles className="w-4 h-4 text-[#00ea90]" />
          </div>
          <h1 className="font-semibold tracking-tight text-white">Subconscious</h1>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono text-neutral-400">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#00ea90] shadow-[0_0_10px_rgba(0,234,144,0.5)] animate-pulse' : 'bg-red-500'}`} />
            {stats}
          </div>
        </div>
      </header>

      <div className="flex flex-1 min-h-0 relative">
        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#090909]">
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

          <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[#090909] via-[#090909] to-transparent xl:pr-[380px]">
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

        {/* Right Sidebar */}
        <aside className="hidden xl:flex w-[380px] shrink-0 border-l border-white/5 bg-[#0c0c0c] flex-col z-10">
          {/* Thoughts Stream */}
          <div className="flex-1 min-h-0 flex flex-col border-b border-white/5 p-5">
            <h3 className="text-xs font-mono uppercase tracking-wider text-neutral-500 mb-4 flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-[#00ea90] animate-pulse" />
              Background Streams
            </h3>
            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {thoughts.length === 0 ? (
                <div className="text-xs text-neutral-600 font-mono italic">Awaiting cognitive activity...</div>
              ) : (
                thoughts.map((t) => (
                  <div key={t.id} className="p-3 rounded-lg bg-[#141414] border-l-2 border-[#00ea90]/50 border-y border-r border-[#1a1a1a] shadow-sm">
                    <div className="text-[10px] font-mono text-neutral-500 mb-1">{t.time}</div>
                    <div className="text-xs text-neutral-300 leading-relaxed">{t.text}</div>
                  </div>
                ))
              )}
              <div ref={thoughtsBottomRef} />
            </div>
          </div>

          {/* D3 Graph Area */}
          <div className="h-[320px] shrink-0 relative p-5 flex flex-col">
            <h3 className="text-xs font-mono uppercase tracking-wider text-neutral-500 mb-2 flex items-center gap-2 z-10">
              <div className="w-1.5 h-1.5 rounded-full bg-[#4cc9f0] animate-pulse" />
              Association Network
            </h3>
            <div className="flex-1 relative w-full rounded-xl bg-[#0f0f0f] border border-white/5 overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center text-xs text-neutral-500 font-mono flex-col gap-2">
                <svg ref={svgRef} className="absolute inset-0 w-full h-full text-white" />
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
