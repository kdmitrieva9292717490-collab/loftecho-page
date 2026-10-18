#!/usr/bin/env python3
"""Собирает сайт ЛофтЭхо из исходников в src/.

    python3 build.py

На выходе:
    dist/index.html          — главная
    dist/paket-<slug>.html   — 9 страниц пакетных предложений (данные — src/packages.json)
    dist/images.css          — все фото (data-URI), общий файл для главной и пакетов:
                               браузер скачивает его один раз
    dist/artifact.html       — главная одним файлом без обёртки <html>/<head>/<body>
                               (фото вшиты внутрь) — в таком виде она публикуется как Claude Artifact
"""
import hashlib, html, json, os, re

IMG_V = ""   # метка версии images.css (хеш содержимого) — чтобы браузер не держал старые фото из кэша

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "src")
DIST = os.path.join(HERE, "dist")


def read(name):
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        return f.read()


def write(name, text):
    with open(os.path.join(DIST, name), "w", encoding="utf-8") as f:
        f.write(text)
    return len(text.encode()) / 1048576


def page(head, body, script, title=None):
    if title:
        head = re.sub(r"<title>.*?</title>", "<title>" + html.escape(title) + "</title>", head, count=1)
    return ('<!doctype html>\n<html lang="ru">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<link rel="stylesheet" href="images.css?v=' + IMG_V + '">\n'
            '</head>\n<body style="margin:0">\n' + head + "\n" + body + "\n" + script + "\n</body>\n</html>\n")


# ─── разделы главной: 2-body.html размечен комментариями «<!-- ════════ ИМЯ ...» ───
def split_parts(body):
    marks = list(re.finditer(r"<!-- ════════ ([^═\n]+?)(?: —[^═\n]*)? ════════ -->", body))
    parts = {"_PRE": body[:marks[0].start()]}          # зерно и полоса прогресса — нужны скрипту
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        parts[m.group(1).strip()] = body[m.start():end]
    return parts


# ─── разметка пакета ───
def rich(s):
    """[текст] → жёлтый, \\n → перенос строки; остальное экранируется."""
    s = html.escape(s)
    s = re.sub(r"\[(.+?)\]", r"<em>\1</em>", s)
    # слова через дефис («караоке-лофте») не разрываем по дефису
    s = re.sub(r"([А-Яа-яЁёA-Za-z]+-[А-Яа-яЁёA-Za-z]+)", r'<span class="nw">\1</span>', s)
    return s.replace("\n", "<br>")


def no_widow(s):
    """Последнее слово заголовка не остаётся одно на строке."""
    return re.sub(r" (\S+)$", " \\1", s)


SHORT = r"в|во|с|со|и|к|ко|о|об|у|а|но|на|по|до|за|из|от|не|для|без|при|про"


def nobr(s):
    """Висячие предлоги: короткое слово склеивается со следующим неразрывным пробелом,
    перед тире — тоже неразрывный пробел. Работает по тексту с [..]-разметкой."""
    s = re.sub(r"(?<![\wЁё])(%s) +" % SHORT, "\\1\u00a0", s, flags=re.I)
    return re.sub(r" +([-–—])", "\u00a0\\1", s)


def card_html(c, level):
    tags = "".join('<span class="tag">%s</span>' % html.escape(t) for t in c["tags"])
    prices = "".join(
        '<div class="pk-price"><div class="t">%s</div><div class="row"><b class="d">%s</b>%s</div></div>'
        % (html.escape(p[0]), html.escape(p[1]).replace(" ", "&nbsp;"),
           ('<s class="d">%s</s>' % html.escape(p[2]).replace(" ", "&nbsp;")) if p[2] else "")
        for p in c["prices"])
    items = "".join('<li%s>%s</li>' % (' class="ys"' if it.startswith("[") else "", rich(it)) for it in c["items"])
    return ('<article class="pk-card l%d rv up">'
            '<div class="pk-head"><h3 class="d">%s</h3><div class="pk-tags">%s</div></div>'
            '<div class="pk-prices%s">%s</div>'
            '<button class="btn btn-pink">Оформить</button>'
            '<div class="pk-list"><h4>Что включает</h4><ul>%s</ul></div>'
            '</article>') % (level, html.escape(c["title"]), tags,
                             " one" if len(c["prices"]) == 1 else "", prices, items)


