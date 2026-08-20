import { useCallback, useEffect, useRef, useState } from 'react';

// Maps our app language codes to BCP-47 tags the Web Speech API expects.
const LANG_TAGS = {
  en: 'en-IN', ta: 'ta-IN', te: 'te-IN', kn: 'kn-IN',
  ml: 'ml-IN', hi: 'hi-IN', bn: 'bn-IN', mr: 'mr-IN', gu: 'gu-IN', pa: 'pa-IN',
};

/**
 * Wake-word variants the browser might transcribe "Hey Bhasha" as.
 * Covers common mishearings: "a bhasha", "he bhasha", "hi bhasha", "hey basha".
 */
const WAKE_REGEX = /\b(?:hey|he|hi|a|aye)\s+b[h]?ash[a-z]*/i;

export function useSpeechRecognition(language = 'en', onFinalTranscript) {
  const [transcript, setTranscript] = useState('');
  const [listening, setListening] = useState(false);
  const [error, setError] = useState(null);
  const [volume, setVolume] = useState(0);

  const recognitionRef = useRef(null);
  const audioCtxRef = useRef(null);
  const transcriptRef = useRef('');
  const callbackRef = useRef(onFinalTranscript);
  const continuousModeRef = useRef(false);
  const languageRef = useRef(language);
  const manualCancelRef = useRef(false);
  // Tracks the index of the last result we already processed in continuous mode
  // so we never re-fire the wake word on accumulated old results.
  const lastProcessedIndexRef = useRef(0);

  useEffect(() => { callbackRef.current = onFinalTranscript; }, [onFinalTranscript]);
  useEffect(() => { languageRef.current = language; }, [language]);

  const supported = typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  // ── Build the SpeechRecognition object ONCE ──────────────────────────────
  useEffect(() => {
    if (!supported) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.interimResults = true;
    rec.maxAlternatives = 1;
    // continuous is toggled at start() time so we don't recreate the object.
    rec.continuous = false;
    rec.lang = LANG_TAGS['en'];

    // ── onresult ────────────────────────────────────────────────────────────
    rec.onresult = (event) => {
      if (continuousModeRef.current) {
        // ── CONTINUOUS / WAKE-WORD mode ──────────────────────────────────
        // Process only NEW results since our last check (avoid re-triggering).
        for (let i = lastProcessedIndexRef.current; i < event.results.length; i++) {
          const result = event.results[i];
          const text = result[0].transcript.trim();

          // Show live interim transcript so the user can see we're hearing them.
          setTranscript(text);
          transcriptRef.current = text;

          const m = text.match(WAKE_REGEX);
          if (m) {
            // Extract any command spoken AFTER the wake phrase.
            const afterWake = text.slice(m.index + m[0].length).trim();
            const cmd = afterWake || '__WAKE__';

            // Mark all results up to here as processed.
            lastProcessedIndexRef.current = event.results.length;
            setTranscript('');
            transcriptRef.current = '';

            // Fire immediately — don't wait for isFinal or onend.
            callbackRef.current?.(cmd);
            return; // skip rest of results for this event
          }

          if (result.isFinal) {
            // Final result but no wake word — mark as processed, keep listening.
            lastProcessedIndexRef.current = i + 1;
            setTranscript('');
            transcriptRef.current = '';
          }
        }
      } else {
        // ── SINGLE-SHOT mode ─────────────────────────────────────────────
        let text = '';
        for (let i = 0; i < event.results.length; i++) {
          text += event.results[i][0].transcript;
        }
        transcriptRef.current = text;
        setTranscript(text);
      }
    };

    // ── onerror ─────────────────────────────────────────────────────────────
    rec.onerror = (event) => {
      if (event.error === 'not-allowed') {
        setError('Microphone permission denied. Please allow mic access and try again.');
        setListening(false);
        return;
      }
      // In continuous mode: no-speech / aborted / network errors are expected
      // between phrases — swallow them silently; onend will restart.
      if (continuousModeRef.current) return;
      // In single-shot mode: surface the error.
      if (event.error !== 'aborted') {
        setError(`ASR error: ${event.error}`);
        setListening(false);
      }
    };

    // ── onend ────────────────────────────────────────────────────────────────
    rec.onend = () => {
      if (continuousModeRef.current && !manualCancelRef.current) {
        // Keep listening — restart immediately.
        // Reset result index so we start fresh each session.
        lastProcessedIndexRef.current = 0;
        setTranscript('');
        transcriptRef.current = '';
        // 300 ms grace period — Chrome throws if restarted too fast.
        setTimeout(() => {
          if (!continuousModeRef.current || manualCancelRef.current) return;
          try {
            rec.lang = LANG_TAGS[languageRef.current] || 'en-IN';
            rec.continuous = true; // ensure it stays continuous on each restart
            rec.start();
          } catch (_) { /* already started or page destroyed */ }
        }, 300);
        return;
      }

      // Single-shot mode — fire callback with whatever was captured.
      if (!manualCancelRef.current) {
        const finalText = transcriptRef.current.trim();
        if (finalText) callbackRef.current?.(finalText);
      }
      manualCancelRef.current = false;
      setListening(false);
    };

    recognitionRef.current = rec;
    return () => { try { rec.abort(); } catch (_) {} };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [supported]);

  // ── Volume meter ─────────────────────────────────────────────────────────
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
        setVolume(data.reduce((a, b) => a + b, 0) / data.length / 255);
        requestAnimationFrame(tick);
      };
      tick();
      audioCtxRef.current.deactivate = () => { active = false; };
    } catch { /* cosmetic only — recognition still works */ }
  }, []);

  const stopAudioMeter = useCallback(() => {
    if (audioCtxRef.current) {
      audioCtxRef.current.deactivate?.();
      audioCtxRef.current.stream?.getTracks().forEach(t => t.stop());
      audioCtxRef.current.ctx?.close().catch(() => {});
      audioCtxRef.current = null;
    }
  }, []);

  // ── start(inContinuousMode) ──────────────────────────────────────────────
  /**
   * @param {boolean} inContinuousMode
   *   true  → wake-word mode: rec.continuous=true, fire on "Hey Bhasha" only
   *   false → single-shot:    rec.continuous=false, fire after user pauses
   *
   * continuousModeRef is set HERE (synchronously) not via a useEffect, so
   * the ref is always correct by the time rec.start() fires.
   */
  const start = useCallback(async (inContinuousMode = false) => {
    if (!supported || !recognitionRef.current) {
      setError('Speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }
    setError(null);
    setTranscript('');
    transcriptRef.current = '';
    lastProcessedIndexRef.current = 0;
    manualCancelRef.current = false;
    continuousModeRef.current = inContinuousMode; // ← synchronous update
    setListening(true);
    await startVolumeMeter();
    const rec = recognitionRef.current;
    rec.lang = LANG_TAGS[language] || 'en-IN';
    rec.continuous = inContinuousMode; // ← set mode right before start
    try {
      rec.start();
    } catch (e) {
      setError(`Could not start listening: ${e.message}`);
      setListening(false);
    }
  }, [language, startVolumeMeter, supported]);

  // ── cancel / stop ────────────────────────────────────────────────────────
  const cancel = useCallback(() => {
    manualCancelRef.current = true;
    continuousModeRef.current = false;
    lastProcessedIndexRef.current = 0;
    recognitionRef.current?.stop();
    stopAudioMeter();
    setListening(false);
    setTranscript('');
    transcriptRef.current = '';
  }, [stopAudioMeter]);

  const stop = useCallback(() => {
    continuousModeRef.current = false;
    recognitionRef.current?.stop();
    stopAudioMeter();
    setListening(false);
  }, [stopAudioMeter]);

  return {
    transcript, listening, error, volume,
    supported: !!supported,
    start, stop, cancel, setTranscript,
  };
}
