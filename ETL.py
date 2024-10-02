import pandas as pd
import os, requests, urllib.parse, time, datetime, zipfile
from bs4 import BeautifulSoup

# 셀레니움
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ChromeDriverManager를 사용하여 크롬 드라이버 자동 설정
service = Service(ChromeDriverManager().install())

# 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--start-maximized")


KEY = 8228483054

os.system('cls')


# API 호출 후 json형태로 받기
def get_data(url='', params={}):
    page_no = 1
    all_df = pd.DataFrame()

    #page넘버 순차적으로 증가하면서 데이터 저장
    while True:
        params['numOfRows'] = 99
        params['pageNo'] = page_no
        param_str = urllib.parse.urlencode(params)
        full_url = f'{url}?key={KEY}&type=json&{param_str}'
        response = requests.get(full_url).json()['intercityLeadTimeLists']
        response_df = pd.DataFrame(response)
        response_df['page_no'] = page_no

        if len(response_df) == 0:
            break  # 더 이상 데이터가 없으면 종료

        all_df = pd.concat([all_df,response_df])

    return all_df


# traffic_time = get_data(url = 'https://data.ex.co.kr/openapi/specialAnal/intercityLeadTime', params={'iYear':'2018'})
# traffic_time.to_csv('test.csv',index=False,encoding='utf-8-sig')



# 영업소간 통행시간 크롤링
def get_csv(min_year = 2015, max_year = int(datetime.datetime.today().year)):
    # 드라이버 초기화
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get('https://data.ex.co.kr/portal/fdwn/view?type=TCS&num=11&requestfrom=dataset')
    time.sleep(5)
    btn = driver.find_element(By.CSS_SELECTOR, 'input[title="1개월"]').click()
    time.sleep(3)

    #버튼 및 박스 선택
    combo_year = driver.find_element(By.CSS_SELECTOR, 'select[title="년도 선택"]')
    combo_month = driver.find_element(By.CSS_SELECTOR, 'select[title="월 선택"]')
    select_btn = driver.find_element(By.CSS_SELECTOR, 'span[class="searchBtn"]')
    down_btn = driver.find_element(By.CSS_SELECTOR, 'span[class="btn_base"]')
    
    #데이터 다운 시작
    for year in range(min_year,max_year+1):
        for month in range(1,13):
        
            #현재 월 은 데이터가 없기 때문에 break
            if year == datetime.datetime.today().year and month == datetime.datetime.today().month:
                #마지막 다운로드 대기
                time.sleep(20)
                break

            Select(combo_year).select_by_visible_text(str(year).zfill(2))
            time.sleep(1)
            Select(combo_month).select_by_visible_text(str(month).zfill(2))
            time.sleep(1)
            select_btn.click()
            time.sleep(3)
            down_btn.click()
            time.sleep(10)

    driver.quit()


# get_csv(min_year=2015,max_year=2024)
