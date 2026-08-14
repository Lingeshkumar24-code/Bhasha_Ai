import { useEffect, useState } from 'react';
import { api } from '../services/api';

function Metric({ label, value }) {
  return (
    <div className="glass-card">
      <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>{label}</div>
      <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
      </div>
    </div>
  );
}

export default function Evaluation() {
  const [metrics, setMetrics] = useState(null);
  useEffect(() => { api.metrics().then(setMetrics).catch(() => setMetrics({ error: 'Backend unreachable' })); }, []);

  return (
    <div className="page">
      <h2 className="gradient-text">Evaluation Dashboard</h2>
      <p style={{ color: 'var(--muted)' }}>
        Real metrics only — never invented. Until training/evaluate.py has been run,
        each metric honestly reads "Not evaluated yet".
      </p>
      {metrics && (
        <div className="grid cols-4">
          <Metric label="Intent Accuracy/F1" value={metrics.intent} />
          <Metric label="NER Precision/Recall/F1" value={metrics.ner} />
          <Metric label="ASR WER" value={metrics.asr_wer} />
          <Metric label="Translation BLEU" value={metrics.translation_bleu} />
        </div>
      )}
    </div>
  );
}
