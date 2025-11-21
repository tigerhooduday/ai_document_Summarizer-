
const DEFAULT_API = import.meta.env.VITE_API_BASE ?? "https://ai-document-summarizer-23496485622.asia-south2.run.app";
export const BASE_URL = DEFAULT_API.endsWith("/api") ? DEFAULT_API.slice(0, -4) : DEFAULT_API;

export async function summarize({ text, file, style = "brief", max_tokens }) {
  const url = `${BASE_URL}/api/summarize`;

  if (file) {
    const form = new FormData();
    form.append("file", file);
    form.append("style", style);
    if (max_tokens) form.append("max_tokens", String(max_tokens));
    const res = await fetch(url, { method: "POST", body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API error");
    }
    return res.json();
  }

  const payload = { text, style };
  if (max_tokens) payload.max_tokens = max_tokens;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}
