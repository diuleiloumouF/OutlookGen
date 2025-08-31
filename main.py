import socket as dsocket
from contextlib import suppress
from ctypes import windll
from dataclasses import dataclass
from json import load
from os import getcwd, listdir, chdir, remove, mkdir, path, name
from random import choice, randrange
from random import randint
from shutil import copytree, rmtree, copyfile
from ssl import create_default_context
from sys import exit
from time import sleep, time
from typing import Any
from urllib.parse import urlparse
from zipfile import ZipFile

from colorama import Fore
from requests import get
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from tqdm import tqdm
from twocaptcha import TwoCaptcha

from Utils import Utils, Timer
from anycaptcha import AnycaptchaClient, FunCaptchaProxylessTask

# Some Value
eGenerated = 0
solvedCaptcha = 0


class AutoUpdater:
    def __init__(self, version):
        self.version = version
        self.latest = self.get_latest()
        self.this = getcwd()
        self.file = "temp/latest.zip"
        self.folder = f"temp/latest_{randrange(1_000_000, 999_999_999)}"

    @dataclass
    class latest_data:
        version: str
        zip_url: str

    def get_latest(self):
        rjson = get("https://api.github.com/repos/MatrixTM/OutlookGen/tags").json()
        return self.latest_data(version=rjson[0]["name"], zip_url=get(rjson[0]["zipball_url"]).url)

    @staticmethod
    def download(host, dPath, filename):
        with dsocket.socket(dsocket.AF_INET, dsocket.SOCK_STREAM) as sock:
            context = create_default_context()
            with context.wrap_socket(sock, server_hostname="api.github.com") as wrapped_socket:
                wrapped_socket.connect((dsocket.gethostbyname(host), 443))
                wrapped_socket.send(
                    f"GET {dPath} HTTP/1.1\r\nHost:{host}\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,file/avif,file/webp,file/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9\r\n\r\n".encode())

                resp = b""
                while resp[-4:-1] != b"\r\n\r":
                    resp += wrapped_socket.recv(1)
                else:
                    resp = resp.decode()
                    content_length = int(
                        "".join([tag.split(" ")[1] for tag in resp.split("\r\n") if "content-length" in tag.lower()]))
                    _file = b""
                    while content_length > 0:
                        data = wrapped_socket.recv(2048)
                        if not data:
                            print("EOF")
                            break
                        _file += data
                        content_length -= len(data)
                    with open(filename, "wb") as file:
                        file.write(_file)

    def update(self):
        if not self.version == self.latest.version:
            rmtree("temp") if path.exists("temp") else ""
            mkdir("temp")
            print("Updating Script...")
            parsed = urlparse(self.latest.zip_url)
            self.download(parsed.hostname, parsed.path, self.file)
            ZipFile(self.file).extractall(self.folder)
            print(path.exists(self.folder))
            print(path.exists(listdir(self.folder)[0]))
            chdir("{}/{}".format(self.folder, listdir(self.folder)[0]))
            for files in listdir():
                if path.isdir(files):
                    with suppress(FileNotFoundError):
                        rmtree("{}/{}".format(self.this, files))
                    copytree(files, "{}/{}".format(self.this, files))
                else:
                    with suppress(FileNotFoundError):
                        remove("{}/{}".format(self.this, files))
                    copyfile(files, "{}/{}".format(self.this, files))
            rmtree("../../../temp")
            exit("Run Script Again!")
            return
        print("Script is up to date!")


