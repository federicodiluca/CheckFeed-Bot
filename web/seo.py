"""SEO: canonical, robots.txt, sitemap.xml. Le pagine pubbliche sono renderizzate lato server."""
from flask import Response, current_app, request, url_for

# Pagine pubbliche indicizzabili: (endpoint, priorità, changefreq)
PUBLIC_PAGES = [
    ("index", "1.0", "weekly"),
    ("auth.register", "0.8", "monthly"),
    ("auth.login", "0.3", "monthly"),
    ("privacy", "0.2", "yearly"),
    ("terms", "0.2", "yearly"),
]


def canonical_url(req=None):
    """URL canonico della pagina corrente (senza query string), basato su APP_BASE_URL se impostato."""
    req = req or request
    base = current_app.config.get("BASE_URL") or req.url_root.rstrip("/")
    return base + req.path


def init_app(app):
    @app.get("/robots.txt")
    def robots():
        base = app.config.get("BASE_URL") or request.url_root.rstrip("/")
        body = "User-agent: *\nAllow: /\nDisallow: /account\nDisallow: /preferenze\n" f"Sitemap: {base}/sitemap.xml\n"
        return Response(body, mimetype="text/plain")

    @app.get("/sitemap.xml")
    def sitemap():
        base = app.config.get("BASE_URL") or request.url_root.rstrip("/")
        urls = "".join(
            f"<url><loc>{base}{url_for(endpoint)}</loc><changefreq>{freq}</changefreq><priority>{prio}</priority></url>"
            for endpoint, prio, freq in PUBLIC_PAGES
        )
        body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
        return Response(body, mimetype="application/xml")
