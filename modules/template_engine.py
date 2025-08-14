from pathlib import Path
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape

from modules.config import i18n
from modules.i18n import plural_days

logger = logging.getLogger("tg_support_bot.template")

DEFAULT_LANG = i18n.get("default_lang", "en")
TEMPLATES_DIR = Path("templates")

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["txt", "html"]),
)

env.filters["plural_days"] = lambda n, lang: plural_days(n, lang)


def render_template(name: str, *, lang: str | None = None, **ctx) -> str:
    lang = (lang or DEFAULT_LANG).split("-")[0]
    candidates = [f"{lang}/{name}", f"{DEFAULT_LANG}/{name}", name]
    for rel in candidates:
        p = TEMPLATES_DIR / rel
        if p.exists():
            template = env.get_template(rel)
            return template.render(**ctx)
    raise FileNotFoundError(name)
