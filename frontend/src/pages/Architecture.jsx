const STEPS = [
  ['🎙 Input', 'Browser microphone capture via getUserMedia'],
  ['🎧 Preprocessing', 'Sample-rate normalization, silence trimming, Voice Activity Detection (client-side)'],
  ['🧠 ASR', 'Browser Web Speech API (server Whisper hook available in app/asr/)'],
  ['🔤 NLP', 'Tokenization and language identification'],
  ['🎯 Intent', 'Fine-tuned IndicBERT classifier (falls back to keyword baseline until trained)'],
  ['🏷 Entity (NER)', 'Fine-tuned token-classification model (falls back to regex+gazetteer until trained)'],
  ['💬 Dialogue Manager', 'Bounded conversation-state object with slot filling'],
  ['⚡ Groq LLM', 'Secure backend call to Groq API — key never exposed to frontend'],
  ['🌐 Translation', 'IndicTrans2 (pluggable) with Google-Translate fallback'],
  ['🔊 TTS', 'Server gTTS / Indic TTS (pluggable), browser SpeechSynthesis as final fallback'],
];

export default function Architecture() {
  return (
    <div className="page">
      <h2 className="gradient-text">System Architecture</h2>
      <p style={{ color: 'var(--muted)' }}>
        Client-side audio processing note: because this build runs ASR/VAD in the browser
        (Web Speech API) rather than a heavy server-side model, "preprocessing" concretely means
        the browser's own noise handling plus a lightweight volume/silence check before ASR
        is invoked — this keeps the deployed app fast and free-tier friendly.
      </p>
      <div className="grid cols-2">
        {STEPS.map(([title, desc]) => (
          <div className="glass-card" key={title}>
            <h4 style={{ margin: 0 }}>{title}</h4>
            <p style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
