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
columns = ["paid_at", "position", "rate" ,"amount","state","id"]
sleepTime = 900
dbManager = None
stocks = None


POSITIONURL = "https://api.robinhood.com/positions/"
def openCred():
    data = None
    with open(MYCRED, 'r') as file:
        data = json.load(file)
    return data
def setDbManager(dbm):
    global dbManager
    dbManager = dbm

def logInAndUpdate():
    t = openCred()
    KEY = t["KEY"]
    EMAIL = t["EMAIL"]
    PASSWD = t["PASSWD"]
    CODE = t["CODE"]

    LOGIN = robinhood.login(EMAIL, PASSWD, mfa_code = CODE)


    divs =  robinhood.get_dividends()
    stocks = robinhood.get_all_positions()
    for stock in stocks:
        if stock["url"] not in urlToTicker.keys():
            urlToTicker[stock["url"]] = stock['symbol']

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
def startThread():
    # t = openCred()
    # KEY = t["KEY"]
    # EMAIL = t["EMAIL"]
    # PASSWD = t["PASSWD"]
    # CODE = t["CODE"]

    # LOGIN = robinhood.login(EMAIL, PASSWD, mfa_code = CODE)


    # divs =  robinhood.get_dividends()
    # stocks = robinhood.get_all_positions()

#ORGNAIZE LATER WORK NOW
    divs = []
    while True:
        lastUpdate = datetime.datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
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

                
        
            
        print("finish update at " + str(datetime.datetime.now()))


        if(__name__ != "__main__" and len(divs) > 0):
            print("new divs added:")
            for div in divs:
               print(str(div))      
            dbManager.commit()
        
        time.sleep(sleepTime)
        newDivs = []
        try:
            newDivs = robinhood.get_dividends()
        except:
            print("robinhood failure")

        #TODO fix this
        divs = [item for item in newDivs if (item["paid_at"] != None and timeHelp.isAfterUpdate(item["paid_at"], lastUpdate) or item["state"] == "pending")]
        print(f"We have {len(divs)} of new dividends to insert into the table")


    

if __name__ == "__main__":

    startThread()


    
    