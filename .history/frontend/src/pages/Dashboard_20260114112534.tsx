import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { userAPI, checklistAPI, System } from "../api/api";
import "./Dashboard.scss";

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [systems, setSystems] = useState<System[]>([]);
  const [uncheckedCount, setUncheckedCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [systemsData, uncheckedData] = await Promise.all([
          userAPI.getSystems(),
          checklistAPI.getUncheckedItems(),
        ]);
        setSystems(systemsData);
        setUncheckedCount(uncheckedData.length);
      } catch (error) {
        console.error("데이터 로딩 실패:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleSystemClick = (systemId: number) => {
    navigate(`/checklist/${systemId}`);
  };

  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  const date = new Date();
  const yyyy = date.getFullYear();
  const mm = date.getMonth() + 1;
  const dd = date.getDate();
  const formattedDate = `${yyyy}년 ${mm}월 ${dd}일`;
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>QA 체크리스트 시스템 {formattedDate}</h1>
          <div className="user-info">
            <span>
              {user?.name}님 ({user?.employee_id})
            </span>
            <button onClick={logout} className="btn btn-secondary">
              로그아웃
            </button>
          </div>
        </div>
      </header>

      <div className="container">
        {uncheckedCount > 0 && (
          <div className="alert alert-warning">
            ⚠️ 오늘 체크되지 않은 항목이 {uncheckedCount}개 있습니다.
          </div>
        )}

        <div className="dashboard-content">
          <h2>담당 시스템</h2>
          {systems.length === 0 ? (
            <div className="empty-state">담당 시스템이 없습니다.</div>
          ) : (
            <div className="systems-grid">
              {systems.map((system) => (
                <div
                  key={system.id}
                  className="system-card"
                  onClick={() => handleSystemClick(system.id)}
                >
                  <h3>{system.system_name}</h3>
                  {system.description && (
                    <p className="system-description">{system.description}</p>
                  )}
                  <div className="system-action">체크리스트 작성 →</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
