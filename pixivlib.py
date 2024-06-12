import json
import os
import pickle
import re
import requests

from bs4 import BeautifulSoup
from glob import glob
from selenium import webdriver
from time import sleep
from tqdm import tqdm, trange





class PixivAPI:
    """
    pixiv からイラストをダウンロードする用のクラス
    """

    # メインページ
    MAIN_URL = "https://www.pixiv.net/"

    # ログインページ
    LOGIN_URL = (
        "https://accounts.pixiv.net/login"
        "?return_to=https://www.pixiv.net/"
        "&lang=ja"
        "&source=pc"
        "&view_type=page")

    # ダウンロード時に使用
    HEADERS = {"Referer": "https://www.pixiv.net/"}
    STREAM = True

    # オリジナルのイラスト URL のプレフィックス
    ILLUST_PREFIX = "https://i.pximg.net/img-original/img/"



    def __init__(self, chromedriver_path, cookies_path="./pixiv_cookies.pkl"):
        """
        ChromeDriver を起動する。
        """
        self.driver = webdriver.Chrome(chromedriver_path)
        self.cookies_path = cookies_path



    def login(self, username=None, password=None):
        """
        pixiv にログインする。
        """
        if os.path.exists(self.cookies_path):
            self.access_main()
            self.load_cookies()
            self.access_main()

        else:
            assert isinstance(username, str)
            assert isinstance(password, str)

            self.access_login()
            self.input_username(username)
            self.input_password(password)
            self.click_login()



    def quit(self):
        """
        Cookie 情報を保存して ChromeDriver を終了する。
        """
        self.save_cookies()
        self.driver.quit()



    def access_main(self):
        """
        メインページを開く。
        """
        self.driver.get(self.MAIN_URL)
        sleep(1)


    def access_login(self):
        """
        ログインページを開く。
        """
        self.driver.get(self.LOGIN_URL)
        sleep(1)


    def access_user_page(self, user_id):
        """
        指定したユーザーページを開く。
        """
        self.driver.get(self.MAIN_URL + f"users/{user_id}/artworks")
        sleep(1)


    def access_artworks(self, artwork_id):
        """
        指定した作品ページを開く。
        """
        self.driver.get(self.MAIN_URL + f"artworks/{artwork_id}")
        sleep(1)



    def input_username(self, username):
        """
        ログイン画面でユーザー名を入力する。
        """
        input_text(self.driver, "//input[@autocomplete='username webauthn']", username)
        sleep(0.5)


    def input_password(self, password):
        """
        ログイン画面でパスワードを入力する。
        """
        input_text(self.driver, "//input[@autocomplete='current-password webauthn']", password)
        sleep(0.5)


    def click_login(self):
        """
        ログイン画面で【ログイン】をクリックする。
        """
        click_button(self.driver, "//button[contains(text(), 'ログイン')]")
        sleep(2)


    def click_view_all(self):
        """
        作品ページが開かれている状態で【すべて見る】をクリックする。
        """
        try:
            click_button(self.driver, "//div[contains(text(), 'すべて見る')]")
        except:
            pass
        sleep(1)



    def load_cookies(self):
        """
        Cookie 情報を読み込む。
        """
        cookies = pickle.load(open(self.cookies_path, "rb"))
        [ self.driver.add_cookie(cookie) for cookie in cookies ]


    def save_cookies(self):
        """
        Cookie 情報を保存する。
        """
        cookies = self.driver.get_cookies()
        pickle.dump(cookies, open(self.cookies_path, "wb"))



    def get_user(self):
        """
        開かれているユーザーページのユーザー名と ID を取得する。
        """
        soup = get_soup(self.driver)
        body = soup.find("body")

        # ユーザー名
        h1 = body.find("h1")
        user_name = h1.text.strip() if h1 is not None else "Noname"

        # ユーザー ID
        current_url = self.driver.current_url
        user_id = int(re.search(r"[0-9]+", current_url).group())

        return user_name, user_id



    def get_all_artworks(self, user_id, verbose=True, init_access=True):
        """
        指定したユーザーの全作品 ID を取得する。
        """
        if init_access: self.access_user_page(user_id)

        soup = get_soup(self.driver)
        body = soup.find("body")

        # 作品数
        div = body.find("div", class_="sc-1mr081w-0 kZlOCw")
        number_of_artworks = int(div.text)

        # ページ数（1 ページにつき最大 48 作品から逆算）
        number_of_pages = (number_of_artworks - 1) // 48 + 1


        if verbose:
            pages = trange(1, number_of_pages + 1)
        else:
            pages = range(1, number_of_pages + 1)

        all_artworks = dict()
        user_page = self.MAIN_URL + f"users/{user_id}/artworks"

        for page in pages:
            self.driver.get(user_page + f"?p={page}")
            sleep(2)

            all_artworks |= self.get_artworks_on_page()

        return all_artworks


    def get_artworks_on_page(self):
        """
        開かれているページの全作品 ID を取得する。
        """
        soup = get_soup(self.driver)
        body = soup.find("body")

        artwork_ids = []
        titles = []
        pattern = re.compile(r"^/artworks/[0-9]+$")

        for a in body.find_all("a", href=pattern):
            children = a.find_all()

            if len(children) > 0: continue

            href = a.get("href")
            artwork_ids.append(int(re.search(r"[0-9]+$", href).group()))
            titles.append(a.text.strip())

        return dict(zip(artwork_ids, titles))



    def get_illust_urls(self, artwork_id):
        """
        指定した作品のイラスト URL を取得する。
        """

        artwork_id = str(artwork_id)
        artwork_url = self.MAIN_URL + "artworks/" + artwork_id


        # 作品タイトル・日時・ページ数の取得

        resp = GET_request(artwork_url, headers=self.HEADERS, stream=self.STREAM)
        soup = BeautifulSoup(resp.text, "html.parser")

        meta = soup.find(id="meta-preload-data")
        contents = json.loads(meta.get("content"))

        artwork_data = contents["illust"][artwork_id]["userIllusts"][artwork_id]

        title = artwork_data["title"]
        number_of_pages = artwork_data["pageCount"]

        thumbnail_url = artwork_data["url"]
        illust_format = thumbnail_url.split(".")[-1]
        date_part = extract_datepart(thumbnail_url)


        # イラスト URL の作成

        url_prefix = self.ILLUST_PREFIX + date_part + "/" + artwork_id
        illust_urls = [ url_prefix + f"_p{page}.{illust_format}" for page in range(number_of_pages) ]


        return title, illust_urls



    def get_illust_urls_on_page(self, artwork_id, init_access=True):
        """
        開いているページのイラスト URL を取得する。
        """

        if init_access:
            self.access_artworks(artwork_id)
            self.click_view_all()

        soup = get_soup(self.driver)
        body = soup.find("body")

        # 作品タイトル
        h1 = body.find("h1")
        title = h1.text.strip() if h1 is not None else "No_title"

        # イラスト URL
        pattern = re.compile(r"(webp|jpg|jpeg|png)$")
        illust_urls = [ a.get("href") for a in body.find_all("a", href=pattern) ]

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
        illust_urls = []
        div_pattern = re.compile(r"slick\-slide")
        img_attrs = {"data-origin": re.compile(".")}
        valid_attrs = {"slick-slide", "slick-current", "slick-active"}

        for div in body.find_all("div", class_=div_pattern):
            class_attrs = set(div.get("class"))
            if not (class_attrs <= valid_attrs): continue

            img = div.find("img", attrs=img_attrs)
            if img is None: continue

            illust_urls.append(img.get("data-origin"))

        return title, illust_urls



    def download_illusts(self, illust_urls, save_dir=".", verbose=True):
        """
        指定したイラストをダウンロードして保存する。
        """
        if verbose:
            urls = tqdm(illust_urls, desc="Downloading")
        else:
            urls = illust_urls

        for illust_url in urls:
            number_of_illusts = len(glob(save_dir + "/*"))
            illust_format = re.search(r"(?<=\.)[^\.]+$", illust_url).group()
            save_file = save_dir + f"/illust_{number_of_illusts:0>3}.{illust_format}"

            illust = self.download_illust(illust_url)
            sleep(1)

            with open(save_file, "wb") as f:
                f.write(illust)


    def download_illust(self, illust_url):
        """
        指定したイラストを URL からダウンロードする。
        """
        resp = GET_request(illust_url, headers=self.HEADERS, stream=self.STREAM)
        return resp.content





def click_button(driver, xpath):
    driver.find_element_by_xpath(xpath).click()


def input_text(driver, xpath, text):
    text_box = driver.find_element_by_xpath(xpath)
    text_box.send_keys(text)


def get_soup(driver):
    html = driver.page_source.encode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    return soup



def GET_request(url, n_trials=5, interval=5, **kwargs):
    for _ in range(n_trials):
        try:
            resp = requests.get(url, **kwargs)
            resp.raise_for_status()
            return resp
        except:
            sleep(interval)
    resp.raise_for_status()



def extract_datepart(thumbnail_url):
    parts = thumbnail_url.split("/")
    return "/".join(parts[-7:-1])
