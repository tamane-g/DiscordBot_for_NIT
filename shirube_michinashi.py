import re
import sys
import asyncio
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


# 毎日7時に時間割を知らせようと思ったが、5組以外のメンバーの追加により全クラス分を表示させるのは長すぎると思い断念
"""
# 60秒に一回ループ
@tasks.loop(seconds=60)
async def loop():
    # 現在の時刻
    lp_now = datetime.datetime.now()
    if lp_now.strftime('%H:%M') == '07:00':
        channel = client.get_channel(channel_id)
        f = open('時間割.txt', 'r',encording='utf_8')
        await channel.send(schedule_check(lp_now, f.readlines()))
        f.close()
"""


@tasks.loop(hours=1.0)
async def news_loop():
    news = check_news()
    if not news == None:
        channel = client.get_channel(channel_id)
        print(news)
        await channel.send(news)


""" membersリストの中から自分を見つける（≒自分のmember型を返す）、これやってくれるやつ絶対discord.pyにあるだろ """
def find_self_in_members(members):
    for member in members:
        if member.id == client.user.id:
            return member
    print("client not found")
    return None


""" 引数に指定されたテキストチャンネルのリストから発言可能なチャンネルを1つ返す """
def search_channel_to_speak(text_channels):
    for channel in text_channels:
        self_member = find_self_in_members(channel.members)
        if self_member != None:
            if channel.permissions_for(self_member).send_messages:
                return channel
    print("channel not found")
    return None


""" 時間割の文字列を作成し返す """
def schedule_check(time_arg, class_name, datalines):
    send_schedule = "本日" + days[time_arg.weekday()] + "曜日の" + class_name + "の時間割です(後期時間割より)。\n======================================\n"
    schedule = datalines[time_arg.weekday()].split()
    if schedule[0] == "none":
        send_schedule = "本日" + days[time_arg.weekday()] + "曜日は" + class_name + "の授業はありません。"
    else:
        for i in range(len(schedule)):
            send_schedule += str(i+1) + "時間目:" + schedule[i] + "\n"
    return send_schedule


""" 苫小牧高専のホームページから最新のお知らせを取得、保存されているお知らせの日付より新しい場合タイトルと内容の一部を返す """
def check_news():
    f = open("newest_news.txt", 'r', encoding='utf_8')
    have_date = f.read().split(',')
    f.close()
    print("have_date is " + str(have_date))

    news_url = "https://www.tomakomai-ct.ac.jp/news"
    html = requests.get(news_url)
    soup = BeautifulSoup(html.content, "html.parser")
    link_title = soup.select_one("[class='post clearfix']")
    got_date = re.split("[年月日]", link_title.select_one(".daytime").get_text())
    print("got_date is " + str(got_date))

    if got_date == "":
        rtn_news = None
    else:
        if (have_date[0] < got_date[0] or
            have_date[0] == got_date[0] and have_date[1] < got_date[1] or
            have_date[0] == got_date[0] and have_date[1] == got_date[1] and have_date[2] < got_date[2]
            ):
            f = open("newest_news.txt", 'w')
            f.write(got_date[0] + ',' + got_date[1] + ',' + got_date[2])
            f.close()
            rtn_news = "苫小牧高専ホームページのお知らせが更新されました。\n詳細は該当ページにて確認してください。(https://www.tomakomai-ct.ac.jp/news)\n======================================\n"
            rtn_news += link_title.select_one(".title").get_text() + '\n'
            rtn_news += link_title.select_one("[class='inner clearfix'] > p").get_text() + '\n'
        else:
            rtn_news = None

    return rtn_news


""" https://www.google.com/search?q=以降の文字列を作成 """
def search_check(count,atoken):
    print(atoken)
    returnchar = ""
    if count >= 2:
        if atoken[count-1] == "と" or atoken[count-1] == "で" or atoken[count-1] == "の":
            for i in range(count-1):
                returnchar += atoken[i]
            return returnchar
        else:
            for i in range(count):
                returnchar += atoken[i]
            return returnchar
    elif count == 1:
        returnchar = atoken[0]
        return returnchar
    else:
        return None


""" googleの検索ページをスクレイピングし、結果を返す """
def search_google(searchwords):
    if searchwords != None:
        try:
            print("google " + searchwords)
            load_url = "https://www.google.com/search?q=" + searchwords.replace(" ","+").replace("　","+")
            print(load_url)
            html = requests.get(load_url)
            soup = BeautifulSoup(html.content, "html.parser")
            link_title = soup.select(".kCrYT > a")
            result = "了解いたしました。以下が検索結果上位3サイトです。\n======================================\n"
            length = len(link_title) if len(link_title) < 3 else 3 
            for i in range(length):
                result += link_title[i].find("h3").get_text() + "\n"
                hoge = unquote(link_title[i].get("href").replace("/url?q=",""))
                result += hoge[0:hoge.find("&sa=U")] + "\n\n"
            return result
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


