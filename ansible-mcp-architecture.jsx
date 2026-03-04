import { useState } from "react";

const layers = [
  {
    id: "clients",
    title: "AI Clients (Vendor-Agnostic)",
    color: "#1e3a5f",
    accent: "#4a9eed",
    items: [
      { name: "Claude Desktop", icon: "⚡" },
      { name: "GitHub Copilot", icon: "🤖" },
      { name: "Cursor / Windsurf", icon: "🖊" },
      { name: "CLI (mcp-cli)", icon: "▸" },
      { name: "VS Code Extension", icon: "◆" },
      { name: "Custom Agent", icon: "○" },
    ],
    desc: "Any MCP-compatible client connects via standard JSON-RPC 2.0",
  },
  {
    id: "transport",
    title: "Transport Layer (Multi-Protocol)",
    color: "#2d1b69",
    accent: "#8b5cf6",
    items: [
      { name: "STDIO", icon: "⟶", detail: "Local dev, CLI" },
      { name: "Streamable HTTP", icon: "⟷", detail: "Remote, scalable" },
      { name: "SSE", icon: "↓", detail: "Legacy compat" },
      { name: "WebSocket", icon: "⇄", detail: "Future / realtime" },
    ],
    desc: "Auto-negotiation: client declares capability, server adapts",
  },
  {
    id: "core",
    title: "Core Server (Python, uv add ansible-mcp)",
    color: "#1a4d2e",
    accent: "#22c55e",
    items: [
      { name: "Tool Router + Registry", icon: "⬡", detail: "Plugin discovery, lazy load" },
      { name: "Token Budget Manager", icon: "◎", detail: "Track & compress per-call" },
      { name: "Context Compressor", icon: "⊘", detail: "Prune stale context" },
      { name: "Resource Provider", icon: "◈", detail: "Dynamic docs, schemas" },
      { name: "Auth & Config", icon: "⊡", detail: "AAP tokens, vault" },
    ],
    desc: "Stateless core with plugin dispatch. No VS Code dependency.",
  },
  {
    id: "plugins",
    title: "Plugin Modules (Lazy-Loaded, Composable)",
    color: "#5c3d1a",
    accent: "#f59e0b",
    items: [
      { name: "Lint & Syntax", icon: "✓", detail: "ansible-lint, yamllint" },
      { name: "Playbook Ops", icon: "▶", detail: "create, run, validate" },
      { name: "Inventory", icon: "≡", detail: "parse, query, manage" },
      { name: "Galaxy & Roles", icon: "⊕", detail: "search, install, scaffold" },
      { name: "AAP / Tower", icon: "⊞", detail: "jobs, templates, RBAC" },
      { name: "EE & Navigator", icon: "◐", detail: "exec env, navigator" },
      { name: "Molecule", icon: "⬢", detail: "test scenarios" },
      { name: "Vault", icon: "⊠", detail: "encrypt, decrypt, rekey" },
    ],
    desc: "Each plugin: separate entry point, own tests, own token budget",
  },
  {
    id: "backend",
    title: "System / Backend Layer",
    color: "#5c1a1a",
    accent: "#ef4444",
    items: [
      { name: "ansible-core CLI", icon: "▸" },
      { name: "ansible-lint", icon: "✓" },
      { name: "molecule", icon: "⬢" },
      { name: "AAP REST API", icon: "⟷" },
      { name: "Galaxy API", icon: "⊕" },
      { name: "ansible-navigator", icon: "◐" },
    ],
    desc: "Subprocess / HTTP calls to actual Ansible tooling on the system",
  },
];

const metrics = [
  { label: "Token/Tool Call", target: "< 800 tokens avg", current: "~2400 (upstream)" },
  { label: "Tool Count", target: "8 core + lazy plugins", current: "11 monolithic" },
  { label: "Latency p50", target: "< 200ms", current: "Unmeasured" },
  { label: "Test Coverage", target: "> 90% unit, 100% contract", current: "~15% est." },
  { label: "Transport Support", target: "STDIO + HTTP + SSE", current: "STDIO only" },
  { label: "Client Support", target: "Any MCP client", current: "Copilot only" },
];

