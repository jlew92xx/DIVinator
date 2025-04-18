from datetime import datetime, timezone, timedelta
import pytz
FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
PAYABLE_FORMAT = '%Y-%m-%d'
def isAfterUpdate(divTime:str, lastUpdate:str):
    
    return datetime.strptime(divTime, FORMAT) >  datetime.strptime(lastUpdate, FORMAT)


