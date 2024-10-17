import pandas as pd
import os, requests, urllib.parse, time, zipfile, chardet, calendar
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime, timedelta


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
service_key = 'JWgg0HGk6X1/iSamZNl29O5awvu46mP+wM/j8WNoLfNNfMeo2zhjPECwNdheapXHpIKbEZ0GCg1sWUm+rTdBfg=='

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

def get_weather_data(api_url, api_key):

    # 데이터프레임을 저장할 리스트 생성
    data = []
    
    #최종데이터프레임
    final_df = pd.DataFrame()

    # 시작일과 종료일 설정
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)

    # 날짜를 반복
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y%m%d')
        _, day = calendar.monthrange(current_date.year, current_date.month)

        for hour in tqdm(range(0, 24), desc=f"Processing {date_str}", leave=False):
            params = {
                'type': 'json',
                'sdate': date_str,
                'stdHour': str(hour).zfill(2),
                'key': api_key
            }
            
            try:
                # API 호출
                response = requests.get(api_url, params=params)
                response.raise_for_status()  # 요청 실패 시 예외 발생
                
                # JSON 응답 파싱
                json_data = response.json()['list']
                df = pd.DataFrame(json_data)
                
                final_df = pd.concat([final_df,df])

            except requests.exceptions.HTTPError as e:
                print(f"HTTP error: {e} - Date: {date_str} Time: {hour}")
                current_date-=timedelta(days=1)
                
            except requests.exceptions.RequestException as e:
                print(f"Error: {e} - Date: {date_str} Time: {hour}")
                current_date-=timedelta(days=1)

        #1일마다 세이브
        if date_str[6:] == str(day).zfill(2):
            final_df.to_csv(f'{current_date.year}_{current_date.month}_weather.csv',index=False,encoding='utf-8-sig')

        # 다음 날짜로 이동
        current_date += timedelta(days=1)


    final_df.to_csv('오류방지2023.csv', index=False, encoding='utf-8-sig')
    final_df = final_df[['sdate','stdHour','unitName','addr','addrCode','addrName','weatherContents','correctNo','tempValue','rainfallValue','snowValue','windValue']]
    final_df = final_df.rename(columns={
                    'sdate' : '날짜',
                    'stdHour' : '시간대',
                    'unitName' : '휴게소명',
                    'addr' : '주소',
                    'addrCode' : '기상실황지역코드',
                    'addrName' : '기상실황지역명',
                    'weatherContents' : '현재일기내용',
                    'correctNo' : '시정값',
                    'tempValue' : '현재기온값',
                    'rainfallValue' : '강수량',
                    'snowValue' : '적설량',
                    'windValue' : '풍속'
                })
    
    # 필요에 따라 CSV로 저장
    final_df.to_csv('weather_data_2023_ALL.csv', index=False, encoding='utf-8-sig')

    filtered_df = final_df[final_df['주소'].str.contains('경기도|서울', na=False)]

    filtered_df.to_csv('weather_data_2023_경기_서울.csv', index=False, encoding='utf-8-sig')

    return final_df, filtered_df



# 영업소간 통행시간 크롤링
def get_csv(url='',min_year = 2015, max_year = int(datetime.today().year)):
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
            if year == datetime.today().year and month == datetime.today().month:
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


def get_csv2(url, year, month):
    chrome_options.add_argument("--headless")  # Headless 모드

     # 드라이버 초기화
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)
    time.sleep(5)

    #버튼 및 박스 선택
    date_picker = driver.find_element(By.CSS_SELECTOR, 'input[name="dataSupplyDate"]')
    print(f'날짜 박스 탐색 완료')
    select_btn = driver.find_element(By.CSS_SELECTOR, 'span[class="searchBtn"]')
    print(f'조회 버튼 탐색 완료')
    down_btn = driver.find_element(By.CSS_SELECTOR, 'span[class="btn_base"]')
    print(f'다운 탐색 완료')
    
    #데이터 다운 시작
    print(f'{year}년 {month}월 다운 중...')
    _, day = calendar.monthrange(year, month)

    for i in tqdm(range(1,day+1)):
        driver.execute_script(f"arguments[0].value = '{year}.{str(month).zfill(2)}.{str(i).zfill(2)}';", date_picker)
        time.sleep(1)
        select_btn.click()
        time.sleep(3)
        down_btn.click()
        time.sleep(2)

    time.sleep(10)

    
    print(f'크롤링 완료')
    driver.quit()

    return


