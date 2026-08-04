PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ASCII_DIGITS = "0123456789"

TO_ASCII = str.maketrans(PERSIAN_DIGITS + ARABIC_DIGITS, ASCII_DIGITS * 2)
TO_PERSIAN = str.maketrans(ASCII_DIGITS, PERSIAN_DIGITS)


def normalize_digits(value):
    """Return a canonical ASCII-digit representation of user input."""
    if value is None:
        return value
    return str(value).translate(TO_ASCII).replace("٫", ".").replace("٬", ",")


def persian_digits(value):
    """Convert ASCII digits for presentation in Persian interfaces."""
    if value is None:
        return ""
    return str(value).translate(TO_PERSIAN)
