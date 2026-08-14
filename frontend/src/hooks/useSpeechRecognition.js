import { useCallback, useEffect, useRef, useState } from 'react';

// Maps our app language codes to BCP-47 tags the Web Speech API expects.
const LANG_TAGS = {
  en: 'en-IN', ta: 'ta-IN', te: 'te-IN', kn: 'kn-IN',
  ml: 'ml-IN', hi: 'hi-IN', bn: 'bn-IN', mr: 'mr-IN', gu: 'gu-IN', pa: 'pa-IN',
};

/**
 * Real ASR using the browser's native SpeechRecognition (Web Speech API).
 *
 * FIX: the browser recognizer is non-continuous — it stops itself
 * automatically a moment after you finish speaking, firing its own
 * `onend` event. Previously the page only sent the transcript onward when
 * a manual "Stop & Send" button was clicked, which raced with (and usually
 * lost to) that auto-stop, so nothing happened after speaking. Now the
 * hook calls `onFinalTranscript` from `onend` whenever there's a non-empty
 * transcript, so simply speaking and pausing is enough to trigger the rest
 * transcript, so simply speaking and pausing is enough to trigger the rest
 * of the pipeline (answer text + spoken reply) — no extra click needed.
 */
export function useSpeechRecognition(language = 'en', onFinalTranscript, continuousMode = false) {
  const [transcript, setTranscript] = useState('');
  const [listening, setListening] = useState(false);
  const [error, setError] = useState(null);
  const [volume, setVolume] = useState(0);
  const recognitionRef = useRef(null);
  const audioCtxRef = useRef(null);
  const transcriptRef = useRef('');
  const callbackRef = useRef(onFinalTranscript);
  const manualCancelRef = useRef(false);
  const continuousModeRef = useRef(continuousMode);

  useEffect(() => { callbackRef.current = onFinalTranscript; }, [onFinalTranscript]);
  useEffect(() => { continuousModeRef.current = continuousMode; }, [continuousMode]);

  const supported = typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  useEffect(() => {
    if (!supported) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.continuous = continuousMode; // In continuous mode, try to keep it open
    rec.interimResults = true;
    rec.lang = LANG_TAGS[language] || 'en-IN';

    rec.onresult = (event) => {
      let text = '';
      for (let i = 0; i < event.results.length; i++) {
        text += event.results[i][0].transcript;
      }
      transcriptRef.current = text;
      setTranscript(text);
    };
    rec.onerror = (event) => {
      setError(event.error === 'not-allowed' ? 'Microphone permission denied.' : `ASR error: ${event.error}`);
      setListening(false);
    };
    rec.onend = () => {
      const finalText = transcriptRef.current.trim();
      let shouldSend = !!finalText && !manualCancelRef.current;
      let textToSend = finalText;

      if (continuousModeRef.current && shouldSend) {
        // Wake word logic: looking for "Hey Bhasha" or "Hey Basha"
        const wakeWordMatch = finalText.match(/(?:hey b[h]?asha)[\s,]*(.*)/i);
        if (wakeWordMatch) {
           textToSend = wakeWordMatch[1].trim();
           // Only send if there is an actual command after the wake word
           shouldSend = !!textToSend;
        } else {
           // Not triggered by wake word
           shouldSend = false;
        }
      }

      if (shouldSend) {
        callbackRef.current?.(textToSend);
      }

      if (continuousModeRef.current && !manualCancelRef.current) {
        // Automatically restart in continuous mode
        setTranscript('');
        transcriptRef.current = '';
        try { rec.start(); } catch (e) { /* already started or err */ }
      } else {
        setListening(false);
      }
      manualCancelRef.current = false;
    };

    recognitionRef.current = rec;
    return () => rec.abort();
  }, [language, supported, continuousMode]);

  const startVolumeMeter = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);
      audioCtxRef.current = { ctx, stream };

      let active = true;
      const tick = () => {
        if (!active) return;
        analyser.getByteFrequencyData(data);
        const avg = data.reduce((a, b) => a + b, 0) / data.length;
        setVolume(avg / 255);
        requestAnimationFrame(tick);
      };
      tick();
      audioCtxRef.current.deactivate = () => { active = false; };
    } catch {
      // Mic volume meter is cosmetic — recognition still works without it.
    }
  }, []);

  const start = useCallback(async () => {
    if (!supported || !recognitionRef.current) {
      setError('Speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }
    setError(null);
    setTranscript('');
    transcriptRef.current = '';
    manualCancelRef.current = false;
    setListening(true);
    await startVolumeMeter();
    recognitionRef.current.lang = LANG_TAGS[language] || 'en-IN';
    recognitionRef.current.start();
  }, [language, startVolumeMeter, supported]);

  const stopAudioMeter = () => {
    if (audioCtxRef.current) {
      audioCtxRef.current.deactivate?.();
      audioCtxRef.current.stream.getTracks().forEach((t) => t.stop());
      audioCtxRef.current.ctx.close();
    }
  };

  /** Stop early and cancel — does NOT auto-send. */
  const cancel = useCallback(() => {
    manualCancelRef.current = true;
    recognitionRef.current?.stop();
    stopAudioMeter();
    setListening(false);
  }, []);

  /** Stop early but DO send whatever was captured (fires onend -> callback). */
  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    stopAudioMeter();
    setListening(false);
  }, []);

  return { transcript, listening, error, volume, supported: !!supported, start, stop, cancel, setTranscript };
}
