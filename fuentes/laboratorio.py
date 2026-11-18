"""Genera el notebook del laboratorio de la clase 1.

Uso, desde la raíz del repo:
    python fuentes/laboratorio.py
"""
import json, sys, os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'clase-01', 'laboratorio-disco-ram-cpu.ipynb')
cells = []
def md(t): cells.append({"cell_type": "markdown", "metadata": {}, "source": t.strip('\n')})
def code(t): cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.strip('\n')})

md('''
# Laboratorio 1 · Disco, RAM y CPU

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/csaybar/curso-ingenieria-de-datos/blob/main/clase-01/laboratorio-disco-ram-cpu.ipynb)

Curso taller *Ingeniería de datos para la investigación: procesamiento de imágenes satelitales con deep learning* · Clase 1 · Cesar Aybar

En clase vimos el camino de los datos: disco → RAM → CPU. Aquí lo medimos en una máquina de verdad, con cinco experimentos:

0. Qué procesador, qué RAM y qué disco tienes.
1. Un archivo grande contra 40 960 archivos chicos.
2. La segunda lectura de un archivo viene de la RAM.
3. Leer la RAM en orden o saltando al azar.
4. El NDVI con y sin instrucciones SIMD.

Corre las celdas en orden con Shift + Enter. Los tiempos cambian de un computador a otro, e incluso de una vez a otra; lo que importa es la diferencia entre los dos casos de cada experimento.

En Colab no hay que instalar nada: ábrelo con el botón de arriba y corre las celdas. También funciona en tu computador con Jupyter o VS Code; ahí necesitas Python con NumPy y, para el experimento 4, un compilador de C (en Linux, `gcc`; en Mac, `xcode-select --install`; en Windows, WSL). Mientras corre ocupa unos 1,3 GB de disco; la última celda borra todo.
''')
code('''
import os, re, sys, time, shutil, platform, subprocess
import numpy as np

CARPETA = os.path.abspath('laboratorio_clase1')    # aquí se guarda todo
os.makedirs(CARPETA, exist_ok=True)
os.chdir(CARPETA)
SISTEMA = platform.system()                        # 'Linux', 'Darwin' (Mac) o 'Windows'
print(SISTEMA, platform.machine(), '| Python', platform.python_version(), '| NumPy', np.__version__)

def correr(comando):
    """Corre un comando del sistema y muestra lo que responde."""
    r = subprocess.run(comando, shell=True, capture_output=True, text=True)
    print((r.stdout + r.stderr).strip('\\n'))

def olvidar(ruta):
    """Saca un archivo de la RAM para que la próxima lectura vaya al disco (solo funciona en Linux)."""
    if hasattr(os, 'posix_fadvise'):
        fd = os.open(ruta, os.O_RDONLY)
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        os.close(fd)

def leer(ruta):
    """Lee un archivo entero, de a 8 MB, con llamadas directas al sistema operativo."""
    fd = os.open(ruta, os.O_RDONLY | getattr(os, 'O_BINARY', 0))
    while os.read(fd, 8 << 20):
        pass
    os.close(fd)
''')

