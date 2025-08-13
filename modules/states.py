class UserState:
    """Possible conversation states for regular users."""

    IDLE = "IDLE"
    WAITING_FOR_ID = "WAITING_FOR_ID"
    WAITING_FOR_REQUEST_BUTTON = "WAITING_FOR_REQUEST_BUTTON"

class AdminState:
    """States for admin interactions."""

    IDLE = "IDLE"
