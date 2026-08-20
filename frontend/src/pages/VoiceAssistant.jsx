import { useMemo, useRef, useState } from 'react';
import Orb from '../three/Orb';
import LanguageSelector from '../components/LanguageSelector';
import PipelineViz from '../components/PipelineViz';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';
import { api, audioUrl } from '../services/api';

const DEMO_COMMANDS = [
  { lang: 'en', text: 'What is the weather today?' },
  { lang: 'ta', text: 'இன்று வானிலை எப்படி இருக்கிறது?' },
  { lang: 'kn', text: 'ಇಂದಿನ ಹವಾಮಾನ ಹೇಗಿದೆ?' },
  { lang: 'te', text: 'ఈరోజు వాతావరణం ఎలా ఉంది?' },
  { lang: 'ml', text: 'ഇന്നത്തെ കാലാവസ്ഥ എങ്ങനെയാണ്?' },
  { lang: 'en', text: 'Fan on karo' },
];

export default function VoiceAssistant() {
  const [inputLang, setInputLang] = useState('en');
  const [outputLang, setOutputLang] = useState('en');
  const [uiState, setUiState] = useState('idle'); // idle | listening | processing | speaking
  const [continuousMode, setContinuousMode] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const sessionId = useMemo(() => `session-${Math.random().toString(36).slice(2)}`, []);
  const audioRef = useRef(null);

  const stopSpeech = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  };

  // Wake-word acknowledgement in each supported output language.
  const WAKE_ACK = {
    en: 'Yes, how can I help you?',
    ta: 'சொல்லுங்கள், எப்படி உதவலாம்?',
    kn: 'ಹೇಳಿ, ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?',
    te: 'చెప్పండి, నేను ఎలా సహాయం చేయాలి?',
    ml: 'പറയൂ, ഞാൻ എങ്ങനെ സഹായിക്കട്ടെ?',
    hi: 'बताइए, मैं कैसे मदद कर सकती हूँ?',
    bn: 'বলুন, আমি কীভাবে সাহায্য করতে পারি?',
    mr: 'सांगा, मी कशी मदत करू?',
    gu: 'કહો, હું કેવી રીતે મદદ કરી શકું?',
    pa: 'ਦੱਸੋ, ਮੈਂ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦੀ ਹਾਂ?',
  };

  const runPipeline = async (text) => {
    if (!text || !text.trim()) { setUiState('idle'); return; }
    stopSpeech();
    if (text === '__WAKE__') {
      // Just "Hey Bhasha" — acknowledge so the user knows it heard them.
      const ack = WAKE_ACK[outputLang] || WAKE_ACK.en;
      setResult(null);
      setUiState('speaking');
      speak(ack, outputLang);
      setTimeout(() => setUiState('idle'), 2500);
      return;
    }
    setUiState('processing');
    setError(null);
    setResult(null);
    try {
      const res = await api.fullPipeline({
        session_id: sessionId,
        transcript: text.trim(),
        input_language: inputLang,
        output_language: outputLang,
      });
      setResult(res);
      speakResult(res);
    } catch (e) {
      setError(e.message);
      setUiState('idle');
    }
  };

  // Fires automatically the moment the browser finishes hearing you — this
  // is the fix: no separate "send" click needed, so the answer always
  // appears and is always spoken back.
  const { transcript, listening, error: asrError, volume, supported, start, cancel, setTranscript } =
    useSpeechRecognition(inputLang, runPipeline, continuousMode);
  const { speak } = useSpeechSynthesis();

  const speakResult = (res) => {
    setUiState('speaking');
    const url = audioUrl(res.audio_url);
    if (url) {
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => setUiState('idle');
      audio.onerror = () => {
        // Server TTS failed to play — fall back to the browser's own voice.
        speak(res.translated_response, outputLang);
        setTimeout(() => setUiState('idle'), 2500);
      };
      audio.play().catch(() => {
        speak(res.translated_response, outputLang);
        setTimeout(() => setUiState('idle'), 2500);
      });
    } else {
      speak(res.translated_response, outputLang);
      setTimeout(() => setUiState('idle'), 2500);
    }
  };

  const handleMicClick = async () => {
    if (continuousMode) {
      setContinuousMode(false); // Turn off continuous mode if they manually click mic
    }
    if (listening) {
      cancel(); // manual stop = cancel, no send (user changed their mind)
      setUiState('idle');
      return;
    }
    setResult(null);
    setError(null);
    setUiState('listening');
    await start();
  };

  const handleContinuousToggle = async () => {
    if (continuousMode) {
      setContinuousMode(false);
      cancel();
      setUiState('idle');
    } else {
      setContinuousMode(true);
      setResult(null);
      setError(null);
      setUiState('listening');
      setTimeout(async () => await start(), 50);
    }
  };

  const runDemo = (cmd) => {
    setInputLang(cmd.lang);
    setTranscript(cmd.text);
    runPipeline(cmd.text);
  };

  return (
    <div className="page">
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 20 }}>
        <LanguageSelector label="Input Language" value={inputLang} onChange={setInputLang} />
        <LanguageSelector label="Output Language" value={outputLang} onChange={setOutputLang} />
      </div>

      <div style={{ textAlign: 'center' }}>
        <Orb state={uiState} volume={volume} size={240} />
        <p style={{ color: 'var(--muted)', marginTop: 6 }}>
          {uiState === 'idle' && 'How can I help you?'}
          {uiState === 'listening' && (continuousMode ? 'Listening for "Hey Bhasha"...' : 'Listening… speak now, I\'ll answer as soon as you pause')}
          {uiState === 'processing' && 'AI Processing…'}
          {uiState === 'speaking' && 'Speaking response…'}
        </p>

        {!supported && (
          <div className="glass-card" style={{ maxWidth: 440, margin: '10px auto', color: '#ffcf5c' }}>
            ⚠ Your browser doesn't support live speech recognition. Try Chrome or Edge,
            or type a command below.
          </div>
        )}

        <button className={`mic-btn ${listening && !continuousMode ? 'listening' : ''}`} onClick={handleMicClick}>
          🎙
        </button>
        {listening && !continuousMode && (
          <p style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: 8 }}>
            Tap again to cancel · transcript so far: <i>{transcript || '…'}</i>
          </p>
        )}
        
        <div style={{ marginTop: 16 }}>
          <button 
            className={`btn ${continuousMode ? 'primary' : 'secondary'}`} 
            onClick={handleContinuousToggle}
            disabled={listening && !continuousMode}
          >
            {continuousMode ? '⏹ Stop Wake Word Mode' : 'Continuous Listen (Hey Bhasha)'}
          </button>
        </div>

        {listening && continuousMode && (
          <p style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: 8 }}>
            Listening... Say "Hey Bhasha [command]" (e.g. "Hey Bhasha what is the weather")
            <br /><i>{transcript || '…'}</i>
          </p>
        )}

        {asrError && <p style={{ color: '#ff5f6d', marginTop: 10 }}>{asrError}</p>}
      </div>

      <div className="glass-card" style={{ margin: '24px 0' }}>
        <form onSubmit={(e) => { e.preventDefault(); runPipeline(transcript); }}>
          <input
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="…or type a command here and press Enter"
            style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--glass-border)',
              background: 'var(--input-bg)', color: '#fff' }}
          />
        </form>
      </div>

      <div className="glass-card" style={{ marginBottom: 24 }}>
        <h4 style={{ marginTop: 0 }}>Demo Mode — try a sample command (runs the real pipeline)</h4>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {DEMO_COMMANDS.map((c) => (
            <button key={c.text} className="btn secondary" onClick={() => runDemo(c)}>{c.text}</button>
          ))}
        </div>
      </div>

      {error && (
        <div className="glass-card" style={{ borderColor: '#ff5f6d', marginBottom: 20 }}>
          ⚠ {error}. Your transcript is still available above — please try again.
        </div>
      )}

      {result && (
        <>
          <div className="grid cols-2" style={{ marginBottom: 20 }}>
            <div className="glass-card">
              <h4 style={{ marginTop: 0, color: 'var(--gold-2)' }}>Transcript</h4>
              <p>{result.transcript}</p>
            </div>
            <div className="glass-card">
              <h4 style={{ marginTop: 0, color: 'var(--gold)' }}>AI Response</h4>
              <p>{result.translated_response}</p>
              <button className="btn secondary" onClick={() => speakResult(result)}>🔁 Replay voice</button>
            </div>
          </div>

          <div className="grid cols-4" style={{ marginBottom: 20 }}>
            <div className="glass-card">
              <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>Intent</div>
              <div style={{ fontWeight: 700 }}>{result.intent.label}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>{result.intent.model}</div>
            </div>
            <div className="glass-card">
              <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>Confidence</div>
              <div style={{ fontWeight: 700 }}>{(result.intent.confidence * 100).toFixed(1)}%</div>
            </div>
            <div className="glass-card">
              <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>Language</div>
              <div style={{ fontWeight: 700 }}>{result.language.toUpperCase()}</div>
            </div>
            <div className="glass-card">
              <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>Entities</div>
              <div>
                {result.entities.length === 0 && <span style={{ color: 'var(--muted)' }}>None detected</span>}
                {result.entities.map((e, i) => (
                  <span key={i} className={`badge ${e.label}`} style={{ marginRight: 4 }}>{e.label}: {e.text}</span>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-card">
            <h4 style={{ marginTop: 0 }}>Pipeline Status</h4>
            <PipelineViz status={result.pipeline} />
          </div>
        </>
      )}
    </div>
  );
}
