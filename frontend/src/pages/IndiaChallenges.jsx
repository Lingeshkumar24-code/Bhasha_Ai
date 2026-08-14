const CHALLENGES = [
  ['Multilingual India', 'India has 22+ scheduled languages.', ['IndicBERT for NLU', 'IndicTrans2 for translation', 'Indian-language TTS']],
  ['Code-Mixing', '"Fan on karo", "Light off pannunga" mix English with Indian languages.', ['Language detection', 'Multilingual tokenizer', 'Code-mixed training examples']],
  ['Accents', 'Tamil-English, Kannada-English, Hindi-English accents vary widely.', ['Diverse training data', 'Fine-tuning on Indian speech', 'Accent-aware evaluation']],
  ['Background Noise', 'Traffic, markets, railway stations, festivals.', ['Noise suppression', 'Voice Activity Detection', 'Audio normalization']],
  ['Low-Resource Languages', 'Some Indian languages have limited training data.', ['Transfer learning', 'Multilingual pretrained models', 'Data augmentation']],
  ['Poor Connectivity', 'Rural/semi-urban network conditions vary.', ['Lightweight frontend', 'Request caching', 'Offline browser TTS fallback']],
  ['Privacy', 'Voice data is sensitive personal information.', ['No unnecessary audio storage', 'User-controlled history', 'Server-side secrets, HTTPS']],
];

export default function IndiaChallenges() {
  return (
    <div className="page">
      <h2 className="gradient-text">India-Specific Challenges &amp; Solutions</h2>
      <div className="grid cols-2">
        {CHALLENGES.map(([title, desc, solutions]) => (
          <div className="glass-card" key={title}>
            <h4 style={{ marginTop: 0 }}>{title}</h4>
            <p style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>{desc}</p>
            <ul style={{ fontSize: '0.85rem' }}>{solutions.map((s) => <li key={s}>{s}</li>)}</ul>
          </div>
        ))}
      </div>
    </div>
  );
}
