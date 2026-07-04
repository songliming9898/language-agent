import { useRef, useCallback } from "react";

interface UseAudioPlayerReturn {
  playBase64: (base64: string) => void;
  playUrl: (url: string) => void;
  stop: () => void;
}

export function useAudioPlayer(): UseAudioPlayerReturn {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  }, []);

  const playBase64 = useCallback(
    (base64: string) => {
      stop();
      const audio = new Audio(`data:audio/mpeg;base64,${base64}`);
      audioRef.current = audio;
      audio.play().catch(console.error);
    },
    [stop]
  );

  const playUrl = useCallback(
    (url: string) => {
      stop();
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.play().catch(console.error);
    },
    [stop]
  );

  return { playBase64, playUrl, stop };
}
