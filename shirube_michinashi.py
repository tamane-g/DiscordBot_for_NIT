import sys
import discord
import datetime
from discord.ext import tasks
from janome.tokenizer import Tokenizer
from shirube_module import task_mgmt
from shirube_module import nittc_news
from shirube_module import basic_module
from shirube_module import search_module

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


# 1時間ごとにNewsCheck()を実行する
@tasks.loop(minutes=1.0)
async def main_loop():
    await nittc_news.SendNews(client.get_channel(channel_id))
    await task_mgmt.UpdateTasks(datetime.datetime.now(),client.get_channel(channel_id))


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
    channel = basic_module.SearchChannelToSpeak(member.guild.text_channels,client.user)
    channel = client.get_channel(channel_id)
    welcome_message = "\fいらっしゃいませ、" + member.name + "さま！"
    print(welcome_message)
    await channel.send(welcome_message)


# サーバー参加時
@client.event
async def on_guild_join(guild):
    channel = basic_module.SearchChannelToSpeak(guild.text_channels,client.user)
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
                await basic_module.SearchChannelToSpeak(message.guild.text_channels,client.user).send("test succeeded")
            elif message.content == "//news":
                await nittc_news.SendNews(client.get_channel(channel_id))
            elif message.content == "//task":
                await task_mgmt.UpdateTasks(datetime.datetime.now(),client.get_channel(channel_id))
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
                    word = search_module.MakeSearchWords(i,tokens)
                    sent += search_module.SearchWikipedia(word)
                    break
                elif len(tokens) > i+1:
                    if tokens[i] == "と" and tokens[i+1] == "は":
                        word = search_module.MakeSearchWords(i,tokens)
                        sent += search_module.SearchWikipedia(word)
                        break

            for i in range(len(tokens)):
                if tokens[i] == "ググ":
                    if tokens[i+1] == "って" or tokens[i+1] == "れ":
                        word = search_module.MakeSearchWords(i,tokens)
                        sent = search_module.SearchGoogle(word)
                        break
                elif tokens[i] == "検索":
                    if tokens[i+1] == "し" and tokens[i+2] == "て" or tokens[i+1] == "しろ":
                        word = search_module.MakeSearchWords(i,tokens)
                        sent = search_module.SearchGoogle(word)
                        break

    # 長すぎるとdiscordのほうから蹴られます
    if not sent == "":
        if len(sent) > 2000:
            sent = "文章が長すぎます。botから2000字以上のメッセージを送ることはできません。"
        print(sent)
        await message.channel.send(sent)

# bot実行
client.run(bot_token)