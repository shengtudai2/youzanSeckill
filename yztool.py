import json, os, datetime, threading, requests, re
# 用户信息类，默认从config.json配置中读取

class User:
    def __init__(self):
        self.msg1 = self.read_config()["msg1"]
        self.msg2 = self.read_config()["msg2"]
        self.msg3 = self.read_config()["msg3"]
        self.cookie = self.read_config()["cookie"]

    def read_config(self, file="config.json"):
        with open(file= file, encoding='utf8') as json_file:
            config = json.load(json_file)
        return config["UserInfo"]

    def __str__(self):
        return "用户加载成功\n备注1:{0}\n备注2:{1}\n备注3:{2}\ncookie:{3}".format(self.msg1, self.msg2, self.msg3, self.cookie)
class Config:
    def __init__(self):
        self.kdt_id = self.read_config()["kdt_id"]
        self.shopId = self.read_config()["shopId"]
        self.keyWords = self.read_config()["keyWords"]
        self.blackWords = self.read_config()["blackWords"]
        self.onSail = self.read_config()["onSail"]

    def read_config(self, file="config.json"):
        with open(file= file, encoding='utf8') as json_file:
            config = json.load(json_file)
        return config["Config"]
    def __str__(self):
        return "商城信息加载成功\nkdt_id:{0}\nshopId:{1}\n关键词:{2}\n屏蔽词:{3}\n无货监控:{4}".format(self.kdt_id, self.shopId, self.keyWords, self.blackWords, self.onSail)
class Time:
    def __init__(self):
        self.enableTiming = self.read_config()["enableTiming"]
        self.startTime = self.read_config()["startTime"]
        self.interval = self.read_config()["interval"]
        self.maxTry = self.read_config()["maxTry"]
        self.num = self.read_config()["num"]
    def read_config(self, file="config.json"):
        with open(file= file, encoding='utf8') as json_file:
            config = json.load(json_file)
        return config["Time"]
    def __str__(self):
        return "程序配置加载成功\n启用倒计时:{0}\n开始时间:{1}\n抢购间隔:{2}\n最大重试次数:{3}\n抢购数量:{4}".format(self.enableTiming, self.startTime, str(self.interval), str(self.maxTry), str(self.num))

