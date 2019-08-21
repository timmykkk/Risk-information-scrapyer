#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tianyancha: A scraper of Tianyancha, the best Chinese Business Database."""

__author__ = 'Qiao Zhang'

import json
import codecs
import time
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from collections import OrderedDict
import os
pd.set_option('mode.chained_assignment', None)


def isElementExist(obj, tag):
    flag = True
    #browser = self.driver
    try:
        obj.find_element_by_css_selector(tag)
        return flag

    except:
        flag = False
        return flag

class WriterJson:
    def __init__(self):
        pass

    # 将单个DataFrame保存为JSON，确保中文显示正确
    def df_to_json(self, df, orient:str = 'table'):
        return json.loads(df.to_json(orient, force_ascii=False))

    # 将多个DataFrames组成的字典批量保存为JSON，确保中文显示正确:服务于类似`金融产品信息表`这样的包含多
    def dfs_to_json(self, dic_dfs, orient:str = 'table'):
        pass

    # 将单个OrderedDict保存为JSON List
    def odict_to_json(self, odict):
        items = list(odict.items())
        list_JSONed = []

        # 把列表中的每个df通过list append变成json
        for i in range(len(items)):
            try:
                list_JSONed.append([items[i][0],json.loads(items[i][1].to_json(orient='table', force_ascii=False))])
            except:
                print(items[i][0] + '表为空，请检查。')
        # 记录版本信息
        list_JSONed.append({'version_date': time.strftime("%Y/%m/%d")})

        return list_JSONed

    # 从list_JSONed获取公司名称，用于设置JSON文件名称
    def get_company_name_from_JSON(self, items_JSONed):
        pass

    # 将一个json list或者json dict存入文件
    def write_json(self, json_list, file_name, indent=4, encoding='utf-8'):
        f_out = codecs.open(file_name, 'w', encoding=encoding)
        json_str = json.dumps(json_list, indent=indent, ensure_ascii=False) #, encoding=encoding)
        f_out.write(json_str)
        f_out.close()

