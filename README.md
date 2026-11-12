# Screenshot

Jednostavan program za snimanje ekrana sa grafičkim interfejsom.

**Izradio:** Aleksandar Sazdanović

## Mogućnosti

- **Ceo ekran na klik** – posle izbora „Ceo ekran“ preko svakog monitora se pojavi poluprovidan sloj; levim klikom birate monitor i tek tada se on snima (Esc ili desni klik otkazuje). Kašnjenje se računa od klika.
- **Više monitora** – „Deo ekrana“ prikazuje sve monitore, pa se oblast može označiti na bilo kom (i preko granice dva monitora).
- **Ceo ekran ili deo ekrana** – posle klika na „Snimi ekran“ otvara se prozorčić sa izborom (tasteri `1` / `2`, `Esc` otkazuje; program pamti poslednji izbor). Za deo ekrana prikazuje se zamrznuta slika ekrana i oblast se označava prevlačenjem miša (`Esc` ili desni klik otkazuje).
- **Formati:** PNG, JPG, JPEG, PDF.
- Kašnjenje pre snimanja (0–30 s), npr. da stignete da otvorite meni.
- Čuvanje uz dijalog „Sačuvaj kao“ ili automatski u izabrani folder.
- **Otvaranje snimka** – opcija „Otvori snimak posle čuvanja“ (uključena podrazumevano) otvara sačuvani fajl u programu koji je u sistemu podrazumevan za taj format.
- Meni **Pomoć → O programu**.
- Prečica `Ctrl+S` = snimi.

## Ikonica

Ikonica se nalazi u `assets/icon.ico` (Windows: program, prečica, instaler) i `assets/icon.png` (prozor programa).
Za svoju ikonicu zamenite ova dva fajla (ista imena; `.ico` treba da sadrži više veličina, bar 16–256 px).
Postojeća ikonica se ponovo pravi komandom `python tools/make_icon.py`.

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
pyinstaller --onefile --windowed --name Screenshot screenshot.py
```

Gotov fajl se nalazi u folderu `dist/`.

## Napomene

- JPG i JPEG su isti format – razlikuje se samo ekstenzija fajla.
- PDF sadrži sliku (nije tekst koji se može pretraživati).

## Windows instaler (MSI)

MSI se pravi automatski preko GitHub Actions (`.github/workflows/build-msi.yml`) na Windows računaru:

- posle svakog pull request-a i promene na `main` – MSI se preuzima na stranici **Actions**, u odeljku **Artifacts** izabranog pokretanja;
- kada se napravi tag `v*` (npr. `v1.0.0`) – MSI se objavljuje i na stranici **Releases**.

Ručno, na Windows-u (Python 3.10–3.14; na 3.13+ se automatski instalira i `python-msilib`):

```bash
pip install -r requirements-build.txt
```

```bash
python setup.py bdist_msi
```

### Nova verzija

1. Povećajte `APP_VERSION` u `screenshot.py` (npr. `1.0.0` → `1.1.0`).
2. Napravite tag sa istim brojem (`v1.1.0`).

Instaler pravi prečice u Start meniju i na radnoj površini. Instaler nove verzije sam uklanja staru. `UPGRADE_CODE` u `setup.py` se **nikada ne menja**.
