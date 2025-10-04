from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import html

def cleanHTMLPreview(raw_content):
    """Rimuove i tag HTML e limita la lunghezza del testo a 400 caratteri."""
    soup = BeautifulSoup(raw_content, "html.parser")
    content_text = soup.get_text(separator=" ", strip=True)
    preview = content_text[:400] + "..." if len(content_text) > 400 else content_text
    return html.escape(preview)


def parse_date(pub_date_str: str) -> datetime:
    """Converte una stringa di data in datetime UTC, se possibile."""
    if not pub_date_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(pub_date_str)
    except ValueError:
        try:
            dt = parsedate_to_datetime(pub_date_str)
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)
    # Assicura che sia timezone-aware in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt
