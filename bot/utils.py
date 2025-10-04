from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import parsedate_to_datetime

import html

def cleanHTMLPreview(raw_content):
    """Rimuove i tag HTML e limita la lunghezza del testo a 100 caratteri."""
    
    soup = BeautifulSoup(raw_content, "html.parser")
    content_text = soup.get_text(separator=" ", strip=True)
    preview = content_text[:400] + "..." if len(content_text) > 400 else content_text
    return html.escape(preview)


def parse_date(pub_date_str: str) -> datetime:
    """Prova a convertire una data in datetime.
    Supporta ISO e formati RSS standard."""
    if not pub_date_str:
        return datetime.min
    try:
        return datetime.fromisoformat(pub_date_str)
    except ValueError:
        try:
            return parsedate_to_datetime(pub_date_str)
        except Exception:
            return datetime.min