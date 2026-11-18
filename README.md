# Ingeniería de datos para la investigación

Curso taller: procesamiento de imágenes satelitales con deep learning. Cesar Aybar.

Material de las clases: slides, notas para el expositor y laboratorios.

| Clase | Fecha | Tema | Material |
|---|---|---|---|
| 1 | Miércoles 18 de noviembre de 2026 | La arquitectura de cómputo: disco, RAM y CPU | [slides](clase-01/slides.html) · [PDF](clase-01/slides.pdf) · [laboratorio](clase-01/laboratorio-disco-ram-cpu.ipynb) |
| 2 | Viernes 20 de noviembre de 2026 | PCIe, VRAM y la GPU | [slides](clase-02/slides.html) · [PDF](clase-02/slides.pdf) |

## Ver las slides

Cada `slides.html` es un solo archivo que funciona sin internet. GitHub muestra el código, no la presentación: descárgalo (botón *Download raw file*) y ábrelo en Chrome, Edge o Firefox. Si solo quieres leerlas, abre el PDF.

| Tecla | Qué hace |
|---|---|
| → / Espacio | siguiente (primero las animaciones de la slide) |
| ← | anterior |
| S | ventana del expositor: notas, siguiente slide y reloj |
| O | ver todas las slides |
| F | pantalla completa |
| B | pantalla en negro |
| D | lápiz para marcar (Z deshace, C borra) |
| número + Enter | ir a esa slide |

## Laboratorio de la clase 1

`clase-01/laboratorio-disco-ram-cpu.ipynb` mide en tu propio computador lo que vimos en clase: muchos archivos chicos contra uno grande, la segunda lectura desde la RAM, la RAM en orden y al azar, y el NDVI en C con y sin instrucciones SIMD.

Necesita Python con NumPy y Jupyter (o VS Code). Para el último experimento hace falta un compilador de C: `gcc` en Linux, `xcode-select --install` en Mac, WSL en Windows. Mientras corre ocupa unos 1,3 GB de disco; la última celda borra todo.

## Editar el material

Las slides se editan en `fuentes/clase-0X.src.html`: cada slide es un `<section class="slide">` y sus notas van en `<aside class="notes">`. Después:

```bash
python fuentes/build.py
node fuentes/pdf.js clase-01/slides.html clase-01/slides.pdf
node fuentes/pdf.js clase-02/slides.html clase-02/slides.pdf
```

El notebook del laboratorio se genera con `python fuentes/laboratorio.py`.

Las fuentes tipográficas (Inter, Space Grotesk y JetBrains Mono) tienen licencia SIL Open Font License; los textos de las licencias están en `fuentes/fuentes-tipograficas/`.
