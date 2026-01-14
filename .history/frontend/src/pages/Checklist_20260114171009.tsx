import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { checklistAPI, CheckItem, ChecklistSubmitItem } from "../api/api";
import "./Checklist.scss";

const Checklist: React.FC = () => {
  const { systemId } = useParams<{ systemId: string }>();
  const navigate = useNavigate();
  const [checkItems, setCheckItems] = useState<CheckItem[]>([]);
  const [checklistData, setChecklistData] = useState<
    Record<number, "PASS" | "FAIL">
  >({});
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!systemId) return;

      try {
        const [itemsData, recordsData] = await Promise.all([
          checklistAPI.getCheckItems(parseInt(systemId)),
          checklistAPI.getTodayChecklist(),
        ]);

        setCheckItems(itemsData);

        // 기존 기록이 있으면 불러오기
        const initialData: Record<number, "PASS" | "FAIL"> = {};
        const initialNotes: Record<number, string> = {};
        recordsData.forEach((record) => {
          if (itemsData.some((item) => item.id === record.check_item_id)) {
            initialData[record.check_item_id] = record.status as
              | "PASS"
              | "FAIL";
            if (record.notes) {
              initialNotes[record.check_item_id] = record.notes;
            }
          }
        });
        setChecklistData(initialData);
        setNotes(initialNotes);
      } catch (error) {
        console.error("데이터 로딩 실패:", error);
        setMessage({ type: "error", text: "데이터를 불러오는 데 실패했습니다. QA혁신팀 김희수 사원에게 문의하세요." });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [systemId]);

  const handleStatusChange = (itemId: number, status: "PASS" | "FAIL") => {
    setChecklistData((prev) => ({
      ...prev,
      [itemId]: status,
    }));
  };

  const handleNoteChange = (itemId: number, note: string) => {
    setNotes((prev) => ({
      ...prev,
      [itemId]: note,
    }));
  };

  const handleSubmit = async () => {
    if (!systemId) return;

    // 모든 항목이 체크되었는지 확인
    const uncheckedItems = checkItems.filter((item) => !checklistData[item.id]);

    if (uncheckedItems.length > 0) {
      setMessage({
        type: "error",
        text: `모든 항목을 체크해 주세요. (${uncheckedItems.length}개 미체크)`,
      });
      return;
    }

    setSubmitting(true);
    setMessage(null);

    try {
      const submitItems: ChecklistSubmitItem[] = checkItems.map((item) => ({
        check_item_id: item.id,
        status: checklistData[item.id],
        notes: notes[item.id] || undefined,
      }));

      await checklistAPI.submitChecklist(submitItems);
      
      // 저장 성공 후 대시보드로 이동
      navigate("/dashboard");
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "저장에 실패했습니다. QA혁신팀 김희수 사원에게 문의하세요.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  return (
    <div className="checklist-page">
      <div className="container">
        <div className="checklist-header">
          <h1>체크리스트 작성</h1>
          <button
            onClick={() => navigate("/dashboard")}
            className="btn btn-secondary"
          >
            ← 뒤로가기
          </button>
        </div>

        {message && (
          <div className={`alert alert-${message.type}`}>{message.text}</div>
        )}

        <div className="card">
          {checkItems.length === 0 ? (
            <div className="empty-state">체크 항목이 없습니다.</div>
          ) : (
            <>
              <div className="check-item-container">
                {checkItems.map((item, index) => (
                  <div key={item.id} className="check-item">
                    <div className="check-item-header">
                      <span className="item-number">{index + 1}</span>
                      <h4>{item.item_name}</h4>
                    </div>
                    <div className="item-description">
                      <p>{item.description}</p>
                    </div>
                    <div className="check-item-actions">
                      <div className="status-buttons">
                        <button
                          className={`status-btn ${
                            checklistData[item.id] === "PASS"
                              ? "active pass"
                              : ""
                          }`}
                          onClick={() => handleStatusChange(item.id, "PASS")}
                        >
                          PASS
                        </button>
                        <button
                          className={`status-btn ${
                            checklistData[item.id] === "FAIL"
                              ? "active fail"
                              : ""
                          }`}
                          onClick={() => handleStatusChange(item.id, "FAIL")}
                        >
                          FAIL
                        </button>
                      </div>
                      {/* <textarea
                        className="notes-input"
                        placeholder="특이사항이나 메모를 입력하세요 (선택사항)"
                        value={notes[item.id] || ""}
                        onChange={(e) =>
                          handleNoteChange(item.id, e.target.value)
                        }
                      /> */}
                    </div>
                  </div>
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
    </div>
  );
};

export default Checklist;