# 날짜 형식을 통일하는 메서드 정의
def unify_date_format(date_str):
    try:
        # pd.to_datetime으로 날짜 변환 (자동으로 여러 형식 인식)
        date_obj = pd.to_datetime(date_str, errors='coerce')
        # 변환된 날짜를 'YYYY-MM-DD' 형식으로 반환
        return date_obj.strftime('%Y-%m-%d')
    except Exception:
        # 변환에 실패하면 원본 값을 반환
        return date_str

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

    final_data = pd.merge(final_data,data1,left_on = '출발영업소코드',right_on='영업소코드',how='left')
    final_data = final_data.rename(columns={'영업소명':'출발영업소명'})
    final_data = pd.merge(final_data,data1,left_on = '도착영업소코드',right_on='영업소코드',how='left')   
    final_data = final_data.rename(columns={'영업소명':'도착영업소명'})

    final_data['집계일자'] = final_data['집계일자'].apply(unify_date_format)
    return final_data.drop(['영업소코드_x','영업소코드_y'], axis=1)

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
    final_data['집계일자'] = final_data['집계일자'].apply(unify_date_format)
    return final_data


def Between_Volume_Days(folder_path, code_file):
    # 'TCS_영업소간통행시간'이 포함된 모든 CSV 파일을 불러오기
    file_list = os.listdir(folder_path)

    # '수도권 영업소 코드' 파일 인코딩 감지 및 불러오기
    code_file_path = os.path.join(code_file)
    code_file_encoding = detect_encoding(code_file_path)
    data1 = pd.read_csv(code_file_path, low_memory=False, encoding=code_file_encoding)
    key = data1['영업소명'].unique()

    # 빈 데이터프레임 생성
    final_data = pd.DataFrame()

    # 각 파일에 대해 필터 적용 및 병합
    for file in tqdm(file_list):
        file_path = os.path.join(folder_path, file)
        file_encoding = detect_encoding(file_path)
        
        if 'csv' not in file:
            continue

        # 파일 읽기
        data = pd.read_csv(file_path, low_memory=False, encoding=file_encoding)[['집계일자', '출발영업소코드', '도착영업소코드', '출발영업소명', '도착영업소명', '도착지방향총교통량']]


        # 필터링 로직 적용
        data = data[data['출발영업소코드'].isin(key)]
        data = data[data['도착영업소코드'].isin(key)]
        
        # 최종 데이터프레임에 병합
        final_data = pd.concat([final_data, data], ignore_index=True)
    final_data['집계일자'] = final_data['집계일자'].apply(unify_date_format)
    return final_data

def Between_Volume_Hours(folder_path, code_file):
    file_list = os.listdir(folder_path)

    # '수도권 영업소 코드' 파일 인코딩 감지 및 불러오기
    code_file_path = os.path.join(code_file)
    code_file_encoding = detect_encoding(code_file_path)
    data1 = pd.read_csv(code_file_path, low_memory=False, encoding=code_file_encoding)
    key = data1['영업소명'].unique()

    # 빈 데이터프레임 생성
    final_data = pd.DataFrame()

    # 각 파일에 대해 필터 적용 및 병합
    for file in tqdm(file_list):
        file_path = os.path.join(folder_path, file)
        file_encoding = detect_encoding(file_path)
        
        if 'csv' not in file:
            continue

        # 파일 읽기
        data = pd.read_csv(file_path, low_memory=False, encoding=file_encoding)[['집계일자', '집계시', '요일명', '영업소', '교통량']]
        data['교통량'] = data['교통량'].astype(int)
        data = data.groupby(['집계일자', '집계시', '영업소', '요일명'], as_index=False)['교통량'].sum()
        data['영업소'] = data['영업소'].str.split('->')
        data['출발영업소명'] = data['영업소'].str[0]
        data['도착영업소명'] = data['영업소'].str[1]
        data = data.drop('영업소',axis=1)

        # 필터링 로직 적용
        data = data[data['출발영업소명'].isin(key)]
        data = data[data['도착영업소명'].isin(key)]
        # os.remove(f'{folder_path}/{file}')

        # 최종 데이터프레임에 병합
        final_data = pd.concat([final_data, data], ignore_index=True)
    
    final_data['집계일자'] = final_data['집계일자'].apply(unify_date_format)
    return final_data


