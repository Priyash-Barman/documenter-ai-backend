from enum import StrEnum, IntEnum

class LogType(StrEnum):
    """Types of log entries"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class UserRole(StrEnum):
    """User role types"""
    END_USER = "end_user"
    ADMIN = "admin"

class TransactionStatus(StrEnum):
    """Transaction status values"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"

class PackageType(StrEnum):
    """Package type classification"""
    USER = "user"
    APP = "app"

class SubscriptionStatus(StrEnum):
    """Subscription lifecycle states"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"

class HTTPMethod(StrEnum):
    """Supported HTTP methods for API docs"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class Currency(StrEnum):
    """Supported currency codes (ISO 4217)"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AUD = "AUD"
    CAD = "CAD"
    CHF = "CHF"
    CNY = "CNY"
    SEK = "SEK"
    NZD = "NZD"

class AuthenticationLevel(IntEnum):
    """API authentication requirement levels"""
    NONE = 0
    BASIC = 1
    BEARER_TOKEN = 2
    OAUTH2 = 3
    API_KEY = 4