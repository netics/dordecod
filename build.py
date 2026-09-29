#!/usr/bin/env python3
"""Static site generator for Dor de codul românesc.

Renders one fully static HTML page per language (/ and /en/), plus markdown
twins, llms.txt, sitemap.xml, robots.txt and the web manifest, into public/.

    python3 build.py            # pages + text files
    python3 build.py --images   # also regenerate favicons and OG images (needs Chrome, rsvg-convert, magick)

Standard library only. Set SITE_URL to the production origin before building.
"""
import datetime, hashlib, html, json, os, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / 'public'
SITE_URL = os.environ.get('SITE_URL', 'https://dordecod.vercel.app').rstrip('/')
PUBLISHED = '2026-09-18'
MODIFIED = '2026-09-29'  # bump only when content changes (JSON-LD dateModified, sitemap lastmod, footer)

AUTHOR = {
    'name': 'Sergiu Vlad',
    'url': 'https://sergiuvlad.com',
    'jobTitle': 'Senior Software Engineer',
    'locality': 'Cluj-Napoca',
    'alternateName': 'Sergiu Madalin Vlad',
    'image': 'https://sergiuvlad.com/sergiu_vlad.jpg',
    'description': 'Senior Software Engineer with 15+ years of experience across ML/MLOps, cloud infrastructure, security and full-stack product engineering.',
    'knowsAbout': ['Machine Learning', 'MLOps', 'Cloud Infrastructure', 'Security Engineering', 'Full-Stack Development', 'Python'],
    'sameAs': ['https://www.linkedin.com/in/netics/', 'https://github.com/netics'],
}
REPO = 'https://github.com/netics/dordecod'

OG_VERSION = 1  # bump when the OG images change, so social networks refetch them
LANGS = {
    'ro': {'path': '/', 'locale': 'ro_RO', 'md': '/index.md', 'og': f'/og/og-ro-v{OG_VERSION}.png'},
    'en': {'path': '/en/', 'locale': 'en_GB', 'md': '/en/index.md', 'og': f'/og/og-en-v{OG_VERSION}.png'},
}

JOKES = json.loads((ROOT / 'content' / 'jokes.json').read_text())
CSS = (ROOT / 'src' / 'style.css').read_text().strip()
FISH = (ROOT / 'src' / 'fish.inner.svg').read_text().strip()
BAND_DEFS = (ROOT / 'src' / 'band.defs.svg').read_text().strip()

esc = lambda s: html.escape(s, quote=False)
attr = lambda s: html.escape(s, quote=True)


def pick(aud, section):
    return [i for i in JOKES[aud] if i['section'] == section]


