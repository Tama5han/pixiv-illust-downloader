import json
import os
import pickle
import re
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from glob import glob
from selenium import webdriver
from time import sleep
from tqdm import tqdm, trange





class PixivIllustDownloader:

    # URLs

    PIXIV_URL = "https://www.pixiv.net/"
    LOGIN_URL = "https://accounts.pixiv.net/login"
    PXIMG_URL = "https://i.pximg.net/img-original/img/"


    # ダウンロードで使用

    HEADERS = {"Referer": "https://www.pixiv.net/"}
    STREAM = True



    def __init__(self, chromedriver_path, cookies_path="./pixiv_cookies.pkl"):

        self.chromedriver_path = chromedriver_path
        self.cookies_path = cookies_path



    def login(self, username=None, password=None):

        self.driver = webdriver.Chrome(self.chromedriver_path)

        if os.path.exists(self.cookies_path):
            self.access_pixiv()
            sleep(1)
            self.load_cookies()
            self.access_pixiv()
            sleep(1)

        else:
            assert isinstance(username, str)
            assert isinstance(password, str)

            self.access_login()
            sleep(1)
            self.input_username(username)
            self.input_password(password)
            sleep(1)
            self.click_login()
            sleep(2)


    def quit(self):
        self.save_cookies()
        self.driver.quit()



    def access_pixiv(self):
        self.driver.get(self.PIXIV_URL)

    def access_login(self):
        self.driver.get(self.LOGIN_URL)

    def access_userpage(self, user_id):
        self.driver.get(self.PIXIV_URL + f"users/{user_id}/artworks")

    def access_artworks(self, artwork_id):
        self.driver.get(self.PIXIV_URL + f"artworks/{artwork_id}")


    # 以下の 3 つはログインページを開いている状態で使用

    def input_username(self, username):
        input_text(self.driver, "//input[@autocomplete='username webauthn']", username)

    def input_password(self, password):
        input_text(self.driver, "//input[@autocomplete='current-password webauthn']", password)

    def click_login(self):
        click_button(self.driver, "//button[contains(text(), 'ログイン')]")


    # 作品ページを開いている状態で使用

    def click_view_all(self):
        click_button(self.driver, "//div[contains(text(), 'すべて見る')]")



    def load_cookies(self):
        cookies = pickle.load(open(self.cookies_path, "rb"))
        [ self.driver.add_cookie(cookie) for cookie in cookies ]

    def save_cookies(self):
        cookies = self.driver.get_cookies()
        pickle.dump(cookies, open(self.cookies_path, "wb"))


    # ユーザーページ（URL: https://www.pixiv.net/users/*/artworks）を開いている状態で使用

    def get_user(self):

        soup = get_soup(self.driver)
        body = soup.find("body")


        # ユーザー名

        h1 = body.find("h1")
        user_name = h1.text.strip() if h1 is not None else "Noname"


        # ユーザー ID

        current_url = self.driver.current_url
        user_id = int(re.search(r"[0-9]+", current_url).group())

        return user_name, user_id



    def get_all_artworks(self, user_id=None, init_access=True, verbose=True):
        """
        指定したユーザーの全作品 ID とそれらのタイトルを取得する。
        """

        if init_access:

            assert user_id is not None

            self.access_userpage(user_id)
            sleep(1)


        soup = get_soup(self.driver)
        body = soup.find("body")


        # 作品数

        div = body.find("div", class_="sc-1mr081w-0 kZlOCw")
        number_of_artworks = int(div.text)


        # ページ数（1 ページにつき最大 48 作品）

        number_of_pages = (number_of_artworks - 1) // 48 + 1


        # ページごとに作品を抽出して統合

        if verbose:
            pages = trange(1, number_of_pages + 1)
        else:
            pages = range(1, number_of_pages + 1)


        all_artworks = dict()
        userpage_url = self.PIXIV_URL + f"users/{user_id}/artworks"

        for page in pages:
            self.driver.get(userpage_url + f"?p={page}")
            sleep(1)

            all_artworks |= self.get_artworks_on_page()

        return all_artworks


    def get_artworks_on_page(self):
        """
        開かれているページの全作品 ID とそれらのタイトルを取得する。
        """

        soup = get_soup(self.driver)
        body = soup.find("body")

        artwork_ids = []
        titles = []

        href_pattern = re.compile(r"^/artworks/[0-9]+$")
        id_pattern = re.compile(r"[0-9]+$")

        for a in body.find_all("a", href=href_pattern):

            children = a.find_all()

            if len(children) > 0: continue

            href = a.get("href")
            artwork_id = int(id_pattern.search(href).group())

            artwork_ids.append(artwork_id)
            titles.append(a.text.strip())

        return dict(zip(artwork_ids, titles))



    def get_illust_urls(self, artwork_id):
        """
        指定した作品に含まれる全イラスト URL を取得する。
        """

        artwork_id = str(artwork_id)
        artwork_url = self.PIXIV_URL + "artworks/" + artwork_id

        response = self._requests_get(artwork_url)
        soup = BeautifulSoup(response.text, "html.parser")

        meta = soup.find(id="meta-preload-data")
        contents = json.loads(meta.get("content"))

        illust_data = contents["illust"][artwork_id]["userIllusts"][artwork_id]


        # 作品タイトル・イラストの枚数・更新日時の取得

        title = illust_data["title"]
        number_of_pages = illust_data["pageCount"]

        update_date = datetime.fromisoformat(illust_data["updateDate"])
        update_date = update_date.strftime("%Y/%m/%d/%H/%M/%S")


        # イラスト URL の作成

        url_prefix = self.PXIMG_URL + f"{update_date}/{artwork_id}"
        illust_urls = [ url_prefix + f"_p{i}.jpg" for i in range(number_of_pages) ]


        return title, illust_urls



    def get_illust_urls_on_page(self):
        """
        開かれている作品に含まれる全イラスト URL を取得する。
        """

        soup = get_soup(self.driver)
        body = soup.find("body")


        # 作品タイトル

        h1 = body.find("h1")
        title = h1.text.strip() if h1 is not None else "Notitle"


        # イラスト URL

        format_pattern = re.compile(r"(jpg|jpeg|png)$")
        illust_urls = [ a.get("href") for a in body.find_all("a", href=format_pattern) ]


        return title, illust_urls



    def get_illust_urls_on_booth(self):
        """
        開かれている Booth の参考用イラスト URL を取得する。
        """

        soup = get_soup(self.driver)
        body = soup.find("body")


        # 作品タイトル

        h2 = body.find("h2")
        title = h2.text.strip() if h2 is not None else "No_title"


        # 参考用イラスト URL

        div_attrs = {"data-slick-index": re.compile(r"[0-9]+")}
        img_attrs = {"data-origin": re.compile(r".")}

        illust_urls = []

        for div in body.find_all("div", attrs=div_attrs):

            if "slick-cloned" in div.get("class"): continue

            img = div.find("img", attrs=img_attrs)

            if img is not None:
                illust_urls.append(img.get("data-origin"))


        return title, illust_urls



    def download_illusts(self, illust_urls, save_dir=".", verbose=True):
        """
        指定した URL のイラストをダウンロードして保存する。
        """

        # 一旦、JPEG に変換

        extension = re.compile(r"\.[^\.]+$")
        illust_urls = [ extension.sub(".jpg", url) for url in illust_urls ]


        if verbose:
            urls = tqdm(illust_urls, desc="Downloading")
        else:
            urls = illust_urls


        for illust_url in urls:

            illust, illust_format = self.download_illust(illust_url)
            sleep(0.7)

            number_of_illusts = len(glob(save_dir + "/*"))

            save_file = save_dir + f"/illust_{number_of_illusts:0>3}.{illust_format}"

            with open(save_file, "wb") as f:
                f.write(illust)


    def download_illust(self, illust_url):
        """
        指定した URL のイラストをダウンロードする。
        """

        # .jpg

        response = self._requests_get(illust_url)
        sleep(0.3)

        if response.status_code == 200:
            return response.content, "jpg"


        # .png

        response = self._requests_get(illust_url[:-3] + "png")
        sleep(0.3)

        if response.status_code == 200:
            return response.content, "png"


        # .jpeg

        response = self._requests_get(illust_url[:-3] + "jpeg")
        sleep(0.3)

        if response.status_code == 200:
            return response.content, "jpg"


        # 上記以外はエラー

        response.raise_for_status()



    def _requests_get(self, url):
        return requests.get(url, headers=self.HEADERS, stream=self.STREAM)







def click_button(driver, xpath):
    driver.find_element_by_xpath(xpath).click()


def input_text(driver, xpath, text):
    text_box = driver.find_element_by_xpath(xpath)
    text_box.send_keys(text)


def get_soup(driver):
    html = driver.page_source.encode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    return soup
