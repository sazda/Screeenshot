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
- Na Linux-u sa Wayland sesijom snimanje ekrana preko X11 ne radi; koristite X11 sesiju.

## Windows instaler (MSI)

MSI se pravi automatski preko GitHub Actions (`.github/workflows/build-msi.yml`) na Windows računaru:

- posle svakog pull request-a i promene na `main` – MSI se preuzima na stranici **Actions**, u odeljku **Artifacts** izabranog pokretanja;
- kada se napravi tag `v*` (npr. `v1.0.0`) – MSI se objavljuje i na stranici **Releases**.

Ručno, na Windows-u:

```bash
pip install -r requirements.txt "cx_Freeze>=7.2,<8"
```

```bash
python setup.py bdist_msi
```

### Nova verzija

1. Povećajte `APP_VERSION` u `screenshot.py` (npr. `1.0.0` → `1.1.0`).
2. Napravite tag sa istim brojem (`v1.1.0`).

Instaler nove verzije sam uklanja staru. `UPGRADE_CODE` u `setup.py` se **nikada ne menja**.
