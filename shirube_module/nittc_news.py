"""

basic_module.py依存

"""

import re
import requests
from bs4 import BeautifulSoup


# 苫小牧高専のホームページから最新のお知らせを取得、保存されているお知らせの日付より新しい場合タイトルと内容の一部を返す
def NewsCheck():
    # 前回取得したニュースの日付を読み込む
    f = open("newest_news.txt", 'r', encoding='utf_8')
    have_date = f.read().split(',')
    f.close()

    # ホームページから最新のニュースを取得
    news_url = "https://www.tomakomai-ct.ac.jp/news"
    html = requests.get(news_url)
    soup = BeautifulSoup(html.content, "html.parser")
    link_title = soup.select_one("[class='post clearfix']")

    # 最新のニュースの日付を抽出
    got_date = re.split("[年月日]", link_title.select_one(".daytime").get_text())

    # 取得済みのニュースよりも最新のニュースの日付のほうが新しいとき
    if got_date != "":
        if basic_module.CheckDeadline(have_date,got_date):

            # 最新のニュースの日付を更新
            f = open("newest_news.txt", 'w')
            f.write(got_date[0] + ',' + got_date[1] + ',' + got_date[2])
            f.close()

            # 送信するメッセージを作成
            rtn_news = "苫小牧高専ホームページのお知らせが更新されました。\n詳細は該当ページにて確認してください。(https://www.tomakomai-ct.ac.jp/news)\n======================================\n"
            rtn_news += link_title.select_one(".title").get_text() + '\n'
            rtn_news += link_title.select_one("[class='inner clearfix'] > p").get_text() + '\n'
            return rtn_news

    # 別にそんなことないとき
    return None


async def SendNews(channel):
    news = NewsCheck()
    if not news == None:
        print(news)
        await channel.send(news)