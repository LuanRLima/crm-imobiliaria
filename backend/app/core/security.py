from base64 import urlsafe_b64decode, urlsafe_b64encode
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest
from secrets import token_bytes

import bcrypt

BCRYPT_PREFIX = "bcrypt$"


def _ensure_bytes(value: str) -> bytes:
    return value.encode("utf-8")


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(_ensure_bytes(password), bcrypt.gensalt(rounds=12))
    return f"{BCRYPT_PREFIX}{hashed.decode('utf-8')}"


def _verify_legacy_pbkdf2_password(password: str, password_hash: str) -> bool:
    encoded_salt, stored_digest = password_hash.split("$", maxsplit=1)
    salt = urlsafe_b64decode(encoded_salt.encode("utf-8"))
    digest = pbkdf2_hmac("sha256", _ensure_bytes(password), salt, 100_000).hex()
    return compare_digest(digest, stored_digest)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        if password_hash.startswith(BCRYPT_PREFIX):
            return bcrypt.checkpw(
                _ensure_bytes(password),
                password_hash.removeprefix(BCRYPT_PREFIX).encode("utf-8"),
            )

        return _verify_legacy_pbkdf2_password(password, password_hash)
    except (ValueError, TypeError):
        return False


def password_hash_needs_upgrade(password_hash: str) -> bool:
    return not password_hash.startswith(BCRYPT_PREFIX)


def create_access_token() -> str:
    return urlsafe_b64encode(token_bytes(32)).decode("utf-8").rstrip("=")


def hash_token(token: str) -> str:
    return sha256(_ensure_bytes(token)).hexdigest()
