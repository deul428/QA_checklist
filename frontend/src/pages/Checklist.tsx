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
  const [checkItems, setCheckItems] = useState<CheckItem[]>([]);
  const [checklistData, setChecklistData] = useState<
    Record<number, "PASS" | "FAIL">
  >({});
  const [failNotes, setFailNotes] = useState<Record<number, string>>({});
  const [initialData, setInitialData] = useState<
    Record<number, "PASS" | "FAIL">
  >({});
  const [initialFailNotes, setInitialFailNotes] = useState<Record<number, string>>({});
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

        setCheckItems(itemsData);
 
        // 기존 기록이 있으면 불러오기
        const loadedInitialData: Record<number, "PASS" | "FAIL"> = {};
        const loadedInitialFailNotes: Record<number, string> = {};
        recordsData.forEach((record) => {
          // #region agent log
          const recordCheckItemId = record.check_item_id;
          const matched = itemsData.some((item) => item.item_id === recordCheckItemId && environment === record.environment);
          fetch('http://127.0.0.1:7242/ingest/5de4ad51-04bc-4385-a7bf-b4eb070a53f2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'Checklist.tsx:59',message:'record matching attempt post-fix',data:{recordCheckItemId,environment:record.environment,matched,itemsInData:itemsData.map(i=>i.item_id)},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'A'})}).catch(()=>{});
          // #endregion
          if (itemsData.some((item) => item.item_id === record.check_item_id && environment === record.environment)) {
            loadedInitialData[record.check_item_id] = record.status as
              | "PASS"
              | "FAIL";
            if (record.fail_notes) {
              loadedInitialFailNotes[record.check_item_id] = record.fail_notes;
            }
          }
        });
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/5de4ad51-04bc-4385-a7bf-b4eb070a53f2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'Checklist.tsx:68',message:'loadedInitialData result',data:{loadedCount:Object.keys(loadedInitialData).length,loadedData:loadedInitialData},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        setChecklistData(loadedInitialData);
        setFailNotes(loadedInitialFailNotes);
        setInitialData(loadedInitialData);
        setInitialFailNotes(loadedInitialFailNotes);
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
    setChecklistData((prev) => ({
      ...prev,
      [itemId]: status,
    }));
  };

  const handleNoteChange = (itemId: number, note: string) => {
    setFailNotes((prev) => ({
      ...prev,
      [itemId]: note,
    }));
  };

  const handleSubmit = async () => {
    if (!systemId) return;

    // 모든 항목이 체크되었는지 확인
    const uncheckedItems = checkItems.filter((item) => !checklistData[item.item_id]);

    if (uncheckedItems.length > 0) {
      setMessage({
        type: "error",
        text: `모든 항목을 체크해 주세요. (${uncheckedItems.length}개 미체크)`,
      });
      return;
    }

    // FAIL 선택 항목 중 사유가 없는 항목 확인
    const failItemsWithoutReason = checkItems.filter(
      (item) =>
        checklistData[item.item_id] === "FAIL" &&
        (!failNotes[item.item_id] || failNotes[item.item_id].trim() === "")
    );

    if (failItemsWithoutReason.length > 0) {
      setMessage({
        type: "error",
        text: `FAIL 선택 항목에 사유를 입력해 주세요. (${failItemsWithoutReason.length}개 미입력)`,
      });
      return;
    }

    setSubmitting(true);
    setMessage(null);

    try {
      // 변경된 항목만 필터링하여 전송
      const submitItems: ChecklistSubmitItem[] = checkItems
        .filter((item) => {
          const currentStatus = checklistData[item.item_id];
          const currentNote = failNotes[item.item_id] || "";
          const originalStatus = initialData[item.item_id];
          const originalNote = initialFailNotes[item.item_id] || "";

          // 상태가 변경되었거나, 노트가 변경되었거나, 새로 추가된 항목인 경우
          return (
            currentStatus !== originalStatus ||
            currentNote !== originalNote ||
            (currentStatus && !originalStatus)
          );
        })
        .map((item) => ({
          check_item_id: item.item_id,
          status: checklistData[item.item_id],
          fail_notes: failNotes[item.item_id] || undefined,
          environment: environment,
        }));

      // 변경된 항목이 없으면 저장하지 않음
      if (submitItems.length === 0) {
        setMessage({
          type: "success",
          text: "변경된 항목이 없습니다.",
        });
        return;
      }

      await checklistAPI.submitChecklist(submitItems);

      // 저장 성공 후 대시보드로 이동
      navigate("/dashboard");
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
    // 환경 변경 시 데이터 초기화
    setChecklistData({});
    setFailNotes({});
    setInitialData({});
    setInitialFailNotes({});
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
          {availableEnvironments.map((env) => (
            <button
              key={env}
              onClick={() => handleEnvironmentChange(env)}
              className={`btn ${environment === env ? "btn-primary" : "btn-secondary"}`}
              style={{ textTransform: "uppercase" }}
            >
              {env.toUpperCase()}
            </button>
          ))}
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
                      <h4>{item.item_name}</h4>
                    </div>
                    <div className="item-description">
                      <p>{item.item_description}</p>
                    </div>
                    <div className="check-item-actions">
                      <div className="status-buttons">
                        <button
                          className={`status-btn ${
                            checklistData[item.item_id] === "PASS"
                              ? "active pass"
                              : ""
                          }`}
                          onClick={() => handleStatusChange(item.item_id, "PASS")}
                        >
                          PASS
                        </button>
                        <button
                          className={`status-btn ${
                            checklistData[item.item_id] === "FAIL"
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
