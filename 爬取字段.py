# -*- encoding: utf-8 -*-


import requests
from urllib.request import urlopen
from tianyancha import Tianyancha
from selenium import webdriver


class company:
    company_name=""
    news_num=0
    def __init__(self,company_name):
        self.company_name=company_name

def login_tianyan_by_session(url):
    file=urlopen(url)
    #print(file.info())
    session=requests.session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}
    data={"mobile":"18923717666","password":"1w2x3y4z"}
    response=session.post(url=url,headers=headers,data=data)
    return response

def login_tianyan_by_webdriver(url):
    driver=webdriver.Chrome() #要装对应浏览器的驱动
    driver.get(url)
    driver.find_element_by_class_name("modulein modulein1 mobile_box  f-base collapse").find_element_by_tag_name("input")
    print(driver)

def get_data_from_tianyancha(filename,account,password):

    table_dict = Tianyancha(username=account, password=password).tianyancha_scraper_batch(input_template=filename,
                                                                                                export='xlsx')

if __name__=="__main__":

    print("请输入要查询的企业列表所在的表格：")
    #filename="input.xlsx"
    filename = str(input())
    print("请输入天眼查用户名：")
    account=str(input())
    print("请输入密码：")
    password=str(input())

    get_data_from_tianyancha(filename,account,password)