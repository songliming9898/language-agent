import { useState, useRef, useCallback } from "react";

interface UseRecorderReturn {
  isRecording: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  error: string | null;
}

export function useRecorder(): UseRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const cleanup = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
  }, []);

  const startRecording = useCallback(async () => {
    setError(null);
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/mp4";

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.start(100); // 每100ms收集一次数据，确保 stop 时能收到最后一片
      setIsRecording(true);
    } catch (err: any) {
      console.error("Recorder error:", err);
      if (err.name === "NotAllowedError") {
        setError("麦克风权限被拒绝，请允许浏览器访问麦克风（需要 HTTPS）");
      } else if (err.name === "NotFoundError") {
        setError("未检测到麦克风设备");
      } else {
        setError("无法访问麦克风：" + err.message);
      }
      cleanup();
    }
  }, [cleanup]);

  const stopRecording = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        setIsRecording(false);
        resolve(null);
        return;
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        cleanup();
        setIsRecording(false);
        resolve(blob);
      };

      // 确保在停止前请求最后一个数据块
      if (recorder.state === "recording") {
        recorder.requestData();
        // 小延迟确保 ondataavailable 触发
        setTimeout(() => {
          if (recorder.state === "recording") {
            recorder.stop();
          }
        }, 150);
      } else {
        resolve(null);
      }
    });
  }, [cleanup]);

  return { isRecording, startRecording, stopRecording, error };
}
