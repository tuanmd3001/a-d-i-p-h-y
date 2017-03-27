# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import unittest
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from xvfbwrapper import Xvfb
import requests
from time import gmtime, strftime
import MySQLdb


class Adiphy(unittest.TestCase):
    def setUp(self):
        self.xvfb = Xvfb()
        self.xvfb.start()
        self.total = 500
        self.click_available = 500
        self.api_key = 'f737a1f15e270537d23bf8e43b189c58'
        self.site_key = ''
        self.username = self.password = ''
        self.login_type = 1  # ACC
        self.url = "http://adiphy.com/"
        self.login_url = self.url + "auth/signin/"
        self.scroll_count = 0
        self.post_start = 0
        self.post_end = 10
        self.clicked_count = 0
        self.sleep_after_like = 2
        self.sleep_after_scroll = 2
        self.scroll_max_try = 3
        self.driver = webdriver.Firefox()
        self.driver.maximize_window()
        self.driver.implicitly_wait(30)
        print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ---------- START ----------'

    def getSettings(self):
        try:
            print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ***** Try to get settings *****'
            db = MySQLdb.connect(host="94.177.199.7", user="user", passwd="passwd", db="adiphy")
            cursor = db.cursor()
            sql = "SELECT * FROM settings WHERE id=1"
            cursor.execute(sql)
            db.commit()
            all_settings = cursor.fetchall()
            if len(all_settings) > 0:
                first_settings = all_settings[0]
                self.total = self.click_available = first_settings[1]
                self.api_key = first_settings[2]
                self.post_start = first_settings[3]
                self.post_end = first_settings[4]
                self.sleep_after_like = first_settings[5]
                self.sleep_after_scroll = first_settings[6]
                self.scroll_max_try = first_settings[7]

            public_ip = requests.get('http://ip.42.pl/raw').text
            sql = 'SELECT * FROM accounts WHERE ip="%s"' % public_ip
            cursor.execute(sql)
            result = cursor.fetchall()
            if len(result) > 0:
                first_user = result[0]
                self.username = first_user[1]
                self.password = first_user[2]
                self.login_type = first_user[4]
            db.close()
        except:
            print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ----- Failed to get settings -----'
            self.getSettings()

    def test_demo(self):
        self.driver.get(self.login_url)
        try:
            self.driver.find_element_by_id('username')
            check_login = False
        except:
            check_login = True

        if check_login is False:
            self.getSettings()
            if self.username != '' and self.password != '':
                if self.login_type == 1:
                    self.driver.find_element_by_id('username').send_keys(self.username)
                    self.driver.find_element_by_id('password').send_keys(self.password)
                    if self.solve_grecaptcha():
                        print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ***** Solve Google reCaptcha success! *****'
                        self.driver.find_element_by_xpath('//button[@type="submit"]').click()
                        self.start_app()
                    else:
                        print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ----- Solve Google reCaptcha failed! -----'
                        self.test_demo()
                else:
                    self.driver.find_element_by_xpath("//a[@href='/fbconnect/']").click()
                    self.driver.find_element_by_id('email').send_keys(self.username)
                    self.driver.find_element_by_id('pass').send_keys(self.password)
                    self.driver.find_element_by_id('loginbutton').click()
                    self.start_app()
            else:
                print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ----- Can not get account info! -----'
        else:
            self.start_app()

    def solve_grecaptcha(self):
        try:
            self.site_key = self.driver.find_element_by_class_name('g-recaptcha').get_attribute('data-sitekey')
            s = requests.Session()
            captcha_id = s.post("http://2captcha.com/in.php?key={}&method=userrecaptcha&googlekey={}&pageurl={}".format(self.api_key, self.site_key, self.url)).text.split('|')[1]
            recaptcha_answer = s.get("http://2captcha.com/res.php?key={}&action=get&id={}".format(self.api_key, captcha_id)).text
            print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " ***** Solving Google reCaptcha *****"
            while 'CAPCHA_NOT_READY' in recaptcha_answer:
                time.sleep(5)
                recaptcha_answer = s.get("http://2captcha.com/res.php?key={}&action=get&id={}".format(self.api_key, captcha_id)).text
            recaptcha_answer = recaptcha_answer.split('|')[1]
            self.driver.execute_script('$("#g-recaptcha-response").val("' + recaptcha_answer + '")')
            return True
        except:
            return False

    def start_app(self):
        try:
            for i in list(range(self.post_start, self.post_end + 1)):
                if self.clicked_count < self.total and self.click_available > 0:
                    start_time = time.time()
                    if self.find_post_and_click(i):
                        self.clicked_count += 1
                        print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ' + str(self.clicked_count) + ' - Done - Time: ' + str(time.time() - start_time) + 's'
                    else:
                        break
                else:
                    break
            if self.clicked_count < self.total and self.click_available > 0:
                self.start_app()
            else:
                print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ---------- END ----------'
        except:
            print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ' + str(self.clicked_count + 1) + ' - Failed - Retrying......'
            time_error = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            self.driver.save_screenshot('click_home - ' + time_error + '.png')

            if self.click_home() is False:
                self.driver.get(self.url)
            print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' --------- RESTART ----------'
            self.test_demo()

    def find_post_and_click(self, index):
        if self.scroll_to_find_el(index, 0):
            if self.click_post(index):
                return self.close_opener_tab()
            else:
                return self.find_post_and_click(index)
        else:
            time_error = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print 'Failed in scroll_to_find_el'
            self.driver.save_screenshot('scroll_to_find_el - ' + time_error + '.png')
            return False

    def scroll_to_find_el(self, index, retry):
        count_post = self.driver.execute_script("return $('.grid-item').length")
        if count_post - 1 > index:
            return True
        else:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.sleep_after_scroll)
            count_post = self.driver.execute_script("return $('.grid-item').length")
            if count_post - 1 < index:
                if count_post > self.scroll_count:
                    self.scroll_count = count_post
                    return self.scroll_to_find_el(index, 0)
                else:
                    if retry > self.scroll_max_try:
                        return False
                    else:
                        return self.scroll_to_find_el(index, retry + 1)
            else:
                self.scroll_count = 0
                return True

    def close_opener_tab(self):
        tabs = self.driver.window_handles
        if len(tabs) == 2:
            self.driver.switch_to.window(window_name=self.driver.window_handles[0])
            self.driver.close()
            self.driver.switch_to.window(window_name=self.driver.window_handles[0])
            self.hover_to_countdown()
        return self.click_like_btn()

    def click_post(self, index):
        try:
            home_show = WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CLASS_NAME, 'grid-item'))
            )
            if self.driver.execute_script('return $(".grid-item").eq(' + str(index) + ').find("img:first").length'):
                self.driver.execute_script('$(".grid-item").eq(' + str(index) + ').find("img:first").click();', home_show)
                return True
            else:
                return False
        except:
            time_error = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print 'Failed in click_post'
            self.driver.save_screenshot('click_post - ' + time_error + '.png')
            return False

    def click_like_btn(self):
        if self.driver.execute_script("return $('#progressBar').length") > 0:
            self.hover_to_countdown()
            time.sleep(1)
            return self.click_like_btn()
        elif self.driver.execute_script("return $('#go-submit-likeUp').length") > 0:
            self.driver.execute_script("$('#go-submit-likeUp').click()")
            time.sleep(self.sleep_after_like)
            return self.click_home()
        elif self.driver.execute_script("return $('#go-link').find('#btns_sub button:last').length") > 0:
            self.driver.execute_script("$('#go-link').find('#btns_sub button:last').click()")
            time.sleep(self.sleep_after_like)
            return self.click_home()
        else:
            time_error = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print 'Failed in click_like_btn'
            self.driver.save_screenshot('click_like_btn - ' + time_error + '.png')
            return False

    def click_home(self):
        try:
            logo = WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.XPATH, '//a[@href="' + self.url + '"]'))
            )
            logo.click()
        except:
            time_error = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print 'Failed in click_home'
            self.driver.save_screenshot('click_home - ' + time_error + '.png')
            self.driver.get(self.url)

        try:
            available_count = WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CLASS_NAME, 'h-item-value'))
            )
            if available_count and available_count.text.strip() != '':
                self.click_available = int(available_count.text)
                print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ***** click available: ' + str(self.click_available) + ' *****'
        except:
            pass
        return True

    def hover_to_countdown(self):
        try:
            self.driver.find_element_by_class_name('img-responsive').click()
        except:
            pass

    def tearDown(self):
        self.driver.quit()
        self.xvfb.stop()


if __name__ == "__main__":
    unittest.main()
