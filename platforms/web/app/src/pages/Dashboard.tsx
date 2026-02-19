import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = "";

interface HealthData {
  status: string;
  service: string;
  version: string;
  engines?: string[];
  uptime_seconds?: number;
  timestamp?: string;
}

interface ModelInfo {
  id: string;
  name?: string;
  provider?: string;
  status: string;
  capabilities?: string[];
}

interface UserInfo {
  id: string;
  email: string;
  role: string;
  urn?: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [prompt, setPrompt] = useState("");
  const [aiResult, setAiResult] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState("");

  const token = localStorage.getItem("eco_token");

  const authHeaders = useCallback((): Record<string, string> => {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (token) h["Authorization"] = `Bearer ${token}`;
    return h;
  }, [token]);

  useEffect(() => {
    const stored = localStorage.getItem("eco_user");
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch {}
    }
    if (!token) {
      navigate("/login");
      return;
    }

    fetch(`${API_BASE}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable", service: "ai", version: "?" }));

    fetch(`${API_BASE}/api/v1/ai/models`, { headers: authHeaders() })
      .then((r) => {
        if (r.status === 401) { navigate("/login"); return []; }
        return r.json();
      })
      .then((data) => {
        if (Array.isArray(data)) setModels(data);
        else if (data?.models) setModels(data.models);
        else if (data?.data) setModels(data.data);
      })
      .catch(() => {});
  }, [token, navigate, authHeaders]);

  async function handleGenerate() {
    if (!prompt.trim()) return;
    setAiLoading(true);
    setAiResult("");
    setError("");

    try {
      const res = await fetch(`${API_BASE}/api/v1/ai/generate`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ prompt, model_id: "default", max_tokens: 512 }),
      });

      if (res.status === 401) { navigate("/login"); return; }

      const data = await res.json();
      if (!res.ok) {
        setError(data.message || data.error || `HTTP ${res.status}`);
      } else {
        setAiResult(data.content || data.result || JSON.stringify(data, null, 2));
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setAiLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("eco_token");
    localStorage.removeItem("eco_refresh_token");
    localStorage.removeItem("eco_user");
    navigate("/login");
  }

  const statusColor = (s: string) =>
    s === "healthy" || s === "available" || s === "ready"
      ? "#06D6A0"
      : s === "degraded" || s === "loading"
      ? "#FFB703"
      : "#F72585";

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "var(--color-bg, #06060F)",
        color: "var(--color-text, #E0E0E0)",
        fontFamily: "monospace",
        padding: 24,
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 32,
          paddingBottom: 16,
          borderBottom: "1px solid #1a1a2e",
        }}
      >
        <div>
          <h1 style={{ color: "var(--color-primary, #00F5D4)", fontSize: 22, margin: 0 }}>
            indestructibleeco
          </h1>
          <span style={{ color: "#6B7A99", fontSize: 12 }}>Dashboard — v1.0</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {user && (
            <span style={{ color: "#9CA3AF", fontSize: 13 }}>
              {user.email} ({user.role})
            </span>
          )}
          <button
            onClick={handleLogout}
            style={{
              padding: "6px 14px",
              borderRadius: 6,
              border: "1px solid #2a2a3e",
              background: "transparent",
              color: "#9CA3AF",
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, maxWidth: 1200 }}>
        {/* Health Card */}
        <div
          style={{
            padding: 20,
            borderRadius: 10,
            background: "var(--color-surface, #0D0D1A)",
            border: "1px solid #1a1a2e",
          }}
        >
          <h2 style={{ fontSize: 14, color: "#9CA3AF", marginBottom: 12 }}>Service Health</h2>
          {health ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: statusColor(health.status),
                    display: "inline-block",
                  }}
                />
                <span style={{ fontSize: 16, fontWeight: 600 }}>{health.status}</span>
                <span style={{ color: "#6B7A99", fontSize: 12 }}>
                  {health.service} v{health.version}
                </span>
              </div>
              {health.engines && health.engines.length > 0 && (
                <div style={{ fontSize: 12, color: "#6B7A99" }}>
                  Engines: {health.engines.join(", ")}
                </div>
              )}
              {health.uptime_seconds !== undefined && (
                <div style={{ fontSize: 12, color: "#6B7A99" }}>
                  Uptime: {Math.floor(health.uptime_seconds / 60)}m {Math.floor(health.uptime_seconds % 60)}s
                </div>
              )}
            </div>
          ) : (
            <span style={{ color: "#6B7A99" }}>Loading...</span>
          )}
        </div>

        {/* Models Card */}
        <div
          style={{
            padding: 20,
            borderRadius: 10,
            background: "var(--color-surface, #0D0D1A)",
            border: "1px solid #1a1a2e",
          }}
        >
          <h2 style={{ fontSize: 14, color: "#9CA3AF", marginBottom: 12 }}>
            Models ({models.length})
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 200, overflowY: "auto" }}>
            {models.length === 0 && <span style={{ color: "#6B7A99", fontSize: 13 }}>No models loaded</span>}
            {models.map((m) => (
              <div
                key={m.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "6px 10px",
                  borderRadius: 6,
                  background: "#0a0a14",
                  fontSize: 13,
                }}
              >
                <span>{m.id}</span>
                <span
                  style={{
                    fontSize: 11,
                    padding: "2px 8px",
                    borderRadius: 10,
                    background: statusColor(m.status) + "22",
                    color: statusColor(m.status),
                  }}
                >
                  {m.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Generate Card — full width */}
        <div
          style={{
            gridColumn: "1 / -1",
            padding: 20,
            borderRadius: 10,
            background: "var(--color-surface, #0D0D1A)",
            border: "1px solid #1a1a2e",
          }}
        >
          <h2 style={{ fontSize: 14, color: "#9CA3AF", marginBottom: 12 }}>AI Generate</h2>
          <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleGenerate(); }}
              placeholder="Enter a prompt..."
              style={{
                flex: 1,
                padding: "10px 12px",
                borderRadius: 6,
                border: "1px solid #2a2a3e",
                background: "#0a0a14",
                color: "#E0E0E0",
                fontSize: 14,
                outline: "none",
              }}
            />
            <button
              onClick={handleGenerate}
              disabled={aiLoading || !prompt.trim()}
              style={{
                padding: "10px 20px",
                borderRadius: 6,
                border: "none",
                background: aiLoading ? "#2a2a3e" : "var(--color-accent, #4361EE)",
                color: "#fff",
                fontSize: 14,
                fontWeight: 600,
                cursor: aiLoading ? "not-allowed" : "pointer",
                whiteSpace: "nowrap",
              }}
            >
              {aiLoading ? "Generating..." : "Generate"}
            </button>
          </div>
          {error && <p style={{ color: "var(--color-danger, #F72585)", fontSize: 13, marginBottom: 8 }}>{error}</p>}
          {aiResult && (
            <pre
              style={{
                padding: 16,
                borderRadius: 6,
                background: "#0a0a14",
                color: "#06D6A0",
                fontSize: 13,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                maxHeight: 300,
                overflowY: "auto",
              }}
            >
              {aiResult}
            </pre>
          )}
        </div>
      </div>
    </main>
  );
}
