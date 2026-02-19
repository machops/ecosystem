export interface ApiClientOptions {
  baseUrl: string;
  getToken?: () => Promise<string | null>;
}

export interface AuthSession {
  access_token: string;
  refresh_token: string;
  expires_at?: number;
}

export interface AuthResponse {
  user: { id: string; email: string; role?: string; urn?: string };
  session: AuthSession | null;
}

export function createApiClient(options: ApiClientOptions) {
  const { baseUrl, getToken } = options;

  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const token = await getToken?.();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }

    return res.json() as Promise<T>;
  }

  return {
    auth: {
      signup: (body: { email: string; password: string; display_name?: string }) =>
        request<AuthResponse>("POST", "/auth/signup", body),
      login: (body: { email: string; password: string }) =>
        request<AuthResponse>("POST", "/auth/login", body),
      refresh: (refresh_token: string) =>
        request<{ session: AuthSession }>("POST", "/auth/refresh", { refresh_token }),
      me: () => request<{ user: { id: string; email: string; role: string; urn: string } }>("GET", "/auth/me"),
      logout: () => request<{ ok: boolean }>("POST", "/auth/logout"),
    },
    platforms: {
      list: () => request<{ platforms: unknown[]; total: number }>("GET", "/api/v1/platforms"),
      get: (id: string) => request<{ platform: unknown }>("GET", `/api/v1/platforms/${id}`),
      create: (body: { name: string; slug: string; capabilities?: string[]; deployTarget?: string }) =>
        request<{ platform: unknown }>("POST", "/api/v1/platforms", body),
      update: (id: string, body: Record<string, unknown>) =>
        request<{ platform: unknown }>("PATCH", `/api/v1/platforms/${id}`, body),
      delete: (id: string) => request<{ message: string }>("DELETE", `/api/v1/platforms/${id}`),
    },
    yaml: {
      generate: (moduleJson: unknown) =>
        request<{ qyaml_content: string; valid: boolean; warnings: string[] }>(
          "POST", "/api/v1/yaml/generate", moduleJson
        ),
      validate: (content: string) =>
        request<{ valid: boolean; missing_blocks: string[] }>(
          "POST", "/api/v1/yaml/validate", { content }
        ),
      registry: () => request<{ services: unknown[] }>("GET", "/api/v1/yaml/registry"),
    },
    ai: {
      generate: (prompt: string, modelId?: string) =>
        request<unknown>("POST", "/api/v1/ai/generate", { prompt, model_id: modelId || "default" }),
      chatCompletions: (body: { model?: string; messages: { role: string; content: string }[] }) =>
        request<unknown>("POST", "/api/v1/ai/chat/completions", body),
      models: () => request<unknown>("GET", "/api/v1/ai/models"),
      getJob: (jobId: string) => request<unknown>("GET", `/api/v1/ai/jobs/${jobId}`),
      vectorAlign: (tokens: string[], targetDim?: number) =>
        request<unknown>("POST", "/api/v1/ai/vector/align", {
          tokens,
          target_dim: targetDim || 1024,
          alignment_model: "quantum-bert-xxl-v1",
        }),
    },
    health: {
      liveness: () => request<{ status: string }>("GET", "/health"),
      readiness: () => request<unknown>("GET", "/ready"),
      metrics: () => fetch(`${baseUrl}/health/metrics`).then((r) => r.text()),
    },
  };
}
