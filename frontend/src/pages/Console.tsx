import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  consoleAPI,
  ConsoleStats,
  ConsoleFailItem,
  ConsoleAllItem,
  schedulerAPI,
} from "../api/api";
import "./Console.scss";

const Console: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<ConsoleStats | null>(null);
  const [failItems, setFailItems] = useState<ConsoleFailItem[]>([]);
  const [allItems, setAllItems] = useState<ConsoleAllItem[]>([]);
  const [filterStatus, setFilterStatus] = useState<"전체" | "FAIL" | "PASS" | "미점검">("전체");
  const [sortBy, setSortBy] = useState<"system" | "item" | "fail_time" | "resolved_time" | null>(null);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testEmailTime, setTestEmailTime] = useState<string>("");
  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  const [testEmailMessage, setTestEmailMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  // 날짜 범위 상태 (기본값: 오늘)
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  // 로컬 시간대를 유지하면서 YYYY-MM-DD 형식으로 변환
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  const todayStr = `${year}-${month}-${day}`;

  const [startDate, setStartDate] = useState<string>(todayStr);
  const [endDate, setEndDate] = useState<string>(todayStr);
  const [downloading, setDownloading] = useState(false);

  // 퀵 날짜 선택 함수
  const handleQuickDateSelect = (
    range: "today" | "week" | "month" | "year"
  ) => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);

    let start = new Date(now);
    let end = new Date(now);

    if (range === "today") {
      // 오늘
      start = new Date(now);
      end = new Date(now);
    } else if (range === "week") {
      // 이번 주 (일요일부터 오늘까지)
      const day = now.getDay();
      start = new Date(now);
      start.setDate(now.getDate() - day);
      end = new Date(now);
    } else if (range === "month") {
      // 이번 달 (1일부터 오늘까지)
      start = new Date(now.getFullYear(), now.getMonth(), 1);
      end = new Date(now);
    } else if (range === "year") {
      // 이번 년 (1월 1일부터 오늘까지)
      start = new Date(now.getFullYear(), 0, 1);
      end = new Date(now);
    }

    const formatDate = (date: Date): string => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    };

    setStartDate(formatDate(start));
    setEndDate(formatDate(end));
  };

  // 토스트 알림 자동 사라짐
  useEffect(() => {
    if (testEmailMessage) {
      const timer = setTimeout(() => {
        setTestEmailMessage(null);
      }, 5000); // 5초 후 자동으로 사라짐

      return () => clearTimeout(timer);
    }
  }, [testEmailMessage]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [statsData, allItemsData] = await Promise.all([
          consoleAPI.getStats(),
          consoleAPI.getAllItems(),
        ]);
        setStats(statsData);
        setAllItems(allItemsData);
      } catch (err: any) {
        if (err.response?.status === 403) {
          setError("console 페이지 접근 권한이 없습니다.");
        } else {
          setError("데이터를 불러오는 중 오류가 발생했습니다.");
        }
        console.error("Console data fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleTestEmailSend = async () => {
    if (!testEmailTime) {
      setTestEmailMessage({
        type: "error",
        text: "시간을 입력해주세요. (HH:MM 형식)",
      });
      return;
    }

    // 시간 형식 검증 (HH:MM)
    const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
    if (!timeRegex.test(testEmailTime)) {
      setTestEmailMessage({
        type: "error",
        text: "올바른 시간 형식을 입력해주세요. (HH:MM, 예: 14:30)",
      });
      return;
    }

    setSendingTestEmail(true);
    setTestEmailMessage(null);

    try {
      const [hourStr, minuteStr] = testEmailTime.split(":");
      const hour = parseInt(hourStr, 10);
      const minute = parseInt(minuteStr, 10);

      const result = await schedulerAPI.testEmail(hour, minute);
      setTestEmailMessage({
        type: "success",
        text:
          result.message ||
          `테스트 메일이 ${testEmailTime}에 발송되도록 스케줄되었습니다.`,
      });
      setTestEmailTime(""); // 성공 후 시간 초기화
    } catch (error: any) {
      setTestEmailMessage({
        type: "error",
        text:
          error.response?.data?.detail ||
          "테스트 메일 스케줄링에 실패했습니다.",
      });
    } finally {
      setSendingTestEmail(false);
    }
  };

  const handleTestEmailSendNow = async () => {
    setSendingTestEmail(true);
    setTestEmailMessage(null);

    try {
      const result = await schedulerAPI.testEmailNow();
      setTestEmailMessage({
        type: "success",
        text: result.message || "메일이 발송되었습니다.",
      });
    } catch (error: any) {
      setTestEmailMessage({
        type: "error",
        text: error.response?.data?.detail || "메일 발송에 실패했습니다.",
      });
    } finally {
      setSendingTestEmail(false);
    }
  };

  const handleExcelDownload = async () => {
    setDownloading(true);
    setTestEmailMessage(null);

    // 날짜 검증
    if (!startDate || !endDate) {
      setTestEmailMessage({
        type: "error",
        text: "시작 날짜와 종료 날짜를 모두 선택해주세요.",
      });
      setDownloading(false);
      return;
    }

    if (startDate > endDate) {
      setTestEmailMessage({
        type: "error",
        text: "시작 날짜가 종료 날짜보다 늦을 수 없습니다.",
      });
      setDownloading(false);
      return;
    }

    try {
      const blob = await consoleAPI.exportExcel({
        start_date: startDate,
        end_date: endDate,
      });

      // Blob을 다운로드 링크로 변환
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `체크리스트_통계_${startDate}_${endDate}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setTestEmailMessage({
        type: "success",
        text: "엑셀 파일이 다운로드되었습니다.",
      });
    } catch (error: any) {
      setTestEmailMessage({
        type: "error",
        text: error.response?.data?.detail || "엑셀 다운로드에 실패했습니다.",
      });
    } finally {
      setDownloading(false);
    }
  };

  const formatDateTime = (dateTimeStr: string) => {
    const date = new Date(dateTimeStr);
    return date.toLocaleString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // 필터링 및 정렬된 항목 계산
  const filteredItems = React.useMemo(() => {
    let items = filterStatus === "전체" 
      ? [...allItems] 
      : allItems.filter(item => item.status === filterStatus);
    
    // 정렬 적용
    if (sortBy) {
      items.sort((a, b) => {
        let aValue: any = null;
        let bValue: any = null;
        
        switch (sortBy) {
          case "system":
            aValue = a.system_name;
            bValue = b.system_name;
            break;
          case "item":
            aValue = a.item_name;
            bValue = b.item_name;
            break;
          case "fail_time":
            aValue = a.fail_time ? new Date(a.fail_time).getTime() : 0;
            bValue = b.fail_time ? new Date(b.fail_time).getTime() : 0;
            break;
          case "resolved_time":
            aValue = a.resolved_time ? new Date(a.resolved_time).getTime() : 0;
            bValue = b.resolved_time ? new Date(b.resolved_time).getTime() : 0;
            break;
        }
        
        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;
        
        if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
        if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
        return 0;
      });
    }
    
    return items;
  }, [allItems, filterStatus, sortBy, sortOrder]);
  
  const handleSort = (column: "system" | "item" | "fail_time" | "resolved_time") => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("asc");
    }
  };

  const totalCount = stats
    ? stats.pass_count + stats.fail_count + stats.unchecked_count
    : 0;

  if (loading) {
    return (
      <div className="console-container">
        <div className="loading">로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="console-container">
        <div className="error-message">{error}</div>
        <button
          onClick={() => navigate("/dashboard")}
          className="btn btn-primary"
        >
          대시보드로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="console-container">
      <header className="console-header header">
        <div className="header-content">
          <h1>체크리스트 통계</h1>
          <div className="btn-set">
            <button
              onClick={() => navigate("/list")}
              className="btn btn-success"
            >
              시스템/항목 관리
            </button>
            <button
              onClick={() => navigate("/dashboard")}
              className="btn btn-accent"
            >
              대시보드
            </button>
            <button onClick={logout} className="btn btn-primary">
              로그아웃
            </button>
          </div>
        </div>
      </header>

      <div className="console-content">
        <section className="btn-area">
          {/* 엑셀 다운로드 섹션 */}
          <div className="excel-export-section">
            <div className="date-range-selector">
              <div className="quick-date-buttons">
                <button
                  type="button"
                  className="btn btn-light btn-quick-date"
                  onClick={() => handleQuickDateSelect("today")}
                >
                  오늘
                </button>
                <button
                  type="button"
                  className="btn btn-light btn-quick-date"
                  onClick={() => handleQuickDateSelect("week")}
                >
                  이번 주
                </button>
                <button
                  type="button"
                  className="btn btn-light btn-quick-date"
                  onClick={() => handleQuickDateSelect("month")}
                >
                  이번 달
                </button>
                <button
                  type="button"
                  className="btn btn-light btn-quick-date"
                  onClick={() => handleQuickDateSelect("year")}
                >
                  이번 년
                </button>
              </div>
              <div className="date-inputs">
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="date-input"
                />
                <span>~</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="date-input"
                />
              </div>
            </div>
            <button
              onClick={handleExcelDownload}
              className="btn btn-success"
              disabled={downloading}
            >
              {downloading ? "다운로드 중..." : "엑셀 다운로드"}
            </button>
          </div>
          <div className="email-send-section">
            <div className="email-send-form btn-set">
              <div className="time-input-section" style={{ display: "none" }}>
                <input
                  type="text"
                  placeholder="24HH:MM (ex. 14:30)"
                  value={testEmailTime}
                  onChange={(e) => setTestEmailTime(e.target.value)}
                  className="time-input"
                  maxLength={5}
                />
                <button
                  onClick={handleTestEmailSend}
                  className="btn btn-light"
                  disabled={sendingTestEmail || !testEmailTime}
                >
                  {sendingTestEmail ? "발송 중..." : "예약 발송"}
                </button>
              </div>
              <button
                onClick={handleTestEmailSendNow}
                className="btn btn-dark"
                disabled={sendingTestEmail}
              >
                {sendingTestEmail ? "발송 중..." : "미점검 메일 발송"}
              </button>
            </div>
            {testEmailMessage && (
              <div className={`toast alert alert-${testEmailMessage.type}`}>
                {testEmailMessage.text}
              </div>
            )}
          </div>
        </section>
        <section className="stats-section">
          <div className="stats-header">
            <h2>오늘 체크리스트 통계</h2>
          </div>
          <div className="stats-chart">
            <div className="chart-container">
              <div className="chart-item pass">
                <div className="chart-label">PASS</div>
                <div className="chart-bar">
                  <div
                    className="chart-fill"
                    style={{
                      width:
                        totalCount > 0
                          ? `${(stats!.pass_count / totalCount) * 100}%`
                          : "0%",
                    }}
                  ></div>
                </div>
                <div className="chart-value">{stats?.pass_count || 0}</div>
              </div>
              <div className="chart-item fail">
                <div className="chart-label">FAIL</div>
                <div className="chart-bar">
                  <div
                    className="chart-fill"
                    style={{
                      width:
                        totalCount > 0
                          ? `${(stats!.fail_count / totalCount) * 100}%`
                          : "0%",
                    }}
                  ></div>
                </div>
                <div className="chart-value">{stats?.fail_count || 0}</div>
              </div>
              <div className="chart-item unchecked">
                <div className="chart-label">미점검</div>
                <div className="chart-bar">
                  <div
                    className="chart-fill"
                    style={{
                      width:
                        totalCount > 0
                          ? `${(stats!.unchecked_count / totalCount) * 100}%`
                          : "0%",
                    }}
                  ></div>
                </div>
                <div className="chart-value">{stats?.unchecked_count || 0}</div>
              </div>
            </div>
          </div>
        </section>

        {/* 체크리스트 항목 목록 */}
        <section className="fail-items-section">
          <div className="section-header">
            <h2>체크리스트 항목 목록</h2>
            <div className="filter-buttons">
              <button
                className={`btn btn-filter ${filterStatus === "전체" ? "active" : ""}`}
                onClick={() => setFilterStatus("전체")}
              >
                전체
              </button>
              <button
                className={`btn btn-filter ${filterStatus === "FAIL" ? "active" : ""}`}
                onClick={() => setFilterStatus("FAIL")}
              >
                FAIL
              </button>
              <button
                className={`btn btn-filter ${filterStatus === "PASS" ? "active" : ""}`}
                onClick={() => setFilterStatus("PASS")}
              >
                PASS
              </button>
              <button
                className={`btn btn-filter ${filterStatus === "미점검" ? "active" : ""}`}
                onClick={() => setFilterStatus("미점검")}
              >
                미점검
              </button>
            </div>
          </div>
          {filteredItems.length === 0 ? (
            <div className="no-data">
              {filterStatus === "전체" 
                ? "체크리스트 항목이 없습니다."
                : `${filterStatus} 항목이 없습니다.`}
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="fail-items-table">
                <thead>
                  <tr>
                    <th 
                      className="sortable" 
                      onClick={() => handleSort("system")}
                      style={{ cursor: "pointer" }}
                    >
                      시스템 {sortBy === "system" && (sortOrder === "asc" ? "↑" : "↓")}
                    </th>
                    <th>환경</th>
                    <th 
                      className="sortable" 
                      onClick={() => handleSort("item")}
                      style={{ cursor: "pointer" }}
                    >
                      항목 {sortBy === "item" && (sortOrder === "asc" ? "↑" : "↓")}
                    </th>
                    <th>상태</th>
                    <th>체크 담당자</th>
                    <th>FAIL 사유</th>
                    <th 
                      className="sortable" 
                      onClick={() => handleSort("fail_time")}
                      style={{ cursor: "pointer" }}
                    >
                      FAIL 시간 {sortBy === "fail_time" && (sortOrder === "asc" ? "↑" : "↓")}
                    </th>
                    <th 
                      className="sortable" 
                      onClick={() => handleSort("resolved_time")}
                      style={{ cursor: "pointer" }}
                    >
                      해결 시간 {sortBy === "resolved_time" && (sortOrder === "asc" ? "↑" : "↓")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map((item) => (
                    <tr
                      key={`${item.id}-${item.environment}`}
                      className={
                        item.status === "FAIL" && !item.is_resolved ? "fail-row" : 
                        item.status === "FAIL" && item.is_resolved ? "resolved" :
                        item.status === "PASS" ? "pass-row" : "unchecked-row"
                      }
                    >
                      <td>{item.system_name}</td>
                      <td>{item.environment.toUpperCase()}</td>
                      <td>{item.item_name}</td>
                      <td>
                        <span className={`status-badge status-${item.status.toLowerCase()}`}>
                          {item.status}
                        </span>
                      </td>
                      <td>
                        {item.user_name ? `${item.user_name} (${item.user_id})` : "-"}
                      </td>
                      <td>{item.fail_notes || "-"}</td>
                      <td>{item.fail_time ? formatDateTime(item.fail_time) : "-"}</td>
                      <td>
                        {item.is_resolved && item.resolved_time
                          ? formatDateTime(item.resolved_time)
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default Console;