class Tianyancha:

    # 常量定义
    url = 'https://www.tianyancha.com/login'

    def __init__(self, username, password, headless=False):
        self.username = username
        self.password = password
        self.headless = headless
        self.driver = self.login(text_login='请输入11位手机号码', text_password='请输入登录密码')

    # 登录天眼查
    def login(self, text_login, text_password):
        time_start = time.time()

        # 操作行为提示
        print ('在自动输入完用户名和密码前，请勿操作鼠标键盘！请保持优雅勿频繁（间隔小于1分钟）登录以减轻服务器负载。')

        # 设置是否为隐藏加载并打开浏览器
        if self.headless:
            option = webdriver.ChromeOptions()
            option.add_argument('headless')
            driver = webdriver.Chrome(chrome_options=option)
        else:
            driver = webdriver.Chrome()

        # 强制声明浏览器长宽为1024*768以适配所有屏幕
        driver.set_window_position(0, 0)
        driver.set_window_size(1024, 768)
        driver.get(self.url)

        # 模拟登陆：Selenium Locating Elements by Xpath
        time.sleep(5)

        # 关闭底栏
        #driver.find_element_by_xpath("//img[@id='tyc_banner_close']").click()
        driver.find_element_by_xpath("//div[@tyc-event-ch='Login.PasswordLogin']").click()
        # 天眼查官方会频繁变化登录框的占位符,所以设置两个新参数来定义占位符
        driver.find_elements_by_xpath("//input[@placeholder='{}']".format(text_login))[-2].send_keys(self.username)
        driver.find_elements_by_xpath("//input[@placeholder='{}']".format(text_password))[-1].send_keys(self.password)

        # 手工登录，完成滑块验证码
        print ('请现在开始操作键盘鼠标，在15s内点击登录并手工完成滑块验证码。批量爬取只需一次登录。')
        time.sleep(10)
        print ('还剩5秒。')
        time.sleep(5)

        time_end = time.time()
        print('您的本次登录共用时{}秒。'.format(int(time_end - time_start)))
        return driver

    # 定义天眼查爬虫
    def tianyancha_scraper(self,
                           keyword,
                           table,
                           use_default_exception=True,
                           change_page_interval=2,
                           export='xlsx',
                           quit_driver=True):
        """
        天眼查爬虫主程序。
        :param keyword: 公司名称，支持模糊或部分检索。比如"北京鸿智慧通实业有限公司"。
        :param table: 需要爬取的表格信息，默认为全部爬取。和官方的元素名称一致。常见的可以是'baseInfo', 'staff', 'invest'等，具体请参考表格名称中英文对照表。
        :param use_default_exception: 是否使用默认的排除列表，以忽略低价值表格为代价来加快爬取速度。
        :param change_page_interval: 爬取多页的时间间隔，默认2秒。避免频率过快IP地址被官方封禁。
        :param export: 输出保存格式，默认为Excel的`xlsx`格式，也支持`json`。
        :return:
        """

        # 公司搜索：顺带的名称检查功能，利用天眼查的模糊搜索能力
        # TODO：将借用模糊搜索的思路写进宣传文章。
        def search_company(driver, url1):
            driver.get(url1)
            time.sleep(1)
            content = driver.page_source.encode('utf-8')
            soup1 = BeautifulSoup(content, 'lxml')
            # TODO：是否要将登录状态监测统一到login函数中
            try:
                # TODO：'中信证券股份有限公司'无法正确检索
                try:
                    url2 = soup1.find('div',class_='header').find('a', class_="name ").attrs['href']
                except:
                    url2 = driver.find_element_by_xpath("//div[@class='content']/div[@class='header']/a[@class='name ']").get_attribute('href')
                print('登录成功。')
            except:
                print('登录过于频繁，请1分钟后再次尝试。')

            # TODO: 如果搜索有误，手工定义URL2地址。有无改善方案？
            driver.get(url2)
            return driver

        # TODO: 改善Base_info稳健性
        def get_base_info(driver):
            base_table = {}
            # TODO:抽象化：频繁变换点
            base_table['名称'] = driver.find_element_by_xpath("//div[@class='header']/h1").text
            base_info = driver.find_element_by_class_name('detail')

            ## 爬取数据不完整,要支持展开和多项合并
            base_table['电话'] = base_info.text.split('电话：')[1].split('邮箱：')[0].split('查看')[0]
            base_table['邮箱'] = base_info.text.split('邮箱：')[1].split('\n')[0].split('查看')[0]
            base_table['网址'] = base_info.text.split('网址：')[1].split('地址')[0]
            base_table['地址'] = base_info.text.split('地址：')[1].split('\n')[0]

            try:
                abstract = driver.find_element_by_xpath("//div[@class='summary']/script") # @class='sec-c2 over-hide'
                base_table['简介'] = driver.execute_script("return arguments[0].textContent", abstract).strip()
            except:
                abstract = driver.find_element_by_xpath("//div[@class='summary']")
                base_table['简介'] = driver.execute_script("return arguments[0].textContent", abstract).strip()[3:]

            # 处理工商信息的两个tables
            tabs = driver.find_elements_by_xpath("//div[@id='_container_baseInfo']/table")

            # 处理第一个table
            rows1 = tabs[0].find_elements_by_tag_name('tr')
            if len(rows1[1].find_elements_by_tag_name('td')[0].text.split('\n')[0]) < 2:
                base_table['法人代表'] = rows1[1].find_elements_by_tag_name('td')[0].text.split('\n')[1]
            else:
                base_table['法人代表'] = rows1[1].find_elements_by_tag_name('td')[0].text.split('\n')[0]


            # 处理第二个table
            rows2 = tabs[1].find_elements_by_tag_name('tr')

            # 使用循环批量爬取base_table_2
            base_table_2 = pd.DataFrame(columns=['Row_Index','Row_Content'])

            for rows2_row in range(len(rows2)):
                for element_unit in rows2[rows2_row].find_elements_by_tag_name('td'):
                    img_list=rows2[rows2_row].find_elements_by_tag_name('img')
                    if len(img_list)>0:
                        base_table["评估等级"]=img_list[0].get_attribute("alt").replace("评分","")
                    if element_unit.text != '':
                        base_table_2 = base_table_2.append({'Row_Index':rows2_row,'Row_Content':element_unit.text},ignore_index=True)

            if len(base_table_2) % 2 == 0:
                for i in range(int(len(base_table_2)/2)):
                    base_table[base_table_2.iloc[2*i,1]] = base_table_2.iloc[2*i+1,1] # 将base_table_2的数据装回base_table
            else:
                print('base_table_2（公司基本信表2）行数不为偶数，请检查代码！')

            return pd.DataFrame([base_table])

        # 特殊处理：主要人员
        # TODO: staff_info定位不准？
        def get_staff_info(driver):
            staff_list = []
            staff_info = driver.find_elements_by_xpath("//div[@class='in-block f14 new-c5 pt9 pl10 overflow-width vertival-middle new-border-right']")
            for i in range(len(staff_info)):
                position = driver.find_elements_by_xpath("//div[@class='in-block f14 new-c5 pt9 pl10 overflow-width vertival-middle new-border-right']")[i].text
                person = driver.find_elements_by_xpath("//a[@class='overflow-width in-block vertival-middle pl15 mb4']")[i].text
                staff_list.append({'职位': position, '人员名称': person})
            staff_table = pd.DataFrame(staff_list, columns=['职位', '人员名称'])
            return staff_table

        # 特殊处理:上市公告
        # TODO:加入类别搜索功能
        def get_announcement_info(driver):
            announcement_df = pd.DataFrame(columns=['序号','日期','上市公告','上市公告网页链接']) ## 子函数自动获取columns
            # TODO:可抽象，函数化
            content = driver.page_source.encode('utf-8')
            # TODO：能不能只Encode局部的driver
            soup = BeautifulSoup(content, 'lxml')
            announcement_info = soup.find('div',id='_container_announcement').find('tbody').find_all('tr')
            for i in range(len(announcement_info)):
                index = announcement_info[i].find_all('td')[0].get_text()
                date = announcement_info[i].find_all('td')[1].get_text()
                announcement = announcement_info[i].find_all('td')[2].get_text()
                announcement_url = 'https://www.tianyancha.com' + announcement_info[i].find_all('td')[2].find('a')['href']
                announcement_df = announcement_df.append({'序号':index,'日期':date,'上市公告':announcement,'上市公告网页链接':announcement_url}, ignore_index=True)

            ### 判断此表格是否有翻页功能:重新封装change_page函数
            announcement_table = driver.find_element_by_xpath("//div[contains(@id,'_container_announcement')]")
            onclickflag = tryonclick(announcement_table)
            if onclickflag == 1:
                PageCount = announcement_table.find_element_by_class_name('company_pager').text
                PageCount = re.sub("\D", "", PageCount)  # 使用正则表达式取字符串中的数字 ；\D表示非数字的意思
                for i in range(int(PageCount) - 1):
                    button = table.find_element_by_xpath(".//a[@class='num -next']") #历史class_name（天眼查的反爬措施）：'pagination-next  ',''
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(change_page_interval)
                    # TODO：函数化
                    content = driver.page_source.encode('utf-8')
                    # TODO：能不能只Encode局部的driver
                    soup = BeautifulSoup(content, 'lxml')
                    announcement_info = soup.find('div',id='_container_announcement').find('tbody').find_all('tr')
                    for i in range(len(announcement_info)):
                        index = announcement_info[i].find_all('td')[0].get_text()
                        date = announcement_info[i].find_all('td')[1].get_text()
                        announcement = announcement_info[i].find_all('td')[2].get_text()
                        announcement_url = 'https://www.tianyancha.com' + announcement_info[i].find_all('td')[2].find('a')['href']
                        announcement_df = announcement_df.append({'序号':index,'日期':date,'上市公告':announcement,'上市公告网页链接':announcement_url}, ignore_index=True)
            return announcement_df

        # 标准表格爬取函数
        def get_table_info(driver,table,name):

            tab = table.find_element_by_tag_name('table')
            df = pd.read_html('<table>' + tab.get_attribute('innerHTML') + '</table>')

            #print(df)
            if isinstance(df, list):
                df = df[0]
            #遍历df每一行
            import re
            if '操作' in df.columns:
                # 动产抵押
                if name == 'mortgage':
                    df.insert(df.shape[1], '抵押权人名称', np.zeros(df.shape[0]))
                    df.insert(df.shape[1], '履行期限', np.zeros(df.shape[0]))
                    df.insert(df.shape[1], '担保范围', np.zeros(df.shape[0]))
                    df.insert(df.shape[1], '抵押物名称', np.zeros(df.shape[0]))
                    df.insert(df.shape[1], '抵押物所有权', np.zeros(df.shape[0]))
                    df.insert(df.shape[1], '抵押物数量、质量、状况、所在地等情况', np.zeros(df.shape[0]))
                    for i in range(df.shape[0]):
                        #逐行操作
                        tmp_str = str(df['操作'][i])
                        tmp_str = re.sub(r'[\:\"\[\]\,\{\}]', "", tmp_str)
                        df['抵押权人名称'][i] = tmp_str[tmp_str.find("peopleName") + len("peopleName"):tmp_str.find("liceseType")]
                        df['履行期限'][i] = tmp_str[
                                          tmp_str.find("overviewTerm") + len("overviewTerm"):tmp_str.find("regDepartment")]
                        df['担保范围'][i] = tmp_str[
                                          tmp_str.find("scope") +  len("scope"):tmp_str.find("status")]
                        df['抵押物名称'][i] = tmp_str[
                                        tmp_str.find("pawnName") +  len("pawnName"):tmp_str.find("detail",tmp_str.find("detail")+1)]
                        df['抵押物所有权'][i] = tmp_str[
                                         tmp_str.find("ownership") +  len("ownership"):tmp_str.find("pawnName")]
                        df['抵押物数量、质量、状况、所在地等情况'][i] = tmp_str[
                                          tmp_str.find("detail") +  len("detail"):tmp_str.find("ownership")]
                # 行政处罚
                if name =='punishmentCreditchina':
                    df.insert(df.shape[1], '来源', np.zeros(df.shape[0]))
                    df.insert(df.shape[1], '处罚依据', np.zeros(df.shape[0]))
                    for i in range(df.shape[0]):
                        tmp_str = str(df['操作'][i])
                        tmp_str = re.sub(r'[\:\"\[\]\,\{\}]', "", tmp_str)
                        df['来源'][i] = "信用中国"
                        df['处罚依据'][i] = tmp_str[
                                                      tmp_str.find("evidence") + len("evidence"):tmp_str.find("punishStatus")]

                #开庭公告
                if name=="announcementcourt":
                    df.insert(df.shape[1], '法院', np.zeros(df.shape[0]))
                    df.insert(df.shape[1], '法庭', np.zeros(df.shape[0]))
                    df.insert(df.shape[1], '当事人', np.zeros(df.shape[0]))
                    for i in range(df.shape[0]):
                        tmp_str = str(df['操作'][i])
                        tmp_str = re.sub(r'[\:\"\[\]\,\{\}]', "", tmp_str)
                        df['法院'][i] = tmp_str[
                                        tmp_str.find("court") + len("court"):tmp_str.find("litigant")]
                        df['法庭'][i] = tmp_str[
                                        tmp_str.find("courtroom") + len("courtroom"):tmp_str.find("caseReason")]
                        df['当事人'][i] = tmp_str[
                                        tmp_str.find("litigant") + len("litigant"):tmp_str.find("litigant2")]
                #法律诉讼
                if  name == "lawsuit":
                    df.insert(df.shape[1], '详情链接', np.zeros(df.shape[0]))
                    #content = driver.page_source.encode('utf-8')
                    if "main" not in name:
                        name="_container_"+name
                    url_list = table.find_element_by_id(name).find_element_by_tag_name("table").find_elements_by_tag_name("td")
                    cnt=0
                    for i in range(len(url_list)):
                        if url_list[i].text=="详情":
                            url=url_list[i].find_element_by_tag_name("a").get_attribute("href")
                            df["详情链接"][cnt]=url
                            cnt+=1
                        #print(url)

                #年报
                if name=="reportCount":
                    df.insert(df.shape[1], '详情链接', np.zeros(df.shape[0]))
                    url_list = table.find_element_by_tag_name("table").find_elements_by_tag_name("td")
                    cnt=0
                    for i in range(len(url_list)):
                        if url_list[i].text=="详情":
                            url=url_list[i].find_element_by_tag_name("a").get_attribute("href")
                            df["详情链接"][cnt]=url
                            cnt+=1

                df = df.drop(columns='操作')

            #招投标
            if name=="bid":
                df.insert(df.shape[1], '详情链接', np.zeros(df.shape[0]))
                name = "_container_" + name
                url_list = table.find_element_by_id(name).find_element_by_tag_name("table").find_elements_by_tag_name(
                    "td")
                cnt=0
                for element in url_list:
                    if isElementExist(element,"a"):
                        url=element.find_element_by_tag_name("a").get_attribute("href")
                        df["详情链接"][cnt]=url
                        cnt+=1
            # TODO：加入更多标准的表格处理条件

            return df

        def tryonclick(table): # table实质上是selenium WebElement
            # 测试是否有翻页
            ## 把条件判断写进tryonclick中
            try:
                # 找到有翻页标记
                table.find_element_by_tag_name('ul')
                onclickflag = 1
            except Exception:
                #print("没有翻页") ## 声明表格名称: name[x] +
                onclickflag = 0
            return onclickflag

        def tryontap(table):
            # 测试是否有翻页
            try:
                table.find_element_by_xpath("//div[contains(@class,'over-hide changeTabLine f14')]")
                ontapflag = 1
            except:
                #print("没有时间切换页") ## 声明表格名称: name[x] +
                ontapflag = 0
            return ontapflag

        def change_page(table, df, driver,name):
            # TODO:抽象化：频繁变换点
            # PageCount = table.find_element_by_class_name('company_pager').text #历史class_name（天眼查的反爬措施）：'total'
            # PageCount = re.sub("\D", "", PageCount)  # 使用正则表达式取字符串中的数字 ；\D表示非数字的意思
            PageCount = len(table.find_elements_by_xpath(".//ul[@class='pagination']/li")) - 1

            for _ in range(int(PageCount) - 1):
                # TODO:抽象化：频繁变换点
                button = table.find_element_by_xpath(".//a[@class='num -next']") #历史class_name（天眼查的反爬措施）：'pagination-next  ',''
                driver.execute_script("arguments[0].click();", button)
                ####################################################################################
                time.sleep(change_page_interval) # 更新换页时间间隔,以应对反爬虫
                ####################################################################################
                df2 = get_table_info(driver,table,name) ## 应该可以更换不同的get_XXXX_info
                df = df.append(df2)
            return df

        # TODO：完善change_tap函数。
        def change_tap(table, df,name,driver):
            TapCount = len(table.find_elements_by_tag_name('div'))
            for i in range(int(TapCount) - 3):
                button = table.find_elements_by_tag_name('div')[i+3]
                driver.execute_script("arguments[0].click();", button)
                time.sleep(2)
                df2 = get_table_info(driver,table,name) ## 应该可以更换不同的get_XXXX_info
                # df2['日期'] = table.find_elements_by_tag_name('div')[i+3].text
                df = df.append(df2, ignore_index=True)
            # df = df.drop(columns=['序号'])
            return df

        def scrapy(driver, table, use_default_exception, quit_driver=quit_driver):
            # 强制确认table类型为list：当只爬取一个元素的时候很可能用户会只传入表明str
            if isinstance(table, str):
                list_table = []
                list_table.append(table)
                table = list_table

            # 定义排除列表
            # TODO:允许用户自主选择保留项目;帮助检查没有重复项
            if use_default_exception:
                list_exception = ['recruit', 'tmInfo', 'holdingCompany', 'invest', 'bonus', 'firmProduct', 'jingpin', \
                                  'bid', 'taxcredit', 'certificate', 'patent', 'copyright', 'product', 'importAndExport', \
                                  'copyrightWorks', 'wechat', 'icp', 'announcementcourt', 'lawsuit', 'court', \
                                  'branch', 'touzi', 'judicialSale', 'bond', 'teamMember', 'check']
                # 两个List取差异部分，只排除不在爬取范围内的名单。参考：https://stackoverflow.com/questions/1319338/combining-two-lists-and-removing-duplicates-without-removing-duplicates-in-orig/1319353#1319353
                list_exception = list(set(list_exception) - set(table))
            else:
                list_exception = []

            # Waiting time for volatilityNum to load
            time.sleep(2)
            tables = driver.find_elements_by_xpath("//div[contains(@id,'_container_')]")

            # 获取每个表格的名字
            c = '_container_'
            #tmp ='nav-main-'
            name = [0] * (len(tables) - 2)
            # 生成一个独一无二的十六位参数作为公司标记，一个公司对应一个，需要插入多个数据表
            id = keyword
            table_dict = {}
            # 年报的特殊处理
            if('reportCount' in table):
                print("正在爬取年报")
                tab=driver.find_element_by_xpath("//div[@tyc-event-ch='CompangyDetail.nianbao']")
             #print(tab.text)
                df=get_table_info(driver,tab,'reportCount')
                table_dict['reportCount'] = df

            for x in range(len(tables)-2):
                name[x] = tables[x].get_attribute('id')
                if c in name[x]:
                    name[x] = name[x].replace(c, '')  # 可以用这个名称去匹配数据库
                #print(name[x])
                # 判断是表格还是表单
                # TODO: Deprecated if being tested not useful anymore.
                # num = tables[x].find_elements_by_tag_name('table')

                # 排除列表：不同业务可以设置不同分类，实现信息的精准爬取
                if name[x] in list_exception:
                    pass

                # 基本信息表：baseInfo，table有两个
                elif (name[x] == 'baseInfo') and (('baseInfo' in table) or (table == ['all'])):
                    print('正在爬取' + 'baseInfo')
                    try:
                        table_dict[name[x]] = get_base_info(driver)
                    except:
                        print('baseInfo表格为特殊格式，使用了标准表格爬取函数。')
                        table_dict[name[x]] = get_base_info(driver)

                # # 公司高管的特殊处理
                # elif name[x] == 'staff':
                #     table_dict[name[x]] = get_staff_info(driver)

                # 公告的特殊处理：加入URL
                elif (name[x] == 'announcement') and (('announcement' in table) or (table == ['all'])):
                    print ('正在爬取' + 'announcement')
                    try:
                        table_dict[name[x]] = get_announcement_info(driver)
                    except:
                        print('announcement表格为特殊格式，使用了标准表格爬取函数。')
                        table_dict[name[x]] = get_base_info(driver)


                # 单纯的表格进行信息爬取
                # TODO: 含头像的行未对齐
                elif ((name[x] in table) or (table == ['all'])):
                    # 检查用
                    print('正在爬取' + str(name[x]))
                    df = get_table_info(driver,tables[x],name[x])
                    onclickflag = tryonclick(tables[x])
                    ontapflag = tryontap(tables[x])
                    time.sleep(1)
                    # 判断此表格是否有翻页功能
                    if onclickflag == 1:
                        df = change_page(tables[x], df, driver,name[x])


                    #  if ontapflag == 1:
                #      df = change_tap(tables[x], df)
                    table_dict[name[x]] = df

                else:
                    pass

            # 退出浏览器
            if quit_driver:
                driver.quit()

            return table_dict
        #下面这些字段对应的英文个别可能是有误的，要手工校对网页对应部分的id
        sheet_name_transfer={"baseInfo":"工商信息",
                             "staff":"主要成员信息",
                             "holder":"股东信息",
                             "branch":"分支机构",
                             "invest":"对外投资",
                             "reportCount":"年报",
                             "changeinfo":"工商变更",
                             "mortgage":"动产抵押",
                             "equity": "股权出质",
                             "punishmentCreditchina": "行政处罚",
                             "":"信息披露",
                             "corpGuarantees":"对外担保",
                             "ownTaxCount":"催缴/欠税",
                             "":"税务非正常户",
                             "abnormal": "经营异常",
                             "announcementcourt": "开庭公告",
                             "lawsuit": "裁判文书",
                             "judicialaAidCount": "司法协助",
                             "zhixing": "失信被执行人",
                             "court": "涉诉公告",
                             "patent": "专利",
                             "copyright": "软件著作权",
                             "copyrightWorks":"作品著作权",
                             "icp": "ICP备案信息",
                             "bid": "招投标",
                             "landMortgagesCount": "土地抵押",
                             "landTransfersCount": "土地转让",
                             "findNewsCount":"最新新闻舆情",
                             "landPublicitys":"土地信息",
                             "courtRegister":"法院公告",
                             "dishonest":"失信信息",
                             "pastZhixing":"被执行人",
                             "check":"抽查检查",
                            "judicialSale":"司法拍卖",
                             "product":"产品信息",
                             "company_chc":"最终受益人",
                             "taxcredit":"税务评级",
                             "licensing":"行政许可",
                             "companySearchReport":"企业研报",
                             "tmInfo":"商标信息",
                             "certificate":"资质证书",
                             "wechat":"微信公众号",
                             "weibo":"微博"
                            }

        def gen_excel(table_dict, keyword):
            if not os.path.exists(".\\result"):
                os.mkdir(".\\result")
            with pd.ExcelWriter(".\\result\\"+keyword+'.xlsx') as writer:
                for sheet_name in table_dict:
                    table_dict[sheet_name].to_excel(writer, sheet_name=sheet_name_transfer[sheet_name], index=None)

        def gen_json(table_dict, keyword):
            list_dic = []
            for i in list(table_dict.keys()):
                list_dic.append((i, table_dict[i]))
            dic = OrderedDict(list_dic)
            list_json = WriterJson().odict_to_json(dic)
            WriterJson().write_json(json_list=list_json, file_name=keyword+'.json')

        time_start = time.time()

        url_search = 'http://www.tianyancha.com/search?key=%s&checkFrom=searchBox' % keyword
        self.driver = search_company(self.driver, url_search)
        table_dict = scrapy(self.driver, table, use_default_exception)
        if export == 'xlsx':
            gen_excel(table_dict, keyword)
        elif export == 'json':
            gen_json(table_dict, keyword)
        else:
            print("请选择正确的输出格式，支持'xlsx'和'json'。")

        time_end = time.time()
        print('您的本次爬取共用时{}秒。'.format(int(time_end - time_start)))
        return table_dict


    # 定义批量爬取爬虫
    def tianyancha_scraper_batch(self, input_template='input.xlsx', change_page_interval=2, export='xlsx'):
        df_input = pd.read_excel(input_template, encoding='gb18030').dropna(axis=1, how='all')
        list_dicts = []

        # 逐个处理输入信息
        for i in range(len(df_input)):
            keyword = df_input['公司名称'].iloc[i]
            '''
            tables = []
            for j in range(len(df_input.columns) - 2):
                if not pd.isna(df_input.iloc[i, j + 2]):
                    tables.append(df_input.iloc[i, j + 2])
            '''

            # 批量调取天眼查爬虫
            table_dict = self.tianyancha_scraper(keyword=keyword, table=['baseInfo',
                                                                                                       'staff',
                                                                                                       'holder',
                                                                                                       'branch',
                                                                                                       'invest',
                                                                                                       'reportCount',
                                                                                                       'changeinfo',
                                                                                                       'mortgage',
                                                                                                       'equity',
                                                                                                       'punishmentCreditchina',
                                                                                                       'ownTaxCount',
                                                                                                       'abnormal',
                                                                                                       'announcementcourt',
                                                                                                       'lawsuit',
                                                                                                       'court',
                                                                                                       'judicialaAidCount',
                                                                                                       'zhixing',
                                                                                                       'patent',
                                                                                                       'copyright',
                                                                                                       'copyrightWorks',
                                                                                                       'icp', 'bid',
                                                                                                       'landMortgagesCount',
                                                                                                       'landTransfersCount',
                                                                         'courtRegister',
                                                                         "copyrightWorks",
                                                                         "certificate",
                                                                         'pastZhixing',
                                                                         'dishonest',
                                                                         "check",
                                                                         "judicialSale",
                                                                         'landPublicitys',
                                                                         "product",
                                                                         "corpGuarantees",
                                                                         "taxcredit",
                                                                         "company_chc",
                                                                         "licensing",
                                                                         "companySearchReport",
                                                                         "wechat",
                                                                         "weibo",
                                                                         "tmInfo"],use_default_exception=False, change_page_interval=change_page_interval, export=export,quit_driver=False)
            list_dicts.append(table_dict)

        # 全部运行完后退出浏览器
        self.driver.quit()
        return tuple(list_dicts)