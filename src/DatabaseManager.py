import sqlite3
from os.path import exists
from PyQt6.QtWidgets import *
from PyQt6.QtSql import *
from PyQt5.QtCore import QObject, Qt, QModelIndex, QDate, QDateTime
from PyQt6.QtGui import QBrush, QColor
import calendar
import datetime
import timeUltil
import sys

DIVABASE_PATH = "/home/jonathan/Repo/DIVinator/src/divabase.db"
DIVABASE_TABLE = "divabase"

class ColorDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        if index.row() % 2 == 0:
            painter.fillRect(option.rect, QBrush(QColor("lightblue")))
        super().paint(painter, option, index)

class LewSQLModel(QSqlTableModel):
    def __init__(self, parent: QObject | None = ..., db: QSqlDatabase = ...) -> None:
        
        super().__init__(parent, db)
        


    
    def data(self, index: QModelIndex, role):
        if role == Qt.ItemDataRole.DisplayRole:
            value = super().data(index, role)
            if isinstance(value, float):
                if index.column() == 5:
                    return f"${value:,.2f}"  # Format as currency
                elif (index.column() == 4):
                    return f"${value:,.4f}"
            else:
                colIndex = index.column()
                if colIndex == 1:
                    return value.split("T")[0]


        return super().data(index, role)

if not exists(DIVABASE_PATH):
  with open(DIVABASE_PATH, "x") as f:
    pass




