from datetime import timedelta


def compute_expiry_status(expiry_date, today):
    if expiry_date < today:
        return "expired"
    if expiry_date <= today + timedelta(days=30):
        return "expiring_soon"
    if expiry_date <= today + timedelta(days=90):
        return "expiring_warning"
    return "ok"
