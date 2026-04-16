import re


EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
SPECIAL_CHAR_PATTERN = r"[!@#$%^&*()_+\-=\[\]{};':\",.<>?/]"


class RegistrationValidationPolicy:
    """Encapsulates validation rules for user registration inputs."""

    @staticmethod
    def validate_password_rules(password: str) -> str | None:
        if not password[:1].isupper():
            return "Password must start with a capital letter."
        if not re.search(SPECIAL_CHAR_PATTERN, password):
            return "Password must include at least one special character (e.g. !@#$)."
        return None

    @staticmethod
    def is_valid_email_format(email: str) -> bool:
        return bool(re.match(EMAIL_PATTERN, email))
