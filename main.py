from asyncore import write
from datetime import datetime
import logging
from requests import Session
from bs4 import BeautifulSoup
from time import sleep
from logging import getLogger


class CPEBot:
    def __init__(self, username: str, password: str):
        self.logger = getLogger(__name__)
        self.username = username
        self.password = password
        self.session = Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
            }
        )
        self.user_data = {}

    def login(self):
        payload = {
            "isFirst": "no",
            "myLevel": "on",
            "id": self.username,
            "pw": self.password,
        }

        while True:
            try:
                res = self.session.get("https://cpe.cse.nsysu.edu.tw/cpe/", timeout=600)
                self.logger.info(f"[Login] Get {res.status_code}")
            except:
                continue

            break

        soup = BeautifulSoup(res.text, "html.parser")
        captcha = soup.select_one("#new_captcha img").get("src")

        # fetch captcha
        while True:
            try:
                resCaptcha = self.session.get(
                    f"https://cpe.cse.nsysu.edu.tw/cpe/{captcha}", timeout=600
                )
                self.logger.info(f"[Login] Get Captcha {res.status_code}")
            except:
                continue

            break

        with open("captcha.jpg", "wb+") as f:
            f.write(resCaptcha.content)

        captcha_code = input("驗證碼: ")

        while True:
            try:
                res = self.session.post(
                    "https://cpe.cse.nsysu.edu.tw/cpe/",
                    data={**payload, "captcha": captcha_code},
                    allow_redirects=False,
                    timeout=600,
                )
                self.logger.info(f"[Login] Post Data {res.status_code}")
            except:
                continue

            break

        if res.is_redirect:  # login success
            while True:
                try:
                    res = self.session.get(
                        "https://cpe.cse.nsysu.edu.tw/cpe/newest", timeout=600
                    )
                    self.logger.info(f"[Login] Get Newest {res.status_code}")
                except:
                    continue

                break

            soup = BeautifulSoup(res.text, "html.parser")
            self.user_data["myGrade"] = soup.select_one(
                "select[name='myGrade'] option[selected]"
            ).get("value")
            self.user_data["myDepartment"] = soup.select_one(
                "input[name='myDepartment']"
            ).get("value")
            self.user_data["mySchoolID"] = soup.select_one(
                "select[name='mySchoolID'] option[selected]"
            ).get("value")
            self.user_data["optionsRadios1"] = (
                1 if soup.select_one("#optionsRadios1[checked]") else 0
            )

        else:
            for err in soup.select(".text-error strong"):
                self.logger.error(err)

    def apply(self, school_id: int):
        while True:
            try:
                res = self.session.post(
                    "https://cpe.cse.nsysu.edu.tw/cpe/newest",
                    data={
                        **self.user_data,
                        "isSend": "yes",
                        "site": school_id,
                        "yesExam": "報名",
                    },
                    timeout=600,
                )
                self.logger.info(f"[Login] PostData {res.status_code}")
            except:
                continue

            if res.is_permanent_redirect:
                self.login()
                continue

            soup = BeautifulSoup(res.text, "html.parser")

            success_alert = soup.select_one(".alert-success")
            error_alert = soup.select_one(".alert-error")

            if success_alert:
                self.logger.info(f"[Apply] {success_alert.text.strip()}")
                break

            if error_alert:
                self.logger.error(f"[Apply] {error_alert.text.strip()}")

            sleep(3)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    bot = CPEBot("username", "password")
    bot.login()
    bot.apply(33)
