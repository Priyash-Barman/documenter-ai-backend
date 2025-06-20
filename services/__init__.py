from services.auth_service import AuthService
from services.converter_service import ConverterService
from services.package_service import PackageService
from services.user_service import UserService
from services.app_service import AppService
from services.api_doc_service import ApiDocService
from services.transaction_service import TransactionService
from services.subscription_service import SubscriptionService
from services.history_service import HistoryService
from services.log_service import LogService
from db.mongo import mongo

class ServiceContainer:
    def __init__(self):
        self.user_service = UserService(mongo)
        self.package_service = PackageService(mongo)
        self.app_service = AppService(mongo)
        self.api_doc_service = ApiDocService(mongo)
        self.transaction_service = TransactionService(mongo)
        self.subscription_service = SubscriptionService(mongo)
        self.history_service = HistoryService(mongo)
        self.log_service = LogService(mongo)
        self.auth_service = AuthService(mongo)
        self.converter_service = ConverterService(mongo)

services = ServiceContainer()
