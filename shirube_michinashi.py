"""

bot運用時の諸注意

・まずクラスごとに「x組」のロールを付与すること。
　時間割教えてもらえないぞ（はぁと

・できればこのbotの使用専用のチャンネルを作っておき、
　他のチャンネルは発言権、閲覧権ともにoffにしておきましょう。
　でないと会話に埋もれてしまったりへんなとこで話しちゃいます。

・時間割は空白区切り、曜日ごとに改行して授業がない日はNoneとしてください。

"""

# 父親に貸してもらい読んでいる「リーダブルコード」、面白いのでおすすめ
# 普通に役立つから絶対読んだほうがいい

import re
import sys
import discord
import requests
import datetime
from discord.ext import tasks
from bs4 import BeautifulSoup
from urllib.parse import unquote
from janome.tokenizer import Tokenizer

f = open("token_and_id.txt", 'r', encoding='utf_8')
tokenid = f.readlines()
f.close()

bot_token = tokenid[0]
channel_id = int(tokenid[1])
intents = discord.Intents.all()
client = discord.Client(intents=intents)

tokenizer = Tokenizer()

days = ["月","火","水","木","金","土","日"]
schedule_files = {"1組":'1組時間割.txt', "2組":'2組時間割.txt', "3組":'3組時間割.txt', "4組":'4組時間割.txt', "5組":'5組時間割.txt', }


# membersリストの中から自分を見つける（≒自分のmember型を返す）
# discord.pyのリファレンス見ても見つからなかったので仕方なく実装
def FindSelfInMembers(members):
    for member in members:
        if member.id == client.user.id:
            return member
    print("client not found")
    return None


# 引数に指定されたテキストチャンネルのリストから発言可能なチャンネルを1つ返す
def SearchChannelToSpeak(text_channels):
    for channel in text_channels:
        self_member = FindSelfInMembers(channel.members)
        if self_member != None:
            if channel.permissions_for(self_member).send_messages:
                return channel
    print("channel not found")
    return None


# 時間割を知らせる文字列を作成し返す
def ScheduleCheck(time_arg, class_name, datalines):
    send_schedule = "本日" + days[time_arg.weekday()] + "曜日の" + class_name + "の時間割です(後期時間割より)。\n======================================\n"
    schedule = datalines[time_arg.weekday()].split()
    if schedule[0] == "none":
        send_schedule = "本日" + days[time_arg.weekday()] + "曜日は" + class_name + "の授業はありません。"
    else:
        for i in range(len(schedule)):
            send_schedule += str(i+1) + "時間目:" + schedule[i] + "\n"
    return send_schedule


# 1時間ごとにNewsCheck()を実行する
@tasks.loop(hours=1.0)
async def news_loop():
    news = NewsCheck()
    if not news == None:
        channel = client.get_channel(channel_id)
        print(news)
        await channel.send(news)


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
        if (have_date[0] < got_date[0] or
            have_date[0] == got_date[0] and have_date[1] < got_date[1] or
            have_date[0] == got_date[0] and have_date[1] == got_date[1] and have_date[2] < got_date[2]
            ):

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
# ほとんどSearchGoogleと同じ
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


# ログイン時処理
# 常駐できるようになれば不要
@client.event
async def on_ready():
    print("logd in\n")
    channel = client.get_channel(channel_id)
    login_message = ""
    login_time = datetime.datetime.now()
    if login_time.hour < 5:
        login_message = "みなさん、こんな真夜中ですが私は対応可能です…ふわあ。"
    elif login_time.hour < 10:
        login_message = "みなさん、おはようございます。私も起床して、対応可能です。今日も頑張って乗り越えましょう！"
    elif login_time.hour < 12:
        login_message = "みなさん、お昼です。あと少しで休み時間です！私も対応可能ですので困ったらぜひ私に頼ってくださいね。"
    elif login_time.hour < 15:
        login_message = "みなさん、正午を回りました。昼食はしっかりとれましたか？現在私は対応可能です。"
    elif login_time.hour < 21:
        login_message = "みなさん、放課後を楽しくお過ごしでしょうか？私にサポートできることがあれば何なりとお申し付けください。"
    else:
        login_message = "みなさん、こんばんは。私は現在対応可能です。夜の時間帯は楽しいですが、くれぐれも夜更かししすぎないように気をつけてくださいね。"

    print(login_message)
    await channel.send(login_message)


