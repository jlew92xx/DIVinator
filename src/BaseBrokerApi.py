from DatabaseManager import DatabaseManager
class BaseBrokerApi:
    DATABASEMANAGER:DatabaseManager
    CRED_DIRECT = 'Cred/'
    @staticmethod
    def setDatabaseManager(input:DatabaseManager):
        DATABASEMANAGER = input
