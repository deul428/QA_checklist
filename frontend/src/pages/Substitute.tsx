import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  substituteAPI,
  userAPI,
  SubstituteAssignment,
  SubstituteAssignmentCreate,
  System,
  User,
} from "../api/api";
import "./Substitute.scss";

const Substitute: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [systems, setSystems] = useState<System[]>([]);
  const [substitutes, setSubstitutes] = useState<SubstituteAssignment[]>([]);
  const [activeSubstitutes, setActiveSubstitutes] = useState<
    SubstituteAssignment[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<SubstituteAssignmentCreate>({
    substitute_user_id: "",
    system_id: 0,
    start_date: "",
    end_date: "",
  });
  const [userSearchQuery, setUserSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(
    null
  );

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [systemsData, substitutesData, activeData] = await Promise.all([
          userAPI.getSystems(),
          substituteAPI.list(),
          substituteAPI.getActive(),
        ]);
        setSystems(systemsData);
        setSubstitutes(substitutesData);
        setActiveSubstitutes(activeData);
      } catch (error) {
        console.error("데이터 로딩 실패:", error);
        setMessage({
          type: "error",
          text: "데이터를 불러오는 데 실패했습니다.",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  // debounce 타이머 정리
  useEffect(() => {
    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
    };
  }, [debounceTimer]);

  const performSearch = async (query: string) => {
    if (query.length < 1) {
      setSearchResults([]);
      setSelectedUser(null);
      return;
    }

    setSearching(true);
    try {
      const results = await userAPI.searchUsers(query);
      setSearchResults(results);
      if (results.length === 1) {
        // 검색 결과가 하나면 자동 선택
        setSelectedUser(results[0]);
        setFormData((prev) => ({ ...prev, substitute_user_id: results[0].user_id }));
      } else {
        setSelectedUser(null);
        setFormData((prev) => ({ ...prev, substitute_user_id: "" }));
      }
    } catch (error) {
      console.error("사용자 검색 실패:", error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleUserSearchChange = (query: string) => {
    setUserSearchQuery(query);

    // 기존 타이머가 있으면 취소
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // 검색어가 비어있으면 즉시 초기화
    if (query.length < 1) {
      setSearchResults([]);
      setSelectedUser(null);
      setFormData((prev) => ({ ...prev, substitute_user_id: "" }));
      return;
    }

    // 500ms 후에 검색 실행 (debounce)
    const timer = setTimeout(() => {
      performSearch(query);
    }, 500);

    setDebounceTimer(timer);
  };

  const handleUserSearchBlur = () => {
    // 포커스가 벗어났을 때, 타이머가 있으면 취소하고 즉시 검색
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      setDebounceTimer(null);
    }

    // 검색어가 있고 선택된 사용자가 없으면 검색 실행
    if (userSearchQuery.length > 0 && !selectedUser) {
      performSearch(userSearchQuery);
    }
  };

  const handleSelectUser = (user: User) => {
    setSelectedUser(user);
    setFormData({ ...formData, substitute_user_id: user.user_id });
    setUserSearchQuery(`${user.user_name} (${user.user_id})`);
    setSearchResults([]);
  };

  const handleCreate = async () => {
    if (
      !formData.substitute_user_id ||
      !formData.system_id ||
      !formData.start_date ||
      !formData.end_date
    ) {
      setMessage({
        type: "error",
        text: "모든 필드를 입력해 주세요.",
      });
      return;
    }

    if (new Date(formData.end_date) < new Date(formData.start_date)) {
      setMessage({
        type: "error",
        text: "종료일은 시작일보다 이후여야 합니다.",
      });
      return;
    }

    setSubmitting(true);
    try {
      await substituteAPI.create(formData);
      setMessage({
        type: "success",
        text: "대체 담당자가 지정되었습니다.",
      });
      setShowCreateForm(false);
      setFormData({
        substitute_user_id: "",
        system_id: 0,
        start_date: "",
        end_date: "",
      });
      setUserSearchQuery("");
      setSelectedUser(null);
      setSearchResults([]);

      // 목록 새로고침
      const [substitutesData, activeData] = await Promise.all([
        substituteAPI.list(),
        substituteAPI.getActive(),
      ]);
      setSubstitutes(substitutesData);
      setActiveSubstitutes(activeData);
    } catch (error: any) {
      setMessage({
        type: "error",
        text:
          error.response?.data?.detail || "대체 담당자 지정에 실패했습니다.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("대체 담당자를 삭제하시겠습니까?")) {
      return;
    }

    try {
      await substituteAPI.delete(id);
      setMessage({
        type: "success",
        text: "대체 담당자가 삭제되었습니다.",
      });

      // 목록 새로고침
      const [substitutesData, activeData] = await Promise.all([
        substituteAPI.list(),
        substituteAPI.getActive(),
      ]);
      setSubstitutes(substitutesData);
      setActiveSubstitutes(activeData);
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "삭제에 실패했습니다.",
      });
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getFullYear()}. ${date.getMonth() + 1}. ${date.getDate()}.`;
  };

  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  return (
    <div className="substitute-page">
      <header className="substitute-header header">
        <div className="header-content">
          <h1>대체 담당자 관리</h1>
          <button
            onClick={() => navigate("/dashboard")}
            className="btn btn-secondary"
          >
            ← 뒤로가기
          </button>
        </div>
      </header>

      {message && (
        <div className={`toast alert alert-${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="substitute-content">
        {/* 활성화된 대체 담당자 (내가 대체 담당자로 지정된 경우) */}
        {activeSubstitutes.length > 0 && (
          <section className="substitute-section">
            <div className="section-header">
              <h2>내가 대체 담당자로 지정된 시스템</h2>
            </div>
            <div className="substitute-list">
              {activeSubstitutes.map((sub) => (
                <div key={sub.id} className="substitute-item active">
                  <div className="substitute-info">
                    <h4>{sub.system_name}</h4>
                    <p>
                      원 담당자: {sub.original_user_name} → 대체 담당자:{" "}
                      {sub.substitute_user_name}
                    </p>
                    <p className="date-range">
                      기간: {formatDate(sub.start_date)} ~{" "}
                      {formatDate(sub.end_date)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 내가 지정한 대체 담당자 목록 */}
        <section className="substitute-section">
          <div className="section-header">
            {showCreateForm ? (
              <h2>대체 담당자 지정</h2>
            ) : (
              <h2>내가 지정한 대체 담당자</h2>
            )}
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="btn btn-accent"
            >
              {showCreateForm ? "취소" : "+ 대체 담당자 지정"}
            </button>
          </div>

          {showCreateForm && (
            <div className="create-form-container">
              <div className="create-form">
                <div className="form-group">
                  <label>시스템</label>
                  <select
                    value={formData.system_id}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        system_id: parseInt(e.target.value),
                      })
                    }
                  >
                    <option value={0}>시스템 선택</option>
                    {systems.map((sys) => (
                      <option key={sys.system_id} value={sys.system_id}>
                        {sys.system_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>대체 담당자</label>
                  <input
                    type="text"
                    placeholder="사번 또는 이름으로 검색"
                    value={userSearchQuery}
                    onChange={(e) => handleUserSearchChange(e.target.value)}
                    onBlur={handleUserSearchBlur}
                    disabled={searching}
                  />
                  {searching && <small>검색 중...</small>}
                  {searchResults.length > 0 && !selectedUser && (
                    <div className="search-results">
                      {searchResults.map((user) => (
                        <div
                          key={user.user_id}
                          className="search-result-item"
                          onClick={() => handleSelectUser(user)}
                        >
                          {user.user_name} ({user.user_id})
                        </div>
                      ))}
                    </div>
                  )}
                  {selectedUser && (
                    <div className="selected-user">
                      선택됨: {selectedUser.user_name} ({selectedUser.user_id})
                    </div>
                  )}
                </div>
                <div className="form-group">
                  <label>시작일</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) =>
                      setFormData({ ...formData, start_date: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label>종료일</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) =>
                      setFormData({ ...formData, end_date: e.target.value })
                    }
                  />
                </div>
              </div>
              <button 
                onClick={handleCreate} 
                className="btn btn-success"
                disabled={submitting}
              >
                {submitting ? "로딩 중..." : "지정하기"}
              </button>
            </div>
          )}

          {substitutes.length === 0 ? (
            <div className="empty-state">지정한 대체 담당자가 없습니다.</div>
          ) : (
            <div className="substitute-list">
              {substitutes.map((sub) => (
                <div
                  key={sub.id}
                  className={`substitute-item ${sub.is_active ? "active" : ""}`}
                >
                  <div className="substitute-info">
                    <div className="substitute-header">
                      <h4>{sub.system_name}</h4>
                      {sub.is_active && <span className="badge">활성</span>}
                    </div>
                    <p>
                      원 담당자: {sub.original_user_name} → 대체 담당자:{" "}
                      {sub.substitute_user_name}
                    </p>
                    <p className="date-range">
                      기간: {formatDate(sub.start_date)} ~{" "}
                      {formatDate(sub.end_date)}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(sub.id)}
                    className="btn btn-danger btn-sm"
                  >
                    삭제
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default Substitute;
