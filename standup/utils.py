from datetime import timedelta


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS string."""
    return str(timedelta(seconds=int(seconds)))
