# PixivAPI クラス

[pixiv](https://www.pixiv.net/) からイラストをダウンロードする用のクラスです。



## メソッド

### `__init__(chromedriver_path, cookies_path="pixiv_cookies.pkl")`

インスタンス作成時に実行されるメソッドです。ChromeDriver を起動します。

- `chromedriver_path` : ChromeDriver のファイルパス
- `cookies_path` : Cookie 情報のファイルパス（読み込み・保存には pickle を使用）


### `login(username=None, password=None)`

pixiv へログインします。Cookie 情報がある場合はそれを参照するので、引数は不要です。

- `username` : メールアドレスまたは pixiv ID
- `password` : パスワード


### `quit()`

Cookie 情報を保存して ChromeDriver を終了します。


### `access_user_page(user_id)`

指定したユーザーのページを開きます。

- `user_id` : ユーザー ID（<https://www.pixiv.net/users/***/artworks> の \*\*\* 部分）


### `access_artworks(artwork_id)`

指定した作品ページを開きます。

- `artwork_id` : 作品 ID（<https://www.pixiv.net/artworks/***> の \*\*\* 部分）


### `get_user()`

開いているページのユーザー名とユーザー ID を取得します。


### `get_all_artworks(user_id, verbose=True, init_access=True)`

指定したユーザーの全作品 ID を取得します。返り値は作品 ID をキー、作品タイトルを値とする dict オブジェクトです。

- `user_id` : ユーザー ID
- `verbose` : プログレスバーを表示するかどうか
- `init_access` : 最初にユーザーのページへ移動するかどうか


### `get_illust_urls(artwork_id)`

指定した作品のイラスト URL を取得します。返り値は 2 成分のタプルで、第 0 要素が作品タイトル、第 1 要素が URL のリストです。

- `artwork_id` : 作品 ID


### `download_illusts(illust_urls, save_dir=".", verbose=True)`

指定した URL のイラストをダウンロードします。

- `illust_urls` : イラスト URL のリスト（上記の `get_illust_urls` メソッドで取得できる URL）
- `save_dir` : ダウンロードしたイラストの保存先
- `verbose` : プログレスバーを表示するかどうか



## 使用例

あるユーザー（ID: 000000）の全イラストをダウンロードする場合、以下のようにします。ただし、作品ごとにフォルダを分けています。

```python
import os
import re

from time import sleep
from tqdm import tqdm

from pixivlib import PixivAPI


pxv = PixivAPI("path/to/chromedriver")
pxv.login("<username>", "<password>")


# 全作品 ID の取得

artworks = pxv.get_all_artworks(user_id=000000)


# 作品ごとのイラスト URL の取得

illust_data = []

for artwork_id in tqdm(artworks.keys(), total=len(artworks)):
    title, illust_urls = pxv.get_illust_urls(artwork_id)
    sleep(1)

    illust_data.append([re.sub(r'[\\/:*?"<>|]+', "_", title), illust_urls])


# イラストのダウンロード

for title, illust_urls in tqdm(illust_data):
    save_dir = "./" + title
    if not os.path.exists(save_dir): os.mkdir(save_dir)

    pxv.download_illusts(illust_urls, save_dir, verbose=False)
    sleep(1)


pxv.quit()

```
