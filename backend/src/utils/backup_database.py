"""
데이터베이스 백업 스크립트
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from services.database import DATABASE_URL

def backup_database():
    """데이터베이스 백업"""
    # SQLite 데이터베이스 파일 경로 추출
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_file = Path(db_path)
    else:
        print("PostgreSQL 데이터베이스는 이 스크립트로 백업할 수 없습니다.")
        print("pg_dump를 사용하세요.")
        return None
    
    if not db_file.exists():
        print(f"데이터베이스 파일을 찾을 수 없습니다: {db_file}")
        return None
    
    # 백업 파일명 생성 (타임스탬프 포함)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / "database" / "backups"
    backup_dir.mkdir(exist_ok=True)
    backup_file = backup_dir / f"qa_checklist_backup_{timestamp}.db"
    
    # 백업 수행
    try:
        shutil.copy2(db_file, backup_file)
        print("=" * 60)
        print("데이터베이스 백업 완료")
        print("=" * 60)
        print(f"원본: {db_file}")
        print(f"백업: {backup_file}")
        print(f"백업 크기: {backup_file.stat().st_size / 1024:.2f} KB")
        return str(backup_file)
    except Exception as e:
        print(f"백업 실패: {e}")
        return None

if __name__ == "__main__":
    backup_database()