md('''
## 0. ¿Qué tengo?

Primero el procesador: modelo, núcleos, tamaño de las cachés y qué instrucciones SIMD entiende.
''')
code('''
if SISTEMA == 'Linux':
    correr("lscpu | grep -E 'Model name|^CPU\\\\(s\\\\)|Thread|L1d|L2|L3'")
    correr("echo SIMD: $(grep -o -w -E 'sse2|avx|avx2|avx512f|asimd' /proc/cpuinfo | sort -u)")
    correr('free -h')
elif SISTEMA == 'Darwin':
    correr('sysctl -n machdep.cpu.brand_string')
    correr('sysctl hw.ncpu hw.l1dcachesize hw.l2cachesize hw.memsize')
    correr("sysctl -a | grep -E 'hw.optional.(neon|avx2_0|avx512f):'")
elif SISTEMA == 'Windows':
    correr('powershell -NoProfile "Get-CimInstance Win32_Processor | Format-List Name,NumberOfCores,L2CacheSize,L3CacheSize"')
    correr('powershell -NoProfile "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)"')
''')
md('''
Anota el tamaño de la **L1d** y de la **L2**: los vas a necesitar en el experimento 4. En Linux, `lscpu` suma las cachés de todos los núcleos: si dice "192 KiB (4 instances)", cada núcleo tiene 48 KiB. En Mac, `hw.memsize` está en bytes.

Ahora el disco.
''')
code('''
if SISTEMA == 'Linux':
    correr('lsblk -d -o NAME,ROTA,TRAN,SIZE,MODEL')
elif SISTEMA == 'Darwin':
    correr('diskutil info disk0 | grep -E "Media Name|Solid State|Protocol"')
elif SISTEMA == 'Windows':
    correr('powershell -NoProfile "Get-PhysicalDisk | Format-Table FriendlyName,MediaType,BusType,Size"')
''')
md('''
Cómo leerlo:

- Linux: `ROTA` 1 es un disco que gira (HDD) y 0 es un SSD. `TRAN` dice si va por `nvme` o por `sata`. Si el nombre empieza con `nvme`, es NVMe.
- Mac: `Solid State: Yes` es un SSD. Los Mac con chip Apple dicen `Protocol: Apple Fabric`: es un SSD conectado por PCIe, como un NVMe.
- Windows: `MediaType` dice SSD o HDD, y `BusType` dice NVMe o SATA.

En una máquina virtual o en la nube esto no sirve: el disco es virtual y puede aparecer como HDD sin serlo. Ahí lo que manda es la velocidad que midamos en el experimento 2.
''')

md('''
## 1. Un archivo grande contra 40 960 archivos chicos

Los mismos 160 MB guardados de dos formas: en un solo archivo o en 40 960 archivos de 4 KB, como un dataset de parches pequeños. Medimos cuánto tarda escribirlos y leerlos.
''')
code('''
TAM, N = 4096, 40_960                       # 40 960 x 4 KB = 160 MB
datos = memoryview(os.urandom(TAM * N))
os.makedirs('chicos', exist_ok=True)
chicos = [os.path.join('chicos', f'parche_{i:05d}.bin') for i in range(N)]

t = time.perf_counter()
with open('grande.bin', 'wb') as f:
    f.write(datos)
escribir_1 = time.perf_counter() - t

t = time.perf_counter()
for i, ruta in enumerate(chicos):
    with open(ruta, 'wb') as f:
        f.write(datos[i * TAM:(i + 1) * TAM])
escribir_n = time.perf_counter() - t

if hasattr(os, 'sync'):
    os.sync()
for ruta in ['grande.bin'] + chicos:
    olvidar(ruta)

t = time.perf_counter(); leer('grande.bin'); leer_1 = time.perf_counter() - t
t = time.perf_counter()
for ruta in chicos:
    leer(ruta)
leer_n = time.perf_counter() - t

print(f"{'':18}{'escribir':>10}{'leer':>10}")
print(f"{'1 archivo':18}{escribir_1:9.2f} s{leer_1:9.2f} s")
print(f"{'40 960 archivos':18}{escribir_n:9.2f} s{leer_n:9.2f} s")
print(f"{'diferencia':18}{escribir_n / escribir_1:9.0f} x{leer_n / leer_1:9.0f} x")
''')
md('''
Son los mismos bytes. La diferencia es el trabajo del sistema operativo con cada archivo: buscarlo en la carpeta, leer o crear su ficha, abrirlo, cerrarlo. En Windows suele ser todavía peor, porque además el antivirus revisa cada archivo.
''')