# --------------------------------------------------------------------------
# Copy. Each entry is (ro, en). Values are HTML-safe unless noted.
# --------------------------------------------------------------------------
C = {
    'title': ('Codul developerului român, dicționar și scuze | Dor de codul românesc',
              "Romanian Developer's Code and dictionary | Dor de codul românesc"),
    'desc': ('Codul developerului român, dicționarul româno-corporate, generatorul oficial de scuze, Jira tradus și ghidul pentru CTO. Umor pentru developeri, PM-i și CTO-i.',
             "The Romanian Developer's Code, a Romanian-to-corporate dictionary, an official excuse generator, Jira translated and a CTO field guide. Humour for devs, PMs and CTOs."),
    'og_alt': ('Un cod (pește) cusut în cruciulițe roșii și bleumarin, lângă titlul Dor de codul românesc',
               'A cross-stitched cod fish in red and navy next to the title Dor de codul românesc'),
    'skip': ('Sari la conținut', 'Skip to content'),
    'nav.label': ('Meniu', 'Menu'), 'lang.label': ('Limbă', 'Language'),
    'nav.cod': ('Codul', 'The Code'), 'nav.excuse': ('Scuze', 'Excuses'), 'nav.dict': ('Dicționar', 'Dictionary'),
    'nav.pm': ('Pentru PM', 'For PMs'), 'nav.cto': ('Pentru CTO', 'For CTOs'),
    'hero.kicker': ('Codul developerului român, dicționarul româno-corporate și scuzele oficiale',
                    "The Romanian Developer's Code, a Romanian-to-corporate dictionary and official excuses"),
    'satire': ('Satiră. Personajele, recenziile și commit-urile sunt fictive.', 'Satire. Characters, reviews and commits are fictional.'),
    'hero.lead': ('Dor — cuvântul pe care nu-l putem traduce. Codul — cel pe care nu-l putem lăsa în pace. Un loc pentru developerii români din țară și de prin lume, pentru PM-ii care îi estimează și pentru CTO-ii care îi angajează.',
                  "Dor (n.) — the Romanian word for missing something you didn't know you needed. Codul — the code. Put together: a love letter to Romanian developers, and a field guide for the PMs who estimate them and the CTOs who hire them."),
    'hero.by': ('Scris de', 'Written by'),
    'hero.cta1': ('Citește Codul', 'Read the Code'), 'hero.cta2': ('Sunt CTO, explicați-mi', "I'm a CTO, explain"),
    'hero.note': ('Fără formulare. Fără cookies. Fără recruiteri cu „hi dear”. Promis.', 'No forms. No cookies. No recruiters opening with “hi dear”. Promise.'),
    'fish.alt': ('Un cod (pește) cusut în cruciulițe roșii și bleumarin, mascota Dor de codul românesc',
                 'A cross-stitched cod fish in red and navy, the Dor de codul românesc mascot'),
    'why.title': ('Ce-i cu dorul ăsta?', "What's with the dor?"),
    'why.p1': ('România a exportat în ultimii 20 de ani mai mulți developeri decât își poate aminti cineva. Unii au plecat la Zürich, alții la Berlin, alții doar pe un Slack cu fus orar din California. Toți au rămas cu același reflex: când merge, zic „lasă că merge”. Când nu merge, zic „se rezolvă”.',
               "Over the last twenty years Romania has exported more developers than anyone can count. Some went to Zürich, some to Berlin, some only as far as a Slack channel on California time. All of them kept the same reflex: when it works, they say „lasă că merge” (leave it, it works). When it doesn't, they say „se rezolvă” (it'll get sorted)."),
    'why.p2': ('Dor de codul românesc e locul unde ne recunoaștem: cei de aici, cei de acolo, managerii care au învățat să citească printre rânduri și companiile care au aflat că un developer român rezolvă lucruri.',
               'Dor de codul românesc is where we recognise each other: the ones here, the ones out there, the managers who learned to read between the lines, and the companies that found out a Romanian developer gets things fixed.'),
    'why.p3': ('Nu e agenție. Nu e platformă de recrutare. Nu colectăm nimic, nici măcar feedback. E doar adevărul, cu simțul umorului la vedere.',
               'Not an agency. Not a recruiting platform. We collect nothing, not even feedback. Just the truth, with its sense of humour in plain sight.'),
    'cod.title': ('Codul developerului român', "The Romanian Developer's Code"),
    'cod.intro': ('Orice popor are un cod. Al nostru nu se aplică, dar se respectă.', 'Every nation has a code. Ours is not enforced, but it is respected.'),
    'cod.copy': ('Copiază', 'Copy'), 'cod.copied': ('Copiat', 'Copied'),
    'cod.copyLabel': ('Copiază articolul', 'Copy article'),
    'cod.amend': ('Ai un articol de propus?', 'Have an article to propose?'),
    'cod.amendLink': ('Deschide un pull request', 'Open a pull request'),
    'exc.title': ('Generatorul oficial de scuze', 'The official excuse generator'),
    'exc.intro': ('Pentru standup, pentru retro, pentru client. Certificat conform Art. 2.', 'For standup, for the retro, for the client. Certified under Art. 2.'),
    'exc.btn': ('Dă-mi altă scuză', 'Give me another one'),
    'exc.meta': ('Folosire nelimitată. Credibilitatea scade după a treia pe sprint.', 'Unlimited use. Credibility drops after the third one per sprint.'),
    'exc.all': ('Toate scuzele, pentru planificare pe termen lung', 'All the excuses, for long-term planning'),
    'log.title': ('git log --oneline, echipa din Iași', 'git log --oneline, the Iași team'),
    'log.intro': ('Mesaje reale de commit. Numele au fost schimbate, codul nu.', 'Real commit messages. Names have been changed, the code has not.'),
    'dict.title': ('Dicționar româno-corporate', 'Romanian-to-corporate dictionary'),
    'dict.intro': ('Pentru managerii străini care lucrează cu developeri români. Traducere contextuală, din experiență, gratuită.',
                   'For managers abroad who work with Romanian developers. Contextual translation, from experience, free of charge.'),
    'dict.c1': ('Se spune', 'They say'), 'dict.c2': ('Se înțelege', 'It means'),
    'dict.more': ('Lipsește o expresie?', 'Missing an expression?'), 'dict.moreLink': ('Adaug-o prin pull request', 'Add it with a pull request'),
    'pm.title': ('Pentru PM, scrum masteri și administratorii de Jira', 'For PMs, scrum masters and Jira admins'),
    'pm.intro': ('Voi țineți proiectul în viață. Noi vă spunem ce se întâmplă de fapt în spatele board-ului.', "You keep the project alive. We'll tell you what actually happens behind the board."),
    'jira.title': ('Jira, tradus', 'Jira, translated'), 'jira.c1': ('Pe board scrie', 'The board says'), 'jira.c2': ('În realitate', 'In reality'),
    'est.title': ('Convertor de estimări', 'Estimate converter'), 'est.c1': ('Developerul zice', 'The dev says'), 'est.c2': ('Tu treci în plan', 'You put in the plan'),
    'bingo.title': ('Bingo de standup', 'Standup bingo'),
    'bingo.intro': ('Bifează ce auzi. Primul care face o linie are voie să închidă camera.', 'Tick what you hear. First to complete a line gets to turn their camera off.'),
    'bingo.reset': ('Sprint nou', 'New sprint'),
    'bingo.win': ('BINGO! Standup-ul poate continua încă 40 de minute.', 'BINGO! Standup may now continue for another 40 minutes.'),
    'cto.title': ('Pentru CTO: ce primești, de fapt', 'For CTOs: what you actually get'),
    'cto.intro': ('Ați lucrat cu un developer român și ceva s-a reparat ce nu reparase nimeni. Sau n-ați lucrat și ați auzit. Iată documentația pe care n-a scris-o nimeni.',
                  "You've worked with a Romanian developer and something got fixed that nobody else could fix. Or you haven't, and you've heard. Here's the documentation nobody wrote."),
    'spec.title': ('Developer român — specificații tehnice', 'Romanian Developer — technical specifications'),
    'faq.title': ('Întrebări frecvente de la CTO', 'Frequently asked CTO questions'),
    'rev.title': ('Ce spun clienții', 'What clients say'),
    'rev.note': ('Recenzii fictive, inspirate din fapte reale.', 'Fictional reviews, inspired by true events.'),
    'about': ('Făcut de <a href="https://sergiuvlad.com" rel="author">Sergiu Vlad</a>, Senior Software Engineer din Cluj-Napoca, cu peste 15 ani de „se rezolvă” în ML, cloud, securitate și produse full-stack pentru companii din afară. Destui cât să știe că „dor” se explică greu, dar „se rezolvă” se înțelege imediat.',
              'Made by <a href="https://sergiuvlad.com" rel="author">Sergiu Vlad</a>, a Senior Software Engineer from Cluj-Napoca with 15+ years of „se rezolvă” in ML, cloud, security and full-stack products for companies abroad. Long enough to know that „dor” is hard to explain and „se rezolvă” is understood immediately.'),
    'updated': ('Ultima actualizare', 'Last updated'),
    'footer': ('© 2026 Dor de codul românesc. Site-ul merge. La noi.', '© 2026 Dor de codul românesc. The site works. On our machine.'),
    '404.title': ('404 — La mine merge', '404 — Works on my machine'),
    '404.p': ('Pagina asta a mers local. Pe producție, se rezolvă.', 'This page worked locally. In production, se rezolvă (it will get sorted).'),
    '404.back': ('Înapoi la Cod', 'Back to the Code'),
}

ORIG_ARTS = [
    ('Orice bug se manifestă exclusiv în producție, vineri, după 17:00.', 'Every bug manifests exclusively in production, on a Friday, after 5 pm.'),
    ('„La mine merge” constituie probă legală.', '“Works on my machine” is admissible evidence.'),
    ('„Lasă că merge” nu este strategie de deploy. (Dar este.)', '„Lasă că merge” (leave it, it works) is not a deployment strategy. (It is.)'),
    ('Comentariile se scriu în engleză, variabilele în română, iar <code>listaClienti2Final</code> este patrimoniu național.',
     'Comments are written in English, variables in Romanian, and <code>listaClienti2Final</code> is national heritage.'),
    ('Diacriticele sunt opționale până când ajung în baza de date.', 'Diacritics are optional until they reach the database.'),
    ('Estimarea se dă în zile și se citește în săptămâni.', 'Estimates are given in days and read in weeks.'),
    ('Orice TODO mai vechi de doi ani devine documentație.', 'Any TODO older than two years becomes documentation.'),
    ('Cafeaua nu e beneficiu extra-salarial. E infrastructură.', 'Coffee is not a perk. It is infrastructure.'),
    ('Developerul român rezolvă. Nu știe încă cum, dar se rezolvă.', "The Romanian developer fixes it. Doesn't know how yet, but it gets fixed."),
]
LAST_ART = ('Prezentul Cod intră în vigoare la data publicării și se modifică exclusiv prin pull request.',
            'This Code enters into force on publication and is amended exclusively by pull request.')
ARTS = ORIG_ARTS + [(esc(i['ro_a']), esc(i['en_a'])) for i in pick('devs', 'code')] + [LAST_ART]

ORIG_DICT = [('merge și așa', 'acceptable technical debt'), ('se rezolvă', 'unblocked; ETA unknown'), ('hai că-i simplu', 'three sprints'),
             ('nu-i nicio problemă', 'there is a problem'), ('vezi că…', 'critical warning'), ('la mine merge', 'cannot reproduce'),
             ('îl bag repede', 'hotfix, no tests'), ('mai vedem', "won't fix"), ('să nu ne grăbim', "they know something you don't"),
             ('e ok, dar…', 'it is not ok')]
DICT = [(esc(a), esc(b)) for a, b in ORIG_DICT] + [(esc(i['ro_a']), esc(i['en_b'])) for aud in ('devs', 'pm', 'cto') for i in pick(aud, 'dict')]

