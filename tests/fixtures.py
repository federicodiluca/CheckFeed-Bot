"""Helper per costruire feed RSS e pagine HTML di test."""
import html


def rss(items, title="Feed di prova"):
    """items: lista di dict con title, link e opzionali published/description/content."""
    parts = [f'<?xml version="1.0"?><rss version="2.0"><channel><title>{html.escape(title)}</title>']
    for it in items:
        parts.append("<item>")
        parts.append(f"<title>{html.escape(it['title'])}</title>")
        parts.append(f"<link>{html.escape(it['link'])}</link>")
        if it.get("published"):
            parts.append(f"<pubDate>{it['published']}</pubDate>")
        if it.get("description") is not None:
            parts.append(f"<description>{html.escape(it['description'])}</description>")
        if it.get("content") is not None:
            parts.append(f'<content:encoded xmlns:content="http://purl.org/rss/1.0/modules/content/">'
                         f"{html.escape(it['content'])}</content:encoded>")
        parts.append("</item>")
    parts.append("</channel></rss>")
    return "".join(parts)


def html_list_page(items, title="Novità dall'USR Prova", feed_href=None, base="https://www.example.org"):
    """Pagina "lista notizie" stile Liferay: <article> con data italiana, tag e h3 > a."""
    head = f"<title>{html.escape(title)}</title>"
    if feed_href:
        head += f'<link rel="alternate" type="application/rss+xml" title="Feed" href="{feed_href}" />'
        head += f'<link rel="alternate" type="application/rss+xml" title="Feed dei commenti" href="{base}/comments/feed/" />'
    body = []
    for it in items:
        body.append(f"""
        <article class="article">
          <div class="article_data_tags">
            <span class="article_data">{it.get('date', '11 settembre 2026')}</span>
            <p class="article_tags"><span><a href="{base}/cat?x=1">Novità</a></span></p>
          </div>
          <h3><a href="{it['link']}">{html.escape(it['title'])}</a></h3>
          <p>{html.escape(it.get('abstract', ''))}</p>
        </article>""")
    nav = f'<nav><h2><a href="{base}/">Home</a></h2><a href="https://facebook.com/x">FB</a></nav>'
    return f"<!DOCTYPE html><html><head>{head}</head><body>{nav}{''.join(body)}</body></html>"
