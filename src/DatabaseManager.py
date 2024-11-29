import sqlite3
from os.path import exists
from PyQt6.QtWidgets import *
from PyQt6.QtSql import *
from PyQt5.QtCore import QObject, Qt, QModelIndex
from PyQt6.QtGui import QBrush, QColor
import calendar
import datetime
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
                if index.column() == 4 or index.column() == 5:
                    return f"${value:,.2f}"  # Format as currency
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
        
        self.model = LewSQLModel(None, db)
        self.model.setTable(DIVABASE_TABLE)
        self.currYear = self.getLatestYear()
        self.model.select()
        self.pendingDict = {}




        self.isNewyear = False

    def setYearFilter(self, year:str):
        self.model.setFilter(f"DATE(paid_at) BETWEEN '{year}-01-01T00:00:00.00' AND '{year}-12-31T23:59:59.99'")
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
            self.model.submit()

    def updateState(self, div:dict):
        db = self.model.database()
        q = QSqlQuery(db)
        paid = div['paid_at']
        if paid == None:
            return
        state = div['state']
        id = div['id']
        q.prepare('''
                UPDATE
                    divabase
                SET
                    paid_at = :paid
                    state= :state
                WHERE
                    id = :id
                    
               ''')
        q.bindValue(":paid", paid)
        q.bindValue(":state", state)
        q.bindValue(":id", id)

        q.exec()
        
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


    def commit(self):
        self.model.select()

if __name__ == "__main__":
   app = QApplication([])
   db = QSqlDatabase.addDatabase("QSQLITE")  # Add your database driver
   db.setDatabaseName(DIVABASE_PATH)
   db.open()
   DATABASE_MAN = DatabaseManager(db)
   
   print(DATABASE_MAN.getLatestYear())

   app.exec()