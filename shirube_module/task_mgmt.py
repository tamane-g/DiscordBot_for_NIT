"""

basic_module.py依存

"""


# タスクを整理して上書きする。
# 整理されたタスクを返す。
async def UpdateTasks(time_arg, channel):
    new_task = [[]]
    task_str = ""

    with open("tasks.txt", 'r', encoding='utf_8') as f:
        all_task =  f.readlines()

    new_task = await AlermAndOrganizeTask(all_task, time_arg, channel)

    with open("tasks.txt", 'w', encoding='utf_8') as f:
        for i in range(len(new_task)):
            task_str += ",".join(map(str,new_task[i])) + "\n"
        f.write(task_str)

    return new_task


# タスクのリストを受け取り、期限を過ぎたタスクが削除されたリストを返す。
# 期限が過ぎたタスクを見つけたときはメンションして知らせる。
async def AlermAndOrganizeTask(task_arg, time_arg, channel):

    # tasks.txtを行ごとにカンマで区切り
    task_list = [[]]
    for i in range(len(task_arg)):
        task_list[i] = task_arg[i].split(',')

        # 数字はintに戻す
        for j in range(2,7):
            task_list[i][j] = int(task_list[i][j])

        if basic_module.CheckDeadline(task_list[i][2:7], [time_arg.year,time_arg.month,time_arg.day,time_arg.hour,time_arg.minute]):
            notice_message = "<@" + task_list[i][0] + "> さん！" + task_list[i][1] + "の期限になりました。終わりましたでしょうか？"
            print(notice_message)
            await channel.send(notice_message)
            del task_list[i]

    print(task_list)
    return task_list