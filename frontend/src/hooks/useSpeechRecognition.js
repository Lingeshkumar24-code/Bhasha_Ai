import { useCallback, useEffect, useRef, useState } from 'react';

// Maps our app language codes to BCP-47 tags the Web Speech API expects.
const LANG_TAGS = {
  en: 'en-IN', ta: 'ta-IN', te: 'te-IN', kn: 'kn-IN',
  ml: 'ml-IN', hi: 'hi-IN', bn: 'bn-IN', mr: 'mr-IN', gu: 'gu-IN', pa: 'pa-IN',
};

/**
 * Real ASR using the browser's native SpeechRecognition (Web Speech API).
 *
 * KEY DESIGN:
 * - The SpeechRecognition object is created ONCE and reused forever.
 * - We deliberately do NOT use rec.continuous=true because Chrome's
 *   continuous mode accumulates results across utterances and rarely fires
 *   onend, making reliable wake-word detection very hard.
 * - Instead, we use rec.continuous=false (the default) and restart in onend.
 *   This gives us a clean result buffer each restart and a reliable onend hook.
 * - All runtime decisions read from refs, never from stale closures.
 * - continuousModeRef is updated SYNCHRONOUSLY from the caller via
 *   setContinuousMode() — NOT via a useEffect — so it is always current
 *   when start() fires even 50ms after a React state update.
 */
export function useSpeechRecognition(language = 'en', onFinalTranscript) {
  const [transcript, setTranscript] = useState('');
  const [listening, setListening] = useState(false);
  const [error, setError] = useState(null);
  const [volume, setVolume] = useState(0);
  const recognitionRef = useRef(null);
  const audioCtxRef = useRef(null);
  const transcriptRef = useRef('');
  const callbackRef = useRef(onFinalTranscript);
  const manualCancelRef = useRef(false);
  // These refs are updated SYNCHRONOUSLY — not via useEffect — so they are
  // always current by the time any async callback or setTimeout reads them.
  const continuousModeRef = useRef(false);
  const languageRef = useRef(language);
  const pendingWakeCmdRef = useRef('');

  useEffect(() => { callbackRef.current = onFinalTranscript; }, [onFinalTranscript]);
  useEffect(() => { languageRef.current = language; }, [language]);

  const supported = typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  // Create the recognizer ONCE. No deps on language or continuousMode —
  // all runtime values come from refs so nothing needs to be recreated.
  useEffect(() => {
    if (!supported) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    // We always use continuous=false for reliability (see module doc above).
    rec.continuous = false;
    rec.interimResults = true;
    rec.lang = LANG_TAGS['en'];

    rec.onresult = (event) => {
      let text = '';
      for (let i = 0; i < event.results.length; i++) {
        text += event.results[i][0].transcript;
      }
      transcriptRef.current = text;
      setTranscript(text);
    };

    rec.onerror = (event) => {
      // In continuous (wake-word) mode, no-speech and aborted are normal
      // between utterances — silently swallow them and let onend restart.
      if (continuousModeRef.current &&
          (event.error === 'no-speech' || event.error === 'aborted')) return;
      if (event.error === 'not-allowed') {
        setError('Microphone permission denied. Please allow mic access and try again.');
      } else if (event.error !== 'aborted') {
        setError(`ASR error: ${event.error}`);
      }
      setListening(false);
    };

    rec.onend = () => {
      const finalText = transcriptRef.current.trim();
      let shouldSend = !!finalText && !manualCancelRef.current;
      let textToSend = finalText;

      if (continuousModeRef.current) {
        if (pendingWakeCmdRef.current) {
          // Wake word was detected mid-utterance in onresult — use stored cmd.
          textToSend = pendingWakeCmdRef.current;
          pendingWakeCmdRef.current = '';
          shouldSend = !manualCancelRef.current;
        } else if (shouldSend) {
          // Full utterance ended — check if the wake phrase is in it.
          const m = finalText.match(/(?:hey\s+b[h]?asha)[\s,]*(.*)/i);
          if (m) {
            textToSend = m[1].trim() || '__WAKE__';
            shouldSend = true;
          } else {
            // Utterance without wake word in continuous mode → ignore.
            shouldSend = false;
          }
        }

        // Always restart in continuous mode (unless manually cancelled).
        // Use 350ms delay — Chrome throws "already started" if too fast.
        if (!manualCancelRef.current) {
          setTranscript('');
          transcriptRef.current = '';
          setTimeout(() => {
            if (!continuousModeRef.current || manualCancelRef.current) return;
            try {
              rec.lang = LANG_TAGS[languageRef.current] || 'en-IN';
              rec.start();
            } catch (_) { /* already started or context destroyed */ }
          }, 350);
        } else {
          setListening(false);
        }
      } else {
        // Normal (single-shot) mode — done.
        setListening(false);
      }

      manualCancelRef.current = false;

      // Fire callback AFTER restart is scheduled so the UI updates feel instant.
      if (shouldSend && callbackRef.current) {
        callbackRef.current(textToSend);
      }
    };

    recognitionRef.current = rec;
    return () => rec.abort();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [supported]); // Intentionally stable — runtime behavior controlled by refs.

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
      // Volume meter is cosmetic — recognition still works without it.
    }
  }, []);

  const stopAudioMeter = useCallback(() => {
    if (audioCtxRef.current) {
      audioCtxRef.current.deactivate?.();
      audioCtxRef.current.stream?.getTracks().forEach((t) => t.stop());
      audioCtxRef.current.ctx?.close();
      audioCtxRef.current = null;
    }
  }, []);

  /**
   * Start listening.
   * @param {boolean} [inContinuousMode] - Pass true to enable wake-word mode.
   *   This updates the ref SYNCHRONOUSLY before rec.start() is called, which
   *   avoids the race condition where a React state update + useEffect would
   *   update the ref too late.
   */
  const start = useCallback(async (inContinuousMode = false) => {
    if (!supported || !recognitionRef.current) {
      setError('Speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }
    setError(null);
    setTranscript('');
    transcriptRef.current = '';
    pendingWakeCmdRef.current = '';
    manualCancelRef.current = false;
    // Update the ref NOW, synchronously — not via useEffect.
    continuousModeRef.current = inContinuousMode;
    setListening(true);
    await startVolumeMeter();
    recognitionRef.current.lang = LANG_TAGS[language] || 'en-IN';
    try {
      recognitionRef.current.start();
    } catch (e) {
      setError(`Could not start listening: ${e.message}`);
      setListening(false);
    }
  }, [language, startVolumeMeter, supported]);

  /** Stop immediately — cancel, do NOT fire the callback. */
  const cancel = useCallback(() => {
    manualCancelRef.current = true;
    continuousModeRef.current = false;
    pendingWakeCmdRef.current = '';
    recognitionRef.current?.stop();
    stopAudioMeter();
    setListening(false);
    setTranscript('');
    transcriptRef.current = '';
  }, [stopAudioMeter]);

  /** Stop but DO fire the callback with whatever was captured. */
  const stop = useCallback(() => {
    continuousModeRef.current = false;
    recognitionRef.current?.stop();
    stopAudioMeter();
    setListening(false);
  }, [stopAudioMeter]);

  return { transcript, listening, error, volume, supported: !!supported, start, stop, cancel, setTranscript };
}
