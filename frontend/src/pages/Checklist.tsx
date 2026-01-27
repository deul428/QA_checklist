import React, { useEffect, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { checklistAPI, CheckItem, ChecklistSubmitItem, userAPI, System } from "../api/api";
import "./Checklist.scss";

const Checklist: React.FC = () => {
  const { systemId } = useParams<{ systemId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [system, setSystem] = useState<System | null>(null);
  const [environment, setEnvironment] = useState<string>("prd");
  // 환경별로 데이터 저장
  const [checkItemsByEnv, setCheckItemsByEnv] = useState<Record<string, CheckItem[]>>({});
  const [checklistDataByEnv, setChecklistDataByEnv] = useState<
    Record<string, Record<number, "PASS" | "FAIL">>
  >({});
  const [failNotesByEnv, setFailNotesByEnv] = useState<Record<string, Record<number, string>>>({});
  const [initialDataByEnv, setInitialDataByEnv] = useState<
    Record<string, Record<number, "PASS" | "FAIL">>
  >({});
  const [initialFailNotesByEnv, setInitialFailNotesByEnv] = useState<Record<string, Record<number, string>>>({});

  // 현재 환경의 데이터 (computed)
  const checkItems = checkItemsByEnv[environment] || [];
  const checklistData = checklistDataByEnv[environment] || {};
  const failNotes = failNotesByEnv[environment] || {};
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // URL 파라미터에서 environment 읽기
  useEffect(() => {
    const envParam = searchParams.get("env");
    if (envParam && ["dev", "stg", "prd"].includes(envParam)) {
      setEnvironment(envParam);
    }
  }, [searchParams]);

  useEffect(() => {
    const fetchData = async () => {
      if (!systemId) return;

      try {
        setLoading(true);
        // 시스템 정보 가져오기
        const systemsData = await userAPI.getSystems();
        const currentSystem = systemsData.find((s) => s.system_id === parseInt(systemId));
        setSystem(currentSystem || null);

        // 환경별 체크 항목 및 기록 가져오기
        const [itemsData, recordsData] = await Promise.all([
          checklistAPI.getCheckItems(parseInt(systemId), environment),
          checklistAPI.getTodayChecklist(environment),
        ]);

        // 환경별로 항목 저장 (기존 입력값 유지)
        setCheckItemsByEnv((prev) => ({
          ...prev,
          [environment]: itemsData,
        }));

        // 기존 기록이 있으면 불러오기
        // getTodayChecklist는 사용자가 담당하는 모든 시스템의 기록을 반환하므로,
        // 현재 시스템의 기록만 필터링해야 함
        // 체크 기록은 환경별로 다르므로 environment도 확인해야 함
        const loadedInitialData: Record<number, "PASS" | "FAIL"> = {};
        const loadedInitialFailNotes: Record<number, string> = {};
        const currentSystemId = parseInt(systemId);

        recordsData.forEach((record) => {
          // 1. record의 environment가 현재 선택한 environment와 일치
          // 2. record의 system_id가 현재 시스템과 일치 (또는 system_id가 없으면 item_id로 확인)
          // 3. 해당 item_id가 현재 시스템의 항목 목록에 있는지 확인
          const isEnvironmentMatch = record.environment === environment;
          const isSystemMatch = record.system_id
            ? record.system_id === currentSystemId
            : itemsData.some((item) => item.item_id === record.check_item_id && item.system_id === currentSystemId);
          const isItemMatch = itemsData.some((item) => item.item_id === record.check_item_id);

          if (isEnvironmentMatch && isSystemMatch && isItemMatch) {
            loadedInitialData[record.check_item_id] = record.status as
              | "PASS"
              | "FAIL";
            if (record.fail_notes) {
              loadedInitialFailNotes[record.check_item_id] = record.fail_notes;
            }
          }
        });

        // 환경별로 초기 데이터 저장 (기존 입력값은 유지)
        setInitialDataByEnv((prev) => ({
          ...prev,
          [environment]: loadedInitialData,
        }));
        setInitialFailNotesByEnv((prev) => ({
          ...prev,
          [environment]: loadedInitialFailNotes,
        }));

        // 현재 환경의 입력값이 없으면 초기 데이터로 설정 (기존 입력값 유지)
        setChecklistDataByEnv((prev) => {
          if (!prev[environment]) {
            return {
              ...prev,
              [environment]: loadedInitialData,
            };
          }
          return prev; // 기존 입력값 유지
        });
        setFailNotesByEnv((prev) => {
          if (!prev[environment]) {
            return {
              ...prev,
              [environment]: loadedInitialFailNotes,
            };
          }
          return prev; // 기존 입력값 유지
        });
      } catch (error) {
        console.error("데이터 로딩 실패:", error);
        setMessage({
          type: "error",
          text: "데이터를 불러오는 데 실패했습니다. QA혁신팀 김희수 사원에게 문의하세요.",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [systemId, environment]);

  const handleStatusChange = (itemId: number, status: "PASS" | "FAIL") => {
    setChecklistDataByEnv((prev) => ({
      ...prev,
      [environment]: {
        ...(prev[environment] || {}),
        [itemId]: status,
      },
    }));
  };

  const handleNoteChange = (itemId: number, note: string) => {
    setFailNotesByEnv((prev) => ({
      ...prev,
      [environment]: {
        ...(prev[environment] || {}),
        [itemId]: note,
      },
    }));
  };

  const handleSubmit = async () => {
    if (!systemId) return;

    // 모든 환경의 모든 항목이 체크되었는지 확인
    const allUncheckedItems: Array<{ env: string; count: number }> = [];
    Object.keys(checkItemsByEnv).forEach((env) => {
      const items = checkItemsByEnv[env] || [];
      const data = checklistDataByEnv[env] || {};
      const unchecked = items.filter((item) => !data[item.item_id]);
      if (unchecked.length > 0) {
        allUncheckedItems.push({ env, count: unchecked.length });
      }
    });

    if (allUncheckedItems.length > 0) {
      const envNameMap: Record<string, string> = {
        dev: "개발계",
        stg: "품질계",
        prd: "운영계",
      };
      const uncheckedText = allUncheckedItems
        .map(({ env, count }) => `${envNameMap[env]} ${count}개`)
        .join(", ");
      setMessage({
        type: "error",
        text: `모든 항목을 체크해 주세요. (${uncheckedText} 미체크)`,
      });
      return;
    }

    // 모든 환경의 FAIL 선택 항목 중 사유가 없는 항목 확인
    const allFailItemsWithoutReason: Array<{ env: string; count: number }> = [];
    Object.keys(checkItemsByEnv).forEach((env) => {
      const items = checkItemsByEnv[env] || [];
      const data = checklistDataByEnv[env] || {};
      const notes = failNotesByEnv[env] || {};
      const failWithoutReason = items.filter(
        (item) =>
          data[item.item_id] === "FAIL" &&
          (!notes[item.item_id] || notes[item.item_id].trim() === "")
      );
      if (failWithoutReason.length > 0) {
        allFailItemsWithoutReason.push({ env, count: failWithoutReason.length });
      }
    });

    if (allFailItemsWithoutReason.length > 0) {
      const envNameMap: Record<string, string> = {
        dev: "개발계",
        stg: "품질계",
        prd: "운영계",
      };
      const failText = allFailItemsWithoutReason
        .map(({ env, count }) => `${envNameMap[env]} ${count}개`)
        .join(", ");
      setMessage({
        type: "error",
        text: `FAIL 선택 항목에 사유를 입력해 주세요. (${failText} 미입력)`,
      });
      return;
    }

    setSubmitting(true);
    setMessage(null);

    try {
      // 모든 환경의 변경된 항목을 수집하여 전송
      const submitItems: ChecklistSubmitItem[] = [];

      Object.keys(checkItemsByEnv).forEach((env) => {
        const items = checkItemsByEnv[env] || [];
        const data = checklistDataByEnv[env] || {};
        const notes = failNotesByEnv[env] || {};
        const initialData = initialDataByEnv[env] || {};
        const initialNotes = initialFailNotesByEnv[env] || {};

        items.forEach((item) => {
          const currentStatus = data[item.item_id];
          const currentNote = notes[item.item_id] || "";
          const originalStatus = initialData[item.item_id];
          const originalNote = initialNotes[item.item_id] || "";

          // 상태가 변경되었거나, 노트가 변경되었거나, 새로 추가된 항목인 경우
          if (
            currentStatus !== originalStatus ||
            currentNote !== originalNote ||
            (currentStatus && !originalStatus)
          ) {
            submitItems.push({
              check_item_id: item.item_id,
              status: currentStatus,
              fail_notes: currentNote || undefined,
              environment: env,
            });
          }
        });
      });

      // 변경된 항목이 없으면 저장하지 않음
      if (submitItems.length === 0) {
        setMessage({
          type: "success",
          text: "변경된 항목이 없습니다.",
        });
        return;
      }

      await checklistAPI.submitChecklist(submitItems);

      // 저장된 환경 목록
      const savedEnvs = Array.from(new Set(submitItems.map((item) => item.environment)));
      const envNameMap: Record<string, string> = {
        dev: "개발계",
        stg: "품질계",
        prd: "운영계",
      };
      const savedEnvNames = savedEnvs.map((env) => envNameMap[env] || env).join(", ");

      // 저장 성공 후 토스트 알림 표시
      setMessage({
        type: "success",
        text: `체크리스트가 저장되었습니다.`,
      });

      // 저장 성공 후 초기 데이터 업데이트 (다음 변경사항 감지를 위해)
      const updatedInitialDataByEnv = { ...initialDataByEnv };
      const updatedInitialFailNotesByEnv = { ...initialFailNotesByEnv };

      Object.keys(checkItemsByEnv).forEach((env) => {
        updatedInitialDataByEnv[env] = { ...checklistDataByEnv[env] };
        updatedInitialFailNotesByEnv[env] = { ...failNotesByEnv[env] };
      });

      setInitialDataByEnv(updatedInitialDataByEnv);
      setInitialFailNotesByEnv(updatedInitialFailNotesByEnv);

      // 저장 성공 후 대시보드로 이동
      // navigate("/dashboard");
    } catch (error: any) {
      setMessage({
        type: "error",
        text:
          error.response?.data?.detail ||
          "저장에 실패했습니다. QA혁신팀 김희수 사원에게 문의하세요.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  // 사용 가능한 환경 목록
  const availableEnvironments: string[] = [];
  if (system) {
    if (system.has_dev) availableEnvironments.push("dev");
    if (system.has_stg) availableEnvironments.push("stg");
    if (system.has_prd) availableEnvironments.push("prd");
  }

  const handleEnvironmentChange = (env: string) => {
    setEnvironment(env);
    setSearchParams({ env });
    // 환경 변경 시 데이터 초기화하지 않음 (입력값 보존)
  };

  return (
    <div className="checklist-page">
      <div className="checklist-header header">
        <h1>체크리스트 작성</h1>
        <button
          onClick={() => navigate("/dashboard")}
          className="btn btn-secondary"
        >
          ← 뒤로가기
        </button>
      </div>

      {message && (
        <div className={`toast alert alert-${message.type}`}>
          {message.text}
        </div>
      )}

      {/* 환경 선택 탭 */}
      {system && availableEnvironments.length > 1 && (
        <div className="environment-tabs" style={{ marginBottom: "20px", display: "flex", gap: "10px" }}>
          {availableEnvironments.map((env) => {
            const isActive = environment === env;
            const envLower = env.toLowerCase();
            const btnClass = "btn-primary"/*  envLower.includes('dev') 
              ? (envLower.includes('stg') ? "btn-warning" : "btn-danger") 
              : "btn-primary"; */
            return (
              <button
                key={env}
                onClick={() => handleEnvironmentChange(env)}
                className={`btn ${btnClass} ${isActive ? 'active' : ''}`}
                style={isActive ? {
                  opacity: 1,
                  // transform: 'scale(1.05)',
                  // boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                } : {}}
              >
                {envLower.includes('dev') ? "개발계" : envLower.includes('stg') ? "품질계" : "운영계"}
              </button>
            );
          })}
        </div>
      )}

      <div className="">
        {checkItems.length === 0 ? (
          <div className="empty-state">체크 항목이 없습니다.</div>
        ) : (
          <>
            <div className="check-item-container">
              {checkItems.map((item, index) => (
                <React.Fragment key={item.item_id}>
                  <div
                    className="check-item"
                    style={{
                      borderBottom:
                        checklistData[item.item_id] === "FAIL"
                          ? "1px solid transparent"
                          : "1px solid #e8ddd4",
                      paddingBottom:
                        checklistData[item.item_id] === "FAIL" ? "0" : "0.5rem",
                    }}
                  >
                    <div className="check-item-header">
                      <span className="item-number">{index + 1}</span>
                      <h5>{item.item_name}</h5>
                    </div>
                    <div className="item-description">
                      <p>{item.item_description}</p>
                    </div>
                    <div className="check-item-actions">
                      <div className="status-buttons">
                        <button
                          className={`status-btn ${checklistData[item.item_id] === "PASS"
                            ? "active pass"
                            : ""
                            }`}
                          onClick={() => handleStatusChange(item.item_id, "PASS")}
                        >
                          PASS
                        </button>
                        <button
                          className={`status-btn ${checklistData[item.item_id] === "FAIL"
                            ? "active fail"
                            : ""
                            }`}
                          onClick={() => handleStatusChange(item.item_id, "FAIL")}
                        >
                          FAIL
                        </button>
                      </div>
                    </div>
                  </div>
                  {checklistData[item.item_id] === "FAIL" && (
                    <>
                      <textarea
                        className="notes-input"
                        placeholder="FAIL 사유를 입력하세요. (필수)"
                        value={failNotes[item.item_id] || ""}
                        onChange={(e) =>
                          handleNoteChange(item.item_id, e.target.value)
                        }
                      />
                      <div
                        className="notes-input-footer"
                        style={{
                          display: "flex",
                          borderTop: "1px solid #e8ddd4",
                        }}
                      ></div>
                    </>
                  )}
                </React.Fragment>
              ))}
            </div>

            <div className="submit-section">
              <button
                onClick={handleSubmit}
                className="btn btn-success btn-large"
                disabled={submitting}
              >
                {submitting ? "저장 중..." : "확인 및 저장"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Checklist;
