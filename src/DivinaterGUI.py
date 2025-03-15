import sys
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, Qt, QModelIndex, QItemSelection
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

listOfLabelHeader = ["Number Of Shares", "Average Price", "Current Price", "Payment Schedule" ,"Average Yield", "Total Capital Gains", "Total Dividend" , "Total Return"]
class YearDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        value = index.siblingAtColumn(0).data(Qt.ItemDataRole.DisplayRole)
        font = QFont()
        if(value == "Total"):
            font.setBold(True)
            font.setPointSize(15)
        elif(value == 'AMD'):
            font.setPointSize(13)
        else:
            month = index.row() + 1
            if month % 3 == 2:
                brush = QBrush(QColor("blue"))
            elif month % 3 == 1:
                brush = QBrush(QColor("orange"))
            elif month % 3 == 0:
                brush = QBrush(QColor("green"))

            painter.fillRect(option.rect, brush)

            
            
        
        

        option.font = font
        super().paint(painter, option, index)

class ValueLayout(QHBoxLayout):
    def __init__(self, labelName:str):
        super().__init__()
        self.setSpacing(1)
        self.labelLabel = QLabel()
        self.labelLabel.setText(labelName + ":")
        self.addWidget(self.labelLabel)

        self.valueLabel = QLabel("-")
        self.addWidget(self.valueLabel)

    def setData(self, newData):
        self.valueLabel.setText(newData)

class DetailsLayout(QVBoxLayout):
    ADDITIONALDETS = "'s Additional Details"
    def __init__(self):
        super().__init__()
        self.titleLabel = QLabel()
        titleFont = QFont()
        titleFont.setPointSize(20)
        self.titleLabel.setFont(titleFont)
        self.titleLabel.setText("---" + self.ADDITIONALDETS)
        self.addWidget(self.titleLabel)
        self.detailsLabelDict = {}
        for labelStr in listOfLabelHeader:
            valueLayout = ValueLayout(labelStr)
            self.detailsLabelDict[labelStr] = valueLayout
            self.addLayout(valueLayout)

        self.addSpacerItem(QSpacerItem(309, 260, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))

    def onSelectionChange(self, ticker:str, newData:dict):
        self.titleLabel.setText(ticker + self.ADDITIONALDETS)
        for labelStr in newData.keys():
            qLabel:ValueLayout = self.detailsLabelDict[labelStr]
            qLabel.setData(newData[labelStr])




class ColorDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        value = index.siblingAtColumn(1).data(Qt.ItemDataRole.DisplayRole)
        if value != None:
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
        
        value = index.siblingAtColumn(6).data(Qt.ItemDataRole.DisplayRole)
        
        font = QFont()
        if value == "paid" or value == "reinvested" or value == "reinvesting":
            font.setBold(True)
            
        if value == "pending" or value == "reinvesting":
            font.setItalic(True)

        

        option.font = font
        super().paint(painter, option, index)



class YearTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("heyt")
        self.setRowCount(14)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["month", "Total", "Last Year +/-"])
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        #self.horizontalHeader().setVisible(False)
        self.setItemDelegate(YearDelegate())
        self.setVisible(True)
        
    def calcAMD(self, newData:dict, newYear):
         #Cal calculate sum for average
       today = datetime.datetime.now()
       avgDiv = 0
       if(int(newYear) < today.year):
           sum = 0
           for value in newData.values():
               sum += value
           avgDiv = sum / 12
       elif (int(newYear) > today.year):
           avgDiv = 0 
       else:
           if today.month == 1:
               avgDiv = 0 
           else:
               listOfPastMonths = list(newData.values())[:today.month - 1]
               s = 0
               for value in listOfPastMonths:
                   s += value
               avgDiv = s / len(listOfPastMonths)
       return avgDiv
    

    def sumTotalYear(self, newData:dict):
        sum = 0
        for d in newData.keys():
           sum += newData[d]
        return sum


    def setTableData(self, currYear):
        monthlyAmountDict = DATABASE_MAN.getMonthlyGraphDataset(currYear)
        lastYearAmountDict = DATABASE_MAN.getMonthlyGraphDataset(currYear - 1)
        amd = self.calcAMD(monthlyAmountDict, currYear)
        lastAmd = self.calcAMD(lastYearAmountDict, currYear - 1)
        total = self.sumTotalYear(monthlyAmountDict)
        lastTotal = self.sumTotalYear(lastYearAmountDict)
        row = 0
        for monthStr in monthlyAmountDict.keys():
            self.setItem(row, 0, QTableWidgetItem(monthStr + " " + str(currYear)))
            amount = monthlyAmountDict[monthStr]
            self.setItem(row, 1, QTableWidgetItem(f"${amount:,.2f}"))
            diff = 0
            if (amount != 0):
                diff = amount - lastYearAmountDict[monthStr]
            self.setItem(row, 2, QTableWidgetItem(f"${diff:,.2f}"))
            row += 1
        self.setItem(row, 0, QTableWidgetItem("AMD"))
        self.setItem(row, 1, QTableWidgetItem(f"${amd:,.2f}"))
        diff = amd - lastAmd
        self.setItem(row, 2, QTableWidgetItem(f"${diff:,.2f}"))

        row += 1
        self.setItem(row, 0, QTableWidgetItem("Total"))
        self.setItem(row, 1, QTableWidgetItem("$" +f"{total:,.2f}"))
        diff = total - lastTotal
        self.setItem(row, 2, QTableWidgetItem(f"${diff:,.2f}"))




