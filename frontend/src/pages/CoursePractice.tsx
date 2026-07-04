import { useEffect, useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getSentences, evaluateSentence, Sentence, EvaluateResult } from "../services/api";
import { useRecorder } from "../hooks/useRecorder";

export default function CoursePractice() {
  const { unitId } = useParams<{ unitId: string }>();
  const navigate = useNavigate();
  const [sentences, setSentences] = useState<Sentence[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [result, setResult] = useState<EvaluateResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const { isRecording, startRecording, stopRecording, error: recError } = useRecorder();

  useEffect(() => {
    if (!unitId) return;
    getSentences(Number(unitId))
      .then(setSentences)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [unitId]);

  const currentSentence = sentences[currentIdx] || null;

  const handleRecord = useCallback(async () => {
    if (isRecording) {
      setEvaluating(true);
      const blob = await stopRecording();
      if (blob && currentSentence) {
        try {
          const res = await evaluateSentence(blob, currentSentence.id, currentSentence.sentence_text);
          setResult(res);
        } catch (e) {
          console.error(e);
        }
      }
      setEvaluating(false);
    } else {
      setResult(null);
      await startRecording();
    }
  }, [isRecording, stopRecording, startRecording, currentSentence]);

  const goNext = () => {
    if (currentIdx < sentences.length - 1) {
      setCurrentIdx(currentIdx + 1);
      setResult(null);
    }
  };

  const goPrev = () => {
    if (currentIdx > 0) {
      setCurrentIdx(currentIdx - 1);
      setResult(null);
    }
  };

  if (loading) {
    return (
      <div className="page" style={{ padding: 0 }}>
        <div className="page-header">
          <button className="back-btn" onClick={() => navigate(-1)}>←</button>
          课程对练
        </div>
        <div className="loading">加载句子中...</div>
      </div>
    );
  }

  if (!currentSentence) {
    return (
      <div className="page" style={{ padding: 0 }}>
        <div className="page-header">
          <button className="back-btn" onClick={() => navigate(-1)}>←</button>
          课程对练
        </div>
        <div className="empty-state">
          <div className="empty-icon">🎉</div>
          <div>本单元暂无句子，请先导入教材内容</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page" style={{ padding: 0, display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate(-1)}>←</button>
        课程对练 ({currentIdx + 1}/{sentences.length})
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
        {/* 句子展示 */}
        <div className="sentence-display">
          <div className="sentence-en">{currentSentence.sentence_text}</div>
          {currentSentence.translation && (
            <div className="sentence-zh">{currentSentence.translation}</div>
          )}
        </div>

        {/* 录音按钮 */}
        <div style={{ margin: "24px 0" }}>
          {recError && (
            <div style={{ color: "var(--danger)", fontSize: 13, marginBottom: 8, textAlign: "center" }}>
              {recError}
            </div>
          )}
          <div
            className={`record-btn ${isRecording ? "recording" : ""}`}
            onClick={handleRecord}
          >
            <div className="record-icon" />
          </div>
          <div style={{ textAlign: "center", marginTop: 8, fontSize: 14, color: "var(--text-light)" }}>
            {evaluating ? "评分中..." : isRecording ? "点击停止" : "点击录音"}
          </div>
        </div>

        {/* 评分结果 */}
        {result && (
          <div className="card" style={{ width: "100%" }}>
            <div className="score-display">
              <div className="score-item">
                <div className="score-value">{result.scores.accuracy}</div>
                <div className="score-label">音准</div>
              </div>
              <div className="score-item">
                <div className="score-value">{result.scores.fluency}</div>
                <div className="score-label">流利度</div>
              </div>
              <div className="score-item">
                <div className="score-value">{result.scores.completeness}</div>
                <div className="score-label">完整度</div>
              </div>
            </div>
            {result.transcript && (
              <div style={{ textAlign: "center", fontSize: 14, color: "var(--text-light)", marginTop: 4 }}>
                你说的: "{result.transcript}"
              </div>
            )}
            <div className="feedback-text">{result.feedback}</div>
          </div>
        )}
      </div>

      {/* 底部导航 */}
      <div style={{ display: "flex", gap: 12, padding: "16px", background: "#fff", borderTop: "1px solid #eee" }}>
        <button
          className="btn btn-primary"
          style={{ flex: 1 }}
          onClick={goPrev}
          disabled={currentIdx === 0}
        >
          ← 上一句
        </button>
        <button
          className="btn btn-accent"
          style={{ flex: 1 }}
          onClick={goNext}
          disabled={currentIdx === sentences.length - 1}
        >
          下一句 →
        </button>
      </div>
    </div>
  );
}