""" wikipediaの検索ページをスクレイピングし、結果を返す """
def search_wiki(searchwords):
    if searchwords != None:
        result = ""
        print("wikipedia " + searchwords)
        result_url = "https://ja.wikipedia.org/w/index.php?search=" + searchwords.replace(" ","+").replace("　","+")
        html = requests.get(result_url)
        soup = BeautifulSoup(html.content, "html.parser")
        if soup.select(".firstHeading")[0].get_text() == "検索結果":
            result += "検索の結果wikipediaにそのような項目はありませんでした。\nwikipedia検索結果上位に該当する項目は以下です。\n======================================\n"
            link_title = soup.select("div.mw-search-result-heading > a")
            length = len(link_title) if len(link_title) < 3 else 3 
            if length == 0:
                result = "wikipediaにそのような項目はありませんでした。\nwikipedia検索においても該当するページはありませんでした。\n検索ワードを変えて試してみてはいかがでしょうか。"
            for i in range(length):
                result += link_title[i].get("title") + "\n"
                print(link_title[i].get("href"))
                result += "https://ja.wikipedia.org" + unquote(link_title[i].get("href")) + "\n\n"
        else:
            result += soup.select(".firstHeading")[0].get_text() + "\n"
            for i in soup.select(".mw-perser-output > p"):
                result += i.get_text()
            result += "\n参照元\n" + result_url.replace("%","%%")
        return result
    else:
        return "検索対象を指定してください。"


""" ログイン時処理、herokuなどで常駐できるようになれば不要 """
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


""" 終了処理、herokuなどで常駐できるようになれば不要 """
async def exit_bot():
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


""" サーバーにほかのメンバーが参加したとき """
@client.event
async def on_member_join(member):
    channel = search_channel_to_speak(member.guild.text_channels)
    channel = client.get_channel(channel_id)
    welcome_message = "\fいらっしゃいませ、" + member.name + "さま！"
    print(welcome_message)
    await channel.send(welcome_message)


""" サーバー参加時 """
@client.event
async def on_guild_join(guild):
    channel = search_channel_to_speak(guild.text_channels)
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
        if len(message.content) > 300:
            sent = "文章が長すぎます。文章を300字以下にしてください。"
        else:
            if message.content == "//end":
                await exit_bot()
            elif message.content == "//test":
                await search_channel_to_speak(message.guild.text_channels).send("test succeeded")
            elif message.content == "//news":
                    news = check_news()
                    if not news == None:
                        print(news)
                        await message.channel.send(news)

            """ 文章を形態素解析して単語ごとに分ける """
            tokens = []
            for token in tokenizer.tokenize(message.content):
                tokens.append(token.surface)
            print(tokens)

            """ 特定の文字列を検索 """
            #「時間割」が含まれていたとき
            for i in range(len(tokens)):
                if tokens[i] == "時間割":
                    sent = "クラス別のロールが付与されていません。管理者に問い合わせてください。\n"
                    user_role = message.author.roles
                    for j in user_role:
                        if j.name in schedule_files.keys():
                            f = open(schedule_files[j.name], 'r', encoding='utf_8')
                            sent = schedule_check(datetime.datetime.now(), j.name, f.readlines())
                            f.close()
            #「ありがとう」が含まれていたとき
            for i in range(len(tokens)):
                if tokens[i] == "ありがとう":
                    sent = "礼には及びません、当然のことです。"
            #「意味」「とは」が含まれていたとき
            for i in range(len(tokens)):
                if tokens[i] == "意味":
                    sent = "こちらのリンクにて参照してください。\n"
                    word = search_check(i,tokens)
                    sent += search_wiki(word)
                    break
                elif len(tokens) > i+1:
                    if tokens[i] == "と" and tokens[i+1] == "は":
                        sent = "こちらのリンクにて参照してください。\n"
                        word = search_check(i,tokens)
                        sent += search_wiki(word)
                        break
            #「ググって」「ググれ」がが含まれていたとき
            for i in range(len(tokens)):
                if tokens[i] == "ググ":
                    if tokens[i+1] == "って" or tokens[i+1] == "れ":
                        word = search_check(i,tokens)
                        sent = search_google(word)
                        break
                elif tokens[i] == "検索":
                    if tokens[i+1] == "し" and tokens[i+2] == "て" or tokens[i+1] == "しろ":
                        word = search_check(i,tokens)
                        sent = search_google(word)
                        break
            
    if not sent == "":
        if len(sent) > 2000:
            sent = "文章が長すぎます。botから2000字以上のメッセージを送ることはできません。"
        print(sent)
        await message.channel.send(sent)

# 没案
# eとxが押されたときexit_boolフラグを立てる(終了時のメッセージ送信のため)
"""
def key_check():
    print("keyboard loop start\n")
    global exit_bool
    while True:
        if keyboard.is_pressed("e") and keyboard.is_pressed("x"):
            # print("plessed e and x")
            exit_bool = True
            break
        time.sleep(0.1)
"""

# 没案
# シンプルにbotの処理を継続させつつinputを待機しようと思ったがなんかダメ
"""
async def key_check():
    global exit_bool
    loop = asyncio.get_event_loop()
    while True:
        i = await loop.run_in_executor(input("keyboard loop start\n"))
        if i == "ex":
            exit_bool = True
            break
"""

# 没案
# botとキーボード入力検出ループ開始(WSL上では上手く動きませんでした)
"""
if __name__ == "__main__":
    bot_func = threading.Thread(target=client.run, args=(bot_token,))
    key_func = threading.Thread(target=key_check)

    bot_func.start()
    key_func.start()

"""

# bot実行
client.run(bot_token)