EXCUSES = [(esc(i['ro_a']), esc(i['en_a'])) for i in pick('devs', 'excuse')]
COMMITS = [(esc(i['ro_a']), esc(i['en_a']), hashlib.sha1(i['ro_a'].encode()).hexdigest()[:7]) for i in pick('devs', 'commit')]
pairs = lambda aud, s: [((esc(i['ro_a']), esc(i['en_a'])), (esc(i['ro_b']), esc(i['en_b']))) for i in pick(aud, s)]
JIRA, ESTIMATES = pairs('pm', 'jira'), pairs('pm', 'estimate')
BINGO = [(esc(i['ro_a']), esc(i['en_a'])) for i in pick('pm', 'bingo')][:16]
SPEC, FAQ, REVIEWS = pairs('cto', 'spec'), pairs('cto', 'faq'), pairs('cto', 'reviews')


def dict_id(phrase):
    import re, unicodedata
    plain = unicodedata.normalize('NFKD', strip_tags(phrase)).encode('ascii', 'ignore').decode()
    return 'dict-' + re.sub(r'[^a-z0-9]+', '-', plain.lower()).strip('-')


def strip_tags(s):
    import re
    return html.unescape(re.sub(r'<[^>]+>', '', s))


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------
def fish_paths(fill=None):
    """The mascot as three paths (one per colour) instead of ~200 rects."""
    import re
    d = {'k': [], 'r': [], 'w': []}
    for c, x, y in re.findall(r'class="([krw])" x="(\d+)" y="(\d+)"', FISH):
        d[c].append(f'M{x} {y}h12v12h-12z')
    colour = (lambda c: f'fill="{COLORS[c]}"') if fill else (lambda c: f'class="{c}"')
    return ''.join(f'<path {colour(c)} d="{"".join(v)}"/>' for c, v in d.items())


FISH_SYMBOL = f'<svg class="sprite" width="0" height="0" aria-hidden="true" focusable="false"><symbol id="fish" viewBox="0 0 312 156">{fish_paths()}</symbol></svg>'


def fish_svg(cls, label=None):
    if label:
        return (f'<svg class="{cls}" viewBox="0 0 312 156" width="312" height="156" role="img" aria-labelledby="fish-t" shape-rendering="crispEdges">'
                f'<title id="fish-t">{esc(label)}</title><use href="#fish"/></svg>')
    return f'<svg class="{cls}" viewBox="0 0 312 156" width="312" height="156" aria-hidden="true" focusable="false" shape-rendering="crispEdges"><use href="#fish"/></svg>'


def band(n):
    defs = BAND_DEFS.replace('id="stitch1"', f'id="stitch{n}"')
    return f'<svg class="band" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">{defs}<rect width="100%" height="100%" fill="url(#stitch{n})"/></svg>'


def url(lang, frag=''):
    return SITE_URL + LANGS[lang]['path'] + frag


