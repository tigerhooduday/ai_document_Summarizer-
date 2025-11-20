const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

export async function summarize({ text, file, style = "brief", max_tokens }) {
  const url = `${BASE_URL}/summarize`;

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
