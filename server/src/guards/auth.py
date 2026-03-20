import hashlib
import hmac

from loguru import logger

from src.schemas.auth import AuthResult, UserACL

_DEFAULT_ACL = UserACL()
_ADMIN_ACL = UserACL(can_access_other_users=True)


class AuthGuard:
    def __init__(self, secret: str = "", dev_mode: bool = True, admin_ids: set[str] | None = None) -> None:
        self._secret = secret.encode() if secret else b""
        self._dev_mode = dev_mode
        self._admin_ids = admin_ids or set()

    def authenticate(self, user_id: str, signature: str = "") -> AuthResult:
        if not user_id:
            return AuthResult(False, user_id, "user_id required")

        if self._dev_mode:
            return AuthResult(True, user_id)

        if user_id == "default":
            return AuthResult(False, user_id, "user_id required")

        if not self._secret:
            return AuthResult(False, user_id, "auth secret not configured")

        expected = hmac.new(self._secret, user_id.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, signature):
            return AuthResult(True, user_id)

        logger.warning(f"Auth failed: user_id={user_id}")
        return AuthResult(False, user_id, "invalid signature")

    def authorize(self, user_id: str, tool_name: str) -> bool:
        acl = _ADMIN_ACL if user_id in self._admin_ids else _DEFAULT_ACL
        if tool_name not in acl.allowed_tools:
            logger.warning(f"ACL denied: {user_id} → {tool_name}")
            return False
        return True
