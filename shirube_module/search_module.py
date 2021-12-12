import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote


# WikipediaやGoogleのURLの検索ワード要素を作成 
def MakeSearchWords(count,tokens):
    print(tokens)
    returnchar = ""
    if count >= 2:
        # 「OOでググって」などの場合
        if tokens[count-1] == "と" or tokens[count-1] == "で" or tokens[count-1] == "の":
            for i in range(count-1):
                returnchar += tokens[i]
        # 「OOとは」などの場合
        else:
            for i in range(count):
                returnchar += tokens[i]
    elif count == 1:
        returnchar = tokens[0]
    else:
        return None

    return returnchar.replace(" ","+").replace("　","+")


# googleの検索ページをスクレイピングし、送信するメッセージを作成
# searchwordsはMakeSearchWordsの返り値
def SearchGoogle(searchwords):
    if searchwords != None:
        try:
            # googleの検索ページを取得、検索結果を取得
            load_url = "https://www.google.com/search?q=" + searchwords
            print(load_url)
            html = requests.get(load_url)
            soup = BeautifulSoup(html.content, "html.parser")
            link_title = soup.select(".kCrYT > a")

            # 検索上位サイトのタイトルとURLを取得する
            # BeautifulSoupのfindメソッドは上から見つけていきます
            length = len(link_title) if len(link_title) < 3 else 3 
            result = "了解いたしました。以下が検索結果上位" + str(length) + "サイトです。\n======================================\n"
            for i in range(length):
                result += link_title[i].find("h3").get_text() + "\n" # サイトのタイトル

                # サイトのURL（余計な文字列がくっつくことがあるので取り除く）
                url = unquote(link_title[i].get("href").replace("/url?q=",""))
                result += url[0:url.find("&sa=U")] + "\n\n" # こっちは標準ライブラリのほうのfindメソッド
            return result

        # なぜかたまにエラー吐きます。原因は不明
        except Exception as e:
            f = open('bot_error.txt', 'w', encoding='UTF-8')
            f.write("type : " + str(type(e)) + "\n")
            f.write("type : " + str(e.args) + "\n")
            f.write("type : " + str(e) + "\n")
            f.write("source : " + str(soup) + "\n")
            f.close()
            return "申し訳ありません。検索結果を取得できませんでした。（" + str(type(e)) + "）\nエラーの詳しい内容はbot_error.txtを参照してください。"

    else:
        return "検索対象を指定してください。"


# wikipediaの検索ページをスクレイピングし、送信するメッセージを作成
# ほとんどSearchGoogle関数と同じ
def SearchWikipedia(searchwords):
    if searchwords != None:
        result = ""
        result_url = "https://ja.wikipedia.org/w/index.php?search=" + searchwords
        html = requests.get(result_url)
        soup = BeautifulSoup(html.content, "html.parser")

        # 完全一致するページがないとき見出しが「検索結果」となる
        if soup.select(".firstHeading")[0].get_text() == "検索結果":
            result += "検索の結果wikipediaにそのような項目はありませんでした。\nwikipedia検索結果上位に該当する項目は以下です。\n======================================\n"
            link_title = soup.select("div.mw-search-result-heading > a")
            length = len(link_title) if len(link_title) < 3 else 3

            # 検索の候補に1つもページがないとき
            if length == 0:
                result = "wikipediaにそのような項目はありませんでした。\nwikipedia検索においても該当するページはありませんでした。\n検索ワードを変えて試してみてはいかがでしょうか。"
            for i in range(length):
                result += link_title[i].get("title") + "\n"
                print(link_title[i].get("href"))
                result += "https://ja.wikipedia.org" + unquote(link_title[i].get("href")) + "\n\n"

        # 完全一致するページがあるときはタイトルリンク原文一段落を返す
        else:
            result += "こちらのリンクにて参照してください。\n======================================\n"
            result += soup.select(".firstHeading")[0].get_text() + "\n"
            exp_texts = soup.select(".mw-parser-output > p")

            # 原文一段落を取得（pタグはなにもないことがある）
            exp_text = exp_texts[0]
            for i in exp_texts:
                if i.get_text().replace("\n", "") != "":
                    exp_text = i
                    break
            result += exp_text.get_text()
            result += "\n参照元\n" + result_url.replace("%","%%")
        return result

    else:
        return "検索対象を指定してください。"