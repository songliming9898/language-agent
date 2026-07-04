import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getUnits, getUnitProgress, Unit, UnitProgress } from "../services/api";

export default function UnitList() {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const [units, setUnits] = useState<Unit[]>([]);
  const [progressMap, setProgressMap] = useState<Record<number, UnitProgress[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!courseId) return;
    getUnits(Number(courseId))
      .then(async (data) => {
        setUnits(data);
        // 并行获取所有单元的进度
        const map: Record<number, UnitProgress[]> = {};
        await Promise.all(
          data.map(async (u) => {
            try {
              map[u.id] = await getUnitProgress(u.id);
            } catch {
              map[u.id] = [];
            }
          })
        );
        setProgressMap(map);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [courseId]);

  const getMasteryRate = (unitId: number): number => {
    const items = progressMap[unitId] || [];
    if (items.length === 0) return 0;
    const mastered = items.filter((i) => i.mastered).length;
    return Math.round((mastered / items.length) * 100);
  };

  return (
    <div className="page" style={{ padding: 0 }}>
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate("/courses")}>
          ←
        </button>
        选择单元
      </div>

      <div style={{ padding: 16 }}>
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          units.map((unit) => {
            const rate = getMasteryRate(unit.id);
            return (
              <div
                key={unit.id}
                className="card"
                style={{ cursor: "pointer" }}
                onClick={() => navigate(`/practice/${unit.id}`)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 12,
                      background: rate >= 80 ? "#4caf50" : rate > 0 ? "#ff9800" : "#e0e0e0",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "#fff",
                      fontSize: 16,
                      fontWeight: 700,
                    }}
                  >
                    {unit.unit_order}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 15, fontWeight: 600 }}>{unit.unit_name}</div>
                    <div style={{ fontSize: 12, color: "var(--text-light)", marginTop: 2 }}>
                      {unit.description}
                    </div>
                    <div className="progress-bar" style={{ marginTop: 8 }}>
                      <div
                        className="progress-fill"
                        style={{ width: `${rate}%` }}
                      />
                    </div>
                  </div>
                  <span style={{ color: "#ccc", fontSize: 20 }}>›</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
