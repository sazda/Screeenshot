# Screenshot alat

Jednostavan program za snimanje ekrana sa grafičkim interfejsom.

**Izradio:** Aleksandar Sazdanović

## Mogućnosti

- **Izbor ekrana** – ako je povezano više monitora, bira se jedan od njih ili „Svi monitori“ (spojena slika).
- **Ceo ekran ili deo ekrana** – za deo ekrana prikazuje se zamrznuta slika izabranog monitora i oblast se označava prevlačenjem miša (`Esc` ili desni klik otkazuje).
- **Formati:** PNG, JPG, JPEG, PDF.
- Kašnjenje pre snimanja (0–30 s), npr. da stignete da otvorite meni.
- Čuvanje uz dijalog „Sačuvaj kao“ ili automatski u izabrani folder.
- Meni **Pomoć → O programu**.
- Prečica `Ctrl+S` = snimi.

## Pokretanje

Potreban je Python 3.9+ (na Windows-u tkinter dolazi uz standardnu instalaciju; na Linux-u može trebati paket `python3-tk`).

```bash
pip install -r requirements.txt
```

```bash
python screenshot.py
```

## Pravljenje .exe fajla (Windows)

```bash
pip install pyinstaller
```

```bash
pyinstaller --onefile --windowed --name ScreenshotAlat screenshot.py
```

Gotov fajl se nalazi u folderu `dist/`.

## Napomene

- JPG i JPEG su isti format – razlikuje se samo ekstenzija fajla.
- PDF sadrži sliku (nije tekst koji se može pretraživati).
