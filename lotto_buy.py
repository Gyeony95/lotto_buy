import os
import time
import schedule
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import sys

load_dotenv()

def send_slack_message(message):
    """슬랙으로 메시지를 전송하는 함수"""
    try:
        client = WebClient(token=os.getenv('SLACK_TOKEN'))
        response = client.chat_postMessage(
            channel=os.getenv('SLACK_CHANNEL'),
            text=message
        )
        return True
    except SlackApiError as e:
        print(f"슬랙 메시지 전송 실패: {e.response['error']}")
        return False

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

def buy_lotto():
    # Chrome 옵션 설정
    # options = webdriver.ChromeOptions()
    # options.add_argument('--start-maximized')
    # options.add_argument('--disable-gpu')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--disable-blink-features=AutomationControlled')
    # options.add_experimental_option('excludeSwitches', ['enable-automation'])
    # options.add_experimental_option('useAutomationExtension', False)
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--window-size=1920,1080')

    # Chrome 실행 경로 명시적 지정
    options.binary_location = "/usr/bin/google-chrome"

    # 디버그 로그 추가
    import logging
    logging.basicConfig(filename='bot.log', level=logging.INFO)
    
    # WebDriver 초기화
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # 자동화 감지 우회를 위한 JavaScript 실행
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 동행복권 로그인 페이지로 이동
        driver.get('https://dhlottery.co.kr/user.do?method=login')
        time.sleep(3)
        
        # 로그인
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
        
        # 로그인 버튼 클릭
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_common.lrg.blu")))
        driver.execute_script("check_if_Valid3();")
        time.sleep(5)  # 로그인 처리 대기
        
        # 구매 전 잔액 확인
        balance_before = get_balance(driver, wait)
        
        # 잔액에서 숫자만 추출하여 정수로 변환
        try:
            balance_amount = int(balance_before.replace('원', '').replace(',', ''))

            # 잔액이 5000원 미만인 경우
            if balance_amount < 5000:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f" 로또 구매 실패 ({current_time})\n"
                message += f"- 현재 잔액: {balance_before}\n"
                message += "- 구매 실패 사유: 잔액 부족\n"
                message += "- 필요 금액: 5,000원"

                # Slack으로 결과 전송
                send_slack_message(message)
                print(message)
                return
                
        except ValueError as e:
            print(f"잔액 변환 실패: {str(e)}")
            return
            
        # 잔액이 충분한 경우 구매 진행
        # 로또 구매 페이지로 이동
        driver.get('https://el.dhlottery.co.kr/game/TotalGame.jsp?LottoId=LO40')
        
        # iframe으로 전환
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'ifrm_tab')))
        
        # 자동 구매 버튼 클릭
        auto_btn = wait.until(EC.element_to_be_clickable((By.ID, 'num2')))
        auto_btn.click()
        
        # 5000원어치 구매 (1000원 * 5장)
        for _ in range(5):
            buy_one_btn = wait.until(EC.element_to_be_clickable((By.ID, 'btnSelectNum')))
            buy_one_btn.click()
            time.sleep(1)
        
        # 구매하기 버튼 클릭
        purchase_btn = wait.until(EC.element_to_be_clickable((By.ID, 'btnBuy')))
        purchase_btn.click()
        
        # 확인 팝업 처리
        alert = driver.switch_to.alert
        alert.accept()
        
        time.sleep(2)
        
        # 구매 후 잔액 확인
        balance_after = get_balance(driver, wait)
        
        # 구매 결과 메시지 생성
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f" 로또 구매 결과 ({current_time})\n"
        message += f"- 구매 전 잔액: {balance_before}\n"
        message += f"- 구매 후 잔액: {balance_after}\n"
        message += "- 구매 금액: 5,000원\n"
        message += " 로또 구매가 완료되었습니다!"
        
        # Slack으로 결과 전송
        send_slack_message(message)
        print(message)
        
    except Exception as e:
        error_message = f" 로또 구매 실패 ({datetime.now()})\n오류 내용: {str(e)}"
        send_slack_message(error_message)
        print(error_message)
    
    finally:
        driver.quit()

def main():
    # 커맨드 라인 인자 확인
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("테스트 모드로 실행합니다...")
        buy_lotto()
    else:
        print("스케줄러 모드로 실행합니다...")
        # 매주 토요일 오전 8:30에 실행
        schedule.every().saturday.at("08:30").do(buy_lotto)
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    main()