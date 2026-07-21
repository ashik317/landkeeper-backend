import calendar
from datetime import date, timedelta


def receipt_upload_path(instance, filename):
    return f"tenants/{instance.tenant_id}/receipts/{filename}"


def parse_int(value, default, field_name):
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid integer")


def parse_date(value, field_name):
    if not value:
        raise ValueError(f"{field_name} is required for custom period")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format")


def get_statement_date_range(period, query_params):
    valid_periods = {"yearly", "monthly", "weekly", "custom"}
    period = (period or "yearly").lower()

    if period not in valid_periods:
        raise ValueError(f"Invalid period. Must be one of {sorted(valid_periods)}")

    today = date.today()

    if period == "yearly":
        year = parse_int(query_params.get("year"), today.year, "year")
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        label = str(year)

    elif period == "monthly":
        year = parse_int(query_params.get("year"), today.year, "year")
        month = parse_int(query_params.get("month"), today.month, "month")
        if not 1 <= month <= 12:
            raise ValueError("month must be between 1 and 12")
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        label = start.strftime("%B %Y")

    elif period == "weekly":
        year = parse_int(query_params.get("year"), today.isocalendar()[0], "year")
        week = parse_int(query_params.get("week"), today.isocalendar()[1], "week")
        try:
            start = date.fromisocalendar(year, week, 1)
        except ValueError:
            raise ValueError("Invalid year/week combination")
        end = start + timedelta(days=6)
        label = f"Week {week}, {year} ({start} to {end})"

    else:
        start = parse_date(query_params.get("start_date"), "start_date")
        end = parse_date(query_params.get("end_date"), "end_date")
        if start > end:
            raise ValueError("start_date must be before end_date")
        label = f"{start} to {end}"

    return start, end, label