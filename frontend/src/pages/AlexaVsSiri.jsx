export default function AlexaVsSiri() {
  const rows = [
    ['Company', 'Amazon', 'Apple'],
    ['Primary Ecosystem', 'Echo devices', 'Apple devices'],
    ['Voice Input', 'Yes', 'Yes'],
    ['Cloud AI', 'Yes', 'Yes'],
    ['On-device AI', 'Varies by device', 'Strong emphasis (Apple Silicon)'],
    ['Smart Home', 'Strong (Alexa Skills)', 'Strong (HomeKit)'],
    ['Multilingual', 'Yes', 'Yes'],
    ['Privacy Positioning', 'Published privacy controls', 'Published privacy controls'],
  ];
  return (
    <div className="page">
      <h2 className="gradient-text">Alexa vs Siri — General Comparison</h2>
      <p style={{ color: 'var(--muted)', maxWidth: 800 }}>
        This is an educational, high-level comparison based on publicly available product
        information. BhashaVoice AI does not claim to replicate Alexa's or Siri's proprietary
        internal architectures — it is an independent educational recreation of the general
        voice-assistant pipeline (ASR → NLP → LLM → TTS) applied to Indian languages.
      </p>
      <table className="styled">
        <thead><tr><th></th><th>Alexa</th><th>Siri</th></tr></thead>
        <tbody>
          {rows.map(([label, a, s]) => (
            <tr key={label}><td>{label}</td><td>{a}</td><td>{s}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