# 下单线程类
class Buy(threading.Thread):
    def __init__(self, session:requests.Session, data, kdt_id:str):
        threading.Thread.__init__(self)
        self.session = session
        self.buy_url = r"https://cashier.youzan.com/pay/wsctrade/order/buy/v2/bill-fast.json?kdt_id={0}".format(kdt_id)
        self.data = data
    def run(self):
        try:
            buy_result = self.session.post(url=self.buy_url, json=self.data, verify=False, timeout=2)
            print('\033[31m{0}\033[0m'.format(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f'))))
            print(buy_result.text)
            if 'orderNo' in buy_result.text:
                print("\033[32m已抢到， 赶紧去下单！\033[0m")
                os._exit(0)
        except Exception as e:
            print("\033[31m出错了，重试中\033[0m")
            print(e)


# 搜索商品链接
def searchGoods(session:requests.Session, shopid:str, kdt_id:str, key:str, black:str="", sail:bool=True):
    url = r"https://{0}.youzan.com/wscshop/showcase/goods_search/goods.json".format(shopid)
    headers =  {
        "Host": "{0}.youzan.com".format(shopid),
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; V1981A Build/RP1A.200720.012; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.72 MQQBrowser/6.2 TBS/045811 Mobile Safari/537.36 MMWEBID/6799 MicroMessenger/8.0.14.2000(0x28000E37) Process/tools WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64"
    }
    params = {
            'kdt_id': kdt_id,
            'offline_id': 0,
            'keyword': key,
            'page': 1,
            'page_size': 20
        }
    good_id = ""
    good_url = ""
    msg = ""
    status = -1
    try:
        search = session.get(url=url, headers=headers,params=params)
        js = search.json()
        if js["code"] == 0:
            goods_list = js["data"]
            for good in goods_list:
                title = good["title"]
                if black == "":
                    pass
                else:
                    if black in title:
                        continue
                if key in title and (not(good["sold_status"]==2) or not(sail)):
                    status = 1
                    good_id = str(good["id"])
                    good_url = good["url"]
                    tail = good_url.split('/')[-1]
                    good_url = "https://{0}.m.youzan.com/wscgoods/detail/".format(shopid)+tail
                    msg = "查到商品\ntitle：{0}\nid:{1}\n{2}\n".format(good["title"], good["id"], good["url"])
            if (good_id == ""):
                status = 0
                msg = "商品未开售"
        else:
            status = -1
            msg = "查询失败"
    except Exception as e:
        status = -1
        msg = "请求错误:\n" + str(e)
    print(msg)
    return status, good_id, good_url


# 查找商品id
def getId(session:requests.Session, good_url:str, shopid:str):
    kdtId = 0
    skuId = 0
    session.headers["Host"] = "{0}.m.youzan.com".format(shopid)
    try:
        good_detail = session.get(good_url).text
        pattern1 = re.compile('kdtId=[0-9]*')
        pattern2= re.compile('"skuId":[0-9]*')
        kdtId = str(pattern1.findall(good_detail)[0][6:])
        skuId = str(pattern2.findall(good_detail)[0][8:])
        print("kdtId:" + kdtId)
        print("skuId:" + skuId)
    except Exception as e:
        print("获取商品id请求出错")
    return kdtId, skuId


# 下单
def order(session:requests.Session, user:User, good_id, skuId, kdt_id, num:int):
    # post的数据
    data = {
        "version": 2,
        "source": {
            "bookKey": "163aa402-974b-44ac-8e52-2afe10717241",
            "clientIp": "59.172.4.216",
            "fromThirdApp": False,
            "isWeapp": False,
            "itemSources": [{
                "activityId": 0,
                "activityType": 0,
                "bizTracePointExt": "{\"yai\":\"wsc_c\",\"st\":\"js\",\"sv\":\"1.1.31\",\"atr_uuid\":\"\",\"page_type\":\"\",\"yzk_ex\":\"\",\"tui_platform\":\"\",\"tui_click\":\"\",\"uuid\":\"17841ecd-9d07-1e78-60a8-53b10aa8022b\",\"userId\":13373954287,\"platform\":\"web\",\"from_source\":\"\",\"wecom_uuid\":\"\",\"wecom_chat_id\":\"\"}",
                "cartCreateTime": 0,
                "cartUpdateTime": 0,
                "gdtId": "",
                "goodsId": good_id,
                "pageSource": "",
                "skuId": skuId
            }],
            "kdtSessionId": "YZ913378021525524480YZ80vtE6Sq",
            "needAppRedirect": False,
            "orderType": 0,
            "platform": "unknown",
            "salesman": "",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
            "bizPlatform": ""
        },
        "config": {
            "bosWorkFlow": False,
            "containsUnavailableItems": False,
            "fissionActivity": {
                "fissionTicketNum": 0
            },
            "paymentExpiry": 0,
            "receiveMsg": True,
            "usePoints": False,
            "useWxpay": False,
            "buyerMsg": "", # 备注信息
            "disableStoredDiscount": True,
            "storedDiscountRechargeGuide": True,
            "yzGuaranteeInfo": {
                "displayTag": {
                    "IS_YZ_SECURED": "0",
                    "FREIGHT_INSURANCE_FREE": "0",
                    "IS_FREIGHT_INSURANCE": "0"
                },
                "freightInsurance": False,
                "mainSupportContent": [],
                "securedItemSnapshotList": [],
                "hideYzGuarantee": False,
                "page": "order"
            }
        },
        "usePayAsset": {},
        "items": [{
            "activityId": 0,
            "activityType": 0,
            "deliverTime": 0,
            "extensions": {
                "OUTER_ITEM_ID": "10000"
            },
            "fCode": "",
            "goodsId": good_id,
            "isSevenDayUnconditionalReturn": False,
            "itemFissionTicketsNum": 0,
            "itemMessage": "[\"{0}\",\"{1}\",\"{2}\"]".format(user.msg1, user.msg2, user.msg3),  # 手机号
            "kdtId": kdt_id,
            "num": num,
            "pointsPrice": 0,
            "price": 100,
            "skuId": skuId,
            "storeId": 0,
            "umpSkuId": 0
        }],
        "seller": {
            "kdtId": kdt_id,
            "storeId": 0
        },
        "ump": {
            "activities": [{
                "activityId": 0,
                "activityType": 0,
                "externalPointId": 0,
                "goodsId": good_id,
                "kdtId": kdt_id,
                "pointsPrice": 0,
                "skuId": skuId,
                "usePoints": False
            }],
            "coupon": {},
            "useCustomerCardInfo": {
                "specified": False
            },
            "costPoints": {
                "kdtId": kdt_id,
                "usePointDeduction": True
            }
        },
        "newCouponProcess": True,
        "unavailableItems": [],
        "asyncOrder": False,
        "delivery": {
            "hasFreightInsurance": False,
            "expressTypeChoice": 0
        },
        "confirmTotalPrice": 100,
        "extensions": {
            "IS_OPTIMAL_SOLUTION": "True",
            "IS_SELECT_PRESENT": "0",
            "SELECTED_PRESENTS": "[]",
            "BIZ_ORDER_ATTRIBUTE": "{\"RISK_GOODS_TAX_INFOS\":\"0\"}"
        },
        "behaviorOrderInfo": {
            "bizType": 158,
            "token": ""
        }
    }
    session.headers["Host"] = "cashier.youzan.com"
    session.headers["Cookie"] = user.cookie
    Buy(session, data, kdt_id).start()

def CheckCookie(url:str ,cookie:str):
    try:
        r= requests.get(url=url, headers={"Cookie":cookie}, allow_redirects=False)
        status = r.status_code
        if status == 200:
            userinfo = r.json()["data"]["customerAttributeInfoList"]  # 0:头像 1：手机号 2：姓名 3：性别 4：生日 5：地区
            print("\n###################\nCookie检查结果\n姓名：{0}\n手机号：{1}".format(userinfo[2]["value"], userinfo[1]["value"]))
            return status
        else:
            return status
    except Exception as e:
        status = 500
    return status

def check(session:requests.Session, kdt_id):
    url = "https://uic.youzan.com/passport/api/captcha/check-behavior-captcha-data-opt.json?kdt_id={0}".format(kdt_id)