class eGen:
    def __init__(self):
        self.version = "v1.2.4"
        AutoUpdater(self.version).update()
        self.Utils = Utils()  # Utils Module
        self.config: Any = load(open('config.json'))  # Config File
        self.checkConfig()  # Check Config File
        self.options = webdriver.ChromeOptions()  # Driver Options
        self.Timer = Timer()  # Timer

        self.driver = None
        self.capabilities = None
        self.first_name = None  # Generate First Name
        self.last_name = None  # Generate Last Name
        self.password = None  # Generate Password
        self.email = None  # Generate Email

        # Values About Captcha
        self.providers = self.config['Captcha']['providers']
        self.api_key = self.config["Captcha"]["api_key"]
        self.site_key = self.config["Captcha"]["site_key"]

        # Other
        self.proxies = [i.strip() for i in open(self.config['Common']['ProxyFile']).readlines()]  # Get Proxies
        for arg in tqdm(self.config["DriverArguments"], desc='Loading Arguments',
                        bar_format='{desc} | {l_bar}{bar:15} | {percentage:3.0f}%'):  # Get Driver Arguments
            self.options.add_argument(arg)  # Add Argument to option
            sleep(0.2)

        # More Options
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.options.add_experimental_option('useAutomationExtension', False)

    def solver(self, site_url, browser):
        # Solve Captcha Function
        global solvedCaptcha
        # TwoCaptcha
        if self.providers == 'twocaptcha':
            try:
                return TwoCaptcha(self.api_key).funcaptcha(sitekey=self.site_key, url=site_url)['code']
            except Exception as exp:
                self.print(exp)

            # AnyCaptcha
        elif self.providers == 'anycaptcha':
            client = AnycaptchaClient(self.api_key)
            task = FunCaptchaProxylessTask(site_url, self.site_key)
            job = client.createTask(task, typecaptcha="funcaptcha")
            self.print("Solving funcaptcha")
            job.join()
            result = job.get_solution_response()
            if result.find("ERROR") != -1:
                self.print(result)
                browser.quit()
            else:
                solvedCaptcha += 1
                return result

    def check_proxy(self, proxy):
        with suppress(Exception):
            get("https://outlook.live.com", proxies={
                "http": "http://{}".format(proxy),
                "https": "http://{}".format(proxy)
            }, timeout=self.config["Common"]["ProxyCheckTimeout"] or 5)
            return True
        return False

    def fElement(self, driver: WebDriver, by: By = By.ID, value=None, delay: float = 0.3):
        # Custom find Element Function
        count = 0
        while count <= 100:
            with suppress(Exception):
                return driver.find_element(by, value)
            sleep(delay)
            count += 1
        self.print(f'tried 100 time to find element...{by} {value}')
        # driver.quit()
        return

    def get_balance(self):
        # Check provider Balance Function
        if self.providers == 'twocaptcha':
            return TwoCaptcha(self.api_key).balance()
        elif self.providers == 'anycaptcha':
            return AnycaptchaClient(self.api_key).getBalance()

    def update(self):
        # Update Title Function
        global eGenerated, solvedCaptcha
        title = f'Email Generated: {eGenerated} | Solved Captcha: {solvedCaptcha} | Balance: {self.get_balance()}'
        windll.kernel32.SetConsoleTitleW(title) if name == 'nt' else print(f'\33]0;{title}\a', end='',
                                                                           flush=True)

    def generate_info(self):
        # Generate Information Function
        self.email = self.Utils.eGen()
        self.password = self.Utils.makeString(self.config["EmailInfo"]["PasswordLength"])  # Generate Password
        self.first_name = self.Utils.makeString(self.config["EmailInfo"]["FirstNameLength"])  # Generate First Name
        self.last_name = self.Utils.makeString(self.config["EmailInfo"]["LastNameLength"])  # Generate Last Name

    def checkConfig(self):
        # Check Config Function
        captcha_sec = self.config['Captcha']
        if captcha_sec['api_key'] == "" or captcha_sec['providers'] == "anycaptcha/twocaptcha" or \
                self.config['EmailInfo']['Domain'] == "@hotmail.com/@outlook.com":
            self.print('Please Fix Config!')
            exit()

    def print(self, text: object, end: str = "\n"):
        # Print With Prefix Function
        print(self.Utils.replace(f"{self.config['Common']['Prefix']}&f{text}",
                                 {
                                     '&a': Fore.LIGHTGREEN_EX,
                                     '&4': Fore.RED,
                                     '&2': Fore.GREEN,
                                     '&b': Fore.LIGHTCYAN_EX,
                                     '&c': Fore.LIGHTRED_EX,
                                     '&6': Fore.LIGHTYELLOW_EX,
                                     '&f': Fore.RESET,
                                     '&e': Fore.LIGHTYELLOW_EX,
                                     '&3': Fore.CYAN,
                                     '&1': Fore.BLUE,
                                     '&9': Fore.LIGHTBLUE_EX,
                                     '&5': Fore.MAGENTA,
                                     '&d': Fore.LIGHTMAGENTA_EX,
                                     '&8': Fore.LIGHTBLACK_EX,
                                     '&0': Fore.BLACK}), end=end)

    def CreateEmail(self, driver: WebDriver):
        # Create Email Function
        try:
            global eGenerated, solvedCaptcha
            # self.update()
            self.print('12321')
            self.Timer.start(time()) if self.config["Common"]['Timer'] else ''
            self.print("CreateEmail")
            driver.get("https://outlook.live.com/mail/0/?prompt=create_account")
            assert 'Create' in driver.title
            if self.config['EmailInfo']['Domain'] == "@hotmail.com":
                domain = self.fElement(driver, By.ID, 'LiveDomainBoxList')
                sleep(0.1)
                domainObject = Select(domain)
                domainObject.select_by_value('hotmail.com')
            emailInput = self.fElement(driver, By.ID, 'floatingLabelInput6')
            emailInput.send_keys(self.email)
            self.print(f"email: {self.email}{self.config['EmailInfo']['Domain']}")
            # 找到按钮元素
            button = self.fElement(driver, By.CSS_SELECTOR, '[data-testid="primaryButton"]')
            sleep(3)
            # 点击按钮
            button.click()
            with suppress(Exception):
                self.print(driver.find_element(By.ID, 'MemberNameError').text)
                self.print("email is already taken")
                # driver.quit()
                return
            passwordinput = self.fElement(driver, By.ID, 'floatingLabelInput12')
            passwordinput.send_keys(self.password)
            self.print("Password: %s" % self.password)
            self.fElement(driver, By.CSS_SELECTOR, '[data-testid="primaryButton"]').click()
            # 月份选择 - 点击月份标签
            sleep(2)
            birthMonth = self.fElement(driver, By.CSS_SELECTOR, 'label[for="BirthMonthDropdown"]')
            driver.execute_script("arguments[0].click();", birthMonth)
            sleep(2)
            # 获取所有月份选项并随机选择
            month_options = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"].fui-Option')
            random_month = choice(month_options)
            driver.execute_script("arguments[0].click();", random_month)
            sleep(2)
            # 日期选择 - 点击日期标签
            birthDay = self.fElement(driver, By.CSS_SELECTOR, 'label[for="BirthDayDropdown"]')
            driver.execute_script("arguments[0].click();", birthDay)
            sleep(2)
            # 获取所有日期选项并随机选择
            day_options = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"].fui-Option')
            if day_options:
                random_day = choice(day_options)
                driver.execute_script("arguments[0].click();", random_day)
            sleep(2)
            # 年份输入（如果年份仍然是输入框的话）
            birthYear = self.fElement(driver, By.ID, "floatingLabelInput22")
            birthYear.send_keys(
                str(randint(self.config['EmailInfo']['minBirthDate'], self.config['EmailInfo']['maxBirthDate'])))
            self.fElement(driver, By.CSS_SELECTOR, '[data-testid="primaryButton"]').click()

            sleep(3)
            # 输入姓名
            first = self.fElement(driver, By.ID, "firstNameInput")
            first.send_keys(self.first_name)
            sleep(3)
            last = self.fElement(driver, By.ID, "lastNameInput")
            last.send_keys(self.last_name)
            self.fElement(driver, By.CSS_SELECTOR, '[data-testid="primaryButton"]').click()
            sleep(3)

            # driver.switch_to.frame(self.fElement(driver, By.ID, 'enforcementFrame'))
            # token = self.solver(driver.current_url, self.driver)
            # sleep(0.5)
            # driver.execute_script(
            #     'parent.postMessage(JSON.stringify({eventId:"challenge-complete",payload:{sessionToken:"' + token + '"}}),"*")')
            # self.print("&aCaptcha Solved")
            # self.update()
            # self.fElement(driver, By.ID, 'idBtn_Back').click()
            self.print(f'Email Created in {str(self.Timer.timer(time())).split(".")[0]}s') if \
                self.config["Common"]['Timer'] else self.print('Email Created')
            eGenerated += 1
            self.Utils.logger(self.email + self.config['EmailInfo']['Domain'], self.password)
            self.update()
            # driver.quit()
        except Exception as e:
            if e == KeyboardInterrupt:
                # driver.quit()
                exit(0)
            self.print("&4Something is wrong | %s" % str(e).split("\n")[0].strip())
        finally:
            self.print("finaly")
            # driver.quit()

    def run(self):
        # Run Script Function
        self.print('&bCoded with &c<3&b by MatrixTeam')
        self.generate_info()
        self.CreateEmail(driver=webdriver.Chrome(options=self.options, desired_capabilities=self.capabilities))
        # with suppress(IndexError):
        #     while True:
        #             self.generate_info()
        #             proxy = choice(self.proxies)  # Select Proxy
        #             if not self.check_proxy(proxy):
        #                 self.print("&c%s &f| &4Invalid Proxy&f" % proxy)
        #                 self.proxies.remove(proxy)
        #                 continue
        #             self.print(proxy)
        #             self.options.add_argument("--proxy-server=http://%s" % proxy)
        #             self.CreateEmail(driver=webdriver.Chrome(options=self.options, desired_capabilities=self.capabilities))
        # self.print("&4No Proxy Available, Exiting!")



if __name__ == '__main__':
    eGen().run()
