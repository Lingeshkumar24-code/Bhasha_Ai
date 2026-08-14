import { useEffect, useState } from 'react';
import { api } from '../services/api';

export default function ModelLab() {
  const [models, setModels] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => { api.models().then(setModels).catch((e) => setError(e.message)); }, []);

  return (
    <div className="page">
      <h2 className="gradient-text">Model Lab</h2>
      <p style={{ color: 'var(--muted)' }}>
        Academic requirement: this page clearly separates <b>pretrained foundation models</b>
        (used as-is for computationally expensive tasks) from <b>our own fine-tuned models</b>
        (trained specifically for this project — see <code>/training</code>).
      </p>
      {error && <div className="glass-card">⚠ {error}. Start the backend to see live model status.</div>}
      {models && (
        <>
          <h3>Pretrained Foundation Models</h3>
          <div className="grid cols-2">
            {models.pretrained_foundation_models.map((m) => (
              <div className="glass-card" key={m.name}>
                <h4 style={{ margin: 0 }}>{m.name}</h4>
                <p style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>{m.task} · {m.source}</p>
              </div>
            ))}
          </div>
          <h3 style={{ marginTop: 28 }}>Our Trained / Fine-Tuned Models</h3>
          <div className="grid cols-2">
            {models.our_trained_models.map((m) => (
              <div className="glass-card" key={m.name}>
                <h4 style={{ margin: 0 }}>{m.name}</h4>
                <p style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>{m.task}</p>
                <p style={{ fontSize: '0.78rem' }}>{m.status}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
