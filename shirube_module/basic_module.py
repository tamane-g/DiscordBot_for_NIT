# a_listの日付がb_listより古ければTrueを返す
def CheckDeadline(a_list, b_list):
    for i in range(len(a_list)):
        if a_list[i] < b_list[i]:
            return True
        elif a_list[i] > b_list[i]:
            return False
    return False


# membersリストの中から自分を見つける（≒自分のmember型を返す）
# discord.pyのリファレンス見ても見つからなかったので仕方なく実装
def FindSelfInMembers(members,user):
    for member in members:
        if member.id == user.id:
            return member
    print("client not found")
    return None


# 引数に指定されたテキストチャンネルのリストから発言可能なチャンネルを1つ返す
def SearchChannelToSpeak(text_channels,user):
    for channel in text_channels:
        self_member = FindSelfInMembers(channel.members,user)
        if self_member != None:
            if channel.permissions_for(self_member).send_messages:
                return channel
    print("channel not found")
    return None