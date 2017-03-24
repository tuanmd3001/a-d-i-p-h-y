# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import unittest
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from xvfbwrapper import Xvfb
import requests
from time import gmtime, strftime


class Adiphy(unittest.TestCase):
    def setUp(self):
        self.total = 500
        self.api_key = 'f737a1f15e270537d23bf8e43b189c58'
        self.site_key = ''
        self.setting_root = 'settings/'
        self.preset_root = 'preset/'
        self.logs_root = 'logs/'
        self.screenshot_root = 'screenshot/'
        self.proxy_filename = self.setting_root + 'proxy.txt'
        self.accounts_filename = self.setting_root + 'accounts.txt'
        self.use_vpn = True
        self.xvfb = Xvfb()
        self.xvfb.start()
        self.username, self.password = self.get_user()
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

    def test_demo(self):
        self.driver.get(self.login_url)
        try:
            self.driver.find_element_by_id('username')
            check_login = False
        except:
            check_login = True

        if check_login is False:
            if self.username != '' and self.password != '':
                self.driver.find_element_by_id('username').send_keys(self.username)
                self.driver.find_element_by_id('password').send_keys(self.password)
                if self.solve_grecaptcha():
                    self.driver.find_element_by_xpath('//button[@type="submit"]').click()
                    self.start_app()
                else:
                    print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ***** Solve Google reCaptcha success! *****'
                    self.test_demo()
            else:
                print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' !!! Account must not empty !!!'
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
                if self.clicked_count < self.total:
                    start_time = time.time()
                    if self.find_post_and_click(i):
                        self.clicked_count += 1
                        print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ' + str(self.clicked_count) + ' - Done - Time: ' + str(time.time() - start_time) + 's'
                    else:
                        break
                else:
                    break
            if self.clicked_count < self.total:
                self.start_app()
            else:
                print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ---------- END ----------'
        except:
            print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' ' + str(self.clicked_count + 1) + ' - Failed - Retrying......'
            if self.click_home() is False:
                self.driver.get(self.url)
            print strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' --------- RESTART ----------'
            self.test_demo()

    def get_user(self):
        with open(self.accounts_filename) as accounts_file:
            content = accounts_file.readlines()
            accounts_file.close()
        content_list = [x.strip() for x in content]
        first_acc = content_list[0]
        acc_split = first_acc.split(' ')
        return acc_split[0].strip(), acc_split[1].strip()

    def find_post_and_click(self, index):
        if self.scroll_to_find_el(index, 0):
            if self.click_post(index):
                return self.close_opener_tab()
            else:
                return self.find_post_and_click(index)
        else:
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
        wait = WebDriverWait(self.driver, 30)
        home_show = wait.until(
            ec.presence_of_element_located((By.CLASS_NAME, 'grid-item'))
        )
        if self.driver.execute_script('return $(".grid-item").eq(' + str(index) + ').find("img:first").length'):
            self.driver.execute_script('$(".grid-item").eq(' + str(index) + ').find("img:first").click();', home_show)
            return True
        else:
            return False

    def click_like_btn(self):
        find_countdown = self.driver.execute_script("return $('#countdown').length")
        if find_countdown == 1:
            countdown = self.driver.execute_script("return $('#countdown').text()")
            self.hover_to_countdown()
            time.sleep(int(countdown) + 1)
            return self.click_like_btn()
        elif self.driver.execute_script("return $('#go-submit-likeUp').length"):
            self.driver.execute_script("$('#go-submit-likeUp').click()")
            time.sleep(self.sleep_after_like)
            return self.click_home()
        elif self.driver.execute_script("return $('#go-link').find('#btns_sub button:last').length"):
            self.driver.execute_script("$('#go-link').find('#btns_sub button:last').click()")
            time.sleep(self.sleep_after_like)
            return self.click_home()
        else:
            return False

    def click_home(self):
        try:
            wait = WebDriverWait(self.driver, 2)
            logo = wait.until(
                ec.presence_of_element_located((By.XPATH, '//a[@href="' + self.url + '"]'))
            )
            logo.click()
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CLASS_NAME, 'boxsearch'))
            )
            return True
        except TimeoutException:
            return False
        except:
            return False

    def hover_to_countdown(self):
        # hover = ActionChains(self.driver).move_to_element(self.driver.find_element_by_tag_name("body"))
        # hover.perform()
        self.driver.find_element_by_id('countdown').click()

    def tearDown(self):
        self.driver.quit()
        self.xvfb.stop()


if __name__ == "__main__":
    unittest.main()
