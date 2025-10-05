from bs4 import BeautifulSoup
from bot.config_loader import get_config
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import html

CONFIG = get_config()

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

def parse_date(n):
    pub_str = n.get("published", "")
    try:
        return parsedate_to_datetime(pub_str)
    except Exception:
        return datetime.min  # se non riesce, mettiamo la news in fondo   

def parse_rss_datetime(pub_str: str) -> str:
    """
    Converte una data RSS o ISO in formato SQLite UTC standard:
    'YYYY-MM-DD HH:MM:SS'
    """
    if not pub_str:
        dt = datetime.utcnow()
    else:
        try:
            dt = parsedate_to_datetime(pub_str)
        except Exception:
            try:
                dt = datetime.fromisoformat(pub_str)
            except Exception:
                dt = datetime.utcnow()

    # Assicura che sia UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.strftime("%Y-%m-%d %H:%M:%S")