def package_sections(p, data):
    hero = ('<!-- ════════ PACKAGE HERO ════════ -->\n'
            '<section class="hero pk-hero" id="top">\n'
            '  <div class="kbs" id="kbs"></div>\n'
            # подложка как на главной (Figma: Gradient Overlay снизу) — затемнение сверху, плавное размытие и вуаль
            '  <div class="hero-top"></div>\n'
            '  <div class="hero-blur"><i></i><i></i><i></i><i></i></div>\n'
            '  <div class="hero-veil"></div>\n'
            '  <div class="wrap"><h1 class="d in" id="heroH1">%s</h1></div>\n'
            '</section>\n') % rich(no_widow(nobr(p["hero"])))
    levels = [1, 2, 3] if len(p["cards"]) == 3 else [1] * len(p["cards"])
    cards = "".join(card_html(c, lv) for c, lv in zip(p["cards"], levels))
    common = data["common"]
    pricing = ('<!-- ════════ PACKAGE PRICING ════════ -->\n'
               '<section class="sec" id="pricing" style="padding-top:var(--gap)">\n<div class="wrap">\n'
               '  <div class="shead rv" style="max-width:930px">\n'
               '    <div class="tb"><span class="label up">Комбо</span><h2 class="d h2 up">%s</h2></div>\n'
               '    <p class="sub up" style="max-width:335px">%s</p>\n'
               '  </div>\n'
               '  <div class="pk-grid">%s</div>\n'
               '  <div class="pk-common rv up"><p>%s</p><h4>%s</h4><ul>%s</ul></div>\n'
               '</div>\n</section>\n') % (
        rich(nobr(p["title"])), rich(nobr(p.get("subtitle", data["corkage"]))), cards,
        html.escape(common["lead"]), html.escape(common["title"]),
        "".join("<li>%s</li>" % html.escape(x) for x in common["items"]))
    return hero + "\n" + pricing


def main():
    os.makedirs(DIST, exist_ok=True)

    head   = read("1-head.html")     # <title>, шрифты, все стили
    images = read("images.css")      # :root{ --i-*: url(data:image/webp;base64,...) }
    body   = read("2-body.html")     # разметка главной + спрайт иконок из Figma
    script = read("3-script.html")   # вся логика
    data   = json.loads(read("packages.json"))
    global IMG_V
    IMG_V = hashlib.md5(images.encode()).hexdigest()[:8]

    # artifact.html — как раньше, всё внутри одного файла
    artifact = head + "\n<style>\n" + images + "\n</style>\n" + body + "\n" + script
    report = [("dist/artifact.html", write("artifact.html", artifact))]

    # сайт: фото отдельным общим файлом
    report.append(("dist/images.css", write("images.css", images)))
    report.append(("dist/index.html", write("index.html", page(head, body, script))))

    parts = split_parts(body)
    shared_top = parts["_PRE"] + parts["ICON SPRITE (exported from Figma)"] + parts["HEADER"]
    shared_bottom = "".join(parts[k] for k in ("ABOUT / FEATURES", "REVIEWS", "SEO", "MAP", "FOOTER",
                                               "MODAL: ROOM DETAILS", "MODAL: GALLERY FULLSCREEN"))
    for p in data["packages"]:
        # якоря разделов, которых нет на странице пакета, ведут на главную
        top = re.sub(r'href="#(rooms|combos|offers|gallery)"', r'href="index.html#\1"', shared_top)
        pbody = top + package_sections(p, data) + shared_bottom
        name = "paket-%s.html" % p["slug"]
        title = "%s — ЛофтЭхо" % p["name"]
        report.append(("dist/" + name, write(name, page(head, pbody, script, title))))

    for n, mb in report:
        print("%-42s %.2f MB" % (n, mb))
    if report[0][1] > 16:
        print("ВНИМАНИЕ: лимит артефакта 16 МБ превышен")


if __name__ == "__main__":
    main()
