# 📘 README – ICC Profile Converter

Een Python tool om **TIFF-bestanden** te converteren van een bron-ICC naar een doel-ICC profiel, 
met de optie om metadata te behouden via ExifTool.

---

## 🔧 Installatie

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

## ⚙️ Configuratie van `EXIFTOOL_PATH`

In `icc_convert.py` staat bovenaan:

```python
# Pas aan indien nodig
EXIFTOOL_PATH = r"C:\Tools\exiftool-13.36_64\exiftool.exe"
```

- **Windows**: zet dit naar de juiste locatie.  
- **macOS/Linux**: laat leeg (`EXIFTOOL_PATH = ""`), dan gebruikt het script automatisch `exiftool` uit je `$PATH`.  

---

## 🚀 Gebruik

### Basissyntax
```bash
python icc_convert.py [bestanden of mappen] -s <source.icc> -t <target.icc> [opties]
```

### Voorbeelden
- Alle TIFFs in `./testdata` converteren:
  ```bash
  python icc_convert.py ./testdata -s CNN808DA.ICC -t AdobeRGB1998.icc
  ```

- Metadata behouden (volledige kopie, `ModifyDate` en `MetadataDate` bijgewerkt):
  ```bash
  python icc_convert.py ./testdata -s CNN808DA.ICC -t AdobeRGB1998.icc --preserve-metadata all
  ```

- Alleen XMP metadata kopiëren:
  ```bash
  python icc_convert.py ./testdata -s CNN808DA.ICC -t AdobeRGB1998.icc --preserve-metadata xmp
  ```

- Alle gevonden ICC-profielen tonen (inclusief extra map):
  ```bash
  python icc_convert.py --list-icc --icc-dirs ./iccprofiles
  ```

---

## 📝 CLI Opties

| Optie | Beschrijving |
|-------|--------------|
| `paths` | Bestanden en/of mappen met TIFFs. Ondersteunt mix van `.tif` en `.tiff`. |
| `-s`, `--source-icc` | Bestandsnaam van het bronprofiel (zoals gevonden met `--list-icc`). |
| `-t`, `--target-icc` | Bestandsnaam van het doelprofiel (zoals gevonden met `--list-icc`). |
| `--icc-dirs` | Extra directories om ICC-profielen in te zoeken. |
| `--list-icc` | Toon alle gevonden ICC-profielen en stop daarna. |
| `-o`, `--overwrite` | Overschrijf de originele bestanden in plaats van `_converted.tif` aan te maken. |
| `--preserve-metadata` | Kopieer metadata met ExifTool: <br>• `smart` – merge metadata (default gedrag)<br>• `all` – volledige kopie (waarden kunnen genormaliseerd worden; `ModifyDate` en `MetadataDate` worden bijgewerkt)<br>• `xmp` – alleen XMP secties |
| `-h`, `--help` | Toon help. |

---

## ✅ Workflow samengevat
1. Zoek ICC-profielen (`--list-icc`).  
2. Kies bron- en doelprofiel.  
3. Run conversie (`-s ... -t ...`).  
4. Optioneel: metadata kopiëren met `--preserve-metadata`.  