class divyTable(QTableView):
    def __init__(self):
      super().__init__()
    
      self.setModel(DATABASE_MAN.model)
      self.setItemDelegate(ColorDelegate())


      

    def filterByYear (self, year:str):
       DATABASE_MAN.setYearFilter(year)

    def filterByText(self, text:str, year:str):
        DATABASE_MAN.setTextFilter(text, year)



class Worker(QObject):
    finished = pyqtSignal()
    sig = pyqtSignal(str)
    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def run(self):
        while True:
            print("Thread updates...")
            robinListener.logInAndUpdate()
            # Your long-running task goes here
            if DATABASE_MAN.newUpdate:
                print("Running in the background...")
                self.sig.emit("This")
            # Add a small sleep to prevent excessive CPU usage
            QThread.msleep(900000)
            

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFixedSize(1300,1010)
        self.setWindowTitle("Divinater")
        self.mainLayout = QVBoxLayout()
        
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)


        searchBarLayout = QHBoxLayout()
        self.searchBar = QTextEdit()
        self.searchBar.setPlaceholderText("Search")
        self.searchBar.setMaximumSize(175, 30)

        self.searchBar.textChanged.connect(self.onTextChange)

        self.yearCombobox = QComboBox()
        comboBoxYears = []
        comboBoxYears.extend(DATABASE_MAN.getUniqueYears())
        comboBoxYears.sort(reverse=True)
        self.yearCombobox.addItems(comboBoxYears)
        self.yearCombobox.currentIndexChanged.connect(self.newYearSelected)
        self.yearCombobox.setFixedWidth(100)
        searchBarLayout.addWidget(self.searchBar)
        
        searchBarLayout.addWidget(self.yearCombobox)
        self.mainLayout.addLayout(searchBarLayout)
        self.setLayout(self.mainLayout)
        
        self.panelLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.panelLayout)

        #Middle table
        self.table = self.buildTable()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.filterByYear(self.yearCombobox.currentText())
        self.table.doubleClicked.connect(self.showPopUp)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.panelLayout.addWidget(self.table)
        self.table.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        

        
        

        #Graph
        self.graph_widget = QWidget(self)
        self.data_layout = QVBoxLayout()
        self.panelLayout.addLayout(self.data_layout)


        currYear = 0
        try:
            currYear = int(self.yearCombobox.currentText())
        except:
            pass

        self.reinvestedSet = QBarSet(f"Reinvested")
        self.pendingSet = QBarSet(f"Pending")
        self.paidSet = QBarSet(f"Paid")
        self.reinvestingSet = QBarSet(f"Reinvesting")
        
        divGraphDict = DATABASE_MAN.getMonthlyGraphList(currYear)


        self.reinvestedSet.append(divGraphDict["reinvested"])
        self.paidSet.append(divGraphDict["paid"])
        self.reinvestingSet.append(divGraphDict['reinvesting'])
        self.pendingSet.append(divGraphDict["pending"])



        

        self.barSeries = QStackedBarSeries()

        self.barSeries.append(self.reinvestedSet)
        self.barSeries.append(self.paidSet)
        self.barSeries.append(self.reinvestingSet)
        self.barSeries.append(self.pendingSet)

        self.divChart = QChart()
        # QFron
        # self.divChart.setFont()
        # self.divChart.setBackgroundBrush(QBrush(QColor(200, 200, 200, 0)))

        self.divChart.addSeries(self.barSeries)
        

        self.divChart.setTitle("Dividends per month")
        #BAD BAD
        self.months = DATABASE_MAN.getMonthlyGraphDataset(currYear).keys()
        self.x_axis = QBarCategoryAxis()
        self.x_axis.append(self.months)
        self.divChart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        
        self.y_axis.setRange(0, DATABASE_MAN.getMaxAmount() * MAX_RANGE_AXIS_RATIO)
        self.y_axis.setTitleText("$$$$")
        self.y_axis.setLabelFormat("$%.2f")
        self.divChart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)

        self.barSeries.attachAxis(self.y_axis)

        self.chartView = QChartView(self.divChart)
        

        self.data_layout.addWidget(self.chartView)

        self.yearTableAndAdditLayout = QHBoxLayout()
        self.data_layout.addLayout(self.yearTableAndAdditLayout)
        self.yearTable = YearTable()
        
        self.yearTable.setTableData(currYear)
        self.yearTable.setVisible(True)



        self.yearTableAndAdditLayout.addWidget(self.yearTable)

        self.detailsLayout = DetailsLayout()
        self.yearTableAndAdditLayout.addLayout(self.detailsLayout)


     

        
        
        
        
        # time.sleep(20)
        self.start_thread()


    
    def onSelectionChanged(self, selected:QItemSelection, deselected):
        selectedRow  = selected.indexes()
        ticker = self.table.model().data(selectedRow[0], 0)
        print("ticker: " + ticker)
        detailsDict = {}
        numOfSharesStr:str = listOfLabelHeader[0]
        numShare =robinListener.getNumShares(ticker)
        if (numShare == None):
            numShare = 0
        detailsDict[numOfSharesStr] = f"{numShare:,.4f}"

        averageStr = listOfLabelHeader[1]
        averageStock = robinListener.getAvgStockPrice(ticker)
        detailsDict[averageStr]= f"${averageStock:,.2f}"

        currentPrStr = listOfLabelHeader[2]
        currentPrFlo = robinListener.getCurrentPrice(ticker)
        detailsDict[currentPrStr] = f"${currentPrFlo:,.2f}"

        paymentSchedStr = listOfLabelHeader[3]
        countInt = DATABASE_MAN.getLastYearDivCount(ticker)
        #listOfPaymentSched = ("Quart.", "Monthly", "Weird", "N/A")
        
        if countInt == 4:
            paymentSchedType = "Quart."
        elif countInt == 12:
            paymentSchedType = "Monthly"
        else:
            paymentSchedType = "N/A"
        
        detailsDict[paymentSchedStr] = paymentSchedType

        averageYieldStr = listOfLabelHeader[4]
        averageYieldFlo = "N/A"
        if(averageStock != 0 and paymentSchedType != "N/A"):
            latestAmount = DATABASE_MAN.getLastRateForDiv(ticker)
            averageYieldFlo = 100 * (latestAmount * countInt) / averageStock
            averageYieldFlo = f"{averageYieldFlo:.4}%"
        detailsDict[averageYieldStr] = averageYieldFlo


        tcpStr = listOfLabelHeader[-3] #capital gains#
        tcpFlo = numShare * (currentPrFlo - averageStock)
        detailsDict[tcpStr] = f"${tcpFlo:,.2f}"

        totalDivFlo = DATABASE_MAN.getTotalDivForTicker(ticker)
        totalDivStr = listOfLabelHeader[-2]
        detailsDict[totalDivStr] = f"${totalDivFlo:,.2f}"

        totalRetStr =  listOfLabelHeader[-1]
        totalRetFlo = totalDivFlo + tcpFlo
        detailsDict[totalRetStr] = f"${totalRetFlo:,.2f}"


        self.detailsLayout.onSelectionChange(ticker, detailsDict)
        

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
            years = DATABASE_MAN.getUniqueYears()
            years.sort(reverse=True)
            self.yearCombobox.addItems(years)
        
        if str(DATABASE_MAN.currYear) == self.yearCombobox.currentText():
            self.newYearSelected()
            self.y_axis.setRange(0, DATABASE_MAN.getMaxAmount() * MAX_RANGE_AXIS_RATIO)
        self.table.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        DATABASE_MAN.resetNewUpdate()


    def onTextChange(self):
        self.table.filterByText(self.searchBar.toPlainText(), self.yearCombobox.currentText())
    
    
    def newYearSelected(self):
       
       self.barSeries.clear()
       self.searchBar.clear()
       newYear = self.yearCombobox.currentText()
       if newYear == "":
        return
       self.table.filterByYear(newYear)
       self.yearTable.setTableData(int(newYear))

       self.reinvestedSet = QBarSet(f"Reinvested")
       self.pendingSet = QBarSet(f"Pending")
       self.reinvestingSet = QBarSet("Reinvesting")
       self.paidSet = QBarSet(f"Paid")
        
       divGraphDict = DATABASE_MAN.getMonthlyGraphList(newYear)


       self.reinvestedSet.append(divGraphDict["reinvested"])
       self.paidSet.append(divGraphDict["paid"])
       self.reinvestingSet.append(divGraphDict["reinvesting"])
       self.pendingSet.append(divGraphDict["pending"])

       self.barSeries.append(self.reinvestedSet)
       self.barSeries.append(self.paidSet)
       self.barSeries.append(self.reinvestingSet)
       self.barSeries.append(self.pendingSet)


       newData = DATABASE_MAN.getMonthlyGraphDataset(newYear)
       


       
       self.chartView.setChart(self.divChart)
   
    def calculateAverageYield(ticker:str) -> float:

        avgStockBuyPrice = float(robinListener.getAvgStockPrice(ticker))
        rateYTD = DATABASE_MAN.getSumRateYTD(ticker)
        averageYield = 0
        if (avgStockBuyPrice != 0):
            averageYield = (rateYTD / avgStockBuyPrice) * 100

        return averageYield
    
    def showPopUp(self):
        
        selectedRow = self.table.selectedIndexes()
        sizeOfSelection = len(selectedRow)

        
        row_data = []
        for index in selectedRow:
            row_data.append(DATABASE_MAN.model.data(index, 0))

        
        
        # Create a popup window
        popupWindow = QMainWindow(self)
        
        popupWindow.setWindowModality(Qt.WindowModality.WindowModal)
        popupWindow.setMinimumSize(500, 420)
        ticker = row_data[0]
        
        

        popupWindow.setWindowTitle(f"{ticker} dividend Report")
        popUpWidget = QWidget()
        
        popupWindow.setCentralWidget(popUpWidget)
        childLayout = QVBoxLayout()
        # for data in row_data:
        #     childLayout.addWidget(QLabel(str(data)))

        ticker = row_data[0]
        chart = self.buildRateGraph(ticker)
        popupWindow.setCentralWidget(chart)
        popUpWidget.setLayout(childLayout)
        popupWindow.show()
        print("show pop up")

    def buildRateGraph (self, ticker:str) -> QChartView:
        chart = QChart()
        data = DATABASE_MAN.getPaidToRateData(ticker)
        series = QLineSeries()
        series.setName(ticker + "'s Dividend rate")
        min = 1000000
        max = 0
        for dt, value in data:
            if value < min:
                min = value
            if value > max:
                max = value
            series.append(dt, value)
        
        chart.addSeries(series)
        axis_x = QDateTimeAxis()
        axis_x.setTickCount(5)
        axis_x.setFormat("MMM yyyy")
        axis_x.setTitleText("Date")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        series.setBestFitLineVisible(False)

        # Create and set the Y-axis (QValueAxis)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.3f/%")
        if(min == max):
            min *= .5
            max *= 1.5
        axis_y.setRange(min, max)
        
        axis_y.setTitleText("Value")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        # Create the chart view
        chart_view = QChartView(chart)
        
        return chart_view



    def buildTable(self) -> divyTable:
       table = divyTable()
       table.setModel(DATABASE_MAN.model)
       table.resizeColumnsToContents()
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
    robinListener.logIn()
    robinListener.buildURLToTickerDict()
    # robinListener.logInAndUpdate()
    # t = threading.Thread(target=robinListener.startThread, daemon=True)
    # t.start()

    

    window = MainWindow()
    window.show()
    sys.exit(app.exec())