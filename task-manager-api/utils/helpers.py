from datetime import datetime, timezone
import re


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def sanitize_string(s):
    if s:
        return s.strip()
    return s


def parse_date(date_string):
    formats = ('%Y-%m-%d', '%d/%m/%Y')
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def is_valid_color(color):
    return bool(color and len(color) == 7 and color[0] == '#')


VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
VALID_ROLES = ('user', 'admin', 'manager')
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
