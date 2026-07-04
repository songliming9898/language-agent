import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCourses, Course } from "../services/api";

export default function CourseList() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCourses()
      .then(setCourses)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page" style={{ padding: 0 }}>
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate("/")}>
          ←
        </button>
        选择课程
      </div>

      <div style={{ padding: 16 }}>
        {loading ? (
          <div className="loading">加载中...</div>
        ) : courses.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📚</div>
            <div>暂无课程数据，请先导入教材</div>
          </div>
        ) : (
          courses.map((course) => (
            <div
              key={course.id}
              className="card"
              style={{ cursor: "pointer" }}
              onClick={() => navigate(`/courses/${course.id}/units`)}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontSize: 32 }}>📗</span>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 600 }}>
                    {course.grade} {course.semester}
                  </div>
                  <div style={{ fontSize: 13, color: "var(--text-light)" }}>
                    人教版 PEP · {course.version}
                  </div>
                </div>
                <span style={{ marginLeft: "auto", color: "#ccc", fontSize: 20 }}>›</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
