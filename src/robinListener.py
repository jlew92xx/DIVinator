import json, copy, time
import datetime
from robin_stocks import robinhood, helper
from DatabaseManager import DatabaseManager
import pytz
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
    try:
        divs =  robinhood.get_dividends()
        stocks = robinhood.get_all_positions()
        for stock in stocks:
            stocksDict[stock['symbol']] = stock

        for div in divs:
            insertDivDict = {}
            posUrl = div["instrument"].replace("instruments", "positions/5UX32878")
            #for some reason the ticker is not part of the dividend dict in the Robinhod api
            insertDivDict['ticker'] = urlToTicker[posUrl]
            for column in columns:
                value = div[column]
                insertDivDict[column] = value
            if insertDivDict['paid_at'] != None:
                if dbManager != None:
                    dbManager.insertDiv(insertDivDict)
            elif div["state"] == 'pending':
                insertDivDict['paid_at'] = div['payable_date'] +'T00:00:00.000000Z'
                dbManager.insertDiv(insertDivDict)
    except:
        logIn()

def updateUrlToTicker(posUrl:str) -> bool:
    output = False
    stocks = robinhood.get_all_positions()
    
    for stock in stocks:
        if stock["url"] not in urlToTicker.keys():
            if stock["url"] == posUrl:
                output = True
            urlToTicker[stock["url"]] = stock['symbol']

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


    
    