md('''
## 2. La segunda lectura viene de la RAM

Ahora un archivo de 1 GB, más o menos lo que pesa una escena Sentinel-2 completa. Lo leemos dos veces seguidas.

Para que la primera lectura vaya de verdad al disco, el archivo no puede estar ya en la RAM. En Linux eso lo hace la celda sola. En Mac, después de crear el archivo abre la Terminal y corre `sudo purge`. En Windows no hay un comando simple: reinicia el computador y corre solo la primera celda del notebook y la de lectura (el archivo queda guardado en la carpeta).
''')
code('''
bloque = os.urandom(64 << 20)                 # 64 MB
with open('escena_1gb.bin', 'wb') as f:
    for _ in range(16):
        f.write(bloque)
if hasattr(os, 'sync'):
    os.sync()
olvidar('escena_1gb.bin')
print('escena_1gb.bin:', os.path.getsize('escena_1gb.bin') // 2**20, 'MB')
''')
code('''
for vez in ['Primera', 'Segunda']:
    t = time.perf_counter()
    leer('escena_1gb.bin')
    s = time.perf_counter() - t
    print(f'{vez} lectura: {s:6.2f} s   ({1024 / s:7.0f} MB/s)')
''')
md('''
La primera vez el archivo viene del disco, y esos MB/s son la velocidad real de tu disco: compáralos con las slides (disco duro ~150 MB/s, SSD SATA ~550 MB/s, NVMe varios miles). La segunda vez el sistema operativo ya tiene una copia en la RAM y ni siquiera toca el disco.
''')

md('''
## 3. La RAM, en orden y al azar

50 millones de números (200 MB) en la RAM. Los sumamos dos veces con el mismo código: primero en orden y después saltando al azar. Lo único que cambia es el orden.
''')
code('''
x = np.ones(50_000_000, dtype=np.float32)
en_orden = np.arange(x.size)
al_azar = np.random.default_rng(0).permutation(x.size)

t = time.perf_counter(); x[en_orden].sum(); t_orden = time.perf_counter() - t
t = time.perf_counter(); x[al_azar].sum();  t_azar = time.perf_counter() - t

print(f'en orden: {t_orden:.2f} s')
print(f'al azar:  {t_azar:.2f} s   ({t_azar / t_orden:.1f} veces más lento)')
del x, en_orden, al_azar
''')
md('''
La caché trae la RAM en líneas de 64 bytes. En orden, cada línea trae 16 números que vamos a usar. Al azar, casi siempre trae uno solo, y por cada número hay que volver a la RAM.
''')

