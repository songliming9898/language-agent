import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getOverallProgress, OverallProgress } from "../services/api";

export default function Home() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState<OverallProgress | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOverallProgress()
      .then(setProgress)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      {/* 顶部欢迎 */}
      <div className="page-header" style={{ justifyContent: "center" }}>
        🌟 英语口语小达人
      </div>

      {/* 进度卡片 */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title">📊 学习进度</div>
        {loading ? (
          <div className="loading">加载中...</div>
        ) : progress ? (
          <>
            <div style={{ display: "flex", justifyContent: "space-around", padding: "12px 0" }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 32, fontWeight: 700, color: "var(--primary)" }}>
                  {progress.total_practices}
                </div>
                <div style={{ fontSize: 13, color: "var(--text-light)" }}>练习次数</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 32, fontWeight: 700, color: "var(--accent)" }}>
                  {progress.mastered_count}
                </div>
                <div style={{ fontSize: 13, color: "var(--text-light)" }}>已掌握</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 32, fontWeight: 700, color: "#2196f3" }}>
                  {progress.mastery_rate}%
                </div>
                <div style={{ fontSize: 13, color: "var(--text-light)" }}>掌握率</div>
              </div>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress.mastery_rate}%` }}
              />
            </div>
          </>
        ) : (
          <div style={{ textAlign: "center", padding: 16, color: "var(--text-light)" }}>
            开始你的第一次练习吧！
          </div>
        )}
      </div>

      {/* 功能入口 */}
      <div className="home-actions">
        <div
          className="home-action-card"
          onClick={() => navigate("/courses")}
          style={{ borderLeft: "4px solid var(--primary)" }}
        >
          <div className="action-icon">📖</div>
          <div className="action-title">课程对练</div>
          <div className="action-desc">跟着课本逐句练习，打好基础</div>
        </div>

        <div
          className="home-action-card"
          onClick={() => navigate("/free-talk")}
          style={{ borderLeft: "4px solid var(--accent)" }}
        >
          <div className="action-icon">💬</div>
          <div className="action-title">自由对练</div>
          <div className="action-desc">和 AI 老师自由聊天，大胆开口</div>
        </div>

        <div
          className="home-action-card"
          onClick={() => navigate("/report")}
          style={{ borderLeft: "4px solid #2196f3" }}
        >
          <div className="action-icon">📈</div>
          <div className="action-title">学习报告</div>
          <div className="action-desc">查看你的学习数据和AI记忆</div>
        </div>
      </div>

      <div style={{ textAlign: "center", marginTop: 32, fontSize: 12, color: "#bbb" }}>
        Demo v0.1 · AI 英语老师陪你练口语
      </div>
    </div>
  );
}
