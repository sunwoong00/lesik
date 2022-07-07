import time

import urllib3
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver

from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def parse(token):
    recipe_name = token.find('h2', attrs={'class': 'RecipeDetailstyle__Title-q7sykd-4 kIVrZW'})
    if recipe_name is None:
        return None
    ingredient_group = token.find('ul', attrs={'class': 'igroups'})
    if ingredient_group is None:
        return None

    recipe_serving = None

    ingredient_list = []
    for ingredient_node in ingredient_group.children:
        sub_ingredient_list = []
        ingredient_meta = ingredient_node.find('div', attrs={'class': 'igroups_title'})
        if ingredient_meta.span is not None and ingredient_meta.span.text != '':
            recipe_serving = ingredient_meta.span.text
        sub_ingredient_list.append("[" + ingredient_meta.p.text + "]")
        for ingredient in ingredient_node.find_all('div', attrs={'class': 'Text__Description02-sc-1qy6bx2-0 fCbbYE'}):
            ingredient_info = ingredient.find_all('div')
            sub_ingredient_list.append(ingredient_info[0].text + " " + ingredient_info[1].text)
        ingredient_list.append(sub_ingredient_list)

    f = open("recipe/" + recipe_name.text + ".txt", "w")
    if recipe_serving is not None:
        f.write(recipe_name.text + "(" + recipe_serving + ")" + "\n")
    else:
        f.write(recipe_name.text + "\n")
    for ingredient in ingredient_list:
        f.write("\n".join(ingredient))
        f.write("\n")

    f.write("[조리방법]\n")

    step_list = token.find_all('p', attrs={'class': 'Text__Pre01-sc-1qy6bx2-2 enJPxd'})
    for i in range(1, len(step_list) + 1):
        f.write(str(i) + ". " + step_list[i-1].text + '\n')


def scroll():
    recipe_url = 'https://wtable.co.kr/recipes'

    driver = webdriver.Safari()
    driver.get(url=recipe_url)
    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'RecipeListstyle__Categories-sc-1s9b4ly-16')))
        recipe_type_list = element.find_elements(By.CLASS_NAME, 'RecipeListstyle__Category-sc-1s9b4ly-17')
        for recipe_type in recipe_type_list:
            if recipe_type.text == '한식':
                recipe_type.click()

        last_height = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                time.sleep(1)
                break
            last_height = new_height

        recipe_list = driver.find_element(By.CLASS_NAME, 'RecipeListstyle__RecipeList-sc-1s9b4ly-20')
        recipe_url_list = []
        for recipe in recipe_list.find_elements(By.TAG_NAME, 'a'):
            recipe_url_list.append(recipe.get_attribute('href'))

    finally:
        driver.quit()

    return recipe_url_list


def request(url):
    http = urllib3.PoolManager()
    response = http.request(
        "POST",
        url,
        headers={"Content-Type": "x-www-form-urlencoded; charset=UTF-8"}
    )

    bs = BeautifulSoup(response.data, 'html.parser')
    token = bs.find('div', attrs={'class': 'token__Component-sc-1o2h3sm-0 jjTxDH'})
    parse(token)


def main():
    recipe_url_list = scroll()
    for recipe_url in recipe_url_list:
        request(recipe_url)


if __name__ == "__main__":
    main()