md('''
## 4. El NDVI con y sin SIMD

Para ver lo que aportan las instrucciones SIMD hay que comparar el mismo programa contra sí mismo. Escribimos el NDVI en C y lo compilamos dos veces: una sin instrucciones vectoriales (una división por instrucción) y otra con ellas (AVX2 en Intel y AMD: 8 divisiones por instrucción; NEON en Mac con chip Apple: 4). Mismo código, mismo compilador; solo cambian las instrucciones.
''')
code('''
%%writefile ndvi.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef LADO
#define LADO 1000
#endif
#define N (LADO * LADO)
#define TOTAL 200000000L     /* en cada prueba se procesan 200 millones de píxeles */

static float nir[N], red[N], out[N];

__attribute__((noinline))
void ndvi(const float *restrict a, const float *restrict b, float *restrict o, int n) {
    for (int i = 0; i < n; i++)
        o[i] = (a[i] - b[i]) / (a[i] + b[i]);
}

int main(void) {
    srand(1);
    for (int i = 0; i < N; i++) {
        nir[i] = rand() / (float)RAND_MAX + 0.01f;
        red[i] = rand() / (float)RAND_MAX + 0.01f;
    }
    long veces = TOTAL / N;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long r = 0; r < veces; r++) ndvi(nir, red, out, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);

    double s = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    double control = 0;
    for (int i = 0; i < N; i++) control += out[i];
    fprintf(stderr, "control %.1f\\n", control);   /* para que el compilador no se salte el cálculo */
    printf("%.4f\\n", s);
    return 0;
}
''')
code('''
cc = shutil.which('gcc') or shutil.which('clang') or shutil.which('cc')
if cc is None:
    print('No encontré un compilador de C (ver la primera celda de texto).')
else:
    clang = 'clang' in subprocess.run([cc, '--version'], capture_output=True, text=True).stdout
    arm = platform.machine().lower() in ('arm64', 'aarch64')
    SIN_SIMD = '-O2 -fno-vectorize -fno-slp-vectorize' if clang else '-O2 -fno-tree-vectorize -fno-tree-slp-vectorize'
    CON_SIMD = '-O3' if arm else '-O3 -mavx2'
    SIMD = 'NEON' if arm else 'AVX2'
    subprocess.run(f'{cc} {SIN_SIMD} -o ndvi_sin_simd ndvi.c', shell=True, check=True)
    subprocess.run(f'{cc} {CON_SIMD} -o ndvi_{SIMD.lower()} ndvi.c', shell=True, check=True)

    def divisiones(binario):
        """Las instrucciones de división que usa la función ndvi, y en qué registros."""
        texto = subprocess.run(['objdump', '-d', binario], capture_output=True, text=True).stdout
        dentro, vistas = False, set()
        for linea in texto.splitlines():
            if re.search(r'<_?ndvi>:', linea):
                dentro = True
                continue
            if dentro and not linea.strip():
                break
            m = re.search(r'\\b(v?div[sp][sd]|fdiv(?:\\.\\d+s)?)\\s+(.*)', linea) if dentro else None
            if m:
                reg = re.search(r'%([xyz]mm)|\\b(v\\d+\\.\\d+s|[sd]\\d+)\\b', m.group(2))
                vistas.add(m.group(1) + (' ' + (reg.group(1) or re.sub(r'\\d+', '', reg.group(2))) if reg else ''))
        return ', '.join(sorted(vistas))

    if shutil.which('objdump'):
        print(f'sin SIMD: {divisiones("ndvi_sin_simd")}')
        print(f'{SIMD}:     {divisiones("ndvi_" + SIMD.lower())}')
''')
md('''
En Intel y AMD, `divss` divide un número en un registro `xmm`; `vdivps` divide 8 a la vez en un registro `ymm` de 256 bits (ss = un número, ps = varios empaquetados). La versión AVX2 también trae `vdivss` para los píxeles que sobran al final. En un Mac con chip Apple, la división de un número se ve como `fdiv s` y la de cuatro como `fdiv v.s` o `fdiv.4s`.

Ahora lo medimos con imágenes de distintos tamaños. En todas se procesan 200 millones de píxeles; lo que cambia es cuánto ocupan los datos (nir, red y el resultado).
''')
code('''
print(f"{'imagen':>11}{'datos':>11}{'sin SIMD':>10}{SIMD:>9}{'ganancia':>10}")
for lado in [64, 128, 256, 512, 1000, 2000, 4000]:
    subprocess.run(f'{cc} {SIN_SIMD} -DLADO={lado} -o prueba_e ndvi.c', shell=True, check=True)
    subprocess.run(f'{cc} {CON_SIMD} -DLADO={lado} -o prueba_v ndvi.c', shell=True, check=True)
    t_e = float(subprocess.run(['./prueba_e'], capture_output=True, text=True).stdout)
    t_v = float(subprocess.run(['./prueba_v'], capture_output=True, text=True).stdout)
    datos = 3 * lado * lado * 4 / 1e6
    print(f'{lado:>5} x {lado:<5}{datos:8.2f} MB{t_e:8.3f} s{t_v:7.3f} s{t_e / t_v:9.1f} x')
''')
md('''
Mira dónde cae la ganancia y compárala con los tamaños de caché del experimento 0.

Mientras los datos caben en la L1 o la L2, la versión SIMD va varias veces más rápido (en un Xeon con AVX2 nos dio casi 5). Cuando ya no caben y hay que traerlos de la RAM, la ganancia se achica: el núcleo pasa más tiempo esperando los datos que calculando. Por eso las librerías de imágenes trabajan por bloques.
''')

md('''
## Para pensar

1. En el experimento 1, ¿qué pasaría con un disco duro en vez de un SSD?
2. En el experimento 2, ¿por qué un programa que abre la misma imagen dos veces parece más rápido la segunda vez?
3. En el experimento 4, ¿por qué no sale 8 veces más rápido si AVX2 hace 8 divisiones a la vez?

Para borrar todo lo que creamos (unos 1,3 GB):
''')
code('''
os.chdir('..')
shutil.rmtree(CARPETA)
print('borrado:', CARPETA)
''')

nb = {"cells": cells,
      "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
for i, c in enumerate(nb["cells"]):
    c["id"] = f"celda-{i:02d}"
json.dump(nb, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(out, len(cells), 'celdas')
