const BASE = import.meta.env.VITE_API_BASE || '';

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request to ${path} failed (${res.status})`);
  }
  return res.json();
}

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`Request to ${path} failed (${res.status})`);
  return res.json();
}

export const api = {
  health: () => get('/health'),
  models: () => get('/api/models'),
  metrics: () => get('/api/metrics'),
  nlpAnalyze: (text, language) => post('/api/nlp/analyze', { text, language }),
  chat: (session_id, message, output_language) =>
    post('/api/chat', { session_id, message, output_language }),
  translate: (text, source_language, target_language) =>
    post('/api/translate', { text, source_language, target_language }),
  tts: (text, language) => post('/api/tts', { text, language }),
  fullPipeline: (payload) => post('/api/voice/full-pipeline', payload),
};

export function audioUrl(path) {
  if (!path) return null;
  return path.startsWith('http') ? path : `${BASE}${path}`;
}
