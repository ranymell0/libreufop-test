## Como funciona

O agregador combina duas estratégias de coleta:

1. **Feeds RSS/Atom nativos** — a maioria das fontes já expõe um feed próprio, listado em [`feeds.opml`](./feeds.opml) (mais de 27 fontes, organizadas por categoria: notícias brasileiras, distribuições GNU/Linux, ambientes gráficos, gerenciadores de janelas, e projetos de Software Livre).
2. **Scraping de fallback** — para fontes sem feed nativo ou quando o feed retorna vazio, o script busca o conteúdo diretamente no HTML da página usando BeautifulSoup.

O script principal, [`generate_feed.py`](./generate_feed.py):
- Coleta os itens mais recentes de cada fonte (`feedparser` para RSS/Atom nativo);
- Aplica scraping como fallback quando necessário;
- Limpa e trunca as descrições dos itens;
- Ordena tudo por data de publicação;
- Gera o [`feed.xml`](./feed.xml) final, no formato RSS 2.0.

## Automação (GitHub Actions)

O workflow **"Atualiza Feed RSS"** roda automaticamente **a cada hora** (`cron: 0 * * * *`), além de poder ser disparado manualmente (`workflow_dispatch`). Em cada execução, ele:

1. Faz checkout do repositório;
2. Configura Python 3.11 e instala as dependências (`feedparser`, `requests`, `beautifulsoup4`);
3. Executa `generate_feed.py`;
4. Faz commit e push automático do `feed.xml` atualizado, usando o bot `github-actions[bot]`.
