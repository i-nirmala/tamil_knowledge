# Code Bloom account setup

Email/OTP verification is intentionally disabled in this version.

Public users only provide:
- Name (during sign-up)
- Email
- Password

Accounts are stored locally in `data/users.json` with PBKDF2 password hashes.

No SMTP credentials, email API keys, OTPs, or verification codes are required.
