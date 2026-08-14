import { useState } from 'react';
import PipelineViz from '../components/PipelineViz';
import StatusPanel from '../components/StatusPanel';
import { api } from '../services/api';

export default function LivePipeline() {
  const [status, setStatus] = useState({});
  const [running, setRunning] = useState(false);

  const simulate = async () => {
    setRunning(true);
    const order = ['preprocessing', 'asr', 'nlp', 'intent', 'ner', 'dialogue', 'llm', 'translation', 'tts'];
    const s = {};
    for (const stage of order) {
      s[stage] = undefined;
      setStatus({ ...s, [stage]: 'active' });
      await new Promise((r) => setTimeout(r, 350));
      s[stage] = 'completed';
      setStatus({ ...s });
    }
    setRunning(false);
  };

  return (
    <div className="page">
      <h2 className="gradient-text">Live AI Pipeline</h2>
      <p style={{ color: 'var(--muted)' }}>
        This view illustrates every stage of the real pipeline used by the Voice Assistant page.
        Click below for a staged walkthrough animation, or go to the Voice Assistant to run it for real.
      </p>
      <button className="btn" onClick={simulate} disabled={running}>
        {running ? 'Running…' : '▶ Animate Pipeline Stages'}
      </button>
      <div className="glass-card" style={{ margin: '20px 0' }}>
        <PipelineViz status={status} />
      </div>
      <StatusPanel />
    </div>
  );
}
