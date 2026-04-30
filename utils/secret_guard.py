import re
import os

"""
=============================================================================
보안 유틸리티 (Secret Guard)
=============================================================================
기능:
  1. 텍스트 내의 민감한 패턴(텔레그램 토큰, API 키, 비밀번호 등)을 감지
  2. 감지된 정보를 ********로 마스킹 처리
  3. 환경 변수 로드 시 보안 경고 제공
=============================================================================
"""

# 민감한 정보를 찾기 위한 정규식 패턴들
SECRET_PATTERNS = {
    "Telegram Token": r"\d{8,10}:[a-zA-Z0-9_-]{35}",           # 텔레그램 봇 토큰
    "Email/User": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", # 이메일 주소
    "Generic Key": r"(key|token|password|secret|auth|pwd)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{16,})['\"]?", # 일반적인 키/비번
}

def mask_text(text: str) -> str:
    """
    텍스트 내의 민감한 정보를 찾아 마스킹 처리한다.
    예: 12345678:ABCDEFG... -> 12345678:********
    """
    if not text:
        return text
    
    masked_text = text
    
    # 1. 텔레그램 토큰 마스킹 (숫자 부분은 남기고 키 부분만 가림)
    def telegram_replacer(match):
        token = match.group(0)
        prefix = token.split(':')[0]
        return f"{prefix}:***********************************"
    
    masked_text = re.sub(SECRET_PATTERNS["Telegram Token"], telegram_replacer, masked_text)
    
    # 2. 기타 일반적인 키/비번 마스킹
    for name, pattern in SECRET_PATTERNS.items():
        if name == "Telegram Token": continue
        
        def general_replacer(match):
            # 매칭된 전체 텍스트 중 실제 값 부분만 가림
            full_match = match.group(0)
            if len(match.groups()) >= 2:
                val = match.group(2)
                return full_match.replace(val, "*" * 8)
            return "*" * 8
            
        masked_text = re.sub(pattern, general_replacer, masked_text, flags=re.IGNORECASE)
        
    return masked_text

def safe_print(message: str):
    """민감한 정보를 마스킹한 후 출력한다."""
    print(mask_text(str(message)))

def check_env_files(directory: str):
    """디렉토리 내에 .env 파일이 있는지 확인하고 보안 경고를 출력한다."""
    found_files = []
    for root, dirs, files in os.walk(directory):
        if ".env" in files:
            found_files.append(os.path.join(root, ".env"))
            
    if found_files:
        print("\n" + "!" * 50)
        print("⚠️ 보안 경고: 다음 위치에 .env 파일이 존재합니다.")
        for f in found_files:
            print(f"  - {f}")
        print("이 파일들은 절대 GitHub 등에 업로드되지 않도록 .gitignore를 확인하세요!")
        print("!" * 50 + "\n")

if __name__ == "__main__":
    # 테스트 코드
    test_str = "내 텔레그램 토큰은 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789 이고, 비번은 password=my_secret_123 입니다."
    print("원본:", test_str)
    print("마스킹:", mask_text(test_str))
