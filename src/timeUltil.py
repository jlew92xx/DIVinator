from datetime import datetime, timezone, timedelta
import pytz
FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
def isAfterUpdate(divTime:str, lastUpdate:str):
    
    return datetime.strptime(divTime, FORMAT) >  datetime.strptime(lastUpdate, FORMAT)


