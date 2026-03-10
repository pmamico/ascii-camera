# ASCII Camera

Terminálban futó, curses alapú ASCII kamera néző macOS-re. A kamera BGR képkockáit 95 nyomtatható ASCII karakter kombinációjává alakítja, majd tisztán zöld (Matrix-hangulatú) betűkkel rajzolja ki.

## Követelmények

- Python 3.11+
- macOS terminál (Terminal.app vagy iTerm2)
- Kamera-hozzáférés engedélyezve a futtatott terminál számára

## Telepítés

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Prototípus futtatása

Az első, curses nélküli lépés egyetlen frame-et konvertál ASCII képpé:

```bash
python -m ascii_cam.prototype [--stats] [--save-frame frame.png] [--no-color]
```

Hasznos opciók:

- `--stats`: a prototípus a végén kiírja a rögzített frame alakját, min/max, átlag, szórás értékeit, így látható, milyen intenzitásokat próbált ASCII-re alakítani.
- `--save-frame frame.png`: elmenti a rögzített (BGR) frame-et PNG-ként, hogy külső nézőben ellenőrizhető legyen az eredeti kép.
- `--no-color`: letiltja a zöld ANSI borítást, ha tisztán ASCII-ra van szükség.

## Teljes képernyős UI futtatása

```bash
ascii-cam  # vagy: python -m ascii_cam.main
```

Billentyűk:

- `q`: kilépés

A program automatikusan kezeli az ablak átméretezését, full-screen módon, zöld ASCII karakterekkel rajzolja ki az élő képet, és státuszsorban jelzi az aktuális felbontást vagy hibát. Ha a terminál túl kicsi (szélesség < 40 vagy magasság < 12), figyelmeztető üzenet jelenik meg.

> Tipp: indításkor a kamera 10 frame-et eldob a szenzor bemelegítéséhez (különösen sötét környezetben az első képkockák lehetnek teljesen sötétek). Ha továbbra is fekete marad a kép, ellenőrizd a macOS kameraengedélyt.

## Tesztek

```bash
pytest
```

## macOS kameraengedély

Az első futtatáskor a Terminal/iTerm2 nem feltétlenül rendelkezik kameraengedéllyel. Ha fekete képernyőt vagy "Unable to open camera" hibát kapsz:

1. Nyisd meg a macOS `System Settings` alkalmazást.
2. `Privacy & Security` → `Camera` menüben engedélyezd a használt terminál programot.
3. Indítsd újra a terminált, majd futtasd a programot újra.
