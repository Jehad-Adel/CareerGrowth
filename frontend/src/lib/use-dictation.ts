"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";

/**
 * Browser dictation via the Web Speech API.
 *
 * Deliberately frontend-only: no upload, no backend route, no AI quota. The
 * recognition happens in the browser's own speech stack, so dictating a long
 * interview answer costs nothing and cannot exhaust a rate limit mid-sentence.
 *
 * Privacy note worth knowing: Chrome's implementation is not local — it streams
 * audio to Google's servers to transcribe. That is the same vendor already
 * receiving the answer text, so it changes no threat model here, but it does
 * mean this is not an offline feature.
 *
 * Support is uneven (no Firefox). `supported` is false there, and callers hide
 * the control rather than showing one that does nothing — typing still works.
 */

// The Web Speech API is not in TypeScript's DOM lib, and the implementation is
// still vendor-prefixed in Chrome. Only the surface actually used is declared.
type SpeechRecognitionAlternative = { transcript: string };
type SpeechRecognitionResult = {
  isFinal: boolean;
  0: SpeechRecognitionAlternative;
};
type SpeechRecognitionEvent = {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: SpeechRecognitionResult;
  };
};
type SpeechRecognitionErrorEvent = { error: string };

type SpeechRecognitionInstance = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

function getConstructor(): SpeechRecognitionConstructor | null {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null;
}

const MESSAGES: Record<string, string> = {
  "not-allowed": "Microphone access was blocked. Allow it in your browser settings.",
  "service-not-allowed": "Microphone access was blocked by your browser.",
  "audio-capture": "No microphone found.",
  network: "Dictation needs a network connection.",
};

/**
 * Chrome ends a recognition session on its own after a few seconds of silence,
 * even with `continuous = true`. Left alone that stops dictation mid-answer
 * while the button still reads "listening" — the single most common way this
 * feature "doesn't work". `onend` restarts it as long as the user has not
 * pressed stop. The cap and the window exist so a session that dies instantly
 * and repeatedly (device unplugged, service refusing) surfaces as an error
 * instead of spinning forever.
 */
const RESTART_LIMIT = 8;
const RESTART_WINDOW_MS = 10_000;

export type Dictation = {
  /** False on browsers without the API. Hide the control rather than disable it. */
  supported: boolean;
  listening: boolean;
  /** Words not yet finalised, for live feedback. Never committed by the hook. */
  interim: string;
  error: string | null;
  start: () => void;
  stop: () => void;
  toggle: () => void;
};

/**
 * @param onResult called with each finalised phrase. The caller decides where
 *   it lands — this hook never writes into a field or submits anything.
 */
// Availability never changes after load, so the store never notifies.
const subscribe = () => () => {};
const getSnapshot = () => getConstructor() !== null;
// False during SSR. Reading `window` in a lazy useState initializer would
// render true on the client and false on the server — a hydration mismatch.
const getServerSnapshot = () => false;

export function useDictation(onResult: (text: string) => void): Dictation {
  const supported = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot,
  );
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [error, setError] = useState<string | null>(null);

  const recognition = useRef<SpeechRecognitionInstance | null>(null);
  // What the *user* asked for, as opposed to whether the engine happens to be
  // running right now. `onend` reads it to decide restart vs. stop, and it is a
  // ref because that callback is installed once and would otherwise close over
  // the first render's state forever.
  const wanted = useRef(false);
  const restarts = useRef<number[]>([]);
  // Held in a ref so re-creating the callback each render does not force the
  // recognition instance to be rebuilt mid-sentence. Assigned in an effect,
  // not during render — a ref write during render is not safe under
  // concurrent rendering, and React 19's lint rules reject it.
  const onResultRef = useRef(onResult);
  useEffect(() => {
    onResultRef.current = onResult;
  });

  useEffect(() => {
    const Recognition = getConstructor();
    if (!Recognition) return;

    const instance = new Recognition();
    instance.lang = navigator.language || "en-US";
    // Long-form answers pause. Without `continuous`, the first breath ends the
    // session and the rest of the sentence is lost.
    instance.continuous = true;
    instance.interimResults = true;

    instance.onresult = (event) => {
      let pending = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        const text = result[0].transcript;
        if (result.isFinal) {
          onResultRef.current(text.trim());
        } else {
          pending += text;
        }
      }
      setInterim(pending);
    };

    instance.onerror = (event) => {
      // Silence between sentences is normal, not a failure worth surfacing —
      // `onend` restarts the session right after.
      if (event.error === "no-speech" || event.error === "aborted") return;
      wanted.current = false;
      setError(MESSAGES[event.error] ?? "Dictation stopped unexpectedly.");
      setListening(false);
    };

    instance.onend = () => {
      setInterim("");
      if (!wanted.current) {
        setListening(false);
        return;
      }

      const now = Date.now();
      restarts.current = [
        ...restarts.current.filter((t) => now - t < RESTART_WINDOW_MS),
        now,
      ];
      if (restarts.current.length > RESTART_LIMIT) {
        wanted.current = false;
        setListening(false);
        setError("Dictation kept dropping. Check your microphone and try again.");
        return;
      }

      try {
        instance.start();
      } catch {
        // Already restarting on its own; the state we want is unchanged.
      }
    };

    recognition.current = instance;

    return () => {
      wanted.current = false;
      instance.onresult = null;
      instance.onerror = null;
      instance.onend = null;
      // abort, not stop: this fires on unmount and on React's development
      // double-invoke, where a graceful stop would still emit a final result
      // into a component that no longer exists.
      instance.abort();
      recognition.current = null;
    };
  }, []);

  const start = useCallback(() => {
    if (!recognition.current || wanted.current) return;
    setError(null);
    restarts.current = [];
    wanted.current = true;
    try {
      recognition.current.start();
    } catch {
      // Chrome throws if start() is called while already running. The state is
      // what we wanted either way.
    }
    setListening(true);
  }, []);

  const stop = useCallback(() => {
    wanted.current = false;
    // stop(), not abort(): it flushes the phrase currently being recognised as
    // a final result, so the last words before the tap are not thrown away.
    recognition.current?.stop();
    setListening(false);
    setInterim("");
  }, []);

  const toggle = useCallback(() => {
    if (wanted.current) stop();
    else start();
  }, [start, stop]);

  return { supported, listening, interim, error, start, stop, toggle };
}