# 샌드위치 휴일을 찾는 함수
def mark_sandwich_holidays(df):
    for i in range(1, len(df) - 1):
        # 공휴일-비공휴일-공휴일
        if df['휴일 여부'].iloc[i - 1] == '공휴일' and df['휴일 여부'].iloc[i + 1] == '공휴일' and df['휴일 여부'].iloc[i] == '비공휴일':
            df.at[i, '휴일 여부'] = '샌드위치'
        
        # 공휴일-비공휴일-주말 또는 주말-비공휴일-공휴일
        if (df['휴일 여부'].iloc[i - 1] == '공휴일' and df['휴일 여부'].iloc[i + 1] == '주말') or \
           (df['휴일 여부'].iloc[i - 1] == '주말' and df['휴일 여부'].iloc[i + 1] == '공휴일'):
            if df['휴일 여부'].iloc[i] == '비공휴일':
                df.at[i, '휴일 여부'] = '샌드위치'
        
        # 비공휴일-주말-주말-공휴일 또는 공휴일-주말-주말-비공휴일
        # 여기서 len(df)보다 크지 않은지 확인하여 인덱스 초과 방지
        if i + 3 < len(df):
            if (df['휴일 여부'].iloc[i] == '비공휴일' and df['휴일 여부'].iloc[i + 1] == '주말' and df['휴일 여부'].iloc[i + 2] == '주말' and df['휴일 여부'].iloc[i + 3] == '공휴일') or \
               (df['휴일 여부'].iloc[i] == '공휴일' and df['휴일 여부'].iloc[i + 1] == '주말' and df['휴일 여부'].iloc[i + 2] == '주말' and df['휴일 여부'].iloc[i + 3] == '비공휴일'):
                df.at[i + 3, '휴일 여부'] = '샌드위치'
                df.at[i, '휴일 여부'] = '샌드위치'
    
    return df


def get_holiday_data(service_key, year):
    """
    1월부터 12월까지 모든 월의 공휴일 데이터를 누적하여 반환하는 함수.
    
    Parameters:
    - service_key: 공공데이터포털에서 발급받은 API 서비스 키
    - year: 조회할 연도 (예: 2024)
    
    Returns:
    - holidays_df: 공휴일 정보가 담긴 pandas 데이터프레임 (1월 ~ 12월 누적)
    """
    url = "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo"

    # 빈 데이터프레임 생성 (누적 저장할 목적)
    total_holidays_df = pd.DataFrame()
    
    with requests.Session() as session:
        for month in range(1, 13):
            params = {
                'ServiceKey': service_key,
                'solYear': year,
                'solMonth': str(month).zfill(2),
                'numOfRows': 100,
                '_type': 'xml'
            }

            try:
                response = session.get(url, params=params)
                response.raise_for_status()  # HTTPError 발생 시 예외 발생
                root = ET.fromstring(response.content)

                holidays = []
                for item in root.findall(".//item"):
                    date_name = item.find('dateName').text
                    locdate = item.find('locdate').text

                    holidays.append({
                        'name': date_name,
                        'date': locdate
                    })

                holidays_df = pd.DataFrame(holidays)
                total_holidays_df = pd.concat([total_holidays_df, holidays_df], ignore_index=True)

            except requests.exceptions.RequestException as e:
                print(f"API 요청 중 오류 발생: {e}")
                continue

    return total_holidays_df

#달력 데이터프레임 생성
def generate_date_range(year):
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    date_list = []

    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)

    return date_list

# API를 호출하여 공휴일 및 주말여부 확인 데이터생성
def get_holiday_status(year, service_key):
    holidays_df = get_holiday_data(service_key, year)
    all_dates = generate_date_range(year)
    
    result = []
    for date in all_dates:
        is_holiday = holidays_df['date'].astype(str).str.contains(date.strftime('%Y%m%d')).any()
        is_weekend = date.weekday() >= 5  # 주말(토요일(5) 또는 일요일(6))인지 확인

        # 휴일 여부 결정
        if is_holiday:
            holiday_status = "공휴일"
        elif is_weekend:
            holiday_status = "주말"
        else:
            holiday_status = "비공휴일"

        result.append({
            '집계일자': date.strftime('%Y-%m-%d'),
            '휴일 여부': holiday_status
        })

    result_df = mark_sandwich_holidays(pd.DataFrame(result))
    result_df.to_csv(f'{year}_years_calendar.csv',index=False,encoding='utf-8-sig')
    return result_df



# 도로 통행시간 크롤링
# get_csv(url = 'https://data.ex.co.kr/portal/fdwn/view?type=TCS&num=11&requestfrom=dataset', min_year=2023, max_year=2023)

# 교통량 크롤링
# get_csv(url = 'https://data.ex.co.kr/portal/fdwn/view?type=TCS&num=34&requestfrom=dataset', min_year=2023, max_year=2023)

# 수도권 교통량 크롤링
# get_csv(url = 'https://data.ex.co.kr/portal/fdwn/view?type=TCS&num=33&requestfrom=dataset#', min_year=2023, max_year=2023)

# 영업소간 교통량 크롤링(일단위)
# get_csv(url = 'https://data.ex.co.kr/portal/fdwn/view?type=TCS&num=35&requestfrom=dataset', min_year=2023, max_year=2023)

# 영업소간 교통량 크롤링(시간단위) - 일 단위로 다운받아야 함
# for i in tqdm(range(1,13)):
#     get_csv2(url = 'https://data.ex.co.kr/portal/fdwn/view?type=TCS&num=64&requestfrom=dataset', year=2023, month=i)


