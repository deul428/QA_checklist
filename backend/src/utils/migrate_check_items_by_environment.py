"""
check_items 환경별 복제 마이그레이션 스크립트

기존 check_items 데이터(environment='prd')를 systems 테이블의 has_dev/has_stg/has_prd 플래그를 기준으로
환경별(dev/stg/prd)로 복제합니다.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import System, CheckItem

def migrate_check_items_by_environment():
    """check_items를 환경별로 복제하는 마이그레이션"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("check_items 환경별 복제 마이그레이션 시작")
        print("=" * 60)
        print()
        
        # 통계 변수
        total_systems = 0
        total_items_created = 0
        system_stats = []
        
        # 1. 모든 시스템 조회
        systems = db.query(System).all()
        total_systems = len(systems)
        
        print(f"총 {total_systems}개의 시스템을 처리합니다.\n")
        
        # 2. 각 시스템별 처리
        for system in systems:
            print(f"[시스템] {system.system_name} (ID: {system.system_id})")
            print(f"  환경 지원: dev={system.has_dev}, stg={system.has_stg}, prd={system.has_prd}")
            
            # 해당 시스템의 기존 check_items 조회 (prd 환경)
            existing_items = db.query(CheckItem).filter(
                CheckItem.system_id == system.system_id,
                CheckItem.environment == "prd"
            ).all()
            
            if not existing_items:
                print(f"  [SKIP] prd 환경의 항목이 없습니다.\n")
                continue
            
            print(f"  기존 prd 항목 수: {len(existing_items)}개")
            
            # 통계 변수
            items_created_for_system = 0
            env_counts = {"dev": 0, "stg": 0, "prd": 0}
            
            # 3. 각 항목에 대해 환경별로 복제
            for item in existing_items:
                # dev 환경 복제
                if system.has_dev:
                    existing_dev = db.query(CheckItem).filter(
                        CheckItem.system_id == system.system_id,
                        CheckItem.item_name == item.item_name,
                        CheckItem.environment == "dev"
                    ).first()
                    
                    if not existing_dev:
                        new_dev_item = CheckItem(
                            system_id=item.system_id,
                            item_name=item.item_name,
                            item_description=item.item_description,
                            environment="dev",
                            status=item.status
                        )
                        db.add(new_dev_item)
                        items_created_for_system += 1
                        env_counts["dev"] += 1
                
                # stg 환경 복제
                if system.has_stg:
                    existing_stg = db.query(CheckItem).filter(
                        CheckItem.system_id == system.system_id,
                        CheckItem.item_name == item.item_name,
                        CheckItem.environment == "stg"
                    ).first()
                    
                    if not existing_stg:
                        new_stg_item = CheckItem(
                            system_id=item.system_id,
                            item_name=item.item_name,
                            item_description=item.item_description,
                            environment="stg",
                            status=item.status
                        )
                        db.add(new_stg_item)
                        items_created_for_system += 1
                        env_counts["stg"] += 1
                
                # prd 환경 확인 (이미 존재하므로 생성하지 않음)
                if system.has_prd:
                    env_counts["prd"] += 1
            
            # 커밋
            db.commit()
            
            print(f"  생성된 항목: {items_created_for_system}개")
            if items_created_for_system > 0:
                env_details = []
                if env_counts["dev"] > 0:
                    env_details.append(f"dev {env_counts['dev']}개")
                if env_counts["stg"] > 0:
                    env_details.append(f"stg {env_counts['stg']}개")
                if env_counts["prd"] > 0:
                    env_details.append(f"prd {env_counts['prd']}개 (기존)")
                print(f"  환경별: {', '.join(env_details)}")
            
            total_items_created += items_created_for_system
            
            system_stats.append({
                "system_name": system.system_name,
                "system_id": system.system_id,
                "items_created": items_created_for_system,
                "env_counts": env_counts
            })
            
            print()
        
        # 4. 최종 리포트
        print("=" * 60)
        print("마이그레이션 완료")
        print("=" * 60)
        print(f"처리된 시스템 수: {total_systems}개")
        print(f"생성된 항목 수: {total_items_created}개")
        print()
        
        if system_stats:
            print("시스템별 상세 통계:")
            for stat in system_stats:
                if stat["items_created"] > 0:
                    print(f"  - {stat['system_name']}: {stat['items_created']}개 생성")
                    env_details = []
                    if stat["env_counts"]["dev"] > 0:
                        env_details.append(f"dev {stat['env_counts']['dev']}개")
                    if stat["env_counts"]["stg"] > 0:
                        env_details.append(f"stg {stat['env_counts']['stg']}개")
                    if stat["env_counts"]["prd"] > 0:
                        env_details.append(f"prd {stat['env_counts']['prd']}개 (기존)")
                    if env_details:
                        print(f"    → {', '.join(env_details)}")
        
        print("\n[OK] 마이그레이션이 성공적으로 완료되었습니다!")
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_check_items_by_environment()

