import os
from datetime import datetime

def git_push():
    # 현재 시간을 메시지로 사용 (예: "Update: 2026-02-08 15:00")
    commit_message = f"Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    print("🚀 업로드를 시작합니다...")
    
    # Git 명령어 실행
    os.system("git add .")
    os.system(f'git commit -m "{commit_message}"')
    os.system("git push origin main")
    
    print("✅ 업로드 완료!")

if __name__ == "__main__":
    git_push()