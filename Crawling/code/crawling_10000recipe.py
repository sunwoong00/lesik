import time
import urllib3
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os

def parse(token, folder_name):  #데이터를 추출하는 함수

    isExist = os.path.exists(folder_name) 
    if not isExist: #디렉토리가 존재하지 않으면 생성
        os.makedirs(folder_name)

    recipe_div = token.find('div', attrs={'class': 'view2_summary st3'})
    recipe_name = recipe_div.find('h3')
    
    if recipe_name is None:
        return None
    
    if '?' in recipe_name.text:
        f = open(folder_name + "/" + (recipe_name.text).replace('?','.') + ".txt", "w", encoding='utf-8')
    elif '/' in recipe_name.text:
        f = open(folder_name + "/" + (recipe_name.text).replace('/',',') + ".txt", "w", encoding='utf-8')
    else:
        f = open(folder_name + "/"  + recipe_name.text + ".txt", "w", encoding='utf-8')
    
    step_ind = token.find_all('div', attrs={'class':'view_step_cont'})
    step_list = token.find_all('div', attrs={'class': 'media-body'})

    for i in range(1, len(step_ind) + 1):
        f.write(str(i) + ". " + step_list[i-1].text + '\n')


def scroll(recipe_url):  #데이터 스크롤링 함수
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(options=options)
    driver.get(url=recipe_url)
    try:
        cnt=0  #페이지가 많아서 오류가 발생할 경우, 작성자 프로필 링크의 총 페이지 수 입력 (아래 for loop 주석 처리)
        page=1
        page_ul = driver.find_element(By.CSS_SELECTOR, '#contents_area > div.brand_cont.mag_t_10 > nav > ul')
        recipe_page = []
        recipe_url_list = []

        for p_u in page_ul.find_elements(By.TAG_NAME, 'li'): #페이지가 많아서 cnt를 직접 입력할 경우, 현재 for loop 주석 처리
            for rr in p_u.find_elements(By.TAG_NAME,'a'):
                recipe_page.append(rr.get_attribute('href'))
                cnt+=1

        while True:
            recipe_list = driver.find_element(By.CSS_SELECTOR, '#contents_area > div.brand_cont.mag_t_10 > ul')
            for recipe in recipe_list.find_elements(By.TAG_NAME, 'li'):
                for rr in recipe.find_elements(By.TAG_NAME,'a'):
                    recipe_url_list.append(rr.get_attribute('href'))
                    
            if cnt >= page:
                rec_url = (recipe_url+'&page={}').format(page)
                driver.get(url=rec_url)
                page+=1
            else:
                break
    finally:
        driver.quit()

    return recipe_url_list


def request(url, folder_name):
    http = urllib3.PoolManager()
    response = http.request(
        "POST",
        url,
        headers={"Content-Type": "x-www-form-urlencoded; charset=UTF-8"}
    )
    bs = BeautifulSoup(response.data, 'html.parser')
    token = bs.find('div', attrs={'id': 'contents_area'})
    parse(token, folder_name)


def main():
    recipe_url = input("크롤링을 진행할 쉐프/의 프로필 링크를 입력해주세요: ")
    folder_name = input("폴더명을 입력해주세요: ")
    recipe_url_list = scroll(recipe_url)

    for recipe_url in recipe_url_list:
        request(recipe_url, folder_name)


if __name__ == "__main__":
    main()
