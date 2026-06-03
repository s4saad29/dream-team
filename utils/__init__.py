from utils.auth_helper import (
    STORAGE_STATE_PATH,
    ensure_authenticated_context,
    is_authenticated,
    login_via_microsoft,
    save_authenticated_session,
    save_storage_state,
    storage_state_exists,
)
from utils.report_dashboard import TestResult, generate_dashboard

__all__ = [
    "STORAGE_STATE_PATH",
    "TestResult",
    "ensure_authenticated_context",
    "generate_dashboard",
    "is_authenticated",
    "login_via_microsoft",
    "save_authenticated_session",
    "save_storage_state",
    "storage_state_exists",
]
