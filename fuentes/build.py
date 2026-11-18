"""Arma las slides: mete las fuentes tipográficas dentro del HTML y escribe clase-XX/slides.html.

Uso, desde la raíz del repo:
    python fuentes/build.py
"""
import base64
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
TIPOS = os.path.join(AQUI, 'fuentes-tipograficas')

LATIN = ("U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, "
         "U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD")
SIMBOLOS = "U+2190-2193, U+2248, U+2264-2265, U+2713"


def b64(nombre):
    with open(os.path.join(TIPOS, nombre), 'rb') as f:
        return base64.b64encode(f.read()).decode()


reglas = []
for familia, archivo, pesos in [('Inter', 'Inter', '400 700'),
                                ('Space Grotesk', 'SpaceGrotesk', '500 700'),
                                ('JetBrains Mono', 'JetBrainsMono', '400 700')]:
    for parte, rango in [('latin', LATIN), ('sym', SIMBOLOS)]:
        reglas.append("@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;"
                      "src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s}"
                      % (familia, pesos, b64(f'{archivo}-{parte}.woff2'), rango))
css = ("/* Fuentes incluidas (Inter, Space Grotesk, JetBrains Mono · licencia SIL Open Font License) */\n"
       + "\n".join(reglas))

for fuente, salida in [('clase-01.src.html', 'clase-01/slides.html'),
                       ('clase-02.src.html', 'clase-02/slides.html')]:
    with open(os.path.join(AQUI, fuente), encoding='utf-8') as f:
        html = f.read()
    assert html.count('/*@FONTS@*/') == 1
    destino = os.path.join(RAIZ, salida)
    with open(destino, 'w', encoding='utf-8') as f:
        f.write(html.replace('/*@FONTS@*/', css))
    print(salida, round(os.path.getsize(destino) / 1024), 'KB')