def jsonld(L):
    ix = 0 if L == 'ro' else 1
    t = lambda k: strip_tags(C[k][ix])
    page = url(L)
    other = 'en' if L == 'ro' else 'ro'
    person_id = AUTHOR['url'] + '/#person'
    website_id = SITE_URL + '/#website'
    image = {'@type': 'ImageObject', '@id': page + '#ogimage', 'url': SITE_URL + LANGS[L]['og'], 'width': 1200, 'height': 630,
             'caption': t('og_alt'), 'inLanguage': L}
    person = {
        '@type': 'Person', '@id': person_id, 'name': AUTHOR['name'], 'url': AUTHOR['url'],
        'alternateName': AUTHOR['alternateName'], 'image': AUTHOR['image'], 'description': AUTHOR['description'],
        'jobTitle': AUTHOR['jobTitle'], 'knowsAbout': AUTHOR['knowsAbout'], 'sameAs': AUTHOR['sameAs'],
        'address': {'@type': 'PostalAddress', 'addressLocality': AUTHOR['locality'], 'addressCountry': 'RO'},
        'knowsLanguage': ['ro', 'en'],
    }
    webpage = {
        '@type': 'WebPage', '@id': page + '#webpage', 'url': page, 'name': t('title'), 'description': t('desc'),
        'inLanguage': L, 'isPartOf': {'@id': website_id}, 'author': {'@id': person_id}, 'publisher': {'@id': person_id},
        'datePublished': PUBLISHED, 'dateModified': MODIFIED, 'genre': 'Satire', 'isFamilyFriendly': True,
        'primaryImageOfPage': {'@id': image['@id']}, 'image': {'@id': image['@id']},
        'about': [{'@type': 'Thing', 'name': n} for n in (
            ('Umor pentru programatori', 'Dezvoltare software în România', 'Developeri români') if L == 'ro'
            else ('Programming humour', 'Software development in Romania', 'Romanian developers'))],
        'hasPart': [{'@id': page + '#codul'}, {'@id': page + '#dictionar'}, {'@id': page + '#faq'}],
        ('workTranslation' if L == 'ro' else 'translationOfWork'): {'@id': url(other) + '#webpage'},
    }
    code = {
        '@type': 'SatiricalArticle', '@id': page + '#codul', 'headline': t('cod.title'), 'description': t('cod.intro'),
        'url': page + '#codul', 'inLanguage': L, 'isPartOf': {'@id': page + '#webpage'},
        'author': {'@id': person_id}, 'publisher': {'@id': person_id}, 'datePublished': PUBLISHED, 'dateModified': MODIFIED,
        'image': {'@id': image['@id']},
        'mainEntity': {
            '@type': 'ItemList', '@id': page + '#codul-list', 'name': t('cod.title'), 'numberOfItems': len(ARTS),
            'itemListOrder': 'https://schema.org/ItemListOrderAscending',
            'itemListElement': [{'@type': 'ListItem', 'position': n, 'url': page + f'#art-{n}', 'name': f'Art. {n}. ' + strip_tags(a[ix])}
                                for n, a in enumerate(ARTS, 1)],
        },
    }
    dictionary = {
        '@type': 'DefinedTermSet', '@id': page + '#dictionar', 'name': t('dict.title'), 'description': t('dict.intro'),
        'url': page + '#dictionar', 'inLanguage': ['ro', 'en'], 'isPartOf': {'@id': page + '#webpage'},
        'hasDefinedTerm': [{'@type': 'DefinedTerm', '@id': page + '#' + dict_id(a), 'url': page + '#' + dict_id(a),
                            'name': strip_tags(a), 'description': strip_tags(b),
                            'inDefinedTermSet': {'@id': page + '#dictionar'}} for a, b in DICT],
    }
    faq = {
        '@type': 'FAQPage', '@id': page + '#faq', 'name': t('faq.title'), 'url': page + '#faq', 'inLanguage': L,
        'isPartOf': {'@id': page + '#webpage'},
        'mainEntity': [{'@type': 'Question', '@id': page + f'#faq-{n}', 'name': strip_tags(q[ix]),
                        'acceptedAnswer': {'@type': 'Answer', 'text': strip_tags(a[ix])}} for n, (q, a) in enumerate(FAQ, 1)],
    }
    graph = [webpage, image, person, code, dictionary, faq]
    if L == 'ro':  # the WebSite node lives on the home page only
        graph.insert(0, {
            '@type': 'WebSite', '@id': website_id, 'url': SITE_URL + '/', 'name': 'Dor de codul românesc',
            'alternateName': ['Dor de cod', 'DorDeCod'], 'inLanguage': ['ro', 'en'],
            'description': strip_tags(C['desc'][0]), 'publisher': {'@id': person_id}, 'author': {'@id': person_id},
        })
    out = {'@context': 'https://schema.org', '@graph': graph}
    return json.dumps(out, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def head(L, title, desc, canonical, alternates=True, robots='index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1', ld=None):
    other = 'en' if L == 'ro' else 'ro'
    alt = ''
    if alternates:
        alt = (f'<link rel="alternate" hreflang="ro" href="{url("ro")}">\n'
               f'<link rel="alternate" hreflang="en" href="{url("en")}">\n'
               f'<link rel="alternate" hreflang="x-default" href="{url("ro")}">\n'
               f'<link rel="alternate" type="text/markdown" href="{SITE_URL}{LANGS[L]["md"]}" title="Markdown">\n')
    og_img = SITE_URL + LANGS[L]['og']
    return f'''<!doctype html>
<html lang="{L}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{attr(desc)}">
{f'<link rel="canonical" href="{canonical}">' + chr(10) if canonical else ''}{alt}<meta name="robots" content="{robots}">
<meta name="author" content="{AUTHOR['name']}">
<link rel="author" href="{AUTHOR['url']}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12162a" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon-96x96.png" type="image/png" sizes="96x96">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="application-name" content="Dor de codul românesc">
<meta name="apple-mobile-web-app-title" content="Dor de cod">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Dor de codul românesc">
<meta property="og:title" content="{attr(title)}">
<meta property="og:description" content="{attr(desc)}">
<meta property="og:url" content="{canonical or SITE_URL + "/"}">
<meta property="og:locale" content="{LANGS[L]['locale']}">
<meta property="og:locale:alternate" content="{LANGS[other]['locale']}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{attr(strip_tags(C['og_alt'][0 if L == 'ro' else 1]))}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image:alt" content="{attr(strip_tags(C['og_alt'][0 if L == 'ro' else 1]))}">
<link rel="preload" href="/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin fetchpriority="high">
{'<link rel="preload" href="/fonts/fraunces-latin-ext.woff2" as="font" type="font/woff2" crossorigin>' + chr(10) if L == 'ro' else ''}
<style>
{FONT_FACES}
{CSS}
</style>
{f'<script type="application/ld+json">{ld}</script>' if ld else ''}
</head>'''


def nav(L, base='', current=True):
    t = lambda k: C[k][0 if L == 'ro' else 1]
    links = ''.join(f'<a href="{base}#{i}">{t(k)}</a>' for i, k in
                    [('codul', 'nav.cod'), ('scuze', 'nav.excuse'), ('dictionar', 'nav.dict'), ('pm', 'nav.pm'), ('cto', 'nav.cto')])
    lang_links = ''.join(
        f'<a href="{LANGS[l]["path"]}" hreflang="{l}" lang="{l}"{" aria-current=\"page\"" if current and l == L else ""}>{l.upper()}</a>'
        for l in ('ro', 'en'))
    return f'''<a class="skip" href="#continut">{t('skip')}</a>
<nav class="nav" aria-label="{t('nav.label')}">
  <div class="wrap">
    <a class="brand" href="{LANGS[L]['path']}">{fish_svg('fish')}<span>dor de cod</span></a>
    <div class="links">{links}</div>
    <div class="lang" role="group" aria-label="{t('lang.label')}">{lang_links}</div>
  </div>
</nav>'''


def page(L):
    ix = 0 if L == 'ro' else 1
    t = lambda k: C[k][ix]
    rows = lambda items, prefix, mono=False: '\n'.join(
        f'          <tr id="{prefix}-{n}"><td{" class=\"mono\"" if mono else ""}>{a[ix]}</td><td>{b[ix]}</td></tr>' for n, (a, b) in enumerate(items, 1))

    arts = '\n'.join(
        f'        <li id="art-{n}"><span class="art">Art. {n}.</span><span class="txt">{a[ix]}</span>'
        f'<button class="copy" type="button"><span class="lbl">{t("cod.copy")}</span><span class="vh"> Art. {n}</span></button></li>'
        for n, a in enumerate(ARTS, 1))
    log = '\n'.join(
        f'        <div class="ln"><span class="h">{h}</span> {ro}</div>' + (f'<span class="g">{en}</span>' if L == 'en' else '')
        for ro, en, h in COMMITS)
    excuses_all = '\n'.join(f'          <li id="scuza-{n}">{e[ix]}</li>' for n, e in enumerate(EXCUSES, 1))
    dict_rows = '\n'.join(f'          <tr id="{dict_id(a)}"><td lang="ro">{a}</td><td lang="en">{b}</td></tr>' for a, b in DICT)
    bingo = '\n'.join(f'        <button type="button" aria-pressed="false">{c[ix]}</button>' for c in BINGO)
    spec = '\n'.join(f'          <dt>{a[ix]}</dt><dd>{b[ix]}</dd>' for a, b in SPEC)
    faq = '\n'.join(f'        <details id="faq-{n}"><summary><h4 class="q">{q[ix]}</h4></summary><p>{a[ix]}</p></details>' for n, (q, a) in enumerate(FAQ, 1))
    reviews = '\n'.join(
        f'        <figure class="review" id="review-{n}"><div class="stars" aria-hidden="true">★★★★★</div><blockquote>{q[ix]}</blockquote><figcaption>— {b[ix]}</figcaption></figure>'
        for n, (q, b) in enumerate(REVIEWS, 1))
    cfg = json.dumps({'copy': t('cod.copy'), 'copied': t('cod.copied'), 'win': t('bingo.win')}, ensure_ascii=False).replace('</', '<\\/')
    modified_h = format_date(MODIFIED, L)

    return head(L, t('title'), t('desc'), url(L), ld=jsonld(L)) + mark_romanian(L, f'''
<body>
{FISH_SYMBOL}
{nav(L)}

<main id="continut">
  <div class="hero">
    <div class="wrap">
      <div>
        <p class="kicker">{t('hero.kicker')}</p>
        <h1>Dor de codul românesc</h1>
        <p class="lead">{t('hero.lead')}</p>
        <div class="ctas">
          <a class="btn" href="#codul">{t('hero.cta1')}</a>
          <a class="btn ghost" href="#cto">{t('hero.cta2')}</a>
        </div>
        <p class="fine">{t('hero.note')} {t('hero.by')} <a href="{AUTHOR['url']}" rel="author">{AUTHOR['name']}</a>.</p>
      </div>
      {fish_svg('fish', strip_tags(t('fish.alt')))}
    </div>
  </div>

  {band(1)}

  <section class="why" aria-labelledby="why-h">
    <div class="wrap measure">
      <h2 id="why-h">{t('why.title')}</h2>
      <p>{t('why.p1')}</p>
      <p>{t('why.p2')}</p>
      <p>{t('why.p3')}</p>
    </div>
  </section>

  <section class="cod" id="codul" aria-labelledby="codul-h">
    <div class="wrap measure">
      <h2 id="codul-h">{t('cod.title')}</h2>
      <p>{t('cod.intro')}</p>
      <ol>
{arts}
      </ol>
      <p class="vh" role="status" data-copy-status></p>
      <p class="after">{t('cod.amend')} <a href="{REPO}">{t('cod.amendLink')}</a></p>
    </div>
  </section>

  <section class="excuse-sec" id="scuze" aria-labelledby="scuze-h">
    <div class="wrap measure">
      <h2 id="scuze-h">{t('exc.title')}</h2>
      <p>{t('exc.intro')}</p>
      <div class="excuse">
        <p data-excuse aria-live="polite">{EXCUSES[0][ix]}</p>
        <button class="btn small" type="button" data-excuse-btn>{t('exc.btn')}</button>
        <p class="meta">{t('exc.meta')}</p>
      </div>
      <details class="faq">
        <summary>{t('exc.all')} ({len(EXCUSES)})</summary>
        <ol data-excuses>
{excuses_all}
        </ol>
      </details>

      <h3 class="sub" id="git-log">{t('log.title')}</h3>
      <p>{t('log.intro')}</p>
      <section class="log" aria-labelledby="git-log" tabindex="0">
        <div class="ln prompt">$ git log --oneline main</div>
{log}
      </section>
    </div>
  </section>

  <section class="dict" id="dictionar" aria-labelledby="dictionar-h">
    <div class="wrap measure">
      <h2 id="dictionar-h">{t('dict.title')}</h2>
      <p>{t('dict.intro')}</p>
      <table class="tbl">
        <thead><tr><th scope="col">{t('dict.c1')}</th><th scope="col">{t('dict.c2')}</th></tr></thead>
        <tbody>
{dict_rows}
        </tbody>
      </table>
      <p class="after">{t('dict.more')} <a href="{REPO}">{t('dict.moreLink')}</a></p>
    </div>
  </section>

  <section class="pm" id="pm" aria-labelledby="pm-h">
    <div class="wrap measure">
      <h2 id="pm-h">{t('pm.title')}</h2>
      <p>{t('pm.intro')}</p>

      <h3 class="sub" id="jira">{t('jira.title')}</h3>
      <table class="tbl">
        <thead><tr><th scope="col">{t('jira.c1')}</th><th scope="col">{t('jira.c2')}</th></tr></thead>
        <tbody>
{rows(JIRA, 'jira', True)}
        </tbody>
      </table>

      <h3 class="sub" id="estimari">{t('est.title')}</h3>
      <table class="tbl">
        <thead><tr><th scope="col">{t('est.c1')}</th><th scope="col">{t('est.c2')}</th></tr></thead>
        <tbody>
{rows(ESTIMATES, 'est')}
        </tbody>
      </table>

      <h3 class="sub" id="bingo">{t('bingo.title')}</h3>
      <p>{t('bingo.intro')}</p>
      <div class="bingo" role="group" aria-labelledby="bingo">
{bingo}
      </div>
      <div class="bingo-bar">
        <button class="btn small ghost" type="button" data-bingo-reset>{t('bingo.reset')}</button>
        <p class="bingo-win" role="status" data-bingo-win></p>
      </div>
    </div>
  </section>

  <section class="cto" id="cto" aria-labelledby="cto-h">
    <div class="wrap">
      <div class="measure">
        <h2 id="cto-h">{t('cto.title')}</h2>
        <p>{t('cto.intro')}</p>
      </div>
      <div class="spec">
        <p class="model">MODEL: RO-DEV · REV. 2026 · MADE IN CLUJ / IAȘI / TIMIȘOARA / BUCUREȘTI</p>
        <h3 id="spec">{t('spec.title')}</h3>
        <dl>
{spec}
        </dl>
      </div>
      <div class="measure">
        <h3 class="sub" id="faq">{t('faq.title')}</h3>
        <div class="faq">
{faq}
        </div>
      </div>
      <h3 class="sub" id="recenzii">{t('rev.title')}</h3>
      <div data-nosnippet>
        <p class="disclaimer">{t('rev.note')}</p>
        <div class="reviews">
{reviews}
        </div>
      </div>
    </div>
  </section>
</main>

{band(2)}

<footer>
  <div class="wrap">
    <div class="cols">
      <p class="about">{t('about')}</p>
      <ul>
        <li><a href="{AUTHOR['url']}" rel="author">sergiuvlad.com</a></li>
        <li><a href="{AUTHOR['sameAs'][0]}" rel="me noopener">LinkedIn</a></li>
        <li><a href="{REPO}">GitHub</a></li>
        <li><a href="{LANGS[L]['md']}" type="text/markdown">Markdown</a></li>
        <li><a href="/llms.txt">llms.txt</a></li>
      </ul>
    </div>
    <p class="line">{t('satire')} {t('footer')} {t('updated')}: <time datetime="{MODIFIED}">{modified_h}</time>.</p>
  </div>
</footer>

<script type="application/json" id="cfg">{cfg}</script>
<script src="/app.js" defer></script>
<script type="speculationrules">{{"prerender":[{{"where":{{"href_matches":"{LANGS['en' if L == 'ro' else 'ro']['path']}"}},"eagerness":"moderate"}}]}}</script>
</body>
</html>
''')


def mark_romanian(L, body):
    """On the English page, tag Romanian phrases („…”) and the Romanian git log so screen readers and parsers switch language."""
    import re
    if L != 'en':
        return body
    body = re.sub(r'(?<![\w"])„([^”<]{1,80})”', r'<span lang="ro">„\1”</span>', body)
    return body.replace('<div class="ln"><span class="h">', '<div class="ln" lang="ro"><span class="h">')


SCRIPT = r'''(function(){
  var CFG = JSON.parse(document.getElementById('cfg').textContent);

  // Copy an article + its link
  document.querySelectorAll('.cod li').forEach(function(li){
    var btn = li.querySelector('.copy');
    btn.addEventListener('click', function(){
      var text = li.querySelector('.art').textContent + ' ' + li.querySelector('.txt').textContent + '\n' + location.origin + location.pathname + '#' + li.id;
      var lbl = btn.querySelector('.lbl'), status = document.querySelector('[data-copy-status]');
      function done(){ lbl.textContent = CFG.copied; btn.setAttribute('data-done','1'); if (status) status.textContent = CFG.copied;
        setTimeout(function(){ lbl.textContent = CFG.copy; btn.removeAttribute('data-done'); if (status) status.textContent = ''; }, 1600); }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, done);
      else done();
    });
  });

  // Excuse generator: reads the full list rendered in the page
  var excuses = Array.prototype.map.call(document.querySelectorAll('[data-excuses] li'), function(li){ return li.innerHTML; });
  var excuseEl = document.querySelector('[data-excuse]'), idx = 0;
  var excuseBtn = document.querySelector('[data-excuse-btn]');
  if (excuseBtn && excuses.length > 1) excuseBtn.addEventListener('click', function(){
    var next = idx;
    while (next === idx) next = Math.floor(Math.random() * excuses.length);
    idx = next; excuseEl.innerHTML = excuses[idx];
  });

  // Standup bingo (nothing is stored)
  var grid = document.querySelector('.bingo');
  var cells = Array.prototype.slice.call(document.querySelectorAll('.bingo button'));
  var winEl = document.querySelector('[data-bingo-win]');
  var LINES = [];
  for (var r = 0; r < 4; r++) { LINES.push([r*4, r*4+1, r*4+2, r*4+3]); LINES.push([r, r+4, r+8, r+12]); }
  LINES.push([0, 5, 10, 15]); LINES.push([3, 6, 9, 12]);
  function checkBingo(){
    var on = cells.map(function(c){ return c.getAttribute('aria-pressed') === 'true'; });
    winEl.textContent = LINES.some(function(l){ return l.every(function(i){ return on[i]; }); }) ? CFG.win : '';
  }
  cells.forEach(function(c){
    c.addEventListener('click', function(){
      c.setAttribute('aria-pressed', c.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      checkBingo();
    });
  });
  var reset = document.querySelector('[data-bingo-reset]');
  if (reset) reset.addEventListener('click', function(){
    for (var i = cells.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var tmp = cells[i]; cells[i] = cells[j]; cells[j] = tmp; }
    cells.forEach(function(c){ c.setAttribute('aria-pressed', 'false'); grid.appendChild(c); });
    checkBingo();
  });
})();'''


MONTHS = {'ro': ['ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie', 'iulie', 'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie'],
          'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']}


