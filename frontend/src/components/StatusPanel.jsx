import { useEffect, useState } from 'react';
import { api } from '../services/api';

function Dot({ ok, label, detail }) {
  const cls = ok === true ? 'ready' : ok === false ? 'down' : 'warn';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0' }}>
      <span className={`dot ${cls}`} />
      <span style={{ fontSize: '0.85rem' }}>{label}</span>
      <span style={{ fontSize: '0.72rem', color: 'var(--muted)', marginLeft: 'auto' }}>{detail}</span>
    </div>
  );
}

export default function StatusPanel() {
  const [health, setHealth] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.health().then(setHealth).catch((e) => setErr(e.message));
  }, []);

  if (err) return <div className="glass-card">⚠ Backend unreachable: {err}. Start it with `uvicorn main:app` in /backend.</div>;
  if (!health) return <div className="glass-card">Checking system status…</div>;

  const c = health.components;
  return (
    <div className="glass-card">
      <h3 style={{ marginTop: 0 }}>System Status</h3>
      <Dot ok={true} label="Microphone (browser)" detail="Web Speech API" />
      <Dot ok={true} label="ASR" detail="Browser SpeechRecognition" />
      <Dot ok={true} label="NLP" detail="Active" />
      <Dot ok={c.intent_model.includes('trained')} label="Intent Model" detail={c.intent_model} />
      <Dot ok={c.ner_model.includes('trained')} label="NER" detail={c.ner_model} />
      <Dot ok={c.groq.includes('READY')} label="Groq" detail={c.groq} />
      <Dot ok={true} label="Translation" detail={c.translation} />
      <Dot ok={true} label="TTS" detail={c.tts} />
    </div>
  );
}
