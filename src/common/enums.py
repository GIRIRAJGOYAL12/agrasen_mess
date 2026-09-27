import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    STAFF = "staff"
    ADMIN = "admin"


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


class EntryMethod(str, enum.Enum):
    QR = "qr"
    MANUAL = "manual"