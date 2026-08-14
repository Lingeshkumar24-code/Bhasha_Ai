import { Link } from 'react-router-dom';
import Orb from '../three/Orb';
import LogoMark from '../components/LogoMark';

const SWATCHES = [
  ['#FFD700', 'CYBER GOLD'],
  ['#FFB703', 'AMBER'],
  ['#FB8500', 'DEEP AMBER'],
  ['#1A1A1A', 'JET'],
  ['#332200', 'BRONZE SHADOW'],
];

export default function Home() {
  return (
    <div className="page" style={{ textAlign: 'center' }}>
      <div style={{ display: 'flex', justifyContent: 'center', marginTop: 10 }}>
        <LogoMark size={90} />
      </div>
      <div style={{ marginTop: 10 }}>
        <Orb state="idle" volume={0} size={260} />
      </div>
      <h1 style={{ fontSize: '2.8rem', marginBottom: 4, letterSpacing: 1 }}>
        Bhasha<span className="gradient-text">AI</span>
      </h1>
      <p style={{ fontSize: '1rem', color: 'var(--gold-2)', letterSpacing: 3, fontWeight: 600 }}>
        MULTILINGUAL VOICE ASSISTANT
      </p>
      <p style={{ color: 'var(--muted)', maxWidth: 560, margin: '14px auto 20px' }}>
        From Voice to Intelligence — Built for India. A deep-learning voice pipeline
        spanning English, Tamil, Telugu, Kannada, Malayalam and Hindi, with real
        code-mixed understanding like "Fan on karo" or "Chennai weather enna?".
      </p>

      <div className="swatch-row" style={{ marginBottom: 26 }}>
        {SWATCHES.map(([hex, label]) => (
          <div className="swatch" key={hex}>
            <div className="swatch-hex" style={{ background: hex }} />
            <span>{hex}</span>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link className="btn" to="/assistant">🎙 Try the Voice Assistant</Link>
        <Link className="btn secondary" to="/pipeline">View Live Pipeline</Link>
      </div>

      <div style={{ display: 'flex', gap: 30, justifyContent: 'center', marginTop: 30, flexWrap: 'wrap' }}>
        <span style={{ color: 'var(--gold-2)', fontSize: '0.85rem', letterSpacing: 1 }}>🎙 VOICE INPUT</span>
        <span style={{ color: 'var(--gold-2)', fontSize: '0.85rem', letterSpacing: 1 }}>🧠 DEEP LEARNING</span>
      </div>

      <div className="grid cols-4" style={{ marginTop: 50 }}>
        {[
          ['🧠', 'Deep Learning Pipeline', 'ASR → NLP → Intent → NER → Dialogue → LLM → Translation → TTS'],
          ['🌐', '6+ Indian Languages', 'English, Tamil, Telugu, Kannada, Malayalam, Hindi and more'],
          ['🔀', 'Code-Mixed Aware', '"Fan on karo", "Light off pannunga" — understood naturally'],
          ['⚡', 'Groq-Powered', 'Fast LLM responses via secure backend integration'],
        ].map(([icon, title, desc]) => (
          <div className="glass-card" key={title}>
            <div style={{ fontSize: '1.6rem' }}>{icon}</div>
            <h4 style={{ margin: '8px 0 4px', color: 'var(--gold)' }}>{title}</h4>
            <p style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
