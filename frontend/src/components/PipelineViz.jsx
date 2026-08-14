const STAGES = [
  ['preprocessing', '🎧', 'Preprocessing'],
  ['asr', '🧠', 'Whisper / Browser ASR'],
  ['nlp', '🔤', 'NLP'],
  ['intent', '🎯', 'Intent'],
  ['ner', '🏷', 'Entity (NER)'],
  ['dialogue', '💬', 'Dialogue Manager'],
  ['llm', '⚡', 'Groq LLM'],
  ['translation', '🌐', 'Translation'],
  ['tts', '🔊', 'TTS'],
];

export default function PipelineViz({ status = {}, activeStage = null }) {
  return (
    <div className="grid cols-3">
      {STAGES.map(([key, icon, label]) => {
        const s = status[key];
        const isActive = activeStage === key;
        const isDone = s === 'completed';
        const isFailed = typeof s === 'string' && s.startsWith('failed');
        const cls = isFailed ? 'failed' : isActive ? 'active' : isDone ? 'done' : '';
        return (
          <div key={key} className={`pipeline-node ${cls}`}>
            <span style={{ fontSize: '1.3rem' }}>{icon}</span>
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{label}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>
                {isFailed ? '⚠ ' + s : isDone ? '✓ Complete' : isActive ? 'Processing…' : s || 'Pending'}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
