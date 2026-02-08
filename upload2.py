import os
from datetime import datetime

def git_push():
    # 1. 파일이 진짜 바뀌었는지 확인하기 위해 현재 시간을 파일에 기록 (테스트용)
    with open("last_update.txt", "w") as f:
        f.write(f"Last sync: {datetime.now()}")

    print("🚀 작업을 시작합니다...")
    
    # 2. 명령어 실행 및 결과 출력
    os.system("git add .")
    
    # 변경사항이 없을 때를 대비해 commit 결과 확인
    status = os.system(f'git commit -m "Auto Update: {datetime.now()}"')
    
    if status == 0: # 성공적으로 커밋됨
        os.system("git push origin main")
        print("✅ GitHub에 성공적으로 올렸습니다!")
    else:
        print("ℹ️ 변경된 내용이 없어서 올리지 않았습니다.")

if __name__ == "__main__":
    git_push()