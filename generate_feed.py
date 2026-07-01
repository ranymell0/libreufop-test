import feedparser
import datetime
from email.utils import formatdate
import time

SOURCES = [
    ("BR-Linux", "https://br-linux.org/feed"),
    ("Viva o Linux", "https://www.vivaolinux.com.br/rss"),
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
    ("Linux Today", "https://www.linuxtoday.com/news/feed/"),
    ("Linux Foundation", "https://www.linuxfoundation.org/feed"),
    ("kernel.org", "https://www.kernel.org/feeds/all.atom.xml"),
    ("GitHub Blog", "https://github.blog/feed"),
    ("Phoronix", "https://www.phoronix.com/rss.php"),
    ("OMG! Ubuntu", "https://www.omgubuntu.co.uk/feed"),
    ("It's FOSS", "https://itsfoss.com/feed"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
]

ITEMS_PER_SOURCE = 5
FEED_URL = "https://ranymell0.github.io/libreufop-test/feed.xml"
SITE_URL = "https://ranymell0.github.io/libreufop-test/"

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

def fetch_items():
    items = []
    for name, url in SOURCES:
        print(f"Buscando: {name}")
        try:
            feed = feedparser.parse(url)
            entries = feed.entries[:ITEMS_PER_SOURCE]
            for entry in entries:
                title = escape_xml(getattr(entry, "title", "(sem título)"))
                link = getattr(entry, "link", url)
                summary = escape_xml(getattr(entry, "summary", ""))
                pub_date = parse_date(entry)
                guid = getattr(entry, "id", link)
                items.append({
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
