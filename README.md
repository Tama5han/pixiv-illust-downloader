# PixivIllustDownloader

[pixiv](https://www.pixiv.net/) からイラストをダウンロードする用のクラスです。コピペして使用してください。現時点では JPG と PNG のみに対応しています。

自分用に作成したものであるため、基本的かつ単純なメソッドしか用意していません。より高度な機能が欲しい場合は使用者自身が機能を実装するか、他のライブラリ（[pixivpy](https://github.com/upbit/pixivpy) 等）をご使用ください。




## 主な機能

- ユーザー ID を入力して、そのユーザーの全作品 ID を取得する。
- 作品 ID を入力して、その作品に含まれる全イラスト URL を取得する。
- イラスト URL を入力して、そのイラストをダウンロードする。




## メソッド

### \_\_init\_\_(chromedriver\_path, cookies\_path="pixiv\_cookies.pkl")

- **chromedriver\_path** : ChromeDriver のファイルパス
- **cookies\_path** : Cookie 情報のファイルパス（読み込み・保存には pickle を使用）

```python
from pixivlib import PixivIllustDownloader

px = PixivIllustDownloader("/path/to/chromedriver.exe")
```



### login(username=None, password=None)

ChromeDriver を起動して pixiv にログインします。Cookie 情報がある場合、それを参照するので引数は不要です。

- **username** : メールアドレスまたは pixiv ID
- **password** : パスワード

```python
# Cookie 情報が無い場合
px.login("<username>", "<password>")

# Cookie 情報がある場合
px.login()
```



### quit()

Cookie 情報を保存して ChromeDriver を終了します。Cookie 情報は cookies_path に保存されます。

```python
px.quit()
```



### access\_userpage(user\_id)

指定したユーザーのページを開きます。

- **user\_id** : ユーザー ID（<https://www.pixiv.net/users/*/artworks> の \* 部分）

```python
# ユーザー（ID: 0123456）にアクセスする場合
px.access_userpage(0123456)
```



### access\_artworks(artwork\_id)

指定した作品ページを開きます。

- **artwork\_id** : 作品 ID（<https://www.pixiv.net/artworks/*> の \* 部分）

```python
# 作品（ID: 098765）にアクセスする場合
px.access_artworks(098765)
```



### get\_user()

ユーザーページ（<https://www.pixiv.net/users/*/artworks>）のユーザー名とユーザー ID を取得します。

```python
# https://www.pixiv.net/users/0123456/artworks を開いている状態で実行
user_name, user_id = px.get_user()

print("name:", user_name)
print("id:", user_id)
# name: Username
# id: 0123456
```



### get\_all\_artworks(user\_id=None, init\_access=True, verbose=True)

指定したユーザーの全作品 ID とそれらのタイトルを取得します。返り値は作品 ID をキー、タイトルを値とする dict オブジェクトです。

- **user\_id** : ユーザー ID
- **init\_access** : 最初にユーザーのページへ移動するかどうか
- **verbose** : プログレスバーを表示するかどうか

```python
# ユーザー（ID: 0123456）の全作品を取得したい場合
artworks = px.get_all_artworks(user_id=0123456)

print(artworks)
# {098765: 'Title_1', 043210: 'Title2', ...}

# 既にユーザーページを開いている場合
artworks = px.get_all_artworks()

print(artworks)
# {098765: 'Title_1', 043210: 'Title2', ...}
```



### get\_illust\_urls(artwork\_id)

指定した作品に含まれる全イラストの URL を取得します。返り値は 2 成分のタプルで、第 0 要素が作品タイトル、第 1 要素が URL のリストです。

- **artwork\_id** : 作品 ID

```python
# 作品（ID: 098765）の場合
title, illust_urls = px.get_illust_urls(098765)

print("title:", title)
# title: Title_1

print(illust_urls)
# ['https://i.pximg.net/img-original/img/2024/01/01/01/01/01/098765_p0.jpg',
#  'https://i.pximg.net/img-original/img/2024/01/01/01/01/01/098765_p1.jpg',
#  ...]
```


### download\_illusts(illust\_urls, save\_dir=".", verbose=True)

指定した URL のイラストをダウンロードします。ダウンロードしたイラストは、"illust_000.jpg" のようなファイル名で保存されます。

- **illust\_urls** : イラスト URL のリスト
- **save\_dir** : ダウンロードしたイラストの保存先
- **verbose** : プログレスバーを表示するかどうか

```python
# ディレクトリ ./illusts に保存する場合
px.download_illusts(illust_urls, save_dir="./illusts")
```



## 特定ユーザーの全イラストをダウンロードする。

作品ごとにディレクトリを分けています。

```python
import os
import re

from time import sleep
from tqdm import tqdm

from pixivlib import PixivIllustDownloader


chromedriver_path = "/path/to/chromedriver.exe"

# ログインするアカウント
username = "<username>"
password = "<password>"

# イラストをダウンロードしたいユーザー ID
user_id = 0123456


px = PixivIllustDownloader(chromedriver_path)
px.login(username, password)


# 全作品 ID の取得

artworks = px.get_all_artworks(user_id)
artworks_ids = sorted(artworks.keys())


# 作品ごとにイラスト URL を取得

title_list = []
urls_list = []

for artwork_id in tqdm(artworks_ids):

    title, illust_urls = px.get_illust_urls(artwork_id)
    sleep(1)

    # ディレクトリに使用できない文字の削除
    title = re.sub(r'[\\/:*?"<>|]+', "_", title)

    title_list.append(title)
    urls_list.append(illust_urls)


# イラストのダウンロード

for title, illust_urls in tqdm(zip(title_list, urls_list), total=len(artworks_ids)):

    # ディレクトリの作成
    save_dir = "./" + title
    if not os.path.exists(save_dir): os.mkdir(save_dir)

    px.download_illusts(illust_urls, save_dir, verbose=False)


px.quit()
```



## 備考

- 作品 ID が既知の場合、イラスト URL の取得やイラストのダウンロードに ChromeDriver は不要です。従って、上記の例の px.quit() を［全作品 ID の取得］の直後に実行しても問題ありません。
- 現時点では、各イラストのダウンロードの間に約 1 秒のインターバルを設けています。
- 例外処理は特にしていないので、エラーが出た場合はその都度、使用者が対応する必要があります。
