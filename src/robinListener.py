import json, copy, time
import datetime
from robin_stocks import robinhood, helper
from DatabaseManager import DatabaseManager
import pytz
#import polyClient as poly
import timeUltil as timeHelp

MYCRED = "Cred/mycred.json"
LOGIN = None
TOTAL = "total"
MONTHLYDIVLIST = 'DIVS'

urlToTicker = {}
columns = ["paid_at", "position", "rate" ,"amount","state", "id"]
sleepTime = 900
dbManager:DatabaseManager
stocksDict = {}
with open('data.json') as json_file:
    freqDict = json.load(json_file)


POSITIONURL = "https://api.robinhood.com/positions/"

def openCred():
    data = None
    with open(MYCRED, 'r') as file:
        data = json.load(file)
    return data
def setDbManager(dbm):
    global dbManager
    dbManager = dbm

def logIn():
    t = openCred()
    KEY = t["KEY"]
    EMAIL = t["EMAIL"]
    PASSWD = t["PASSWD"]
    CODE = t["CODE"]

    LOGIN = robinhood.login(EMAIL, PASSWD, mfa_code = CODE)


def buildURLToTickerDict():
    stocks = robinhood.get_all_positions()
    for stock in stocks:
        if stock["url"] not in urlToTicker.keys():
            urlToTicker[stock["url"]] = stock['symbol']
def getNumShares(ticker:str) -> float:
    if(ticker in stocksDict.keys()):
        return float(stocksDict[ticker]["quantity"])
def logInAndUpdate():
    
    divs =  robinhood.get_dividends()
    stocks = robinhood.get_all_positions()
    start_time = time.perf_counter()
    stockOrders = robinhood.get_all_stock_orders()
    newStocksDict = {}
    for stock in stocks:
        newStocksDict[stock['symbol']] = stock
        #stock["freq"] = poly.getFreq(stock['symbol']) 
        instrument = stock["instrument"]
        i = 0
        orders = []
        stock ["orders"] = orders
        for order in stockOrders[:]:
            if order["instrument"] == instrument and order["side"] == 'buy' and order['state'] == "filled":
                orders.append(order)
            i += 1
    end_time = time.perf_counter()
    global stocksDict
    stocksDict = newStocksDict
    for div in divs:
        insertDivDict = {}
        posUrl = div["instrument"].replace("instruments", "positions/5UX32878")
        #for some reason the ticker is not part of the dividend dict in the Robinhod api
        insertDivDict['ticker'] = urlToTicker[posUrl]
        for column in columns:
            value = div[column]
            insertDivDict[column] = value

        insertDivDict["yield"] = calculateYield(div["record_date"], insertDivDict['ticker'], float(div["rate"]))
        if insertDivDict['paid_at'] != None:
            if dbManager != None:
                dbManager.insertDiv(insertDivDict)
        elif div["state"] == 'pending':
            insertDivDict['paid_at'] = div['payable_date'] +'T00:00:00.000000Z'
            dbManager.insertDiv(insertDivDict)
    # except:
    #     print("Something fails")
    #     logIn()
def calculateYield(recordDateStr, ticker , rate):
    recordDate = datetime.datetime.strptime(recordDateStr, "%Y-%m-%d")
    orders = stocksDict[ticker]['orders']
    
    numOfShares = 0
    sumOfPrice = 0
    for order in reversed(orders):
        orderDateStr = order['last_transaction_at'].split("T")[0]
        orderDate = datetime.datetime.strptime(orderDateStr, "%Y-%m-%d")
        if orderDate < recordDate:
            
            averagePrice = float(order['average_price'])
            quantity = float(order['quantity'])
            numOfShares += quantity
            sumOfPrice += (quantity * averagePrice)
        else:
            break
   
    divCount = int(freqDict[ticker])
    if numOfShares == 0:
        print(f"Ticker {ticker} returns zero!")
        return 0
    averagePrice = sumOfPrice/numOfShares
    divYield = (divCount * rate / averagePrice) * 100
    return divYield
def updateUrlToTicker(posUrl:str) -> bool:
    output = False
    stocks = robinhood.get_all_positions()
    
    for stock in stocks:
        if stock["url"] not in urlToTicker.keys():
            if stock["url"] == posUrl:
                output = True
            urlToTicker[stock["url"]] = stock['symbol']

    return output 

def getStockPositions() -> list:
    urls = robinhood.get_all_positions("url")
    output = []
    for url in urls:
        output.append(robinhood.get_symbol_by_url(url))
    return output

def getCurrentPrice(ticker:str):
    try:
        x = float(robinhood.get_latest_price(ticker)[0])
        return x
    except:
        logIn()
        return -404
# def startThread():
#     # t = openCred()
#     # KEY = t["KEY"]
#     # EMAIL = t["EMAIL"]
#     # PASSWD = t["PASSWD"]
#     # CODE = t["CODE"]

#     # LOGIN = robinhood.login(EMAIL, PASSWD, mfa_code = CODE)


#     # divs =  robinhood.get_dividends()
#     # stocks = robinhood.get_all_positions()

# #ORGNAIZE LATER WORK NOW
#     divs = []
#     while True:
#         lastUpdate = datetime.datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
#         for div in divs:
#             insertDivDict = {}
#             posUrl = div["instrument"].replace("instruments", "positions/5UX32878")
#             #for some reason the ticker is not part of the dividend dict in the Robinhod api
#             if posUrl in urlToTicker or updateUrlToTicker(posUrl):
#                 insertDivDict['ticker'] = urlToTicker[posUrl]
#             else:
#                 print("SUM TING WONG with insert in robinlistener accessing the Ticker symbol")
#                 insertDivDict["ticker"] = "n/a"
            
                

#             for column in columns:
#                 value = div[column]
#                 insertDivDict[column] = value
#             if insertDivDict['paid_at'] != None:
#                 if dbManager != None:
#                     dbManager.insertDiv(insertDivDict)
#             elif div["state"] == 'pending':
#                 insertDivDict['paid_at'] = div['payable_date'] +'T00:00:00.000000Z'
#                 dbManager.insertDiv(insertDivDict)

#         dbManager.newUpdates = dbManager.newUpdate

                
        
            
#         print("finish update at " + str(datetime.datetime.now()))


#         if(__name__ != "__main__" and len(divs) > 0):
#             print("new divs added:")
#             for div in divs:
#                print(str(div))      
#             dbManager.commit()
        
#         time.sleep(sleepTime)
#         newDivs = []
#         try:
#             newDivs = robinhood.get_dividends()
#         except:
#             logIn()
#             print("robinhood failure")

#         divs = newDivs

def getAvgStockPrice(ticker:str) -> float:
    if not ticker in stocksDict.keys():
        return 0.0
    return float(stocksDict[ticker]["average_buy_price"])
    
    

if __name__ == "__main__":

    logIn()
    #stockData = robinhood.account.get_all_positions()
    #instruments = robinhood.orders.get_instruments_by_symbols("BTI")
    start_time = time.perf_counter()
    fart2 = robinhood.find_stock_orders(symbol="BTI", cancel=None)
    end_time = time.perf_counter()
    print("Time taken for find_stock_orders:", end_time - start_time)


    start_time = time.perf_counter()
    fart2 = robinhood.get_all_stock_orders()
    end_time = time.perf_counter()
    print("Time taken for all stocks:", end_time - start_time)



    #turds = robinhood.get_all_stock_orders()

    print("farts")


    
    