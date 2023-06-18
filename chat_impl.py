import itchat, time
from itchat.content import *

from main import StockA


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_reply(msg):
    if msg.text == '推荐股票':
        start_ts = time.time()
        stock = StockA()
        rs = stock.run()
        rs.sort(key=lambda r: r['code'])
        end_ts = time.time()

        for idx, row in enumerate(rs):
            msg.user.send(
                f"{str(idx+1)}, code={row['code']}, name={row['name']}, 市盈率-动态={row['shi_val']}, 总市值={row['total_val']}, 流通市值={row['flow_val']}")
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
itchat.run(True)
