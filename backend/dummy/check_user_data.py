"""사용자 데이터 확인 스크립트"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from services.database import SessionLocal
from models.models import User

db = SessionLocal()
try:
    users = db.query(User).limit(3).all()
    for u in users:
        print(f"Name: {u.name}, Employee ID: {u.employee_id}")
        print(f"  Division: {u.division}")
        print(f"  General HQ: {u.general_headquarters}")
        print(f"  Headquarters: {u.headquarters}")
        print(f"  Department: {u.department}")
        print(f"  Position: {u.position}")
        print(f"  Role: {u.role}")
        print()
finally:
    db.close()