def format_date(iso, L):
    d = datetime.date.fromisoformat(iso)
    m = MONTHS[L][d.month - 1]
    return f'{d.day} {m} {d.year}' if L == 'ro' else f'{d.day} {m} {d.year}'


FONT_FACES = '''@font-face{font-family:"Fraunces";font-style:normal;font-weight:400 700;font-display:swap;src:url(/fonts/fraunces-latin.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:"Fraunces";font-style:normal;font-weight:400 700;font-display:swap;src:url(/fonts/fraunces-latin-ext.woff2) format("woff2");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
@font-face{font-family:"Fraunces";font-style:italic;font-weight:400 600;font-display:swap;src:url(/fonts/fraunces-italic-latin.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:"Fraunces";font-style:italic;font-weight:400 600;font-display:swap;src:url(/fonts/fraunces-italic-latin-ext.woff2) format("woff2");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
@font-face{font-family:"IBM Plex Mono";font-style:normal;font-weight:400;font-display:swap;src:url(/fonts/plex-mono-latin.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:"IBM Plex Mono";font-style:normal;font-weight:400;font-display:swap;src:url(/fonts/plex-mono-latin-ext.woff2) format("woff2");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}'''


def page_404():
    L = 'ro'
    body = f'''
<body>
{FISH_SYMBOL}
{nav(L, base='/', current=False)}
<main id="continut">
  <div class="hero"><div class="wrap"><div>
    <p class="kicker">Art. 2.</p>
    <h1>{C['404.title'][0]}</h1>
    <p class="lead" lang="ro">{C['404.p'][0]}</p>
    <p class="lead" lang="en">{C['404.p'][1]}</p>
    <div class="ctas"><a class="btn" href="/#codul">{C['404.back'][0]}</a><a class="btn ghost" href="/en/#codul" lang="en">{C['404.back'][1]}</a></div>
  </div>{fish_svg('fish', strip_tags(C['fish.alt'][0]))}</div></div>
</main>
</body>
</html>
'''
    return head(L, C['404.title'][0], C['404.p'][0], None, alternates=False, robots='noindex, follow') + body


