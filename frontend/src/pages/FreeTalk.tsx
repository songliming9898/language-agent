import { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { startSession, sendChatMessage, sendVoiceMessage, getChatHistory, ChatMessage } from "../services/api";
import { useRecorder } from "../hooks/useRecorder";
import { useAudioPlayer } from "../hooks/useAudioPlayer";

export default function FreeTalk() {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const { isRecording, startRecording, stopRecording, error: recorderError } = useRecorder();
  const { playBase64 } = useAudioPlayer();
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 初始化会话
  useEffect(() => {
    startSession("free_talk").then((sid) => {
      setSessionId(sid);
      setMessages([
        {
          id: 0,
          role: "assistant",
          text: "Hello! 👋 I'm your English teacher. Let's chat! What would you like to talk about?",
          time: new Date().toISOString(),
        },
      ]);
    });
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendText = useCallback(async () => {
    const text = inputText.trim();
    if (!text || !sessionId || sending) return;
    setInputText("");
    setSending(true);

    // 添加用户消息
    const userMsg: ChatMessage = {
      id: Date.now(),
      role: "user",
      text,
      time: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await sendChatMessage(text, sessionId);
      const aiMsg: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: res.reply,
        time: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);

      if (res.audio_base64) {
        playBase64(res.audio_base64);
      }
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 2, role: "assistant", text: "Sorry, something went wrong. Try again! 🙈", time: new Date().toISOString() },
      ]);
    } finally {
      setSending(false);
    }
  }, [inputText, sessionId, sending, playBase64]);

  const handleVoice = useCallback(async () => {
    if (isRecording) {
      setLoading(true);
      const blob = await stopRecording();
      if (blob && sessionId) {
        setSending(true);
        try {
          const res = await sendVoiceMessage(blob, sessionId);
          setMessages((prev) => [
            ...prev,
            { id: Date.now(), role: "user", text: res.user_text, time: new Date().toISOString() },
            { id: Date.now() + 1, role: "assistant", text: res.reply, time: new Date().toISOString() },
          ]);
          if (res.audio_base64) {
            playBase64(res.audio_base64);
          }
        } catch (e) {
          console.error(e);
        } finally {
          setSending(false);
        }
      }
      setLoading(false);
    } else {
      await startRecording();
    }
  }, [isRecording, stopRecording, startRecording, sessionId, playBase64]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSendText();
    }
  };

  return (
    <div className="page" style={{ padding: 0, display: "flex", flexDirection: "column", height: "100vh" }}>
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate("/")}>←</button>
        自由对练
      </div>

      {/* 对话区 */}
      <div className="chat-container" style={{ flex: 1, padding: "12px 16px", overflowY: "auto" }}>
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-bubble ${msg.role}`}>
            <div>{msg.text}</div>
            <div className="bubble-time">
              {new Date(msg.time).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
            </div>
          </div>
        ))}
        {(loading || sending) && (
          <div className="chat-bubble assistant">
            <div>Thinking... 🤔</div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* 错误提示 */}
      {recorderError && (
        <div style={{ padding: "8px 16px", background: "#fff3cd", color: "#856404", fontSize: 13, textAlign: "center" }}>
          ⚠️ {recorderError}
        </div>
      )}

      {/* 输入区 */}
      <div className="chat-input-bar">
        {/* 语音按钮 */}
        <div
          onClick={handleVoice}
          title={isRecording ? "点击停止录音" : "点击开始语音输入"}
          style={{
            width: 44,
            height: 44,
            borderRadius: "50%",
            background: isRecording ? "var(--danger)" : "var(--primary-light)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 20 }}>{isRecording ? "⏹" : "🎤"}</span>
        </div>

        {/* 文字输入 */}
        <input
          ref={inputRef}
          className="chat-input"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入英语..."
          disabled={sending}
        />

        {/* 发送 */}
        <button
          onClick={handleSendText}
          disabled={!inputText.trim() || sending}
          style={{
            width: 44,
            height: 44,
            borderRadius: "50%",
            background: inputText.trim() ? "var(--primary)" : "#e0e0e0",
            border: "none",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: inputText.trim() ? "pointer" : "default",
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 18, color: "#fff" }}>↑</span>
        </button>
      </div>
    </div>
  );
}
