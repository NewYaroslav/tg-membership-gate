from __future__ import annotations

def humanize_period(seconds: int) -> str:
    """Convert seconds to human readable Russian label."""
    if seconds == 0:
        return "бессрочно"
    units = [
        (365 * 24 * 3600, "год"),
        (30 * 24 * 3600, "месяц"),
        (7 * 24 * 3600, "неделю"),
        (24 * 3600, "день"),
        (3600, "час"),
        (60, "минуту"),
    ]
    for unit_seconds, name in units:
        if seconds % unit_seconds == 0 and seconds >= unit_seconds:
            amount = seconds // unit_seconds
            if name == "минуту" and amount > 1:
                name = "минут"
            elif name == "час" and amount > 1:
                name = "часов" if amount >= 5 else "часа"
            elif name == "день" and amount > 1:
                name = "дней" if amount >= 5 else "дня"
            elif name == "неделю" and amount > 1:
                name = "недель" if amount >= 5 else "недели"
            elif name == "месяц" and amount > 1:
                name = "месяцев" if amount >= 5 else "месяца"
            elif name == "год" and amount > 1:
                name = "лет" if amount >= 5 else "года"
            return f"{amount} {name}"
    # Fallback
    if seconds < 60:
        return f"{seconds} с"
    if seconds < 3600:
        return f"{seconds // 60} мин"
    if seconds < 86400:
        return f"{seconds // 3600} ч"
    return f"{seconds // 86400} дн"