# --------------------------------------------------------------------------
# Markdown / llms.txt
# --------------------------------------------------------------------------
def md(s):
    import re
    s = re.sub(r'<code>(.*?)</code>', r'`\1`', s)
    s = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', s)
    return strip_tags(s)


def markdown(L, full_header=True):
    ix = 0 if L == 'ro' else 1
    t = lambda k: md(C[k][ix])
    o = []
    if full_header:
        o += ['---', f'title: "{strip_tags(C["title"][ix])}"', f'canonical_url: {url(L)}', f'lang: {L}',
              f'author: {AUTHOR["name"]} ({AUTHOR["url"]})', f'date_published: {PUBLISHED}', f'last_updated: {MODIFIED}',
              f'genre: satire', f'summary: "{t("desc")}"', '---', '',
              '# Dor de codul românesc', '', f'> {t("desc")}', '',
              f'- {"Autor" if L == "ro" else "Author"}: [{AUTHOR["name"]}]({AUTHOR["url"]}), {AUTHOR["jobTitle"]}, {AUTHOR["locality"]}',
              f'- {"Dacă citați, puneți link către articol (#art-N) și autor." if L == "ro" else "If you quote it, please link the article (#art-N) and credit the author."}', '']
    o += [f'> {t("satire")}', '', t('hero.lead'), '', f'## {t("why.title")}', '', t('why.p1'), '', t('why.p2'), '', t('why.p3'), '',
          f'## {t("cod.title")}', '', t('cod.intro'), '']
    o += [f'{n}. **Art. {n}.** {md(a[ix])} ([#art-{n}]({url(L, f"#art-{n}")}))' for n, a in enumerate(ARTS, 1)]
    o += ['', f'## {t("exc.title")}', '', t('exc.intro'), '']
    o += [f'- {md(e[ix])}' for e in EXCUSES]
    o += ['', f'### {t("log.title")}', '', '```', *[f'{h} {md(ro)}' + (f'   # {md(en)}' if L == 'en' else '') for ro, en, h in COMMITS], '```']
    o += ['', f'## {t("dict.title")}', '', t('dict.intro'), '', f'| {t("dict.c1")} | {t("dict.c2")} |', '|---|---|']
    o += [f'| {md(a)} | {md(b)} |' for a, b in DICT]
    o += ['', f'## {t("pm.title")}', '', t('pm.intro'), '', f'### {t("jira.title")}', '', f'| {t("jira.c1")} | {t("jira.c2")} |', '|---|---|']
    o += [f'| {md(a[ix])} | {md(b[ix])} |' for a, b in JIRA]
    o += ['', f'### {t("est.title")}', '', f'| {t("est.c1")} | {t("est.c2")} |', '|---|---|']
    o += [f'| {md(a[ix])} | {md(b[ix])} |' for a, b in ESTIMATES]
    o += ['', f'### {t("bingo.title")}', '', t('bingo.intro'), '']
    o += [f'- {md(c[ix])}' for c in BINGO]
    o += ['', f'## {t("cto.title")}', '', t('cto.intro'), '', f'### {t("spec.title")}', '']
    o += [f'- **{md(a[ix])}:** {md(b[ix])}' for a, b in SPEC]
    o += ['', f'### {t("faq.title")}', '']
    for q, a in FAQ:
        o += [f'**{md(q[ix])}**', '', md(a[ix]), '']
    o += [f'### {t("rev.title")}', '', f'_{t("rev.note")}_', '']
    o += [f'> {md(q[ix])}  \n> — {md(b[ix])}\n' for q, b in REVIEWS]
    o += ['---', '', t('about'), '']
    return '\n'.join(o)


