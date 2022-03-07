from yztool import *
import time
requests.packages.urllib3.disable_warnings()

if __name__ == '__main__':
    # 1.1 加载用户
    user = User()
    print("#################\n" + str(user))
    # 1.2 加载商城配置
    config = Config()
    print("#################\n" + str(config))
    # 1.3 加载程序配置
    Time = Time()
    print("#################\n" + str(Time))
    # 1.4 检查cookie
    status = CheckCookie("https://{0}.youzan.com/wscuser/membercenter/setting/getCustomerAttributeInfoWithScene.json".format(config.shopId), user.cookie)
    if  status== 200:
        print("\033[32mCookie有效\n\033[0m")
    elif status == 302:
        print("\033[31m警告：Cookie已经失效,5s后程序继续运行\n\033[0m")
        time.sleep(5)
    else:
        print("\033[31m警告：尝试登陆超时,5s后程序继续运行\n\033[0m")
        time.sleep(5)

    # 2.初始化会话session
    session = requests.Session()

    header = {
        'authority': 'cashier.youzan.com',
        "method": "POST",
        'path': '/pay/wsctrade/order/buy/v2/bill-fast.json?kdt_id={0}'.format(config.kdt_id),
        'scheme': 'https',
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        # 'content-length': '2752',
        'content-type': 'application/json',
        'extra-data': '{"sid":"","version":"","bizEnv":""}',
        'origin': 'https://cashier.youzan.com',
        'pragma': 'no-cache',
        'referer': 'https://cashier.youzan.com/pay/wsctrade_buy?kdt_id={0}&book_key=da2fc884-3271-4e71-a6ce-7bcd278e9f6a&bookKey=da2fc884-3271-4e71-a6ce-7bcd278e9f6a'.format(config.kdt_id),
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        'x-yz-action-id': 'wsc-h5-trade-0a136044-1645757763013-250533',
        }

    session.headers = header
    # 3.搜索商品信息
    count = 0
    while True:
        if count == 10:
            print("搜索出错次数过多，程序退出")
            exit(1)
        status, good_id, good_url = searchGoods(session, shopid=config.shopId, kdt_id=config.kdt_id, key=config.keyWords, black=config.blackWords,sail=config.onSail)  # sail为True,只搜索有货/预售, sail为False，搜索有货/预售/售罄
        if status == 1:
            break
        if status == 0:
            count = 0
            print(0)
        else:
            count += 1
            print(1)
        time.sleep(3)
          # 未搜索到商品，下次搜索间隔时间

    # 4.获取商品id(kdtId 和 skuId)
    kdtId,skuId = getId(session, good_url=good_url, shopid=config.shopId)
    if skuId == 0:
        print("未找到商品")
        exit(1)

    # 5. 创建线程并发下单
    starttime = datetime.datetime.strptime("{0}".format(Time.startTime),"%H:%M:%S")
    diff = (starttime-datetime.datetime.now()).seconds
    if Time.enableTiming == True:
        print("等待{0}s".format(diff))
        time.sleep(diff)
    count = 0
    while True:
        if count == Time.maxTry:
            exit(0)
        order(session, user, good_id, skuId, config.kdt_id, Time.num)
        count += 1
        time.sleep(Time.interval)

