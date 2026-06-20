from base64 import urlsafe_b64decode, urlsafe_b64encode
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest
from secrets import token_bytes


def _ensure_bytes(value: str) -> bytes:
    return value.encode("utf-8")


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    digest = pbkdf2_hmac("sha256", _ensure_bytes(password), salt, 100_000)
    return f"{urlsafe_b64encode(salt).decode()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    encoded_salt, stored_digest = password_hash.split("$", maxsplit=1)
    salt = urlsafe_b64decode(encoded_salt.encode("utf-8"))
    digest = pbkdf2_hmac("sha256", _ensure_bytes(password), salt, 100_000).hex()
    return compare_digest(digest, stored_digest)


def create_access_token() -> str:
    return urlsafe_b64encode(token_bytes(32)).decode("utf-8").rstrip("=")


def hash_token(token: str) -> str:
    return sha256(_ensure_bytes(token)).hexdigest()
