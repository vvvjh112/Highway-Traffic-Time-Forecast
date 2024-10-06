import pandas as pd
import os, requests, urllib.parse, time, datetime, zipfile, chardet
from bs4 import BeautifulSoup
from tqdm import tqdm

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

os.system('clear')


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
def get_csv(url='',min_year = 2015, max_year = int(datetime.datetime.today().year)):
    # 드라이버 초기화
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # driver.get('https://data.ex.co.kr/portal/fdwn/view?type=TCS&num=11&requestfrom=dataset')
    driver.get(url)
    time.sleep(5)
    btn = driver.find_element(By.CSS_SELECTOR, 'input[title="1개월"]').click()
    print(f'1개월 단위 버튼 선택 완료')
    time.sleep(3)

    #버튼 및 박스 선택
    combo_year = driver.find_element(By.CSS_SELECTOR, 'select[title="년도 선택"]')
    print(f'연도 박스 탐색 완료')
    combo_month = driver.find_element(By.CSS_SELECTOR, 'select[title="월 선택"]')
    print(f'월 선택 박스 탐색 완료')
    select_btn = driver.find_element(By.CSS_SELECTOR, 'span[class="searchBtn"]')
    print(f'조회 버튼 탐색 완료')
    down_btn = driver.find_element(By.CSS_SELECTOR, 'span[class="btn_base"]')
    print(f'다운 탐색 완료')
    
    #데이터 다운 시작
    for year in range(min_year,max_year+1):
        for month in range(1,13):
            print(f'{year}년 {month}월 다운 중...')

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

    
    print(f'크롤링 완료')
    driver.quit()

    return

def detect_encoding(file_path):
    # 파일의 인코딩을 감지
    with open(file_path, 'rb') as file:
        result = chardet.detect(file.read(100000))  # 파일의 일부분만 읽어서 인코딩 감지
    return result['encoding']

def Traffic_Time(folder_path, code_file):
    # 'TCS_영업소간통행시간'이 포함된 모든 CSV 파일을 불러오기
    file_list = os.listdir(folder_path)

    # '수도권 영업소 코드' 파일 인코딩 감지 및 불러오기
    code_file_path = os.path.join(code_file)
    code_file_encoding = detect_encoding(code_file_path)
    data1 = pd.read_csv(code_file_path, low_memory=False, encoding=code_file_encoding)
    key = data1['영업소코드'].unique()

    # 빈 데이터프레임 생성
    final_data = pd.DataFrame()

    # 각 파일에 대해 필터 적용 및 병합
    for file in tqdm(file_list):
        file_path = os.path.join(folder_path, file)
        file_encoding = detect_encoding(file_path)
        
        if 'csv' not in file:
            continue

        # 파일 읽기
        data = pd.read_csv(file_path, low_memory=False, encoding=file_encoding)

        # 필터링 로직 적용
        data = data[(data['TCS차종구분코드'] == 1) & (data['통행시간'] != -1)]
        data = data[data['출발영업소코드'].isin(key)]
        data = data[data['도착영업소코드'].isin(key)]
        
        # 최종 데이터프레임에 병합
        final_data = pd.concat([final_data, data], ignore_index=True)

    return final_data

def Traffic_Volume(folder_path, code_file):
    # 'TCS_영업소간통행시간'이 포함된 모든 CSV 파일을 불러오기
    file_list = os.listdir(folder_path)

    # '수도권 영업소 코드' 파일 인코딩 감지 및 불러오기
    code_file_path = os.path.join(code_file)
    code_file_encoding = detect_encoding(code_file_path)
    data1 = pd.read_csv(code_file_path, low_memory=False, encoding=code_file_encoding)
    key = data1['영업소코드'].unique()

    # 빈 데이터프레임 생성
    final_data = pd.DataFrame()

    # 각 파일에 대해 필터 적용 및 병합
    for file in tqdm(file_list):
        file_path = os.path.join(folder_path, file)
        file_encoding = detect_encoding(file_path)
        
        if 'csv' not in file:
            continue

        # 파일 읽기
        data = pd.read_csv(file_path, low_memory=False, encoding=file_encoding)[['집계일자', '집계시', '영업소코드', '입출구구분코드', '총교통량']]

        # 필터링 로직 적용
        data = data[data['영업소코드'].isin(key)]
        
        # 최종 데이터프레임에 병합
        final_data = pd.concat([final_data, data], ignore_index=True)

    return final_data

# 도로 통행시간 크롤링
# get_csv(url = 'https://data.ex.co.kr/portal/fdwn/view?type=TCS&num=11&requestfrom=dataset', min_year=2023, max_year=2023)

# 교통량 크롤링
# get_csv(url = 'https://data.ex.co.kr/portal/fdwn/view?type=TCS&num=34&requestfrom=dataset', min_year=2023, max_year=2023)

# 통행시간 데이터셋_ 2023
# Time_Data = Traffic_Time('Raw_data/TrafficTime','Raw_data/gyeonggi_code.csv')
# Time_Data.to_csv('timedata_test.csv',index=False,encoding='utf-8-sig')

#교통량 데이터셋_2023
Volume_Data = Traffic_Volume('Raw_data/TrafficVolume','Raw_data/gyeonggi_code.csv')
Volume_Data.to_csv('volumedata_test.csv',index=False,encoding='utf-8-sig')

#연휴 유무 알고리즘
