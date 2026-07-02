import feedparser
import requests
from bs4 import BeautifulSoup
import datetime
from email.utils import formatdate
from urllib.parse import urljoin
import time

SOURCES = [
    ("BR-Linux", "https://br-linux.org/feed"),
    ("Diolinux", "https://diolinux.com.br/feed"),
    ("Movimento Software Livre", "https://movimento.softwarelivre.tec.br/feed/"),
    ("Debian News", "https://www.debian.org/News/news"),
    ("Fedora Magazine", "https://fedoramagazine.org/feed"),
    ("Ubuntu Blog", "https://ubuntu.com/blog/feed"),
    ("Linux Mint Blog", "https://blog.linuxmint.com/?feed=rss2"),
    ("BigLinux", "https://www.biglinux.com.br/feed"),
    ("openSUSE News", "https://news.opensuse.org/feed/"),
    ("Planet GNOME", "https://planet.gnome.org/rss20.xml"),
    ("Planet KDE", "https://planet.kde.org/index.xml"),
    ("Ubuntu MATE", "https://ubuntu-mate.org/rss.xml"),
    ("Xfce News", "https://xfce.org/feed"),
    ("i3wm", "https://github.com/i3/i3/releases.atom"),
    ("Sway", "https://github.com/swaywm/sway/releases.atom"),
    ("Hyprland", "https://github.com/hyprwm/Hyprland/releases.atom"),
    ("FSF News", "https://www.fsf.org/news/RSS"),
    ("Planet GNU", "https://planet.gnu.org/rss20.xml"),
    ("OSI", "https://opensource.org/feed/"),
    ("kernel.org", "https://www.kernel.org/feeds/all.atom.xml"),
    ("GitHub Blog", "https://github.blog/feed"),
    ("Phoronix", "https://www.phoronix.com/rss.php"),
    ("OMG! Ubuntu", "https://www.omgubuntu.co.uk/feed"),
    ("It's FOSS", "https://itsfoss.com/feed"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("Viva o Linux", "https://www.vivaolinux.com.br/rss"),
    ("Linux Today", "https://www.linuxtoday.com/news/feed/"),
    ("Linux Foundation", "https://www.linuxfoundation.org/feed"),
]

SCRAPE_FALLBACK = {
    "Viva o Linux": {
        "url": "https://www.vivaolinux.com.br/",
        "base_url": "https://www.vivaolinux.com.br/",
        "container_selector": "div.boxAula, div.list-noticias li, article",
        "link_selector": "a",
        "title_selector": "h2, h3",
    },
    "Linux Today": {
        "url": "https://www.linuxtoday.com/blog/",
        "base_url": "https://www.linuxtoday.com/",
        "container_selector": "article",
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
    "FSFLA": {
        "url": "https://www.fsfla.org/ikiwiki/index.pt.html",
        "base_url": "https://www.fsfla.org/",
        "container_selector": "div#content li, div.inline li",
        "link_selector": "a",
        "title_selector": None,
    },
    "4Linux": {
        "url": "https://blog.4linux.com.br/",
        "base_url": "https://blog.4linux.com.br/",
        "container_selector": "article, .post, .elementor-post",
        "link_selector": "a",
        "title_selector": "h2, h3, .elementor-post__title",
    },
    "LWN": {
        "url": "https://lwn.net/",
        "base_url": "https://lwn.net/",
        "container_selector": "div.ListLine, div.BlurbListing p",
        "link_selector": "a",
        "title_selector": None,
    },
}

SCRAPE_ONLY_SOURCES = ["FSFLA", "4Linux", "LWN"]

ITEMS_PER_SOURCE = 5
FEED_URL = "https://ranymell0.github.io/libreufop-test/feed.xml"
SITE_URL = "https://ranymell0.github.io/libreufop-test/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 LibreUFOP-FeedBot/1.0"
    )
}


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
                summary = escape_xml(getattr(entry, "summary", ""))
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
