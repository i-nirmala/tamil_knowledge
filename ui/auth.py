"""Local account authentication for the Code Bloom UI.

This module is presentation/authentication only. The AI/RAG pipeline under
src/ is intentionally untouched. No email/OTP verification is required.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
USERS_FILE = ROOT / "data" / "users.json"
USERS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_users() -> dict[str, dict[str, Any]]:
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_users(users: dict[str, dict[str, Any]]) -> None:
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256$120000${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def create_user(name: str, email: str, password: str) -> tuple[bool, str, dict[str, Any] | None]:
    """Create a local account immediately; no email verification/OTP."""
    name = name.strip()
    email = email.strip().lower()
    users = _load_users()

    if not name:
        return False, "Please enter your name.", None
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return False, "Please enter a valid email address.", None
    if email in users:
        return False, "This email is already registered. Please log in.", None
    if len(password) < 6:
        return False, "Password must contain at least 6 characters.", None

    user = {
        "name": name,
        "password_hash": _hash_password(password),
        "verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users[email] = user
    _save_users(users)
    return True, "Account created successfully.", user


def authenticate(email: str, password: str) -> tuple[bool, str, dict[str, Any] | None]:
    email = email.strip().lower()
    user = _load_users().get(email)
    if not user:
        return False, "Account not found. Please sign up first.", None
    if not _verify_password(password, user.get("password_hash", "")):
        return False, "Invalid email or password.", None
    return True, "Login successful.", user
