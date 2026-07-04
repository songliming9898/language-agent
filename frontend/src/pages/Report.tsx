import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getOverallProgress, getMemorySummary, OverallProgress, MemorySummary } from "../services/api";

const TYPE_LABELS: Record<string, string> = {
  vocab_mastered: "✅ 已掌握词汇",
  vocab_weak: "📝 薄弱词汇",
  grammar_weak: "📖 语法弱点",
  pronunciation_issue: "🗣️ 发音问题",
  learning_preference: "💡 学习偏好",
  interest_topic: "⭐ 兴趣话题",
};

export default function Report() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState<OverallProgress | null>(null);
  const [memory, setMemory] = useState<MemorySummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getOverallProgress(), getMemorySummary()])
      .then(([p, m]) => {
        setProgress(p);
        setMemory(m);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page" style={{ padding: 0 }}>
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate("/")}>←</button>
        学习报告
      </div>

      <div style={{ padding: 16 }}>
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <>
            {/* 进度总览 */}
            <div className="card">
              <div className="card-title">📊 学习统计</div>
              <div style={{ display: "flex", justifyContent: "space-around", padding: "16px 0" }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 36, fontWeight: 700, color: "var(--primary)" }}>
                    {progress?.total_practices || 0}
                  </div>
                  <div style={{ fontSize: 13, color: "var(--text-light)" }}>总练习次数</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 36, fontWeight: 700, color: "var(--star)" }}>
                    {progress?.mastered_count || 0}
                  </div>
                  <div style={{ fontSize: 13, color: "var(--text-light)" }}>已掌握句子</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 36, fontWeight: 700, color: "#2196f3" }}>
                    {progress?.mastery_rate || 0}%
                  </div>
                  <div style={{ fontSize: 13, color: "var(--text-light)" }}>掌握率</div>
                </div>
              </div>
            </div>

            {/* AI 记忆 */}
            <div className="card">
              <div className="card-title">🧠 AI 记忆 (个性化数据)</div>
              {memory && Object.keys(memory.records).length > 0 ? (
                Object.entries(memory.records).map(([type, items]) => (
                  <div key={type} style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
                      {TYPE_LABELS[type] || type}
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {items.map((item, idx) => (
                        <span
                          key={idx}
                          style={{
                            background: type === "vocab_mastered" ? "#e8f5e9" : "#fff3e0",
                            color: type === "vocab_mastered" ? "#2e7d32" : "#e65100",
                            padding: "4px 10px",
                            borderRadius: 12,
                            fontSize: 13,
                          }}
                        >
                          {item.key}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ textAlign: "center", padding: 16, color: "var(--text-light)" }}>
                  还没有记忆数据，完成一些练习后 AI 会更了解你！
                </div>
              )}
            </div>

            {/* 上下文预览 */}
            {memory?.context_text && (
              <div className="card">
                <div className="card-title">📋 AI 使用的上下文</div>
                <pre
                  style={{
                    fontSize: 12,
                    color: "var(--text-light)",
                    whiteSpace: "pre-wrap",
                    fontFamily: "monospace",
                    background: "#f9f9f9",
                    padding: 12,
                    borderRadius: 8,
                  }}
                >
                  {memory.context_text}
                </pre>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
