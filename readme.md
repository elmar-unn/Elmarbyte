# Elmarbyte

Elmarbyte on töölauarakendus mängude kogu haldamiseks ja käivitamiseks.  
Rakendus võimaldab lisada mänge oma librarysse, salvestada nende kohta infot, lisada cover-pilte ning käivitada mänge otse rakendusest.

Projekt on tehtud kooli andmebaasiprojektina, kus keskmes on **SQLite andmebaas** ning selle ühendamine **visuaalse kasutajaliidesega**.

---

## Funktsionaalsus

Elmarbyte võimaldab:

- lisada uusi mänge andmebaasi
- muuta olemasolevate mängude andmeid
- kustutada mänge
- otsida mänge nime, platvormi ja žanri järgi
- filtreerida mänge:
  - platvormi järgi
  - žanri järgi
  - staatuse järgi
  - favoriitide järgi
- vaadata mänge:
  - **list view**
  - **grid view**
- lisada mängule:
  - pealkirja
  - platvormi
  - žanri
  - hinnangu
  - staatuse
  - favorite märgi
  - cover-pildi
  - launcher pathi / URI
  - märkmed
- kuvada valitud mängu detailvaadet
- käivitada mänge otse rakendusest

### Toetatud käivitamise viisid

Rakendus toetab erinevaid launcher-tüüpe:

- **local_file**  
  Tavaline `.exe`, `.bat` või `.lnk` fail

- **steam_shortcut**  
  Steam internet shortcut (`.url`) või shortcut fail

- **steam_uri**  
  Näiteks:
  `steam://rungameid/APPID`

- **epic_uri**  
  Näiteks:
  `com.epicgames.launcher://apps/...`

### Importimise funktsioonid

Rakenduses on olemas ka automaatne import:

- **Import Steam**
  - otsib Steam `.url` shortcut'e
  - impordib need automaatselt librarysse

- **Import Epic**
  - loeb Epic Games installide infot failist `LauncherInstalled.dat`
  - lisab Epic mängud librarysse

---

## Tech

Projekt kasutab järgmisi tehnoloogiaid:

### Programmeerimiskeel
- **Python 3**

### GUI
- **Tkinter**
- **ttk**

### Andmebaas
- **SQLite**

### Pilditugi
- **Pillow**
  - kasutatakse cover-piltide laadimiseks ja kuvamiseks

### Muud Python moodulid
- `sqlite3`
- `json`
- `os`
- `shutil`
- `webbrowser`
- `pathlib`
- `configparser`

---

## Andmebaasi struktuur

Rakenduse keskmes on tabel **games**.

### Tabel: `games`

| Väli | Tüüp | Kirjeldus |
|---|---|---|
| id | INTEGER | Primaarvõti |
| title | TEXT | Mängu nimi |
| platform | TEXT | Platvorm |
| genre | TEXT | Žanr |
| rating | INTEGER | Hinnang 0–10 |
| status | TEXT | Staatuse väli |
| favorite | INTEGER | Kas mäng on favoriit |
| cover_path | TEXT | Cover-pildi failitee |
| launcher_type | TEXT | Launcheri tüüp |
| launcher_path | TEXT | EXE, shortcut või URI |
| notes | TEXT | Märkmed |

---

## How to run

### 1. Paigalda Python
Veendu, et sul on arvutis olemas **Python 3** ja pillow, kui ei ole pip install pillow.

Kontroll:
```bash

python --version
