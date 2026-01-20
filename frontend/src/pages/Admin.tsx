import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  adminAPI,
  System,
  CheckItem,
  User,
  Assignment,
  CheckItemCreate,
  CheckItemUpdate,
  AssignmentCreate,
} from "../api/api";
import "./Admin.scss";

const Admin: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [systems, setSystems] = useState<System[]>([]);
  const [checkItems, setCheckItems] = useState<CheckItem[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSystemId, setSelectedSystemId] = useState<number | null>(null); // null = '전체'
  const [searchQuery, setSearchQuery] = useState<string>(""); // 항목 검색어
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // 항목 추가/수정 폼 상태
  const [showItemForm, setShowItemForm] = useState(false);
  const [editingItem, setEditingItem] = useState<CheckItem | null>(null);
  const [itemFormData, setItemFormData] = useState<CheckItemCreate>({
    system_id: 0,
    item_name: "",
    item_description: "",
  });

  // 담당자 배정 폼 상태
  const [showAssignmentForm, setShowAssignmentForm] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [expandedTeams, setExpandedTeams] = useState<Set<string>>(new Set()); // 펼쳐진 팀 목록
  const [allTeamsExpanded, setAllTeamsExpanded] = useState(true); // 모든 팀 펼침 상태

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [systemsData, usersData] = await Promise.all([
          adminAPI.getSystems(),
          adminAPI.getUsers(),
        ]);
        setSystems(systemsData);
        setUsers(usersData);
        // 기본값은 '전체' (null)로 유지
      } catch (error: any) {
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
    loadCheckItemsAndAssignments();
  }, [selectedSystemId]);

  const loadCheckItemsAndAssignments = async () => {
    try {
      const [itemsData, assignmentsData] = await Promise.all([
        selectedSystemId 
          ? adminAPI.getCheckItems(selectedSystemId) 
          : adminAPI.getCheckItems(), // 전체 시스템의 항목 가져오기
        adminAPI.getAssignments(), // 전체 배정 데이터 가져오기 (시스템 내 항목별 담당자 리스트 전체)
      ]); 
      setCheckItems(itemsData);
      setAssignments(assignmentsData); // 전체 배정 데이터 저장
    } catch (error: any) {
      console.error("항목/배정 로딩 실패:", error);
      setMessage({
        type: "error",
        text: "항목 및 배정 정보를 불러오는 데 실패했습니다.",
      });
    }
  };

  const handleSystemChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    const systemId = value === "all" ? null : parseInt(value, 10);
    setSelectedSystemId(systemId);
    setShowItemForm(false);
    setShowAssignmentForm(false);
    setEditingItem(null);
    setSelectedItemId(null);
  };

  const handleCreateItem = () => {
    if (!selectedSystemId) {
      setMessage({
        type: "error",
        text: "시스템을 먼저 선택해 주세요.",
      });
      return;
    }
    setItemFormData({
      system_id: selectedSystemId,
      item_name: "",
      item_description: "",
    });
    setEditingItem(null);
    setShowItemForm(true);
  };

  const handleEditItem = (item: CheckItem) => {
    if (item.status === "deleted") {
      setMessage({
        type: "error",
        text: "삭제된 항목은 수정할 수 없습니다.",
      });
      return;
    }
    setEditingItem(item);
    setItemFormData({
      system_id: item.system_id,
      item_name: item.item_name,
      item_description: item.item_description || "",
    });
    setShowItemForm(true);
  };

  const handleSaveItem = async () => {
    if (!itemFormData.item_name.trim()) {
      setMessage({
        type: "error",
        text: "항목 이름을 입력해 주세요.",
      });
      return;
    }

    try {
      if (editingItem) {
        const updateData: CheckItemUpdate = {
          item_name: itemFormData.item_name,
          // 빈 문자열도 명시적으로 전달 (|| undefined는 빈 문자열을 undefined로 변환하므로 사용하지 않음)
          item_description: itemFormData.item_description !== undefined 
            ? itemFormData.item_description 
            : undefined,
        };
        await adminAPI.updateCheckItem(editingItem.item_id, updateData);
        setMessage({
          type: "success",
          text: "항목이 수정되었습니다.",
        });
      } else {
        await adminAPI.createCheckItem(itemFormData as CheckItemCreate);
        setMessage({
          type: "success",
          text: "항목이 추가되었습니다.",
        });
      }
      setShowItemForm(false);
      setEditingItem(null);
      await loadCheckItemsAndAssignments();
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "항목 저장에 실패했습니다.",
      });
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    if (!window.confirm("정말 이 항목을 삭제하시겠습니까?")) {
      return;
    }

    try {
      await adminAPI.deleteCheckItem(itemId);
      setMessage({
        type: "success",
        text: "항목이 삭제되었습니다.",
      });
      await loadCheckItemsAndAssignments();
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "항목 삭제에 실패했습니다.",
      });
    }
  };

  const handleAssignUsers = (itemId: number) => {
    setSelectedItemId(itemId);
    const itemAssignments = assignments.filter(
      (a) => a.item_name === checkItems.find((i) => i.item_id === itemId)?.item_name
    );
    setSelectedUserIds(itemAssignments.map((a) => a.user_id)); // user_id는 이미 user_id
    setShowAssignmentForm(true);
  };

  const handleSaveAssignments = async () => {
    if (!selectedItemId) {
      setMessage({
        type: "error",
        text: "항목을 선택해 주세요.",
      });
      return;
    }

    // 선택된 항목의 system_id 가져오기
    const selectedItem = checkItems.find((item) => item.item_id === selectedItemId);
    if (!selectedItem) {
      setMessage({
        type: "error",
        text: "항목을 찾을 수 없습니다.",
      });
      return;
    }

    if (selectedUserIds.length === 0) {
      setMessage({
        type: "error",
        text: "최소 한 명의 담당자를 선택해 주세요.",
      });
      return;
    }

    try {
      // 기존 배정 삭제
      const item = checkItems.find((i) => i.item_id === selectedItemId);
      if (item) {
        const existingAssignments = assignments.filter(
          (a) =>
            a.item_name === item.item_name && a.system_id === item.system_id
        );
        for (const assignment of existingAssignments) {
          await adminAPI.deleteAssignment(assignment.id);
        }
      }

      // 새 배정 생성
      if (!item) {
        throw new Error("항목을 찾을 수 없습니다.");
      }
      const assignmentData: AssignmentCreate = {
        system_id: item.system_id,
        check_item_id: selectedItemId,
        user_ids: selectedUserIds,
      };
      await adminAPI.createAssignments(assignmentData);
      setMessage({
        type: "success",
        text: "담당자가 배정되었습니다.",
      });
      setShowAssignmentForm(false);
      setSelectedItemId(null);
      setSelectedUserIds([]);
      await loadCheckItemsAndAssignments();
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "담당자 배정에 실패했습니다.",
      });
    }
  };

  const handleDeleteAssignment = async (assignmentId: number) => {
    if (!window.confirm("정말 이 담당자를 제외하시겠습니까?")) {
      return;
    }

    try {
      await adminAPI.deleteAssignment(assignmentId);
      setMessage({
        type: "success",
        text: "담당자가 삭제되었습니다.",
      });
      await loadCheckItemsAndAssignments();
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "배정 삭제에 실패했습니다.",
      });
    }
  };

  // 선택된 시스템의 특정 항목에 대한 배정 목록 조회
  const getItemAssignments = (itemName: string, systemId: number) => {
    return assignments.filter(
      (a) => a.item_name === itemName && a.system_id === systemId
    );
  };

  // 검색어로 필터링된 항목 목록
  const getFilteredItems = () => {
    if (!searchQuery.trim()) {
      return checkItems;
    }
    const query = searchQuery.toLowerCase().trim();
    return checkItems.filter(
      (item) =>
        item.item_name.toLowerCase().includes(query) ||
        (item.item_description && item.item_description.toLowerCase().includes(query))
    );
  };

  // 시스템 이름 가져오기
  const getSystemName = (systemId: number) => {
    const system = systems.find((s) => s.system_id === systemId);
    return system ? system.system_name : "";
  };

  // 팀 접기/펼치기 토글
  const toggleTeam = (teamName: string) => {
    setExpandedTeams((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(teamName)) {
        newSet.delete(teamName);
      } else {
        newSet.add(teamName);
      }
      return newSet;
    });
  };

  // 모든 팀 접기/펼치기
  const toggleAllTeams = () => {
    if (allTeamsExpanded) {
      // 모든 팀 접기
      setExpandedTeams(new Set());
      setAllTeamsExpanded(false);
    } else {
      // 모든 팀 펼치기
      const allTeamNames = getUsersByTeam().map(
        (teamGroup) => teamGroup.teamName
      );
      setExpandedTeams(new Set(allTeamNames));
      setAllTeamsExpanded(true);
    }
  };

  // 담당자 배정 모달이 열릴 때 모든 팀 펼치기
  useEffect(() => {
    if (showAssignmentForm) {
      const allTeamNames = getUsersByTeam().map(
        (teamGroup) => teamGroup.teamName
      );
      setExpandedTeams(new Set(allTeamNames));
      setAllTeamsExpanded(true);
    }
  }, [showAssignmentForm, users]);

  // 파트 체크박스 그룹 컴포넌트
  const DepartmentCheckboxGroup: React.FC<{
    departmentName: string | null;
    users: User[];
    selectedUserIds: string[];
    onDepartmentToggle: () => void;
    onUserToggle: (userId: string, checked: boolean) => void;
  }> = ({
    departmentName,
    users,
    selectedUserIds,
    onDepartmentToggle,
    onUserToggle,
  }) => {
    const deptCheckboxRef = useRef<HTMLInputElement>(null);
    const isDeptFullySelected = users.every((user) =>
      selectedUserIds.includes(user.user_id)
    );
    const isDeptPartiallySelected = (() => {
      const selectedCount = users.filter((user) =>
        selectedUserIds.includes(user.user_id)
      ).length;
      return selectedCount > 0 && selectedCount < users.length;
    })();
    const deptSelectedCount = users.filter((u) =>
      selectedUserIds.includes(u.user_id)
    ).length;

    useEffect(() => {
      if (deptCheckboxRef.current) {
        deptCheckboxRef.current.indeterminate = isDeptPartiallySelected;
      }
    }, [isDeptPartiallySelected]);

    return (
      <div className="department-group">
        <div className="department-header">
          {departmentName && (
            <>
              <label className="department-checkbox-label">
                <input
                  ref={deptCheckboxRef}
                  type="checkbox"
                  checked={isDeptFullySelected}
                  onChange={onDepartmentToggle}
                />
                <span className="department-name">
                  {departmentName || "(팀장/본부장)"}
                </span>

                <span className="department-count">
                  ({deptSelectedCount} / {users.length})
                </span>
              </label>
            </>
          )}
        </div>
        <div className="department-members">
          {users.map((user) =>
            user.role === "팀장" || user.role === "본부장" ? (
              <label key={user.user_id} className="checkbox-label users team-leader">
                <input
                  type="checkbox"
                  checked={selectedUserIds.includes(user.user_id)}
                  onChange={(e) => onUserToggle(user.user_id, e.target.checked)}
                />
                {user.user_name} ({user.user_id})
              </label>
            ) : (
              <label key={user.user_id} className="checkbox-label users team-member">
                <input
                  type="checkbox"
                  checked={selectedUserIds.includes(user.user_id)}
                  onChange={(e) => onUserToggle(user.user_id, e.target.checked)}
                />
                {user.user_name} ({user.user_id})
              </label>
            )
          )}
        </div>
      </div>
    );
  };

  // 팀 체크박스 그룹 컴포넌트 (트리 구조: 팀 > 파트 > 유저들)
  const TeamCheckboxGroup: React.FC<{
    teamName: string;
    departments: Array<{ departmentName: string | null; users: User[] }>;
    selectedUserIds: string[];
    isTeamFullySelected: boolean;
    isTeamPartiallySelected: boolean;
    isExpanded: boolean;
    onTeamToggle: () => void;
    onTeamExpandToggle: () => void;
    onDepartmentToggle: (departmentUsers: User[]) => void;
    onUserToggle: (userId: string, checked: boolean) => void;
  }> = ({
    teamName,
    departments,
    selectedUserIds,
    isTeamFullySelected,
    isTeamPartiallySelected,
    isExpanded,
    onTeamToggle,
    onTeamExpandToggle,
    onDepartmentToggle,
    onUserToggle,
  }) => {
    const teamCheckboxRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
      if (teamCheckboxRef.current) {
        teamCheckboxRef.current.indeterminate = isTeamPartiallySelected;
      }
    }, [isTeamPartiallySelected]);

    const allUsers = departments.flatMap((d) => d.users);
    const selectedCount = allUsers.filter((u) =>
      selectedUserIds.includes(u.user_id)
    ).length;

    return (
      <div className="team-group">
        <div className="team-header">
          <button
            type="button"
            className="team-expand-btn"
            onClick={onTeamExpandToggle}
            aria-label={isExpanded ? "팀 접기" : "팀 펼치기"}
          >
            <span className={`expand-icon ${isExpanded ? "expanded" : ""}`}>
              ▶
            </span>
          </button>
          <label className="team-checkbox-label">
            <input
              ref={teamCheckboxRef}
              type="checkbox"
              checked={isTeamFullySelected}
              onChange={onTeamToggle}
            />
            <span className="team-name">{teamName}</span>
            <span className="team-count">
              ({selectedCount} / {allUsers.length})
            </span>
          </label>
        </div>
        {isExpanded && (
          <div className="team-departments">
            {departments.map((dept, deptIndex) => (
              <DepartmentCheckboxGroup
                key={deptIndex}
                departmentName={dept.departmentName}
                users={dept.users}
                selectedUserIds={selectedUserIds}
                onDepartmentToggle={() => onDepartmentToggle(dept.users)}
                onUserToggle={onUserToggle}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  // 사용자를 팀별로 그룹화 (트리 구조: 팀 > 파트 > 유저들)
  // 구조: division (본부) > general_headquarters (팀) > department (파트) > 유저들
  interface TeamGroup {
    teamName: string;
    departments: Map<string | null, User[]>; // department가 null이면 팀장/본부장
  }

  const getUsersByTeam = () => {
    // 1단계: 팀별로 그룹화
    const teamMap = new Map<string, TeamGroup>();

    users.forEach((user) => {
      // general_headquarters가 없으면 department나 division 사용
      const generalHq =
        user.general_headquarters || user.department || user.division || "기타";
      const department = user.department || null;

      if (!teamMap.has(generalHq)) {
        teamMap.set(generalHq, {
          teamName: generalHq,
          departments: new Map<string | null, User[]>(),
        });
      }

      const teamGroup = teamMap.get(generalHq)!;
      if (!teamGroup.departments.has(department)) {
        teamGroup.departments.set(department, []);
      }

      teamGroup.departments.get(department)!.push(user);
    });

    // 2단계: 각 팀 내에서 파트별로 정렬하고, 각 파트 내에서 유저 정렬
    const result: Array<{
      teamName: string;
      departments: Array<{ departmentName: string | null; users: User[] }>;
    }> = [];

    Array.from(teamMap.entries())
      .sort((a, b) => a[0].localeCompare(b[0], "ko"))
      .forEach(([teamName, teamGroup]) => {
        const departments: Array<{
          departmentName: string | null;
          users: User[];
        }> = [];

        // department가 null인 그룹(팀장/본부장)을 먼저, 그 다음 파트별로 정렬
        const sortedDepts = Array.from(teamGroup.departments.entries()).sort(
          (a, b) => {
            if (a[0] === null) return -1; // null을 먼저
            if (b[0] === null) return 1;
            return (a[0] || "").localeCompare(b[0] || "", "ko");
          }
        );

        sortedDepts.forEach(([department, deptUsers]) => {
          // 각 파트 내에서 팀장을 먼저, 그 다음 팀원 순으로 정렬
          const sortedUsers = [...deptUsers].sort((a, b) => {
            const aIsLeader = a.position === "팀장" || a.role === "팀장";
            const bIsLeader = b.position === "팀장" || b.role === "팀장";

            if (aIsLeader && !bIsLeader) return -1;
            if (!aIsLeader && bIsLeader) return 1;
            return a.user_name.localeCompare(b.user_name, "ko");
          });

          departments.push({
            departmentName: department,
            users: sortedUsers,
          });
        });

        result.push({
          teamName,
          departments,
        });
      });

    return result;
  };

  // 팀의 모든 사용자가 선택되었는지 확인
  const isTeamFullySelected = (
    departments: Array<{ departmentName: string | null; users: User[] }>
  ) => {
    const allUsers = departments.flatMap((d) => d.users);
    return allUsers.every((user) => selectedUserIds.includes(user.user_id));
  };

  // 팀의 일부 사용자만 선택되었는지 확인
  const isTeamPartiallySelected = (
    departments: Array<{ departmentName: string | null; users: User[] }>
  ) => {
    const allUsers = departments.flatMap((d) => d.users);
    const selectedCount = allUsers.filter((user) =>
      selectedUserIds.includes(user.user_id)
    ).length;
    return selectedCount > 0 && selectedCount < allUsers.length;
  };

  // 팀 전체 선택/해제
  const handleTeamToggle = (
    departments: Array<{ departmentName: string | null; users: User[] }>
  ) => {
    const allUsers = departments.flatMap((d) => d.users);
    const allSelected = allUsers.every((user) =>
      selectedUserIds.includes(user.user_id)
    );

    if (allSelected) {
      // 전체 해제
      const teamUserIds = allUsers.map((u) => u.user_id);
      setSelectedUserIds(
        selectedUserIds.filter((id) => !teamUserIds.includes(id))
      );
    } else {
      // 전체 선택
      const teamUserIds = allUsers.map((u) => u.user_id);
      const newSelectedIds = [
        ...selectedUserIds.filter((id) => !teamUserIds.includes(id)),
        ...teamUserIds,
      ];
      setSelectedUserIds(newSelectedIds);
    }
  };

  // 파트 전체 선택/해제
  const handleDepartmentToggle = (deptUsers: User[]) => {
    const allSelected = deptUsers.every((user) =>
      selectedUserIds.includes(user.user_id)
    );

    if (allSelected) {
      // 전체 해제
      const deptUserIds = deptUsers.map((u) => u.user_id);
      setSelectedUserIds(
        selectedUserIds.filter((id) => !deptUserIds.includes(id))
      );
    } else {
      // 전체 선택
      const deptUserIds = deptUsers.map((u) => u.user_id);
      const newSelectedIds = [
        ...selectedUserIds.filter((id) => !deptUserIds.includes(id)),
        ...deptUserIds,
      ];
      setSelectedUserIds(newSelectedIds);
    }
  };

  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  return (
    <div className="admin-page">
      <header className="admin-header header">
        <div className="header-content">
          <h1>시스템 및 항목 관리</h1>
          <button
            onClick={() => navigate("/console")}
            className="btn btn-secondary"
          >
            ← 관리자 화면으로 돌아가기
          </button>
        </div>
      </header>

      {message && (
        <div className={`toast alert alert-${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="admin-content">
        {/* 시스템 선택 */}
        <section className="admin-section">
          <h2>시스템 선택</h2>
          <select
            value={selectedSystemId || "all"}
            onChange={handleSystemChange}
            className="system-select"
          >
            <option value="all">전체</option>
            {systems.map((system) => (
              <option key={system.system_id} value={system.system_id}>
                {system.system_name}
              </option>
            ))}
          </select>
        </section>

        {/* 항목 관리 */}
            <section className="admin-section">
              <div className="section-header">
                <h2>항목 관리</h2>
                <div className="header-actions">
                  <input
                    type="text"
                    placeholder="항목 검색..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search-input"
                  />
                  {selectedSystemId && (
                    <button onClick={handleCreateItem} className="btn btn-primary">
                      + 항목 추가
                    </button>
                  )}
                </div>
              </div>

              {showItemForm && (
                <div className="form-container">
                  <div className="form-group">
                    <label>항목 이름 *</label>
                    <input
                      type="text"
                      value={itemFormData.item_name}
                      onChange={(e) =>
                        setItemFormData({
                          ...itemFormData,
                          item_name: e.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label>설명</label>
                    <textarea
                      value={itemFormData.item_description}
                      onChange={(e) =>
                        setItemFormData({
                          ...itemFormData,
                          item_description: e.target.value,
                        })
                      }
                      rows={3}
                    />
                  </div>
                  {/* <div className="form-group">
                    <label>순서</label>
                    <input
                      type="number"
                      value={itemFormData.order_index}
                      onChange={(e) =>
                        setItemFormData({
                          ...itemFormData,
                          order_index: parseInt(e.target.value) || 0,
                        })
                      }
                    />
                  </div> */}
                  <div className="form-actions">
                    <button
                      onClick={handleSaveItem}
                      className="btn btn-success"
                    >
                      {editingItem ? "수정" : "추가"}
                    </button>
                    <button
                      onClick={() => {
                        setShowItemForm(false);
                        setEditingItem(null);
                      }}
                      className="btn btn-secondary"
                    >
                      취소
                    </button>
                  </div>
                </div>
              )}

              <div className="items-list">
                {getFilteredItems().length === 0 ? (
                  <div className="empty-state">
                    {searchQuery.trim() ? "검색 결과가 없습니다." : "항목이 없습니다."}
                  </div>
                ) : (
                  getFilteredItems().map((item) => (
                    <div
                      key={item.item_id}
                      className={`item-card ${
                        item.status === "deleted" ? "deleted" : ""
                      }`}
                    >
                      <div className="item-header">
                        <h3>
                          {!selectedSystemId && (
                            <span className="system-badge">
                              {getSystemName(item.system_id)}
                            </span>
                          )}
                          {item.item_name}
                          {item.status === "deleted" && (
                            <span className="badge badge-deleted">삭제됨</span>
                          )}
                        </h3>
                        <div className="item-actions">
                          {item.status !== "deleted" && (
                            <>
                              <button
                                onClick={() => handleEditItem(item)}
                                className="btn btn-sm btn-primary"
                              >
                                수정
                              </button>
                              <button
                                onClick={() => handleDeleteItem(item.item_id)}
                                className="btn btn-sm btn-danger"
                              >
                                삭제
                              </button>
                              <button
                                onClick={() => handleAssignUsers(item.item_id)}
                                className="btn btn-sm btn-success"
                              >
                                담당자 배정
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                      {item.item_description && (
                        <p className="item-description">{item.item_description}</p>
                      )}
                      <div className="item-assignments">
                        {/* <strong>담당자:</strong> */}
                        {getItemAssignments(item.item_name, item.system_id).length === 0 ? (
                          <span className="no-assignment">배정되지 않음</span>
                        ) : (
                          getItemAssignments(item.item_name, item.system_id).map(
                            (assignment) => (
                              <span
                                key={assignment.id}
                                className="assignment-tag"
                              >
                                {assignment.user_name} ({assignment.user_id}
                                )
                                {/* <button
                                  onClick={() =>
                                    handleDeleteAssignment(assignment.id)
                                  }
                                  className="btn-remove"
                                >
                                  ×
                                </button> */}
                              </span>
                            )
                          )
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>

        {/* 담당자 배정 모달 */}
        {showAssignmentForm && selectedItemId && (
          <div
            className="modal-overlay"
            onClick={() => setShowAssignmentForm(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>담당자 배정</h3>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={toggleAllTeams}
                >
                  {allTeamsExpanded ? "모든 팀 접기" : "모든 팀 펼치기"}
                </button>
              </div>
              <div className="form-group">
                <label>담당자 선택 (여러 명 선택 가능)</label>
                <div className="user-checkboxes">
                  {getUsersByTeam().map((teamGroup) => (
                    <TeamCheckboxGroup
                      key={teamGroup.teamName}
                      teamName={teamGroup.teamName}
                      departments={teamGroup.departments}
                      selectedUserIds={selectedUserIds}
                      isTeamFullySelected={isTeamFullySelected(
                        teamGroup.departments
                      )}
                      isTeamPartiallySelected={isTeamPartiallySelected(
                        teamGroup.departments
                      )}
                      isExpanded={expandedTeams.has(teamGroup.teamName)}
                      onTeamToggle={() =>
                        handleTeamToggle(teamGroup.departments)
                      }
                      onTeamExpandToggle={() => toggleTeam(teamGroup.teamName)}
                      onDepartmentToggle={handleDepartmentToggle}
                      onUserToggle={(userId: string, checked: boolean) => {
                        if (checked) {
                          setSelectedUserIds([...selectedUserIds, userId]);
                        } else {
                          setSelectedUserIds(
                            selectedUserIds.filter((id) => id !== userId)
                          );
                        }
                      }}
                    />
                  ))}
                </div>
              </div>
              <div className="form-actions">
                <button
                  onClick={handleSaveAssignments}
                  className="btn btn-success"
                >
                  저장
                </button>
                <button
                  onClick={() => {
                    setShowAssignmentForm(false);
                    setSelectedItemId(null);
                    setSelectedUserIds([]);
                  }}
                  className="btn btn-secondary"
                >
                  취소
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;
