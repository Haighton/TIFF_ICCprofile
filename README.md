# ICC Profile Converter

Een Python tool om **TIFF-bestanden** te converteren naar een doel-ICC profiel.
Het bronprofiel wordt automatisch uit de embedded metadata van de TIFF gelezen.
Bestanden zonder embedded profiel krijgen het doelprofiel direct ingebed.
Optioneel kan metadata worden behouden via ExifTool.

---

## Installatie

1. **Clone of download** dit project.
   ```bash
   git clone <repo-url>
   cd TIFF_ICCprofile
   ```

2. **Installeer dependencies** (Pillow + tqdm vereist).
   ```bash
   python -m venv .venv
   source .venv/bin/activate    # macOS/Linux
   .venv\Scripts\activate       # Windows
   pip install -r requirements.txt
   ```

3. **ExifTool installeren**
   - **macOS/Linux**: meestal via `brew install exiftool` of pakketbeheer.
   - **Windows (zonder admin-rechten)**:
     1. Download ZIP van [ExifTool website](https://exiftool.org/).
     2. Pak uit naar `C:\Tools\exiftool-13.36_64` (of vergelijkbare versie).
     3. Hernoem `exiftool(-k).exe` naar **`exiftool.exe`**.

---

## Configuratie van `EXIFTOOL_PATH`

In `icc_convert.py` staat bovenaan:

```python
# Pas aan indien nodig
if platform.system() == "Windows":
    EXIFTOOL_PATH = r"C:\Tools\exiftool-13.36_64\exiftool.exe"
else:
    EXIFTOOL_PATH = ""  # gebruik 'exiftool' uit PATH
```

---

## Gebruik

### Basissyntax
```bash
python icc_convert.py [bestanden of mappen] -t <target.icc> [opties]
```

### Voorbeelden
- Alle TIFFs in `./testdata` converteren:
  ```bash
  python icc_convert.py ./testdata -t AdobeRGB1998.icc
  ```

- Metadata behouden (volledige kopie, `ModifyDate` en `MetadataDate` bijgewerkt):
  ```bash
  python icc_convert.py ./testdata -t AdobeRGB1998.icc --preserve-metadata all
  ```

- Alleen XMP metadata kopiëren:
  ```bash
  python icc_convert.py ./testdata -t AdobeRGB1998.icc --preserve-metadata xmp
  ```

- Alle gevonden ICC-profielen tonen (inclusief extra map):
  ```bash
  python icc_convert.py --list-icc --icc-dirs ./iccprofiles
  ```

- Output in aparte map met behoud van mappenstructuur + logging naar CSV:
  ```bash
  python icc_convert.py ./testdata -t AdobeRGB1998.icc --outdir ./converted --log resultaten.csv
  ```

- Configbestand gebruiken:
  ```bash
  python icc_convert.py ./testdata --config config.yaml
  ```

---

## CLI Opties

| Optie | Beschrijving |
|-------|--------------|
| `paths` | Bestanden en/of mappen met TIFFs. Ondersteunt mix van `.tif` en `.tiff`. |
| `-t`, `--target-icc` | Bestandsnaam van het doelprofiel (zoals gevonden met `--list-icc`). |
| `--icc-dirs` | Extra directories om ICC-profielen in te zoeken. |
| `--list-icc` | Toon alle gevonden ICC-profielen en stop daarna. |
| `--overwrite` | Overschrijf de originele bestanden. |
| `--outdir` | Map waar geconverteerde bestanden worden opgeslagen (default: `./output`). De volledige mappenstructuur van de bron wordt gespiegeld. |
| `--log` | Schrijf resultaten weg in een logbestand (CSV). |
| `--preserve-metadata` | Kopieer metadata met ExifTool: <br>• `smart` – merge metadata (default gedrag)<br>• `all` – volledige kopie (waarden kunnen genormaliseerd worden; `ModifyDate`/`MetadataDate` bijgewerkt)<br>• `xmp` – alleen XMP secties |
| `--config` | YAML-configbestand met standaardwaarden. |
| `--version` | Toon de versie van de tool en stop. |
| `-h`, `--help` | Toon help. |

---

## Bronprofiel detectie

Het script leest het embedded ICC-profiel automatisch uit elke TIFF:

- **Mét embedded profiel** → kleurconversie van embedded profiel naar doelprofiel.
- **Zonder embedded profiel** → pixels ongewijzigd opgeslagen, doelprofiel direct ingebed.

Welk bronprofiel per bestand gebruikt is, wordt gelogd in de uitvoer en het CSV-logbestand.

---

## Mappenstructuur

Bij gebruik van `--outdir` wordt de volledige mappenstructuur van de bronmap gespiegeld in de outputmap:

```
./testdata/scan1/foo.tif        →  ./converted/scan1/foo.tif
./testdata/scan2/sub/bar.tiff   →  ./converted/scan2/sub/bar.tiff
```

---

## Config.yaml voorbeeld

```yaml
target_icc: AdobeRGB1998.icc
outdir: ./converted
preserve_metadata: all
```

---

## Workflow samengevat
1. Zoek ICC-profielen (`--list-icc`).
2. Kies doelprofiel (`-t`).
3. Run conversie — bronprofiel wordt automatisch per TIFF gelezen.
4. Optioneel: metadata kopiëren (`--preserve-metadata`), logging (`--log`), outputmap (`--outdir`).

---

## Dev

thomas.haighton@kb.nl voor KB Digitalisering (09-2025).