def llms_txt():
    return f'''# Dor de codul românesc

> A bilingual (Romanian/English) humour site about Romanian software developers, written by {AUTHOR['name']} ({AUTHOR['jobTitle']}, {AUTHOR['locality']}). It contains "The Romanian Developer's Code" ({len(ARTS)} tongue-in-cheek articles), a Romanian-to-corporate dictionary ({len(DICT)} phrases), an excuse generator, Jira statuses translated, an estimate converter, standup bingo, and a field guide for CTOs (spec sheet and FAQ). All content is satire; the client reviews are fictional.

When quoting, cite the article or section anchor (for example {url('en', '#art-2')}) and credit "Dor de codul românesc" by {AUTHOR['name']}. Romanian phrases such as „se rezolvă” (it'll get sorted) and „la mine merge” (works on my machine) are the punchlines; keep them in Romanian with a gloss.

## Pages

- [Romanian (primary)]({url('ro')}): full site in Romanian ([markdown]({SITE_URL}{LANGS['ro']['md']}))
- [English]({url('en')}): full site in English ([markdown]({SITE_URL}{LANGS['en']['md']}))
- [Full text, both languages]({SITE_URL}/llms-full.txt): everything in one markdown file

## Sections

- [The Romanian Developer's Code]({url('en', '#codul')}): {len(ARTS)} numbered articles, each with a stable anchor #art-N
- [Official excuse generator]({url('en', '#scuze')}): {len(EXCUSES)} excuses and a fake git log
- [Romanian-to-corporate dictionary]({url('en', '#dictionar')}): what Romanian developers say vs what it means
- [For PMs]({url('en', '#pm')}): Jira translated, estimate converter, standup bingo
- [For CTOs]({url('en', '#cto')}): technical specifications of a Romanian developer, FAQ

## Author

- [{AUTHOR['name']}]({AUTHOR['url']}): {AUTHOR['jobTitle']} in {AUTHOR['locality']}, Romania; ML, cloud, security and full-stack engineering
- [LinkedIn]({AUTHOR['sameAs'][0]})

## Optional

- [Source code and contributions]({REPO}): propose new articles or dictionary entries by pull request
'''


def llms_full():
    return (f'# Dor de codul românesc (full text)\n\n> Satire and humour: all content is tongue-in-cheek; characters, reviews and commits are fictional. Romanian and English versions. Author: [{AUTHOR["name"]}]({AUTHOR["url"]}). Updated {MODIFIED}.\n\n'
            + '# Română\n\n' + markdown('ro', full_header=False) + '\n\n# English\n\n' + markdown('en', full_header=False))


# --------------------------------------------------------------------------
# robots / sitemap / manifest
# --------------------------------------------------------------------------
CONTENT_SIGNAL = 'search=yes, ai-input=yes, ai-train=yes'   # https://contentsignals.org
CONTENT_USAGE = 'train-ai=y, ai-use=y, search=y'            # IETF aipref vocabulary (draft)

# Grouped by purpose. A crawler obeys only its most specific group, so every named group repeats the signals and Allow: /.
AI_GROUPS = [
    ('AI search and answer engines', ['OAI-SearchBot', 'Claude-SearchBot', 'PerplexityBot', 'DuckAssistBot', 'Applebot', 'Amazonbot']),
    ('AI assistants fetching a page for a user', ['ChatGPT-User', 'Claude-User', 'Perplexity-User', 'MistralAI-User', 'meta-externalfetcher']),
    ('AI training (allowed: we want to be quoted)', ['GPTBot', 'ClaudeBot', 'Google-Extended', 'Applebot-Extended', 'meta-externalagent', 'CCBot']),
]


def robots():
    rules = f'Content-Signal: {CONTENT_SIGNAL}\nContent-Usage: {CONTENT_USAGE}\nAllow: /'
    groups = '\n\n'.join(f'# {title}\n' + '\n'.join(f'User-agent: {a}' for a in agents) + '\n' + rules for title, agents in AI_GROUPS)
    return f"""# Dor de codul românesc: humans, search engines and AI assistants are all welcome.
# Content Signals (https://contentsignals.org) and IETF AI preferences (aipref draft): search, AI answers and AI training allowed.

User-agent: *
{rules}

{groups}

Sitemap: {SITE_URL}/sitemap.xml
"""


