import { useState } from 'react';
import LanguageSelector from '../components/LanguageSelector';
import { api } from '../services/api';

export default function NLPAnalyzer() {
  const [text, setText] = useState('Book a flight to Chennai tomorrow at 7 PM');
  const [lang, setLang] = useState('en');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    setLoading(true); setError(null);
    try {
      const res = await api.nlpAnalyze(text, lang);
      setResult(res);
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const highlighted = () => {
    if (!result) return text;
    let parts = [{ t: text, label: null }];
    result.entities.sort((a, b) => a.start - b.start).forEach((e) => {
      const newParts = [];
      parts.forEach((p) => {
        if (p.label || !p.t.includes(e.text)) { newParts.push(p); return; }
        const idx = p.t.indexOf(e.text);
        newParts.push({ t: p.t.slice(0, idx), label: null });
        newParts.push({ t: e.text, label: e.label });
        newParts.push({ t: p.t.slice(idx + e.text.length), label: null });
      });
      parts = newParts;
    });
    return parts.map((p, i) => p.label
      ? <span key={i} className={`badge ${p.label}`} style={{ margin: '0 2px' }}>{p.t}</span>
      : <span key={i}>{p.t}</span>);
  };

  return (
    <div className="page">
      <h2 className="gradient-text">NLP Analysis Panel</h2>
      <div className="glass-card" style={{ margin: '16px 0' }}>
        <LanguageSelector label="Language" value={lang} onChange={setLang} />
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3}
          style={{ width: '100%', marginTop: 10, padding: 10, borderRadius: 10,
            background: 'var(--input-bg)', color: '#fff', border: '1px solid var(--glass-border)' }} />
        <button className="btn" style={{ marginTop: 10 }} onClick={analyze} disabled={loading}>
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </div>
      {error && <div className="glass-card" style={{ borderColor: '#ff5f6d' }}>⚠ {error}</div>}
      {result && (
        <div className="grid cols-2">
          <div className="glass-card">
            <h4 style={{ marginTop: 0 }}>Entities Highlighted</h4>
            <p>{highlighted()}</p>
          </div>
          <div className="glass-card">
            <h4 style={{ marginTop: 0 }}>NLP Analysis</h4>
            <p><b>Language:</b> {result.language}</p>
            <p><b>Intent:</b> {result.intent.label} ({(result.intent.confidence * 100).toFixed(1)}%)</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Model: {result.intent.model}</p>
            <p><b>Sentiment:</b> {result.sentiment}</p>
            <p><b>Entities:</b></p>
            <ul>
              {result.entities.map((e, i) => <li key={i}>{e.label} → {e.text}</li>)}
              {result.entities.length === 0 && <li>None detected</li>}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
