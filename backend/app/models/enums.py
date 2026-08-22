from enum import StrEnum


class StudentStatus(StrEnum):
    ACTIVE = "active"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"


class ClubStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class MembershipRole(StrEnum):
    MEMBER = "member"
    CORE = "core"
    LEADER = "leader"


class MembershipStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ActivityStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RegistrationStatus(StrEnum):
    REGISTERED = "registered"
    CANCELLED = "cancelled"
    WAITLISTED = "waitlisted"


class RegistrationSource(StrEnum):
    WEB = "web"
    IMPORT = "import"
    GENERATED = "generated"


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"


class UserRole(StrEnum):
    ADMIN = "admin"
    CLUB_MANAGER = "club_manager"
    STUDENT = "student"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
