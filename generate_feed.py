import feedparser
import requests
from bs4 import BeautifulSoup
import datetime
import re
from email.utils import formatdate
from urllib.parse import urljoin
import time

SOURCES = [
    ("Viva o Linux", "https://www.vivaolinux.com.br/rss"),
    ("Linux Today", "https://feeds.feedburner.com/linuxtoday/linux"),
    ("Linux Foundation", "https://www.linuxfoundation.org/feed"),
    ("FSFLA", "https://www.fsfla.org/ikiwiki/index.all.rss"),
    ("4Linux", "https://blog.4linux.com.br/feed/"),
]

SCRAPE_FALLBACK = {
    "Viva o Linux": {
        "url": "https://www.vivaolinux.com.br/",
        "base_url": "https://www.vivaolinux.com.br/",
        "container_selector": "div.boxAula, div.list-noticias li, article",
        "link_selector": "a",
        "title_selector": "h2, h3",
    },
    "Linux Foundation": {
        "url": "https://www.linuxfoundation.org/blog",
        "base_url": "https://www.linuxfoundation.org/",
        "container_selector": "article, .blog-card, .card",
        "link_selector": "a",
        "title_selector": "h2, h3",
    },
    "LWN": {
        "url": "https://lwn.net/",
        "base_url": "https://lwn.net/",
        "container_selector": "div.ListLine, div.BlurbListing p",
        "link_selector": "a",
        "title_selector": None,
    },
}

SCRAPE_ONLY_SOURCES = ["LWN"]

ITEMS_PER_SOURCE = 5
FEED_URL = "https://lecompufop.github.io/LibreUFOP/feed.xml"
SITE_URL = "https://lecompufop.github.io/LibreUFOP/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 LibreUFOP-FeedBot/1.0"
    )
}


def truncar_descricao(texto, limite=300):
    if not texto:
        return ""
    texto_limpo = re.sub(r"<[^>]+>", " ", texto)
    texto_limpo = " ".join(texto_limpo.split())
    if len(texto_limpo) > limite:
        texto_limpo = texto_limpo[:limite].rsplit(" ", 1)[0] + "..."
    return escape_xml(texto_limpo)


def escape_xml(text):
    if not text:
        return ""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;"))


def parse_date(entry):
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                dt = datetime.datetime(*val[:6])
                return formatdate(time.mktime(dt.timetuple()))
            except Exception:
                pass
    return formatdate()


def scrape_source(name, cfg):
    try:
        resp = requests.get(cfg["url"], headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [scrape] Erro ao acessar {cfg['url']}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    containers = soup.select(cfg["container_selector"])
    itens = []
    vistos = set()

    for c in containers:
        a = c.select_one(cfg["link_selector"])
        if not a or not a.get("href"):
            continue

        link = urljoin(cfg["base_url"], a["href"])
        if link in vistos:
            continue

        if cfg["title_selector"]:
            title_el = c.select_one(cfg["title_selector"])
            titulo = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        else:
            titulo = a.get_text(strip=True)

        titulo = " ".join(titulo.split())
        if not titulo or len(titulo) < 3:
            continue

        vistos.add(link)
        itens.append({
            "title": f"[{name}] {escape_xml(titulo)}",
            "link": link,
            "description": "",
            "pubDate": formatdate(),
            "guid": link,
            "source_name": name,
            "source_url": cfg["url"],
        })

        if len(itens) >= ITEMS_PER_SOURCE:
            break

    return itens


def fetch_items():
    items = []
    fontes_ja_feitas = set()

    for name, url in SOURCES:
        if name in SCRAPE_ONLY_SOURCES:
            continue

        print(f"Buscando (feed): {name}")
        encontrados = []
        try:
            feed = feedparser.parse(url)
            entries = feed.entries[:ITEMS_PER_SOURCE]
            for entry in entries:
                title = escape_xml(getattr(entry, "title", "(sem título)"))
                link = getattr(entry, "link", url)
                summary = truncar_descricao(getattr(entry, "summary", ""))
                pub_date = parse_date(entry)
                guid = getattr(entry, "id", link)
                encontrados.append({
                    "title": f"[{name}] {title}",
                    "link": link,
                    "description": summary,
                    "pubDate": pub_date,
                    "guid": guid,
                    "source_name": name,
                    "source_url": url,
                })
        except Exception as e:
            print(f"  Erro em {name}: {e}")

        if not encontrados and name in SCRAPE_FALLBACK:
            print(f"  [aviso] Feed vazio para {name}, tentando scraping...")
            encontrados = scrape_source(name, SCRAPE_FALLBACK[name])
            if encontrados:
                print(f"  [ok] {len(encontrados)} itens via scraping.")
            else:
                print(f"  [falhou] Nada encontrado nem via scraping para {name}.")

        items.extend(encontrados)
        fontes_ja_feitas.add(name)

    for name in SCRAPE_ONLY_SOURCES:
        if name not in SCRAPE_FALLBACK:
            continue
        print(f"Buscando (scraping): {name}")
        encontrados = scrape_source(name, SCRAPE_FALLBACK[name])
        if encontrados:
            print(f"  [ok] {len(encontrados)} itens via scraping.")
        else:
            print(f"  [falhou] Nada encontrado para {name}.")
        items.extend(encontrados)

    items.sort(key=lambda x: x["pubDate"], reverse=True)
    return items


def generate_xml(items):
    now = formatdate()
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  LibreUFOP - Feed RSS Agregador
  Projeto de Extensão - ICEA/UFOP
  Grupo de Trabalho: RSS / Newsletter / Podcast
  Gerado automaticamente por GitHub Actions.
-->
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>LibreUFOP</title>
    <link>{SITE_URL}</link>
    <description>Feed agregador do projeto LibreUFOP (ICEA/UFOP). Reúne notícias sobre Software Livre, GNU/Linux, distribuições, ambientes gráficos e tecnologia open source.</description>
    <language>pt-BR</language>
    <copyright>Conteúdo de propriedade de cada fonte original</copyright>
    <managingEditor>libreufop@ufop.edu.br</managingEditor>
    <lastBuildDate>{now}</lastBuildDate>
    <ttl>60</ttl>
    <atom:link href="{FEED_URL}" rel="self" type="application/rss+xml"/>
"""
    for item in items:
        xml += f"""
    <item>
      <title>{item['title']}</title>
      <link>{item['link']}</link>
      <description>{item['description']}</description>
      <pubDate>{item['pubDate']}</pubDate>
      <guid isPermaLink="false">{escape_xml(item['guid'])}</guid>
      <source url="{item['source_url']}">{escape_xml(item['source_name'])}</source>
    </item>"""

    xml += "\n  </channel>\n</rss>\n"
    return xml


if __name__ == "__main__":
    print("Iniciando agregação de feeds...")
    items = fetch_items()
    print(f"Total de itens coletados: {len(items)}")
    xml = generate_xml(items)
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(xml)
    print("feed.xml gerado com sucesso!")
