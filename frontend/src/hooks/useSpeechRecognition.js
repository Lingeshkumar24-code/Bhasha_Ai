import { useCallback, useEffect, useRef, useState } from 'react';

// Maps our app language codes to BCP-47 tags the Web Speech API expects.
const LANG_TAGS = {
  en: 'en-IN', ta: 'ta-IN', te: 'te-IN', kn: 'kn-IN',
  ml: 'ml-IN', hi: 'hi-IN', bn: 'bn-IN', mr: 'mr-IN', gu: 'gu-IN', pa: 'pa-IN',
};

/**
 * Real ASR using the browser's native SpeechRecognition (Web Speech API).
 *
 * FIX (continuous mode / wake word):
 *  - The recognizer is created ONCE and reused. Previously it was re-created
 *    every time `continuousMode` changed (it was in the useEffect dep array),
 *    which meant the new (correct) recognizer object wasn't yet assigned to
 *    recognitionRef when start() fired 50 ms later — so the OLD, non-continuous
 *    recognizer was started instead, and "Hey Bhasha" was never detected.
 *  - All runtime decisions (whether to restart, whether to check the wake word)
 *    now read continuousModeRef instead of the closed-over state value.
 *  - rec.continuous is set dynamically just before every start() call.
 *  - Restart delay raised 250 → 400 ms (Chrome needs the extra breathing room).
 *
 * FIX (auto-send after speaking):
 *  The browser recognizer fires `onend` automatically after you stop speaking.
 *  `onFinalTranscript` is called from `onend` whenever there is a non-empty
 *  transcript, so simply speaking and pausing is enough to trigger the full
 *  pipeline — no extra "Stop & Send" click needed.
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
  // These refs are the source of truth for runtime decisions — avoids stale closures.
  const continuousModeRef = useRef(continuousMode);
  const languageRef = useRef(language);
  const pendingWakeCmdRef = useRef('');

  useEffect(() => { callbackRef.current = onFinalTranscript; }, [onFinalTranscript]);
  useEffect(() => { continuousModeRef.current = continuousMode; }, [continuousMode]);
  useEffect(() => { languageRef.current = language; }, [language]);

  const supported = typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  // Create the recognizer ONCE — no dependency on continuousMode or language so
  // it is never thrown away and re-built mid-session.
  useEffect(() => {
    if (!supported) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    // continuous is set dynamically in start() via continuousModeRef
    rec.interimResults = true;
    rec.lang = LANG_TAGS[language] || 'en-IN';

    rec.onresult = (event) => {
      let text = '';
      for (let i = 0; i < event.results.length; i++) {
        text += event.results[i][0].transcript;
      }
      transcriptRef.current = text;
      setTranscript(text);

      if (continuousModeRef.current && !manualCancelRef.current) {
        // Wake word detection on LIVE interim results.
        // Chrome's continuous recognizer rarely fires `onend` between phrases,
        // so we also check here and force a stop→restart to flush the buffer.
        const wakeWordMatch = text.match(/(?:hey\s+b[h]?asha)[\s,]*(.*)/i);
        if (wakeWordMatch && !pendingWakeCmdRef.current) {
          const cmd = wakeWordMatch[1].trim();
          pendingWakeCmdRef.current = cmd || '__WAKE__';
          setTranscript('');
          transcriptRef.current = '';
          rec.stop(); // triggers onend → picks up pendingWakeCmdRef → restarts
        }
      }
    };

    rec.onerror = (event) => {
      // In continuous mode, no-speech / aborted are normal — don't surface them.
      if (continuousModeRef.current &&
          (event.error === 'no-speech' || event.error === 'aborted')) return;
      setError(
        event.error === 'not-allowed'
          ? 'Microphone permission denied.'
          : `ASR error: ${event.error}`
      );
      setListening(false);
    };

    rec.onend = () => {
      const finalText = transcriptRef.current.trim();
      let shouldSend = !!finalText && !manualCancelRef.current;
      let textToSend = finalText;

      if (continuousModeRef.current) {
        if (pendingWakeCmdRef.current) {
          // A wake word was already detected in onresult — use the captured cmd.
          textToSend = pendingWakeCmdRef.current;
          pendingWakeCmdRef.current = '';
          shouldSend = !manualCancelRef.current;
        } else if (shouldSend) {
          // Full utterance ended — check if it contains the wake word.
          const wakeWordMatch = finalText.match(/(?:hey\s+b[h]?asha)[\s,]*(.*)/i);
          if (wakeWordMatch) {
            textToSend = wakeWordMatch[1].trim() || '__WAKE__';
            shouldSend = true;
          } else {
            // Utterance without wake word in continuous mode → ignore it.
            shouldSend = false;
          }
        }
      }

      if (shouldSend) {
        callbackRef.current?.(textToSend);
      }

      if (continuousModeRef.current && !manualCancelRef.current) {
        // Restart so we keep listening for the next "Hey Bhasha".
        // 400 ms delay — Chrome raises "already started" if we restart too fast.
        setTranscript('');
        transcriptRef.current = '';
        setTimeout(() => {
          if (!continuousModeRef.current || manualCancelRef.current) return;
          try {
            rec.continuous = true;
            rec.lang = LANG_TAGS[languageRef.current] || 'en-IN';
            rec.start();
          } catch (e) { /* already started or context gone */ }
        }, 400);
      } else {
        setListening(false);
      }
      manualCancelRef.current = false;
    };

    recognitionRef.current = rec;
    return () => rec.abort();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [supported]); // intentionally stable — runtime state comes from refs

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
    pendingWakeCmdRef.current = '';
    setListening(true);
    await startVolumeMeter();
    // Set language & continuous mode dynamically right before starting —
    // this is safe because the recognizer is stopped at this point.
    recognitionRef.current.lang = LANG_TAGS[language] || 'en-IN';
    recognitionRef.current.continuous = continuousModeRef.current;
    try {
      recognitionRef.current.start();
    } catch (e) {
      setError(`Could not start listening: ${e.message}`);
      setListening(false);
    }
  }, [language, startVolumeMeter, supported]);

  const stopAudioMeter = () => {
    if (audioCtxRef.current) {
      audioCtxRef.current.deactivate?.();
      audioCtxRef.current.stream.getTracks().forEach((t) => t.stop());
      audioCtxRef.current.ctx.close();
      audioCtxRef.current = null;
    }
  };

  /** Stop early and cancel — does NOT auto-send. */
  const cancel = useCallback(() => {
    manualCancelRef.current = true;
    pendingWakeCmdRef.current = '';
    recognitionRef.current?.stop();
    stopAudioMeter();
    setListening(false);
  }, []);

  /** Stop early but DO send whatever was captured (fires onend → callback). */
  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    stopAudioMeter();
    setListening(false);
  }, []);

  return { transcript, listening, error, volume, supported: !!supported, start, stop, cancel, setTranscript };
}
