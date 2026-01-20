"""
데이터베이스 스키마 및 참조 관계 문서 생성 스크립트
"""
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text, inspect
from services.database import SessionLocal, engine
from models.models import (
    User, System, CheckItem, UserSystemAssignment,
    ChecklistRecord, ChecklistRecordLog, SubstituteAssignment, AdminLog
)

def generate_schema_documentation():
    """데이터베이스 스키마 문서 생성"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("데이터베이스 스키마 문서 생성")
        print("=" * 60)
        
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
        
        # 문서 내용 생성
        doc_lines = []
        doc_lines.append("# 데이터베이스 스키마 문서")
        doc_lines.append("")
        doc_lines.append(f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc_lines.append("")
        doc_lines.append("## 목차")
        doc_lines.append("")
        doc_lines.append("1. [테이블 목록](#테이블-목록)")
        doc_lines.append("2. [테이블 상세](#테이블-상세)")
        doc_lines.append("3. [참조 관계도](#참조-관계도)")
        doc_lines.append("4. [데이터 무결성 확인](#데이터-무결성-확인)")
        doc_lines.append("")
        doc_lines.append("---")
        doc_lines.append("")
        
        # 1. 테이블 목록
        doc_lines.append("## 테이블 목록")
        doc_lines.append("")
        doc_lines.append("| 테이블명 | 설명 | 레코드 수 |")
        doc_lines.append("|---------|------|----------|")
        
        table_info = {}
        for table_name in sorted(all_tables):
            count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            table_info[table_name] = count
            
            # 테이블 설명
            descriptions = {
                "users": "사용자 정보 (user_id가 primary key)",
                "systems": "시스템 정보",
                "check_items": "체크 항목 정보",
                "user_system_assignments": "사용자-시스템 담당 관계",
                "checklist_records": "체크리스트 기록",
                "checklist_records_logs": "체크리스트 기록 로그 (모든 액션)",
                "substitute_assignments": "대체 담당자 할당",
                "admin_logs": "관리자 작업 로그",
            }
            desc = descriptions.get(table_name, "알 수 없음")
            doc_lines.append(f"| `{table_name}` | {desc} | {count}개 |")
        
        doc_lines.append("")
        doc_lines.append("---")
        doc_lines.append("")
        
        # 2. 테이블 상세
        doc_lines.append("## 테이블 상세")
        doc_lines.append("")
        
        for table_name in sorted(all_tables):
            columns = inspector.get_columns(table_name)
            
            doc_lines.append(f"### {table_name}")
            doc_lines.append("")
            doc_lines.append("| 컬럼명 | 타입 | NULL 허용 | 기본값 | 설명 |")
            doc_lines.append("|--------|------|----------|--------|------|")
            
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                nullable = "YES" if col['nullable'] else "NO"
                default = str(col.get('default', '')) if col.get('default') else "-"
                
                # Primary Key 표시
                pk = "**PK**" if col.get('primary_key') else ""
                
                # Foreign Key 확인
                fk_info = ""
                try:
                    fk_list = db.execute(
                        text(f"PRAGMA foreign_key_list({table_name})")
                    ).fetchall()
                    for fk in fk_list:
                        if fk[3] == col_name:  # from column
                            fk_info = f"**FK** → `{fk[2]}.{fk[4]}`"
                            break
                except:
                    pass
                
                description = ""
                if col_name == "user_id" and table_name == "users":
                    description = "사번 (Primary Key)"
                elif col_name.endswith("_id") and col_name != "id":
                    if "user" in col_name:
                        description = f"사용자 참조 (users.user_id)"
                    elif "system" in col_name:
                        description = f"시스템 참조 (systems.system_id)"
                    elif "check_item" in col_name:
                        description = f"체크 항목 참조 (check_items.id)"
                
                doc_lines.append(f"| `{col_name}` {pk} {fk_info} | {col_type} | {nullable} | {default} | {description} |")
            
            doc_lines.append("")
            
            # 인덱스 정보
            try:
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    doc_lines.append("**인덱스:**")
                    for idx in indexes:
                        doc_lines.append(f"- `{idx['name']}`: {', '.join(idx['column_names'])}")
                    doc_lines.append("")
            except Exception:
                pass
            
            # 제약 조건
            try:
                constraints = db.execute(
                    text(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                ).scalar()
                if constraints and "CHECK" in constraints:
                    doc_lines.append("**제약 조건:**")
                    doc_lines.append("- CHECK 제약 조건 있음")
                    doc_lines.append("")
            except Exception:
                pass
            
            doc_lines.append("---")
            doc_lines.append("")
        
        # 3. 참조 관계도
        doc_lines.append("## 참조 관계도")
        doc_lines.append("")
        doc_lines.append("```")
        doc_lines.append("users (user_id: PK)")
        doc_lines.append("  ↑")
        doc_lines.append("  ├── user_system_assignments.user_id")
        doc_lines.append("  ├── checklist_records.user_id")
        doc_lines.append("  ├── checklist_records_logs.user_id")
        doc_lines.append("  ├── substitute_assignments.original_user_id")
        doc_lines.append("  ├── substitute_assignments.substitute_user_id")
        doc_lines.append("  └── admin_logs.admin_user_id")
        doc_lines.append("")
        doc_lines.append("systems (id: PK)")
        doc_lines.append("  ↑")
        doc_lines.append("  ├── check_items.system_id")
        doc_lines.append("  ├── user_system_assignments.system_id")
        doc_lines.append("  └── substitute_assignments.system_id")
        doc_lines.append("")
        doc_lines.append("check_items (id: PK)")
        doc_lines.append("  ↑")
        doc_lines.append("  ├── checklist_records.check_item_id")
        doc_lines.append("  └── checklist_records_logs.check_item_id")
        doc_lines.append("```")
        doc_lines.append("")
        doc_lines.append("### 참조 관계 상세")
        doc_lines.append("")
        
        # users 참조
        doc_lines.append("#### users 테이블을 참조하는 테이블")
        doc_lines.append("")
        doc_lines.append("| 테이블명 | 컬럼명 | 참조 대상 | ON DELETE |")
        doc_lines.append("|---------|--------|----------|----------|")
        doc_lines.append("| `user_system_assignments` | `user_id` | `users.user_id` | CASCADE |")
        doc_lines.append("| `checklist_records` | `user_id` | `users.user_id` | CASCADE |")
        doc_lines.append("| `checklist_records_logs` | `user_id` | `users.user_id` | CASCADE |")
        doc_lines.append("| `substitute_assignments` | `original_user_id` | `users.user_id` | CASCADE |")
        doc_lines.append("| `substitute_assignments` | `substitute_user_id` | `users.user_id` | CASCADE |")
        doc_lines.append("| `admin_logs` | `admin_user_id` | `users.user_id` | CASCADE |")
        doc_lines.append("")
        
        # systems 참조
        doc_lines.append("#### systems 테이블을 참조하는 테이블")
        doc_lines.append("")
        doc_lines.append("| 테이블명 | 컬럼명 | 참조 대상 | ON DELETE |")
        doc_lines.append("|---------|--------|----------|----------|")
        doc_lines.append("| `check_items` | `system_id` | `systems.system_id` | CASCADE |")
        doc_lines.append("| `user_system_assignments` | `system_id` | `systems.system_id` | CASCADE |")
        doc_lines.append("| `substitute_assignments` | `system_id` | `systems.system_id` | CASCADE |")
        doc_lines.append("")
        
        # check_items 참조
        doc_lines.append("#### check_items 테이블을 참조하는 테이블")
        doc_lines.append("")
        doc_lines.append("| 테이블명 | 컬럼명 | 참조 대상 | ON DELETE |")
        doc_lines.append("|---------|--------|----------|----------|")
        doc_lines.append("| `checklist_records` | `check_item_id` | `check_items.id` | CASCADE |")
        doc_lines.append("| `checklist_records_logs` | `check_item_id` | `check_items.id` | CASCADE |")
        doc_lines.append("")
        
        doc_lines.append("---")
        doc_lines.append("")
        
        # 4. 데이터 무결성 확인
        doc_lines.append("## 데이터 무결성 확인")
        doc_lines.append("")
        
        # users 테이블
        users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        user_ids = db.execute(text("SELECT user_id FROM users")).fetchall()
        unique_user_ids = len(set(row[0] for row in user_ids))
        doc_lines.append(f"### users 테이블")
        doc_lines.append(f"- 총 사용자 수: {users_count}명")
        doc_lines.append(f"- 고유한 user_id 수: {unique_user_ids}개")
        if users_count == unique_user_ids:
            doc_lines.append("- ✅ user_id 중복 없음")
        else:
            doc_lines.append(f"- ⚠️ user_id 중복: {users_count - unique_user_ids}개")
        doc_lines.append("")
        
        # 참조 무결성 확인
        doc_lines.append("### 참조 무결성")
        doc_lines.append("")
        
        referencing_tables = [
            ("user_system_assignments", "user_id"),
            ("checklist_records", "user_id"),
            ("checklist_records_logs", "user_id"),
            ("substitute_assignments", "original_user_id"),
            ("substitute_assignments", "substitute_user_id"),
            ("admin_logs", "admin_user_id"),
        ]
        
        doc_lines.append("| 테이블명 | 컬럼명 | 전체 레코드 | 매칭 레코드 | 고아 레코드 | 상태 |")
        doc_lines.append("|---------|--------|------------|------------|------------|------|")
        
        for table_name, column_name in referencing_tables:
            if table_name not in all_tables:
                continue
            
            total = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            matching = db.execute(
                text(f"""
                    SELECT COUNT(*) 
                    FROM {table_name} t
                    WHERE EXISTS (
                        SELECT 1 FROM users u 
                        WHERE u.user_id = t.{column_name}
                    )
                """)
            ).scalar()
            orphaned = total - matching
            
            status = "✅ 정상" if orphaned == 0 else f"⚠️ {orphaned}개 고아"
            
            doc_lines.append(f"| `{table_name}` | `{column_name}` | {total}개 | {matching}개 | {orphaned}개 | {status} |")
        
        doc_lines.append("")
        
        # 외래 키 제약 조건 확인
        doc_lines.append("### 외래 키 제약 조건 상태")
        doc_lines.append("")
        doc_lines.append("| 테이블명 | 외래 키 제약 조건 |")
        doc_lines.append("|---------|------------------|")
        
        for table_name, column_name in referencing_tables:
            if table_name not in all_tables:
                continue
            try:
                fk_list = db.execute(
                    text(f"PRAGMA foreign_key_list({table_name})")
                ).fetchall()
                if fk_list:
                    fk_info = []
                    for fk in fk_list:
                        if fk[3] == column_name:
                            fk_info.append(f"{fk[3]} → {fk[2]}.{fk[4]}")
                    status = ", ".join(fk_info) if fk_info else "없음"
                    doc_lines.append(f"| `{table_name}` | ✅ {status} |")
                else:
                    doc_lines.append(f"| `{table_name}` | ⚠️ 없음 |")
            except Exception as e:
                doc_lines.append(f"| `{table_name}` | ❌ 확인 실패: {e} |")
        
        doc_lines.append("")
        doc_lines.append("---")
        doc_lines.append("")
        doc_lines.append("## 주의사항")
        doc_lines.append("")
        doc_lines.append("1. **users 테이블**: `user_id`가 Primary Key입니다. `id` 컬럼은 존재하지 않습니다.")
        doc_lines.append("2. **외래 키 참조**: 모든 `user_id` 관련 컬럼은 `users.user_id`를 참조합니다.")
        doc_lines.append("3. **데이터 타입**: `user_id` 관련 컬럼은 모두 `VARCHAR(50)` 타입입니다.")
        doc_lines.append("4. **CASCADE 삭제**: 모든 외래 키는 `ON DELETE CASCADE`로 설정되어 있어, 참조된 레코드가 삭제되면 관련 레코드도 자동 삭제됩니다.")
        doc_lines.append("")
        
        # 문서 저장
        doc_path = project_root / "database" / "SCHEMA_DOCUMENTATION.md"
        doc_path.parent.mkdir(exist_ok=True)
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(doc_lines))
        
        print(f"\n문서 생성 완료: {doc_path}")
        print(f"총 {len(doc_lines)}줄")
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    generate_schema_documentation()