# 終了処理
# 常駐できるようになれば不要
async def ExitBot():
    channel = client.get_channel(channel_id)
    logout_message = ""
    logout_time = datetime.datetime.now()
    if logout_time.hour < 5:
        logout_message = "みなさん、私は夜更かししすぎてしまいました…おやすみなさい…:zzz:"
    elif logout_time.hour < 10:
        logout_message = "みなさん、あともう少しだけ寝かせてください…:zzz:"
    elif logout_time.hour < 12:
        logout_message = "みなさん、私はお昼寝します…おやすみなさい…:zzz:"
    elif logout_time.hour < 15:
        logout_message = "お昼ご飯を食べて眠たくなってしまいました…私はお昼寝します…:zzz:"
    elif logout_time.hour < 21:
        logout_message = "みなさん、私は少し早めに眠らせていただきます…おやすみなさい…:zzz:"
    else:
        logout_message = "みなさん、私はそろそろ眠らせていただきます…おやすみなさい…:zzz:"
    print(logout_message)
    await channel.send(logout_message)
    sys.exit()


# サーバーにほかのメンバーが参加したとき
@client.event
async def on_member_join(member):
    channel = SearchChannelToSpeak(member.guild.text_channels)
    channel = client.get_channel(channel_id)
    welcome_message = "\fいらっしゃいませ、" + member.name + "さま！"
    print(welcome_message)
    await channel.send(welcome_message)


# サーバー参加時
@client.event
async def on_guild_join(guild):
    channel = SearchChannelToSpeak(guild.text_channels)
    join_message = "はじめまして。" + guild.name + "のみなさま、廸無 導（みちなし しるべ）と申します。\n文章の解析やその他ちょっとした機能があります。また機能の追加もありますのでぜひご利用くださいませ。"
    print(join_message)
    await channel.send(join_message)


# メッセージ受信時
@client.event
async def on_message(message):
    if message.author.bot:
        return
    inf = await client.application_info()
    sent = ""
    # メンションされたとき
    if client.user in message.mentions:
        sent = "何かお呼びでしょうか？"
    else:
        # 文章が長いと形態素解析にあまりにも時間がかかりすぎてしまう
        if len(message.content) > 300:
            sent = "文章が長すぎます。文章を300字以下にしてください。"
        else:
            if message.content == "//end":
                await ExitBot()
            elif message.content == "//test":
                await SearchChannelToSpeak(message.guild.text_channels).send("test succeeded")
            elif message.content == "//news":
                    news = NewsCheck()
                    if not news == None:
                        print(news)
                        await message.channel.send(news)

            # 文章を形態素解析して単語ごとに分ける
            tokens = []
            for token in tokenizer.tokenize(message.content):
                tokens.append(token.surface)
            print(tokens)

            # 特定の文字列を検索
            # たぶんもっと短くできる
            for i in range(len(tokens)):
                if tokens[i] == "時間割":
                    sent = "クラス別のロールが付与されていません。管理者に問い合わせてください。\n"
                    user_role = message.author.roles
                    for j in user_role:
                        if j.name in schedule_files.keys():
                            f = open(schedule_files[j.name], 'r', encoding='utf_8')
                            sent = ScheduleCheck(datetime.datetime.now(), j.name, f.readlines())
                            f.close()

            for i in range(len(tokens)):
                if tokens[i] == "ありがとう":
                    sent = "礼には及びません、当然のことです。"

            for i in range(len(tokens)):
                if tokens[i] == "意味":
                    word = MakeSearchWords(i,tokens)
                    sent += SearchWikipedia(word)
                    break
                elif len(tokens) > i+1:
                    if tokens[i] == "と" and tokens[i+1] == "は":
                        word = MakeSearchWords(i,tokens)
                        sent += SearchWikipedia(word)
                        break

            for i in range(len(tokens)):
                if tokens[i] == "ググ":
                    if tokens[i+1] == "って" or tokens[i+1] == "れ":
                        word = MakeSearchWords(i,tokens)
                        sent = SearchGoogle(word)
                        break
                elif tokens[i] == "検索":
                    if tokens[i+1] == "し" and tokens[i+2] == "て" or tokens[i+1] == "しろ":
                        word = MakeSearchWords(i,tokens)
                        sent = SearchGoogle(word)
                        break

    # 長すぎるとdiscordのほうから蹴られます
    if not sent == "":
        if len(sent) > 2000:
            sent = "文章が長すぎます。botから2000字以上のメッセージを送ることはできません。"
        print(sent)
        await message.channel.send(sent)

# bot実行
client.run(bot_token)