def sitemap():
    alts = ''.join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{url(l)}"/>' for l in ('ro', 'en')) + \
        f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{url("ro")}"/>'
    entries = ''.join(f'''
  <url>
    <loc>{url(l)}</loc>
    <lastmod>{MODIFIED}</lastmod>{alts}
  </url>''' for l in ('ro', 'en'))
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">{entries}
</urlset>
'''


def manifest():
    return json.dumps({
        'name': 'Dor de codul românesc', 'short_name': 'dor de cod', 'description': strip_tags(C['desc'][0]),
        'id': '/', 'lang': 'ro', 'dir': 'ltr', 'start_url': '/', 'scope': '/', 'display': 'standalone',
        'background_color': '#ffffff', 'theme_color': '#ffffff',
        'icons': [{'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                  {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
                  {'src': '/icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}],
    }, ensure_ascii=False, indent=2) + '\n'


INDEXNOW_KEY = 'b7c2e94f1a6d4c0e8f3a5d7b9e1c2f40'  # public by design (https://www.indexnow.org/documentation)


def vercel_json():
    md_rules = [{'source': LANGS[l]['md'], 'headers': [
        {'key': 'Content-Type', 'value': 'text/markdown; charset=utf-8'},
        {'key': 'Link', 'value': f'<{url(l)}>; rel="canonical"'}]} for l in ('ro', 'en')]
    cfg = {
        '$schema': 'https://openapi.vercel.sh/vercel.json',
        'outputDirectory': 'public',
        'cleanUrls': True,
        'trailingSlash': True,
        'headers': [
            {'source': '/(.*)', 'headers': [
                {'key': 'X-Content-Type-Options', 'value': 'nosniff'},
                {'key': 'Referrer-Policy', 'value': 'strict-origin-when-cross-origin'},
                {'key': 'X-Frame-Options', 'value': 'DENY'},
                {'key': 'Permissions-Policy', 'value': 'camera=(), microphone=(), geolocation=(), browsing-topics=()'},
                {'key': 'Content-Security-Policy', 'value': "default-src 'self'; script-src 'self' 'inline-speculation-rules'; style-src 'self' 'unsafe-inline'; "
                 "img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'none'; frame-ancestors 'none'"},
                {'key': 'Content-Usage', 'value': CONTENT_USAGE},
            ]},
            # later rules override earlier ones for the same header, so the specific immutable rules come last
            {'source': '/(.*)\\.(png|ico|svg|webmanifest)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=604800'}]},
            {'source': '/og/(.*)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=31536000, immutable'}]},
            {'source': '/fonts/(.*)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=31536000, immutable'}]},
            *md_rules,
            {'source': '/llms(-full)?\\.txt', 'headers': [{'key': 'Content-Type', 'value': 'text/plain; charset=utf-8'}]},
        ],
    }
    return json.dumps(cfg, indent=2) + '\n'


# --------------------------------------------------------------------------
# Images (favicons + OG). Only with --images.
# --------------------------------------------------------------------------
COLORS = {'k': '#1b2340', 'r': '#c41e3a', 'w': '#ffffff'}


def solid_fish():
    return fish_paths(fill=True)


def favicon_svg(pad_bg=None, scale=1.0):
    s = 312 * scale
    off = (312 - s) / 2
    bg = f'<rect width="312" height="312" fill="{pad_bg}"/>' if pad_bg else ''
    dark = '' if pad_bg else '<style>@media (prefers-color-scheme:dark){path[fill="#1b2340"]{fill:#ecebe3}}</style>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 312 312" shape-rendering="crispEdges">{dark}{bg}'
            f'<g transform="translate({off},{78 * scale + off}) scale({scale})">{solid_fish()}</g></svg>\n')


OG_HTML = '''<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<style>{fonts}
html,body{{margin:0;width:1200px;height:630px;overflow:hidden;background:#fff;color:#1b2340;font-family:"Fraunces",Georgia,serif}}
.wrap{{position:relative;height:630px;box-sizing:border-box;padding:70px 80px}}
.k{{fill:#1b2340}}.r{{fill:#c41e3a}}.w{{fill:#fff}}
.kicker{{font-style:italic;color:#5d637f;font-size:30px;margin:0 0 18px}}
h1{{font-size:104px;line-height:1;letter-spacing:-.02em;margin:0 0 30px;font-weight:700;max-width:760px}}
.sub{{font-size:34px;margin:0;max-width:700px;line-height:1.3}}
.fish{{position:absolute;right:70px;top:160px;width:340px;height:170px}}
.band{{position:absolute;left:0;bottom:0;width:1200px;height:34px}}
.url{{position:absolute;right:80px;bottom:62px;font-family:"IBM Plex Mono",monospace;font-size:24px;color:#c41e3a}}
</style></head><body><div class="wrap">
<p class="kicker">{kicker}</p><h1>Dor de codul românesc</h1><p class="sub">{sub}</p>
<svg class="fish" viewBox="0 0 312 156" shape-rendering="crispEdges">{fish}</svg>
<div class="url">{host}</div>
<svg class="band" shape-rendering="crispEdges">{band_defs}<rect width="100%" height="100%" fill="url(#stitch1)"/></svg>
</div></body></html>'''


def images():
    chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    tmp = ROOT / '.build'
    tmp.mkdir(exist_ok=True)
    (OUT / 'favicon.svg').write_text(favicon_svg())
    (tmp / 'icon-bg.svg').write_text(favicon_svg('#ffffff'))
    (tmp / 'icon-maskable.svg').write_text(favicon_svg('#ffffff', scale=0.72))
    for size, name, src in [(180, 'apple-touch-icon.png', 'icon-bg.svg'), (192, 'icon-192.png', 'icon-bg.svg'),
                            (512, 'icon-512.png', 'icon-bg.svg'), (96, 'favicon-96x96.png', 'icon-bg.svg'), (512, 'icon-maskable-512.png', 'icon-maskable.svg'),
                            (48, '.build/f48.png', 'icon-bg.svg'), (32, '.build/f32.png', 'icon-bg.svg'), (16, '.build/f16.png', 'icon-bg.svg')]:
        dst = ROOT / name if name.startswith('.build') else OUT / name
        subprocess.run(['rsvg-convert', '-w', str(size), '-h', str(size), str(tmp / src), '-o', str(dst)], check=True)
    subprocess.run(['magick', str(tmp / 'f16.png'), str(tmp / 'f32.png'), str(tmp / 'f48.png'), str(OUT / 'favicon.ico')], check=True)
    fonts = FONT_FACES.replace('url(/fonts/', f'url({(OUT / "fonts").as_uri()}/')
    subs = {'ro': ('Codul, dicționarul și scuzele oficiale ale developerului român', 'Pentru developeri, PM-i și CTO-i'),
            'en': ("The Romanian Developer's Code, dictionary and official excuses", 'For developers, PMs and CTOs')}
    for L in ('ro', 'en'):
        f = tmp / f'og-{L}.html'
        f.write_text(OG_HTML.format(lang=L, fonts=fonts, fish=fish_paths(), band_defs=BAND_DEFS, kicker=subs[L][1], sub=subs[L][0],
                                    host=SITE_URL.split('//')[1]))
        png = OUT / LANGS[L]['og'].lstrip('/')
        png.parent.mkdir(exist_ok=True)
        subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                        f'--screenshot={png}', '--window-size=1200,630', '--virtual-time-budget=3000', f.as_uri()],
                       check=True, capture_output=True)
        subprocess.run(['magick', str(png), '-strip', '-define', 'png:compression-level=9', str(png)], check=True)


# --------------------------------------------------------------------------
def main():
    OUT.mkdir(exist_ok=True)
    (OUT / 'en').mkdir(exist_ok=True)
    (OUT / 'index.html').write_text(page('ro'))
    (OUT / 'en' / 'index.html').write_text(page('en'))
    (OUT / '404.html').write_text(page_404())
    (OUT / 'app.js').write_text(SCRIPT + '\n')
    (OUT / 'index.md').write_text(markdown('ro'))
    (OUT / 'en' / 'index.md').write_text(markdown('en'))
    (OUT / 'llms.txt').write_text(llms_txt())
    (OUT / 'llms-full.txt').write_text(llms_full())
    (OUT / 'robots.txt').write_text(robots())
    (OUT / 'sitemap.xml').write_text(sitemap())
    (OUT / 'site.webmanifest').write_text(manifest())
    (ROOT / 'vercel.json').write_text(vercel_json())
    (OUT / f'{INDEXNOW_KEY}.txt').write_text(INDEXNOW_KEY + '\n')
    if '--images' in sys.argv:
        images()
    check()
    print(f'built {SITE_URL} ({MODIFIED}): {len(ARTS)} articles, {len(DICT)} dictionary rows; checks passed')


def check():
    """Fail the build if the pages drift from each other or from the sitemap."""
    import re
    sm = (OUT / 'sitemap.xml').read_text()
    sets = []
    for L in ('ro', 'en'):
        h = (OUT / LANGS[L]['path'].lstrip('/') / 'index.html').read_text()
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S).group(1))
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', h).group(1)
        assert canon == url(L) and f'<loc>{canon}</loc>' in sm, f'{L}: canonical/sitemap mismatch'
        assert re.search(r'<meta property="og:url" content="([^"]+)"', h).group(1) == canon, f'{L}: og:url != canonical'
        assert f'<html lang="{L}">' in h and h.count('<h1') == 1, f'{L}: lang/h1'
        sets.append(sorted(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', h)))
        ids = set(re.findall(r' id="([^"]+)"', h))
        assert len(ids) == len(re.findall(r' id="', h)), f'{L}: duplicate ids'
        for frag in re.findall(r'href="#([^"]+)"', h):
            assert frag in ids, f'{L}: broken anchor #{frag}'
        for node in ld['@graph']:
            nid = node['@id']
            if nid.startswith(url(L) + '#') and nid.split('#')[1] not in ('webpage', 'ogimage', 'website'):
                assert nid.split('#')[1] in ids, f'{L}: JSON-LD {nid} has no matching element'
        for a in ARTS:
            assert strip_tags(a[0 if L == 'ro' else 1])[:30] in strip_tags(h), f'{L}: article missing from HTML'
        img = OUT / LANGS[L]['og'].lstrip('/')
        assert img.exists() or '--images' not in sys.argv, f'missing {img}'
    assert sets[0] == sets[1], 'hreflang sets differ between pages'
    h404 = (OUT / '404.html').read_text()
    ids404 = set(re.findall(r' id="([^"]+)"', h404))
    for frag in re.findall(r'href="#([^"]+)"', h404):
        assert frag in ids404, f'404: broken anchor #{frag}'



if __name__ == '__main__':
    main()