const tokenStrategies = [
  { title: "Lazy Tool Registration", desc: "Only advertise tools the client needs. Use listChanged to add/remove dynamically." },
  { title: "Compressed Descriptions", desc: "Short schema descriptions, move verbose docs to resources (ansible:// URIs)." },
  { title: "Streaming Results", desc: "For large outputs (lint results, inventory), stream chunks instead of one giant blob." },
  { title: "Context-Aware Pruning", desc: "If prior tool call returned inventory, don't re-send in subsequent calls." },
  { title: "Result Truncation", desc: "Cap output at N lines with a 'fetch more' resource pattern for pagination." },
  { title: "Plugin Scoping", desc: "Detect workspace type (roles/ vs playbooks/) and only load relevant plugins." },
];

const testMatrix = [
  { layer: "Unit", scope: "Each tool function", framework: "pytest", count: "~120 tests" },
  { layer: "Contract", scope: "MCP JSON-RPC schema", framework: "pytest + jsonschema", count: "~40 tests" },
  { layer: "Integration", scope: "Tool → ansible-core", framework: "pytest + tmpdir", count: "~30 tests" },
  { layer: "Protocol Conformance", scope: "MCP spec compliance", framework: "mcp-inspector", count: "Full spec" },
  { layer: "Transport", scope: "STDIO / HTTP / SSE", framework: "pytest-asyncio", count: "~20 tests" },
  { layer: "Token Budget", scope: "Output size assertions", framework: "custom fixtures", count: "Per tool" },
];

