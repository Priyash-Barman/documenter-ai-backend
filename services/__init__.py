from services.auth_service import AuthService
from services.user_service import UserService
from db.mongo import mongo

class ServiceContainer:
    def __init__(self):
        self.user_service = UserService(mongo)
        # self.auth_service = AuthService(mongo)

services = ServiceContainer()
