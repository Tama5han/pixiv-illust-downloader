# pixivlib.py

[pixiv](https://www.pixiv.net/) にアクセスしてイラストをダウンロードする。



## 使用方法

### pixiv へのログイン

- PixivAPI のインスタンス作成時に ChromeDriver のパスを渡す。
- login メソッドにログインするユーザー名（またはメールアドレス）とパスワードを渡す。
- 1 回目の終了時に Cookie 情報を保存しておけば、2 回目以降はユーザー名とパスワードが不要。

```python
from pixivlib import PixivAPI

pxv = PixivAPI("path/to/chromedriver.exe")
pxv.login(username="<username>", password="<password>")
```


### 終了

- close メソッドを使うことで ChromeDriver 終了時に Cookie 情報を保存する。
- 2 回目以降のログインでは保存した Cookie 情報を参照するので、ユーザー名とパスワードの入力が不要になる。

```python
pxv.close()
```


### 作品 ID の取得

- 作品 ID を取得したいユーザーの ID（<https://www.pixiv.net/users/******> の ****** 部分）を入力する。
- 返り値は作品 ID をキー、作品タイトルを値とする dict オブジェクト。

```python
artworks = pxv.get_all_artworks(user_id=0123456)
```


### イラストのダウンロード

- get_illust_urls メソッドにダウンロードしたい作品 ID を渡して、イラストの URL を取得する。
- 取得した URL からイラストをダウンロードする。

```python
import os

title, urls = pxv.get_illust_urls(artwork_id=0123456)

save_dir = "./" + title

if not os.path.exists(save_dir):
    os.mkdir(save_dir)

pxv.download_illusts(urls, save_dir=save_dir)
```
