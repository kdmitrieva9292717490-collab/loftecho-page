#!/usr/bin/env python3
"""Собирает страницу ЛофтЭхо из исходников в src/.

    python3 build.py

На выходе:
    dist/index.html     — обычная страница, открывается двойным кликом
    dist/artifact.html  — тот же документ без обёртки <html>/<head>/<body>,
                          в таком виде он публикуется как Claude Artifact
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "src")
DIST = os.path.join(HERE, "dist")

def read(name):
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        return f.read()

def main():
    os.makedirs(DIST, exist_ok=True)

    head   = read("1-head.html")     # <title>, шрифты, все стили
    images = read("images.css")      # :root{ --i-*: url(data:image/webp;base64,...) }
    body   = read("2-body.html")     # разметка + спрайт иконок из Figma
    script = read("3-script.html")   # вся логика

    artifact = head + "\n<style>\n" + images + "\n</style>\n" + body + "\n" + script

    page = ('<!doctype html>\n<html lang="ru">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '</head>\n<body style="margin:0">\n' + artifact + '\n</body>\n</html>\n')

    with open(os.path.join(DIST, "artifact.html"), "w", encoding="utf-8") as f:
        f.write(artifact)
    with open(os.path.join(DIST, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    mb = len(page.encode()) / 1048576
    print(f"dist/index.html     {mb:.2f} MB")
    print(f"dist/artifact.html  {len(artifact.encode())/1048576:.2f} MB")
    if mb > 16:
        print("ВНИМАНИЕ: лимит артефакта 16 МБ превышен")

if __name__ == "__main__":
    main()
