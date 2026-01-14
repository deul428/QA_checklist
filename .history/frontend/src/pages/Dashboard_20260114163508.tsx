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
  const [checkedSystemIds, setCheckedSystemIds] = useState<Set<number>>(new Set());
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
        
        // 체크 완료된 시스템 ID 추출
        // unchecked items에 없는 system_id는 모두 체크 완료
        const uncheckedSystemIds = new Set(
          uncheckedData.map((item: any) => item.system_id)
        );
        const allSystemIds = new Set(systemsData.map((s) => s.id));
        const checkedIds = new Set(
          Array.from(allSystemIds).filter((id) => !uncheckedSystemIds.has(id))
        );
        setCheckedSystemIds(checkedIds);
      } catch (error) {
        console.error("데이터 로딩 실패:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []); // 컴포넌트 마운트 시와 대시보드로 돌아올 때마다 데이터 갱신

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
          <h1>QA 체크리스트 시스템 ({formattedDate})</h1>
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
              {systems.map((system) => {
                const isChecked = checkedSystemIds.has(system.id);
                return (
                  <div
                    key={system.id}
                    className={`system-card ${isChecked ? "checked" : ""}`}
                    onClick={() => handleSystemClick(system.id)}
                  >
                    <h3>{system.system_name}</h3>
                    {system.description && (
                      <p className="system-description">{system.description}</p>
                    )}
                    <div className="system-action">
                      {isChecked ? "✓ 체크 완료" : "체크리스트 작성 →"}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
