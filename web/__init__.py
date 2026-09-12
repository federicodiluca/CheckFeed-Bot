"""School Feed Monitor — layer web (Flask, server-side rendering).

Processo separato dal bot Telegram, stesso database SQLite (WAL).
Configurazione via ambiente / .env:
    SECRET_KEY      chiave per firmare i cookie di sessione (obbligatoria fuori dal debug)
    APP_BASE_URL    URL pubblico (canonical, sitemap, link nelle email)
    FLASK_DEBUG     1 per il server di sviluppo
"""
import os
import secrets

from flask import Flask, render_template, request

from bot.db import init_db
from bot.env import env, env_bool
from web import seo, security
from web.auth import bp as auth_bp

APP_NAME = "School Feed Monitor"
PRIVACY_VERSION = "2026-09-12"   # aggiorna quando cambia l'informativa: gli utenti dovranno riaccettarla


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")

    secret = env("SECRET_KEY")
    debug = env_bool("FLASK_DEBUG", False)
    if not secret:
        if not debug and not test_config:
            raise RuntimeError("SECRET_KEY mancante: impostala in .env (es. `python -c \"import secrets; print(secrets.token_hex(32))\"`)")
        secret = secrets.token_hex(32)  # solo sviluppo/test: le sessioni non sopravvivono al riavvio

    app.config.update(
        SECRET_KEY=secret,
        APP_NAME=APP_NAME,
        PRIVACY_VERSION=PRIVACY_VERSION,
        BASE_URL=(env("APP_BASE_URL") or "").rstrip("/"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(env("APP_BASE_URL") or "").startswith("https://"),
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30,  # 30 giorni
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    init_db()
    security.init_app(app)
    seo.init_app(app)
    app.register_blueprint(auth_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/privacy")
    def privacy():
        return render_template("privacy.html")

    @app.get("/termini")
    def terms():
        return render_template("termini.html")

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errore.html", code=404, message="Pagina non trovata."), 404

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errore.html", code=403, message="Richiesta non valida o sessione scaduta: riprova."), 403

    @app.errorhandler(429)
    def too_many(_e):
        return render_template("errore.html", code=429, message="Troppi tentativi: riprova tra qualche minuto."), 429

    @app.context_processor
    def inject_globals():
        return {"app_name": APP_NAME, "current_user": security.current_user(), "canonical": seo.canonical_url(request)}

    return app
