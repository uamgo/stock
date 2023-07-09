import itchat, time
from itchat.content import *
from chinese_calendar import is_workday
import schedule

from main import StockA


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_reply(msg):
    if msg.text == '推荐股票':
        start_ts = time.time()
        stock = StockA()
        rs = stock.run()
        rs.sort(key=lambda r: r['code'])
        end_ts = time.time()
        msg.user.send('收到，正在安排...')

        for idx, row in enumerate(rs):
            code = row['code']
            code_type = ""
            if code.startswith('30') or code.startswith('00'):
                code_type = '0.'
            elif code.startswith('60'):
                code_type = '1.'
            else:
                code_type = 'no_found'
            msg.user.send(
                f"""{str(idx+1)}, code={row['code']}, 
                name={row['name']}\n市盈率-动态={row['shi_val']}
                \n总市值={row['total_val']}\n流通市值={row['flow_val']}
                \n https://wap.eastmoney.com/quote/stock/{code_type}{code}.html?appfenxiang=1
                """)
        msg.user.send(
            "\nElapse: %.2f s,  %s" % ((end_ts - start_ts), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    else:
        msg.user.send('%s: %s' % (msg.type, msg.text))


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def download_files(msg):
    msg.download(msg.fileName)
    typeSymbol = {
        PICTURE: 'img',
        VIDEO: 'vid', }.get(msg.type, 'fil')
    return '@%s@%s' % (typeSymbol, msg.fileName)


@itchat.msg_register(FRIENDS)
def add_friend(msg):
    msg.user.verify()
    msg.user.send('Nice to meet you!')


@itchat.msg_register(TEXT, isGroupChat=True)
def text_reply(msg):
    if msg.isAt:
        msg.user.send(u'@%s\u2005I received: %s' % (
            msg.actualNickName, msg.text))


# picture version
# itchat.auto_login(True)
itchat.auto_login(enableCmdQR=2)


def job_function():
    friends = itchat.get_friends()
    itchat.auto_login(hotReload=True)

    for i in friends:
        remark_name = i['RemarkName']
        itchat.send('开玩笑的，我并没有1000万', toUserName=remark_name)


schedule.every().day.at("9:00").at("")

itchat.run(True)
