import sys
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, Qt, QModelIndex
from PyQt6.QtWidgets import *
import robinListener
import DatabaseManager
import threading
import datetime
import time
from PyQt6.QtCharts import *

DATABASE = "database/divabase.db"
DATABASE_MAN = None
MAX_RANGE_AXIS_RATIO = 1.05

class ColorDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        
        if value != None:
            if index.column() == 1:
                if isinstance(value, str):
                    month = value.split("-")[1]
                    month = int(month)
                    if month % 3 == 2:
                        brush = QBrush(QColor("blue"))
                    elif month % 3 == 1:
                        brush = QBrush(QColor("orange"))
                    elif month % 3 == 0:
                        brush = QBrush(QColor("green"))


                    painter.fillRect(option.rect, brush)
        super().paint(painter, option, index)



class divyTable(QTableView):
    def __init__(self):
      super().__init__()
    
      self.setModel(DATABASE_MAN.model)
      self.setItemDelegate(ColorDelegate())

      

    def filterByYear (self, year:str):
       DATABASE_MAN.setYearFilter(year)



class Worker(QObject):
    finished = pyqtSignal()
    sig = pyqtSignal(str)
    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def run(self):
        while True:
            # Your long-running task goes here
            if DATABASE_MAN.newUpdate:
                print("Running in the background...")
                self.sig.emit("FUCK THIS")
            # Add a small sleep to prevent excessive CPU usage
            QThread.msleep(1000)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFixedSize(1300,1010)
        self.setWindowTitle("Divindends")
        self.mainLayout = QVBoxLayout()
        
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)


        searchBarLayout = QHBoxLayout()
        searchBar = QTextEdit()
        searchBar.setPlaceholderText("Search")
        searchBar.setMaximumSize(175, 30)

        self.yearCombobox = QComboBox()
        comboBoxYears = []
        comboBoxYears.extend(DATABASE_MAN.getUniqueYears())
        
        self.yearCombobox.addItems(comboBoxYears)
        self.yearCombobox.currentIndexChanged.connect(self.newYearSelected)
        self.yearCombobox.setFixedWidth(100)
        searchBarLayout.addWidget(searchBar)
        
        searchBarLayout.addWidget(self.yearCombobox)
        self.mainLayout.addLayout(searchBarLayout)
        self.setLayout(self.mainLayout)
        
        self.panelLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.panelLayout)

        #Middle table
        self.table = self.buildTable()
        self.table.doubleClicked.connect(self.showPopUp)
        self.panelLayout.addWidget(self.table)
        
        

        
        

        #Graph
        self.graph_widget = QWidget(self)
        self.data_layout = QVBoxLayout()
        self.panelLayout.addLayout(self.data_layout)


        currYear = 0
        try:
            currYear = int(self.yearCombobox.currentText())
        except:
            pass
        self.setDiv = QBarSet(f"{currYear} dividends")
        
        year2024 = DATABASE_MAN.getMonthlyGraphDataset(currYear)

        self.setDiv.append(year2024.values())

        self.barSeries = QBarSeries()
        self.barSeries.append(self.setDiv)

        self.divChart = QChart()

        self.divChart.addSeries(self.barSeries)
        

        self.divChart.setTitle("Dividends per month")
        self.months = year2024.keys()
        print(self.months)
        self.x_axis = QBarCategoryAxis()
        self.x_axis.append(self.months)
        self.divChart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        
        self.y_axis.setRange(0, DATABASE_MAN.getMaxAmount() * MAX_RANGE_AXIS_RATIO)
        self.y_axis.setTitleText("$$$$")
        self.divChart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)

        self.barSeries.attachAxis(self.y_axis)

        self.chartView = QChartView(self.divChart)
        

        self.data_layout.addWidget(self.chartView)

        self.summDataLayout = QVBoxLayout()
        totalLayout = QHBoxLayout()
        totalLayout.addWidget(QLabel("Total"))
        self.totalAmountLabel = QLabel()

        averageLayout = QHBoxLayout()
        averageLayout.addWidget(QLabel("AMD"))

        self.AMDLabel = QLabel()
        averageLayout.addWidget(self.AMDLabel)

        totalLayout.addWidget(self.totalAmountLabel)
        self.summDataLayout.addLayout(totalLayout)
        self.summDataLayout.addLayout(averageLayout)
     

        
        
        self.data_layout.addLayout(self.summDataLayout)
        
        # time.sleep(20)
        self.start_thread()





    def start_thread(self):
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.sig.connect(self.doSomething)

        self.thread.start()

    def doSomething(self, p):
        print("it does something")
        if DATABASE_MAN.isNewyear:
            self.yearCombobox.clear()
            self.yearCombobox.addItems(DATABASE_MAN.getUniqueYears())
        
        if str(DATABASE_MAN.currYear) == self.yearCombobox.currentText():
            self.newYearSelected()
            self.y_axis.setRange(0, DATABASE_MAN.getMaxAmount() * MAX_RANGE_AXIS_RATIO)
        self.table.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        DATABASE_MAN.resetNewUpdate()
    

    def newYearSelected(self):
       
       self.barSeries.clear()
       
       newYear = self.yearCombobox.currentText()
       if newYear == "":
        return
       self.table.filterByYear(newYear)  
       newData = DATABASE_MAN.getMonthlyGraphDataset(newYear)
       self.setDiv = QBarSet(newYear + " dividends")
       self.setDiv.append(newData.values())
       self.barSeries.append(self.setDiv)

       sum = 0
       for d in newData.keys():
           sum += newData[d]

        #Cal calculate sum for average
       today = datetime.datetime.now()
       avgDiv = 0
       if(int(newYear) < today.year):
           avgDiv = sum / 12
       else:
           if today.month == 1:
               avgDiv = 0
           else:
               listOfPastMonths = list(newData.values())[:today.month - 1]
               s = 0
               for value in listOfPastMonths:
                   s += value
               avgDiv = s / len(listOfPastMonths)
       
       
       self.totalAmountLabel.setText(f"${sum:.2f}")
       self.AMDLabel.setText(f"${avgDiv:.2f}")
       
       self.chartView.setChart(self.divChart)
   

    def showPopUp(self):
        print('double click')
        selectedRow = self.table.selectedIndexes()
        sizeOfSelection = len(selectedRow)

        #Make sure it's a single row. correct later where you can only select one row at a time.
        if (sizeOfSelection != 6):
            return
        
        row_data = []
        for index in selectedRow:
            row_data.append(DATABASE_MAN.model.data(index, 0))

        
        
        # Create a popup window
        popupWindow = QMainWindow(self)
        
        popupWindow.setWindowModality(Qt.WindowModality.WindowModal)
        ticker = row_data[0]
        popupWindow.setWindowTitle(f"{ticker} divendend Report")
        popUpWidget = QWidget()
        
        popupWindow.setCentralWidget(popUpWidget)
        childLayout = QVBoxLayout()
        for data in row_data:
            childLayout.addWidget(QLabel(str(data)))
        popUpWidget.setLayout(childLayout)
        popupWindow.show()
        print("show pop up")



    def buildTable(self) -> divyTable:
       table = divyTable()
       table.setModel(DATABASE_MAN.model)
       table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

       table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
       table.verticalHeader().setVisible(False)
       table.hideColumn(3)
       table.hideColumn(7)
       table.setVisible(True)
       table.sortByColumn(1, Qt.SortOrder.DescendingOrder)
       return table





if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = QSqlDatabase.addDatabase("QSQLITE")  # Add your database driver
    db.setDatabaseName(DatabaseManager.DIVABASE_PATH)
    db.open()
    DATABASE_MAN = DatabaseManager.DatabaseManager(db)
   
    robinListener.dbManager = DATABASE_MAN
    robinListener.logInAndUpdate()
    t = threading.Thread(target=robinListener.startThread, daemon=True)
    t.start()
    


    window = MainWindow()
    window.show()
    sys.exit(app.exec())