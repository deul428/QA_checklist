import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { userAPI, checklistAPI, System } from "../api/api";
import "./Dashboard.scss";

const Dashboard: React.FC = () => {
  const { user, logout, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [systems, setSystems] = useState<System[]>([]); 
  const [uncheckedCount, setUncheckedCount] = useState(0);
  const [checkedSystemIds, setCheckedSystemIds] = useState<Set<number>>(
    new Set()
  );
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    // AuthContext의 로딩이 완료되고 user가 있을 때만 데이터 로드
    if (authLoading || !user) {
      return;
    }

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
        const allSystemIds = new Set(systemsData.map((s) => s.system_id));
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
  }, [authLoading, user]); // authLoading과 user가 변경될 때마다 실행

  const handleSystemClick = (systemId: number) => {
    // 기본 환경(prd)으로 체크리스트 페이지로 이동
    navigate(`/checklist/${systemId}?env=prd`);
  };

  // AuthContext 로딩 중이거나 user가 없으면 로딩 표시
  if (authLoading || !user || loading) {
    return <div className="loading">로딩 중...</div>;
  }

  const date = new Date();
  const yyyy = date.getFullYear();
  const mm = date.getMonth() + 1;
  const dd = date.getDate();
  const formattedDate = `${yyyy}년 ${mm}월 ${dd}일`;
  return (
    <div className="dashboard">
      <header className="dashboard-header header">
        <div className="header-content ">
          <h1>DX본부 시스템 체크리스트 ({formattedDate})</h1>
          <div className="user-info">
            <span>
              {user?.general_headquarters} {user?.user_name}님 (
              {user?.user_id})
            </span>
            <div className="btn-set">
              <button
                onClick={() => navigate("/substitute")}
                className="btn btn-warning"
              >
                대체 담당자 지정
              </button>
              {user?.console_role && (
                <button
                  onClick={() => navigate("/console")}
                  className="btn btn-accent"
                >
                  관리자
                </button>
              )}
              <button onClick={logout} className="btn btn-primary">
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </header>

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
              const isChecked = checkedSystemIds.has(system.system_id);
              return (
                <div
                  key={system.system_id}
                  className={`system-card ${isChecked ? "checked" : ""}`}
                  onClick={() => handleSystemClick(system.system_id)}
                >
                  <h3>{system.system_name}</h3>
                  {system?.system_description && (
                    <p className="system-description">{system?.system_description}</p>
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
  );
};

export default Dashboard;
