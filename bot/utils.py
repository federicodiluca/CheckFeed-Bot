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
        dt = datetime.now(timezone.utc)
    else:
        dt = None
        # 1️⃣ Prova con formato RFC 2822 (RSS standard)
        try:
            dt = parsedate_to_datetime(pub_str)
        except Exception:
            pass

        # 2️⃣ Se fallisce, prova ISO 8601
        if dt is None:
            try:
                dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)

    # 3️⃣ Se manca il timezone, assumiamo che la data sia in locale e la convertiamo in UTC
    if dt.tzinfo is None:
        # Consideriamo l’ora locale e la convertiamo in UTC
        local_dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
        dt = local_dt.astimezone(timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    # 4️⃣ Restituiamo in formato SQLite standard
    return dt.strftime("%Y-%m-%d %H:%M:%S")
