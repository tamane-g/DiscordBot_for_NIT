import sys
import time
import asyncio
import discord
import keyboard
import requests
import datetime
import threading
from discord.ext import tasks
from bs4 import BeautifulSoup
from urllib.parse import unquote
from janome.tokenizer import Tokenizer


bot_token = "himitsu"
channel_id = 0
intents = discord.Intents.all()
client = discord.Client(intents=intents)

tokenizer = Tokenizer()

exit_bool = False
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

async def exit_bot():
    # print("task loop start")
    # print("exit is true")
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


def schedule_check(atime, classstr, datalines):
    send_schedule = "本日" + days[atime.weekday()] + "曜日の" + classstr + "の時間割です(後期時間割より)。\n======================================\n"
    schedule = datalines[atime.weekday()].split()
    if schedule[0] == "none":
        send_schedule = "本日" + days[atime.weekday()] + "曜日は" + classstr + "の授業はありません。"
    else:
        for i in range(len(schedule)):
            send_schedule += str(i+1) + "時間目:" + schedule[i] + "\n"
    return send_schedule


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


# ログイン時
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


# サーバーにほかのメンバーが参加したとき
@client.event
async def on_member_join(member):
    print("\fいらっしゃいませ、" + member.name + "さま！")
    print("\npless 'e' and 'x' to stop this bot")
    channel = client.get_channel(channel_id)
    await channel.send("いらっしゃいませ、" + member.name + "さま！")

"""
    for i in member.guild.channels:
        if type(i) == discord.channel.TextChannel and count == 0:
            count += 1
        elif type(i) == discord.channel.TextChannel:
            await i.send("いらっしゃいませ、" + member.name + "さま！")
            break
"""


# サーバー参加時
@client.event
async def on_guild_join(guild):
    channel = client.get_channel(channel_id)
    join_message = "はじめまして。" + guild.name + "のみなさま、廸無 導（みちなし しるべ）と申します。\n文章の解析やその他ちょっとした機能があります。また機能の追加もありますのでぜひご利用くださいませ。"
    print(join_message)
    print("\npless 'e' and 'x' to stop this bot")
    await channel.send(join_message)
    #下は応急処置的にトップにあることの多い参加履歴チャンネルをよけるよう2番目のチャンネルに送信
    #将来的にはメッセージ送信権限を確認して権限のあるチャンネルに送信する
"""
    for i in guild.channels:
        if type(i) == discord.channel.TextChannel and count == 0:
            count += 1
        elif type(i) == discord.channel.TextChannel:
            await i.send("はじめまして。" + guild.name + "のみなさま、廸無 導（みちなし しるべ）と申します。\n文章の解析やその他ちょっとした機能があります。また機能の追加もありますのでぜひご利用くださいませ。")
            break
"""


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
            # sent = "文章解析結果\n======================================\n"
            # 文章を形態素解析して単語ごとに分ける
            tokens = []
            # a = 0
            for token in tokenizer.tokenize(message.content):
                #a += 1
                # sent += str(token) + "\n"
                tokens.append(token.surface)
                # print(str(token.surface))
                # print(a)
            print(tokens)
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
            # print("schedule check")
            #「ありがとう」が含まれていたとき
            for i in range(len(tokens)):
                if tokens[i] == "ありがとう":
                    sent = "礼には及びません、当然のことです。"
            # print("arigato check")
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
            # print("google check")
            
    if not sent == "":
        if len(sent) > 2000:
            sent = "文章が長すぎます。botから2000字以上のメッセージを送ることはできません。"
        print(sent)
        # print("pless 'e' and 'x' to stop this bot>>")
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

async def key_check():
    global exit_bool
    loop = asyncio.get_event_loop()
    while True:
        i = await loop.run_in_executor(input("keyboard loop start\n"))
        if i == "ex":
            exit_bool = True
            break

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
