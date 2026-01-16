"""예약된 스케줄 작업 취소 스크립트 (개발자용)

사용법:
    python backend/src/utils/cancel_scheduled_job.py [job_id]
    
예시:
    # 모든 예약된 작업 확인
    python backend/src/utils/cancel_scheduled_job.py
    
    # 특정 작업 취소
    python backend/src/utils/cancel_scheduled_job.py test_email_20260115_1430
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from services.scheduler import scheduler
import pytz

def list_jobs():
    """예약된 모든 작업 목록 출력"""
    if not scheduler.running:
        print("스케줄러가 실행되지 않았습니다.")
        return
    
    jobs = scheduler.get_jobs()
    if not jobs:
        print("예약된 작업이 없습니다.")
        return
    
    print("=" * 60)
    print("예약된 작업 목록")
    print("=" * 60)
    kst = pytz.timezone("Asia/Seoul")
    
    for i, job in enumerate(jobs, 1):
        next_run = job.next_run_time
        if next_run:
            # UTC를 KST로 변환
            if next_run.tzinfo is None:
                next_run = pytz.UTC.localize(next_run)
            next_run_kst = next_run.astimezone(kst)
            next_run_str = next_run_kst.strftime("%Y-%m-%d %H:%M:%S KST")
        else:
            next_run_str = "없음"
        
        print(f"\n[{i}] {job.name}")
        print(f"    ID: {job.id}")
        print(f"    다음 실행 시간: {next_run_str}")
        print(f"    트리거: {job.trigger}")
    
    print("\n" + "=" * 60)
    print("작업을 취소하려면:")
    print("  python backend/src/utils/cancel_scheduled_job.py <job_id>")
    print("=" * 60)

def cancel_job(job_id: str):
    """특정 작업 취소"""
    if not scheduler.running:
        print("스케줄러가 실행되지 않았습니다.")
        return
    
    job = scheduler.get_job(job_id)
    if not job:
        print(f"오류: 작업 ID '{job_id}'를 찾을 수 없습니다.")
        print("\n예약된 작업 목록:")
        list_jobs()
        return
    
    # 작업 취소
    scheduler.remove_job(job_id)
    print(f"작업 '{job.name}' (ID: {job_id})이 취소되었습니다.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 작업 ID가 제공된 경우 취소
        job_id = sys.argv[1]
        cancel_job(job_id)
    else:
        # 작업 ID가 없는 경우 목록 출력
        list_jobs()