# 통행시간 데이터셋_ 2023
# Time_Data = Traffic_Time('Raw_data/TrafficTime','Raw_data/gyeonggi_code.csv')
# Time_Data.to_csv('timedata_test.csv',index=False,encoding='utf-8-sig')

#교통량 데이터셋_2023
# Volume_Data = Traffic_Volume('Raw_data/TrafficVolume','Raw_data/gyeonggi_code.csv')
# Volume_Data.to_csv('volumedata_test.csv',index=False,encoding='utf-8-sig')

#영업소간 교통량 데이터셋(일별)_2023
# Between_Data_Day = Between_Volume_Days('Raw_data/BetweenVolume(일별)','Raw_data/gyeonggi_code.csv')
# Between_Data_Day.to_csv('03.영업소간통행량(일별).csv',index=False,encoding='utf-8-sig')

#영업소간 교통량 데이터셋(시간)_2023
# Between_Data_Hours = Between_Volume_Hours('Raw_data/BetweenVolume(시간)','Raw_data/gyeonggi_code.csv')
# Between_Data_Hours.to_csv('04.영업소간통행량(시간).csv',index=False,encoding='utf-8-sig')

#연휴 유무 알고리즘
# 주말과 공휴일 데이터프레임 생성
# result_df = get_holiday_status(2023, service_key)

# 1차데이터셋 생성 코드
def mk_FirstData():
    df01 = pd.read_csv('dataset/01.영업소간통행시간.csv',low_memory=False).drop('Unnamed: 6',axis = 1)
    df04 = pd.read_csv('dataset/04.영업소간통행량(시간).csv',low_memory=False)
    calendar2023 = pd.read_csv('dataset/2023_years_calendar.csv',low_memory=False)

    data = pd.merge(df01,df04,on=['집계일자','집계시','출발영업소명','도착영업소명'],how='left')
    data = pd.merge(data,calendar2023,on='집계일자')
    
    return data

# First_data = mk_FirstData()
# First_data.to_csv('dataset/1차데이터셋.csv',index=False,encoding='utf-8-sig')




# 날씨 테스트
# data = pd.read_csv('Raw_data/ETC_O3_03_04_523880.csv',low_memory=False, encoding= detect_encoding('Raw_data/ETC_O3_03_04_523880.csv'))

# print(data['기상실황지역'].unique())
# # print(data['현재일기내용'].unique())

weather_data_all, weather_data_part = get_weather_data('https://data.ex.co.kr/openapi/restinfo/restWeatherList', KEY)


## 공사데이터 크롤링 + 1차 데이터셋 Join 해서 Row수 및 용량 테스트
## 적합 모델 서칭
## 추가 필요 데이터셋 탐색

# 날씨도 추가 하면 좋을 듯 함.
# https://data.gg.go.kr/portal/data/service/selectServicePage.do?page=1&rows=10&sortColumn=&sortDirection=&infId=458YRRY04VI3BBMI6Q8326869752&infSeq=4&order=&loc=
# https://data.kma.go.kr/data/grnd/selectAwsRltmList.do?pgmNo=56
# 위 코드에서 경기도,서울 AWS코드를 가져옴 -> 도로교통포털에서 날씨정보에서 필터링
# https://apihub.kma.go.kr/apiList.do?seqApi=10&seqApiSub=286&apiMov=4.%20%EB%8F%99%EB%84%A4%EC%98%88%EB%B3%B4(%EC%B4%88%EB%8B%A8%EA%B8%B0%EC%8B%A4%ED%99%A9%C2%B7%EC%B4%88%EB%8B%A8%EA%B8%B0%EC%98%88%EB%B3%B4%C2%B7%EB%8B%A8%EA%B8%B0%EC%98%88%EB%B3%B4)%20%EC%A1%B0%ED%9A%8C
# 좌표값 받아서 날씨 조회 API   (추가 위도경도 데이터 활용해보자) -> 쓰기 어려워보임
# 휴게소 날씨를 이용해야 할듯,,, 아니면 날씨를 입력받거나,,
# 문제 -> 서울데이터가 없음,, 휴게소 고민해봐야할 듯
# 각 지역별로 묶어서 날씨가 제일 빈도 수가 많은 것을 채택

#   
# / 미래 도착시간 예측은 학습 데이터셋을 따로 해야함. 즉, 모델이 2개가 필요 (현재 소요시간예축, 미래 소요시간예측)

## 성능 보고 집계일을 월 단위로 할지,,

# 미래 예측 모델은 현재 통행량, 1시간 전~2시간 전 통행량을 input으로
# 톨게이트간 통행량 API -  https://data.ex.co.kr/openapi/basicinfo/openApiInfoM?apiId=0111&pn=-1