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
      // Silence between sentences is normal, not a failure worth surfacing.
      if (event.error === "no-speech" || event.error === "aborted") return;
      setError(MESSAGES[event.error] ?? "Dictation stopped unexpectedly.");
      setListening(false);
    };

    instance.onend = () => {
      setListening(false);
      setInterim("");
    };

    recognition.current = instance;

    return () => {
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
    if (!recognition.current || listening) return;
    setError(null);
    try {
      recognition.current.start();
      setListening(true);
    } catch {
      // Chrome throws if start() is called while already running. The state is
      // what we wanted either way.
      setListening(true);
    }
  }, [listening]);

  const stop = useCallback(() => {
    recognition.current?.stop();
    setListening(false);
    setInterim("");
  }, []);

  const toggle = useCallback(() => {
    if (listening) stop();
    else start();
  }, [listening, start, stop]);

  return { supported, listening, interim, error, start, stop, toggle };
}
