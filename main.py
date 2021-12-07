from datetime import datetime
from requests import Session
from bs4 import BeautifulSoup
from time import sleep
from base64 import b64decode


class CPEBot:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
            }
        )
        self.isLogin = False
        self.isSuccess = False
        self.user_data = {}

    def login(self):
        payload = {
            "isFirst": "no",
            "myLevel": "on",
            "id": self.username,
            "pw": self.password,
        }

        while not self.isLogin:
            try:
                r = self.session.get("https://cpe.cse.nsysu.edu.tw/cpe/", timeout=10)
            except TimeoutError:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            captcha = soup.select_one("#new_captcha img").get("src")

            try:
                r1 = self.session.get(f"https://cpe.cse.nsysu.edu.tw/cpe/{captcha}")
            except TimeoutError:
                continue

            with open("captcha.jpg", "wb+") as f:
                f.write(r1.content)

            captcha_code = input("驗證碼: ")

            try:
                r = self.session.post(
                    "https://cpe.cse.nsysu.edu.tw/cpe/",
                    data={**payload, "captcha": captcha_code},
                    allow_redirects=False,
                )
            except TimeoutError:
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            if r.is_redirect:  # login success
                self.isLogin = True
                r = self.session.get("https://cpe.cse.nsysu.edu.tw/cpe/newest")
                soup = BeautifulSoup(r.text, "html.parser")

                self.user_data["myGrade"] = soup.select_one("select[name='myGrade'] option[selected]").get("value")
                self.user_data["myDepartment"] = soup.select_one("input[name='myDepartment']").get("value")
                self.user_data["mySchoolID"] = soup.select_one("select[name='mySchoolID'] option[selected]").get(
                    "value"
                )
                self.user_data["optionsRadios1"] = 1 if soup.select_one("#optionsRadios1[checked]") else 0

                success_alert = soup.select_one(".alert-success")
                if success_alert:
                    print("已報名過了!", success_alert.text.strip())
                    return

            else:
                for error in soup.select(".text-error strong"):
                    print(error.text.strip())

    def apply(self, school_id: int):
        while not self.isSuccess:
            try:
                r = self.session.post(
                    "https://cpe.cse.nsysu.edu.tw/cpe/newest",
                    data={
                        **self.user_data,
                        "isSend": "yes",
                        "site": school_id,
                        "yesExam": "報名",
                    },
                    timeout=3,
                )
            except TimeoutError:
                continue

            if r.is_permanent_redirect:
                self.login()
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            success_alert = soup.select_one(".alert-success")
            error_alert = soup.select_one(".alert-error")
            if success_alert:
                self.isSuccess = True
                print(success_alert.text.strip())

            if error_alert:
                print(error_alert.text.strip())

            sleep(3)


bot = CPEBot("username", "password")
bot.login()
bot.apply(33)