class DatabaseManager():



    # def filterByYear (self, year:str):
    #    self.model.setFilter(f"DATE(paid_at) BETWEEN '{year}-01-01T00:00:00.00' AND '{year}-12-31T23:59:59.99'")

    # def sumAmount (self):
    #    output = 0
    #    for i in range(self.model.rowCount()):
    #     output += self.model.data(self.model.index(i, ))

    def __init__(self, db):
        self.conn = sqlite3.connect(DIVABASE_PATH, check_same_thread=False)
        self.curs = self.conn.cursor()
        self.curs.execute("""
                CREATE TABLE IF NOT EXISTS divabase (
                          ticker text,
                          paid_at text,
                          position real,
                          placeholder real,
                          rate real,
                          amount real,
                          state text,
                          id text,
                          UNIQUE(id)
                );""")
        self.conn.commit()
        
        self.newUpdate = True
        self.newUpdates = False
        
        self.model = LewSQLModel(None, db)
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnRowChange)
        self.model.setTable(DIVABASE_TABLE)
        self.currYear = self.getLatestYear()
        self.model.select()
        self.pendingDict = {}




        self.isNewyear = False

    def setYearFilter(self, year:str):
        self.model.setFilter(f"DATE(paid_at) BETWEEN '{year}-01-01T00:00:00.00' AND '{year}-12-31T23:59:59.99'")
        self.model.select()

    def setTextFilter(self, text:str, year:str):
        self.model.setFilter(f"(DATE(paid_at) BETWEEN '{year}-01-01T00:00:00.00' AND '{year}-12-31T23:59:59.99') AND ticker LIKE '{text}%'")
        self.model.select()

    

    def setYear(self):
        self.currYear = str(datetime.datetime.now().year)

    def insertDiv(self, div:dict):
        r = self.model.record()
        
        for key in div.keys():
            
            value = div[key]
            try:
                value = float(value)
            except ValueError:
                pass

            r.setValue(key, value)
        


        #self.model.database().exec()
        if self.model.insertRowIntoTable(r):
            self.newUpdate = True
            newDivDate = div["paid_at"]
            newDivYear = newDivDate.split("-")[0]
            if self.currYear == None:
                self.currYear = -69

            if int(newDivYear) > int(self.currYear):
                self.isNewyear = True
                self.currYear = newDivYear
        
            self.model.submit()
        elif div['state'] != self.getState(div['id']):
            #If the state of the div changes
            print("updates state of " + div['ticker'])
            self.newUpdate = True
            self.updateState(div)
            self.model.submitAll()

    def updateState(self, div:dict):
        # db = self.model.database()
        # q = QSqlQuery(db)
        # self.model.find
        # paid = div['paid_at']
        # if paid == None:
        #     return
        # state = div['state']
        # id = div['id']
        # q.prepare('''
        #         UPDATE
        #             divabase
        #         SET
        #             paid_at = :paid
        #             state= :state
        #         WHERE
        #             id = :id
                    
        #        ''')
        # q.bindValue(":paid", paid)
        # q.bindValue(":state", state)
        # q.bindValue(":id", id)

        # q.exec()
        newState = div["state"]
        id = div["id"] 
        self.curs.execute ("""
                                UPDATE
                                    divabase   
                                SET
                                    state = ?
                                    WHERE
                                        id = ?""", (newState, id,))
        self.conn.commit()

        

        
    


    def getIndexFromId(self, id_value) -> int:
        for row in range(self.model.rowCount()):
            record = self.model.record(row)
            if record.value("id") == id_value:  # Assuming "id" is the primary key column
                return row  # Return the index of the first column in the row

        return -1  # Return an invalid index if not found

        
    def getState(self, id):
        db = self.model.database()
        q = QSqlQuery(db)
        q.prepare('''SELECT state
                     FROM
                        divabase
                    WHERE
                        id =:id
                ''')
        q.bindValue(":id", id)
        if q.exec():  
                while q.next():
                    return q.value(0)






    def isNewyear(self):
        return self.isNewyear
    
    def getMaxAmount(self):
        max = 0
        years = self.getUniqueYears()
        
        i = 0
        for year in years:
            year = int(year)
            divPerMonthDict = self.getMonthlyGraphDataset(year)
            for div in divPerMonthDict.values():
                if(div > max):
                    max = div
            i += 1


        return max

    def getSumRateYTD(self, ticker):
        db = self.model.database()
        q = QSqlQuery(db)
        q.prepare('''
        SELECT
            max(paid_at) FROM divabase
            WHERE ticker = :ticker
        ''')
        q.bindValue(":ticker", ticker)
        dateMostCurr = None
        if q.exec():
            if q.next():
                dateStr = q.value(0)
                dateMostCurr = datetime.datetime.strptime(dateStr, timeUltil.FORMAT)
        
        if dateMostCurr == None:
            return -1.0
        
        dateYearAgo = dateMostCurr - datetime.timedelta(days=340) #15 days subtracted to not include last years dividend maybe.

        q.prepare('''
        SELECT SUM(rate)
        FROM divabase
        WHERE paid_at BETWEEN :start_date and :end_date
        AND ticker = :ticker
        ''')
        q.bindValue(":end_date", dateMostCurr.strftime(timeUltil.FORMAT))
        q.bindValue(":start_date", dateYearAgo.strftime(timeUltil.FORMAT))
        q.bindValue(":ticker", ticker)
        output = 0
        if q.exec():
            if q.next():
                output = q.value(0)

        return output




    def getMonthlyGraphList(self, year):
        output = {}

        output["pending"] = []
        output["paid"] = []
        output["reinvested"] = []
        output["reinvesting"] = []
        db = self.model.database()
        q = QSqlQuery(db)
        month = 1
        while month <= 12:
            total = 0
            for state in output.keys():
                q.prepare('''SELECT SUM(amount) FROM divabase
                    WHERE strftime('%Y', paid_at) = :year
                    AND strftime('%m', paid_at) = :month
                    AND state = :state
                    ''')
                q.bindValue(":year", str(year))
                q.bindValue(":month", str(month).zfill(2))
                q.bindValue(":state", state)
                if q.exec():
                    if q.next():
                        total = q.value(0)
                        if total != "":
                            total = float(total)
                        else:
                            total = 0
                        output[state].append(total)
                     
                else:
                    print("not good!!", q.lastError().text())
            month += 1

        return output



    def getMonthlyGraphDataset(self, year:int) -> dict:
        
        output = {}
        #database = QSqlDatabase()
        db = self.model.database()
        q = QSqlQuery(db)
        month = 1
        while month <= 12:
            total = 0
            q.prepare('''SELECT SUM(amount) FROM divabase
                WHERE strftime('%Y', paid_at) = :year
                AND strftime('%m', paid_at) = :month
                ''')
            q.bindValue(":year", str(year))
            q.bindValue(":month", str(month).zfill(2))
            if q.exec():
                if q.next():
                    total = q.value(0)
                    if total != "":
                        total = float(total)
                    else:
                        total = 0
                     
            else:
                print("not good!!", q.lastError().text())
            

            
            monthName = calendar.month_name[month]
            output[monthName[:3]] = total
            month += 1
        
        return output

    def getUniqueYears(self) :
        db = self.model.database()
        q = QSqlQuery(db)

        q.prepare('''
                    SELECT DISTINCT strftime('%Y', paid_at) as year
                    FROM divabase
                  ''')
        output = []
        if q.exec():  
                while q.next():
                    output.append(q.value(0))
        return output
    

    
    def getLatestYear(self):
        years = self.getUniqueYears()
        if len(years) == 0:
            return None
        return years[0]


    def resetNewUpdate(self):
        self.isNewyear = False
        self.newUpdate = False
        self.newUpdates = False

    def getPaidToRateData(self, ticker:str):
        db = self.model.database()
        q = QSqlQuery(db)

        q.prepare('''
            SELECT paid_at,rate
            FROM divabase
            WHERE ticker = :ticker
        ''')
        q.bindValue(":ticker", ticker)
        output = []
        if q.exec():
            
            while q.next():
                qdatetime = self.convertToQDatetime(q.value(0))
                if not qdatetime.isValid():
                    print("does not workd!" + q.value(0))
                output.append((qdatetime.toMSecsSinceEpoch(), q.value(1)))

        return output

    def convertToQDatetime(self, strDate:str):
        strDay = strDate.split("T")[0]
        dayStrList = strDay.split('-')


        return QDateTime(int(dayStrList[0]), int(dayStrList[1]), int(dayStrList[2]), 0, 0 ,0, 0, 1)

    def commit(self):
        self.model.select()

if __name__ == "__main__":
   app = QApplication([])
   db = QSqlDatabase.addDatabase("QSQLITE")  # Add your database driver
   db.setDatabaseName(DIVABASE_PATH)
   db.open()
   DATABASE_MAN = DatabaseManager(db)
   xxx = DATABASE_MAN.getSumRateYTD("KMB")
   

   app.exec()