# 可以自己import我们平台支持的第三方python模块，比如pandas、numpy等。
import datetime
import numpy as np

# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # 在context中保存全局变量
    context.s1 = "600028.XSHG"
    # 实时打印日志
    logger.info("RunInfo: {}".format(context.run_info))
    # 平均交易量
    context.avgVolume = getAvgVolumne(context, 3, context.now)
    # 当天换手率
    context.turnoverRate = get_turnover_rate(context.s1, count=1, fields='today')
    # 过去5天换手率
    context.FiveDayTurnoverRate = get_turnover_rate(context.s1, count=5, fields='today')
    # 当天涨跌幅
    context.priceChange = get_price_change_rate(context.s1,count=1)
    # 120天内最高价
    context.OTZDayHighPrice = getHighPrice(context,120,context.now)
    # 400天内最高价
    context.FHDayHighPrice = getHighPrice(context,400,context.now)
    context.buy = 3.5

# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    pass


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑
    print("启动>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    isBuy = False
    isSale = False
    Msg = ""
    
    #买入条件（买入条件是所有都符合才执行）
    #print("order_book_id: ",bar_dict[context.s1].order_book_id)
    #1.当天成交量大于前三天平均值的3倍
    #print("前三天平均Volume: ",context.avgVolume)
    if float(bar_dict[context.s1].volume) > (float(context.avgVolume) * 3.0):
        #2.换手率低于10%
        #print("当天换手率: ",context.turnoverRate)
        if float(context.turnoverRate) < 0.1:
            #3.当天涨幅大于5%
            #print("当天涨跌幅: ", context.priceChange)
            if float(context.priceChange) > 0.05:
                #4.当天收盘价大于5日平均价格（即在5日平均线之上）
                #print("当天收盘价: ",bar_dict[context.s1].close)
                #print("连续5日收盘均价: ",np.mean(history_bars(context.s1, 5, '1d', 'close')))       
                if float(bar_dict[context.s1].close) > float(np.mean(history_bars(context.s1, 5, '1d', 'close'))):
                    #5.（前面120天最高价-当天收盘价）/前面120天最高价>50%
                    #print("120天内最高价: ", context.highPrice)
                    if (float(context.OTZDayHighPrice)-float(bar_dict[context.s1].close))/float(context.OTZDayHighPrice) > 0.5:
                        isBuy = True
                    else:
                        Msg = "（前面120天最高价-当天收盘价）/前面120天最高价>50%"
                else:
                    Msg = "当天收盘价大于5日平均价格（即在5日平均线之上）"
            else:
                Msg = "当天涨幅大于5%"
        else:
            Msg = "当天换手率低于10%"
    else:
        Msg = "当天成交量大于前三天平均值的3倍"
    if isBuy:
        print("满足条件，建议买入")
    else:
        print("不满足", Msg, "条件，不建议买入")
    
    print("--------------------------------")
    
    #卖出条件（只要任意一个条件即执行）：
    _arg = float(bar_dict[context.s1].close) - float(context.buy) / float(context.buy)
    #1.5天内有3次换手率大于10%
    if (context.FiveDayTurnoverRate >= 0.1).sum() >= 3:
        isSale = True
        Msg = "5日均价低于20日均价"
    #2.（400天内的最高价-当天收盘价）/400天内最高价<10%
    elif (float(context.FHDayHighPrice) - float(bar_dict[context.s1].close))/float(context.FHDayHighPrice) < 0.1:
        isSale = True
        Msg = "（当天收盘价-买入价）/买入价>80%或者<-10%"
    #3.当天换手率>20%
    elif float(context.turnoverRate) > 0.2:
        isSale = True
        Msg = "5日平均换手率>10%"
    #4.（当天收盘价-买入价）/买入价>80%或者<-10%
    elif _arg > 0.8 or _arg < -0.1:
        isSale = True
        Msg = "当天换手率>20%"
    #5.5日平均换手率>10%
    elif float(np.mean(context.FiveDayTurnoverRate)) > 0.1:
        isSale = True
        Msg = "（400天内的最高价-当天收盘价）/400天内最高价<10%"
    #6.5日均价低于20日均价
    elif float(np.mean(history_bars(context.s1, 5, '1d', 'close'))) < float(np.mean(history_bars(context.s1, 20, '1d', 'close'))):
        isSale = True
        Msg = "5天内有3次换手率大于10%"
        
    if isSale:
        print("满足", Msg, "条件，建议卖出")
    else:
        print("不满足条件，不建议卖出")
    
    print("结束<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    
    
    # bar_dict[order_book_id] 可以拿到某个证券的bar信息
    # context.portfolio 可以拿到现在的投资组合信息

    # 使用order_shares(id_or_ins, amount)方法进行落单

    # TODO: 开始编写你的算法吧！
    # order_shares(context.s1, 1000)

# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    pass


# 获取前N天交易量平均值
# 参数：天数，交易量平均值
def getAvgVolumne(context, num , baseDate):
    if num <= 0:
        return -1

    print(datetime.date.isoformat(baseDate))
    preDate = baseDate
    sum = 0.0
    for i in range(num):
        preDate = get_previous_trading_date(preDate)
        obj = get_price(context.s1, start_date=preDate, end_date=preDate)
        sum += float(obj['volume'])
        # print("date:",datetime.date.isoformat(preDate),",volume:",obj['volume'])
        # print("sum:",sum)
    return sum/(1.0*num)
        
        
# 获取前N天交易量平均值
# 参数：天数，起始日期
def getHighPrice(context, num , baseDate):
    _start = datetime.date.isoformat( baseDate + datetime.timedelta(days=-num))
    _end = datetime.date.isoformat(baseDate + datetime.timedelta(days=-1))
    return np.max(get_price(context.s1, start_date=_start, end_date=_end, frequency='1d', fields="high"))
