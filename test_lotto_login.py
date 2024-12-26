import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

def get_balance(driver, wait):
    """현재 예치금 잔액을 확인하는 함수"""
    try:
        # 마이페이지로 이동
        driver.get('https://dhlottery.co.kr/userSsl.do?method=myPage')
        time.sleep(2)
        
        # 예치금 잔액 확인 (새로운 선택자 사용)
        balance_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.total_new strong")))
        amount = balance_element.text.strip()
        return f"{amount}원"
    except Exception as e:
        print(f"잔액 확인 실패: {str(e)}")
        return "잔액 확인 실패"

def test_login():
    # Chrome 옵션 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # WebDriver 초기화
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # 자동화 감지 우회를 위한 JavaScript 실행
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 동행복권 로그인 페이지로 이동
        driver.get('https://dhlottery.co.kr/user.do?method=login')
        time.sleep(3)
        
        # 로그인 폼이 있는지 확인
        print("페이지 제목:", driver.title)
        print("현재 URL:", driver.current_url)
        
        # 로그인 입력
        id_input = wait.until(EC.presence_of_element_located((By.NAME, "userId")))
        pw_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        
        id_input.clear()
        time.sleep(1)
        id_input.send_keys(os.getenv('LOTTO_ID'))
        time.sleep(1)
        
        pw_input.clear()
        time.sleep(1)
        pw_input.send_keys(os.getenv('LOTTO_PW'))
        time.sleep(1)
        
        # 로그인 버튼 클릭 시도
        try:
            # 클래스로 로그인 버튼 찾기
            login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_common.lrg.blu")))
            print("로그인 버튼 찾음")
            
            # 직접 JavaScript 함수 호출
            driver.execute_script("check_if_Valid3();")
            print("로그인 함수 호출")
            
            time.sleep(5)  # 로그인 처리 대기
            
            # 로그인 성공 여부 확인
            current_url = driver.current_url
            print("로그인 후 URL:", current_url)
            
            # 메인 페이지 URL로 로그인 성공 여부 확인
            if "common.do?method=main" in current_url:
                print("로그인 성공!")
                # 잠시 대기 후 잔액 확인
                time.sleep(2)
                balance = get_balance(driver, wait)
                print(f"현재 예치금 잔액: {balance}")
            else:
                print("로그인 실패 - 현재 URL:", current_url)
                driver.save_screenshot("login_failed.png")
        
        except Exception as e:
            print(f"로그인 버튼 클릭 중 오류: {str(e)}")
            driver.save_screenshot("click_error.png")
        
    except Exception as e:
        print(f"테스트 실패: {str(e)}")
        driver.save_screenshot("error_screenshot.png")
    
    finally:
        time.sleep(3)  # 결과 확인을 위한 대기
        driver.quit()

if __name__ == "__main__":
    test_login() 