export default function AnsibleMCPArchitecture() {
  const [activeLayer, setActiveLayer] = useState(null);
  const [activeTab, setActiveTab] = useState("arch");

  const tabs = [
    { id: "arch", label: "Architecture" },
    { id: "tokens", label: "Token Strategy" },
    { id: "tests", label: "Test Matrix" },
    { id: "metrics", label: "Metrics" },
    { id: "migration", label: "Migration Plan" },
  ];

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0f",
      color: "#e5e5e5",
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      padding: "24px",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
      `}</style>

      {/* Header */}
      <div style={{ borderBottom: "1px solid #222", paddingBottom: 20, marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8,
            background: "linear-gradient(135deg, #22c55e 0%, #4a9eed 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18, fontWeight: 700,
          }}>A</div>
          <h1 style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontSize: 26, fontWeight: 700, margin: 0,
            background: "linear-gradient(90deg, #22c55e, #4a9eed)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          }}>ansible-mcp</h1>
          <span style={{ color: "#555", fontSize: 14, marginLeft: 4 }}>v2.0 Architecture</span>
        </div>
        <p style={{ color: "#777", fontSize: 13, margin: 0 }}>
          Standalone, vendor-agnostic MCP server for Ansible development tooling — pip installable, plugin-based, token-optimized
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 24 }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: "8px 16px", border: "1px solid",
            borderColor: activeTab === t.id ? "#4a9eed" : "#333",
            background: activeTab === t.id ? "#4a9eed15" : "transparent",
            color: activeTab === t.id ? "#4a9eed" : "#888",
            borderRadius: 6, cursor: "pointer", fontSize: 13,
            fontFamily: "inherit", transition: "all 0.2s",
          }}>{t.label}</button>
        ))}
      </div>

      {/* Architecture Tab */}
      {activeTab === "arch" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {layers.map((layer, i) => (
            <div key={layer.id}
              onMouseEnter={() => setActiveLayer(layer.id)}
              onMouseLeave={() => setActiveLayer(null)}
              style={{
                border: `1px solid ${activeLayer === layer.id ? layer.accent : "#222"}`,
                borderRadius: 10, padding: 16,
                background: activeLayer === layer.id ? `${layer.color}40` : `${layer.color}20`,
                transition: "all 0.3s",
              }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <h3 style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontSize: 15, fontWeight: 600, margin: 0,
                  color: layer.accent,
                }}>{layer.title}</h3>
                <span style={{ fontSize: 11, color: "#555", fontStyle: "italic" }}>Layer {i + 1}</span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
                {layer.items.map(item => (
                  <div key={item.name} style={{
                    padding: "6px 12px", borderRadius: 6,
                    background: `${layer.accent}15`, border: `1px solid ${layer.accent}40`,
                    fontSize: 12, display: "flex", alignItems: "center", gap: 6,
                  }}>
                    <span style={{ opacity: 0.6 }}>{item.icon}</span>
                    <span>{item.name}</span>
                    {item.detail && <span style={{ color: "#666", fontSize: 10 }}>({item.detail})</span>}
                  </div>
                ))}
              </div>
              <p style={{ fontSize: 11, color: "#666", margin: 0 }}>{layer.desc}</p>
              {i < layers.length - 1 && (
                <div style={{ textAlign: "center", marginTop: 8, color: "#444", fontSize: 18 }}>↓</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Token Strategy Tab */}
      {activeTab === "tokens" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{
            padding: 16, borderRadius: 10, border: "1px solid #333",
            background: "#111", marginBottom: 8,
          }}>
            <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 15, color: "#f59e0b", margin: "0 0 8px" }}>
              Why Token Optimization Matters
            </h3>
            <p style={{ fontSize: 12, color: "#999", margin: 0, lineHeight: 1.6 }}>
              The upstream MCP server dumps entire tool schemas + verbose descriptions in every <code style={{color:"#4a9eed"}}>tools/list</code> response.
              With 11 tools averaging ~220 tokens each in description alone, that's ~2,400 tokens <em>before a single tool call</em>.
              Our target: {"<"}800 tokens for tool listing, {"<"}500 tokens per tool response.
            </p>
          </div>
          {tokenStrategies.map((s, i) => (
            <div key={i} style={{
              padding: 14, borderRadius: 8, border: "1px solid #2a2a2a",
              background: "#0f0f15",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <span style={{
                  width: 22, height: 22, borderRadius: "50%",
                  background: "#f59e0b20", border: "1px solid #f59e0b40",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, color: "#f59e0b",
                }}>{i + 1}</span>
                <span style={{ fontWeight: 600, fontSize: 13, color: "#f59e0b" }}>{s.title}</span>
              </div>
              <p style={{ fontSize: 12, color: "#999", margin: 0, paddingLeft: 30 }}>{s.desc}</p>
            </div>
          ))}
        </div>
      )}

      {/* Test Matrix Tab */}
      {activeTab === "tests" && (
        <div>
          <div style={{
            display: "grid", gridTemplateColumns: "1fr 2fr 1.5fr 1fr",
            gap: 1, background: "#222", borderRadius: 10, overflow: "hidden",
          }}>
            {["Layer", "Scope", "Framework", "Coverage"].map(h => (
              <div key={h} style={{
                padding: "10px 14px", background: "#1a1a2e",
                fontSize: 12, fontWeight: 600, color: "#8b5cf6",
              }}>{h}</div>
            ))}
            {testMatrix.map((row, i) => (
              ["layer", "scope", "framework", "count"].map((key, j) => (
                <div key={`${i}-${j}`} style={{
                  padding: "10px 14px", background: i % 2 ? "#0f0f18" : "#111",
                  fontSize: 12, color: j === 0 ? "#22c55e" : "#ccc",
                  fontWeight: j === 0 ? 600 : 400,
                }}>{row[key]}</div>
              ))
            ))}
          </div>
          <div style={{
            marginTop: 16, padding: 14, borderRadius: 8,
            border: "1px solid #333", background: "#111",
          }}>
            <h4 style={{ fontSize: 13, color: "#22c55e", margin: "0 0 8px" }}>CI Pipeline</h4>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {["lint (ruff+mypy)", "unit tests", "contract tests", "integration tests",
                "protocol conformance", "token budget checks", "transport matrix", "coverage gate (90%)"].map(s => (
                <span key={s} style={{
                  padding: "4px 10px", borderRadius: 4, fontSize: 11,
                  background: "#22c55e15", border: "1px solid #22c55e30", color: "#22c55e",
                }}>{s}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Metrics Tab */}
      {activeTab === "metrics" && (
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: 12,
        }}>
          {metrics.map(m => (
            <div key={m.label} style={{
              padding: 16, borderRadius: 10, border: "1px solid #222",
              background: "#0f0f18",
            }}>
              <div style={{ fontSize: 11, color: "#666", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>
                {m.label}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 16, fontWeight: 600, color: "#22c55e" }}>{m.target}</span>
              </div>
              <div style={{ fontSize: 11, color: "#ef4444", marginTop: 6 }}>
                Current upstream: {m.current}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Migration Plan Tab */}
      {activeTab === "migration" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {[
            { phase: "Phase 1", title: "Extract & Scaffold", weeks: "Wk 1-2", color: "#4a9eed",
              tasks: [
                "Create standalone repo: github.com/ansible/ansible-mcp",
                "Python project with pyproject.toml, FastMCP SDK",
                "Port core tools: lint, playbook_create, playbook_run, inventory_parse",
                "STDIO transport working with mcp-inspector validation",
                "Unit tests for every ported tool (>90% coverage)",
              ]},
            { phase: "Phase 2", title: "Plugin System & Transports", weeks: "Wk 3-4", color: "#8b5cf6",
              tasks: [
                "Implement plugin registry with entry_points discovery",
                "Lazy loading: tools only instantiated on first call",
                "Add Streamable HTTP transport for remote hosting",
                "SSE transport for legacy client compat",
                "Contract tests: every tool validated against MCP JSON-RPC schema",
                "Token budget manager: measure & cap output per tool",
              ]},
            { phase: "Phase 3", title: "Advanced Plugins & AAP", weeks: "Wk 5-6", color: "#22c55e",
              tasks: [
                "Galaxy plugin: search, install, scaffold roles/collections",
                "AAP/Tower plugin: job templates, launches, inventories via REST API",
                "Molecule plugin: init, test, converge lifecycle",
                "Vault plugin: encrypt/decrypt/rekey operations",
                "EE plugin: build, inspect execution environments",
                "Integration tests with real ansible-core subprocess calls",
              ]},
            { phase: "Phase 4", title: "Distribution & VS Code Bridge", weeks: "Wk 7-8", color: "#f59e0b",
              tasks: [
                "Publish to PyPI: uv add ansible-mcp / uvx ansible-mcp",
                "Docker image for remote MCP hosting",
                "VS Code extension thin wrapper (just spawns the pip package)",
                "MCP Registry listing for discoverability",
                "Full protocol conformance test suite",
                "Performance benchmarks: latency p50/p99, token usage per tool",
                "Documentation site with client-specific setup guides",
              ]},
          ].map(phase => (
            <div key={phase.phase} style={{
              padding: 16, borderRadius: 10,
              border: `1px solid ${phase.color}40`,
              background: `${phase.color}08`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{
                    padding: "4px 10px", borderRadius: 4, fontSize: 11,
                    background: `${phase.color}20`, color: phase.color, fontWeight: 600,
                  }}>{phase.phase}</span>
                  <span style={{ fontSize: 14, fontWeight: 600, color: "#e5e5e5" }}>{phase.title}</span>
                </div>
                <span style={{ fontSize: 11, color: "#666" }}>{phase.weeks}</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {phase.tasks.map((t, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12, color: "#bbb" }}>
                    <span style={{ color: phase.color, marginTop: 1, flexShrink: 0 }}>▸</span>
                    <span>{t}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div style={{
        marginTop: 24, paddingTop: 16, borderTop: "1px solid #222",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <span style={{ fontSize: 11, color: "#444" }}>
          ansible-mcp rewrite — standalone, vendor-agnostic, token-optimized
        </span>
        <span style={{ fontSize: 11, color: "#444" }}>
          uv add ansible-mcp | docker pull ansible/mcp-server
        </span>
      </div>
    </div>
  );
}
