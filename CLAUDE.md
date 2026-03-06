# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

CLI-tool die TIFF-bestanden converteert naar een doel-ICC kleurprofiel. Ontwikkeld voor KB Digitalisering.

## Omgeving opzetten

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install exiftool  # macOS
```

## Veelgebruikte commando's

```bash
# Beschikbare ICC-profielen tonen (inclusief lokale map)
python icc_convert.py --list-icc --icc-dirs ./iccprofiles

# Conversie uitvoeren via config.yaml
python icc_convert.py ./testdata --config config.yaml

# Conversie met expliciete opties
python icc_convert.py ./testdata -t AdobeRGB1998.icc --outdir ./converted --preserve-metadata all --log resultaten.csv

# Originelen overschrijven (let op: onomkeerbaar)
python icc_convert.py ./testdata -t AdobeRGB1998.icc --overwrite
```

## Architectuur

Alles staat in één script: `icc_convert.py` (v2.0.0). De verwerkingspijplijn:

1. **ICC-profielen zoeken** — `build_icc_map()` zoekt op OS-specifieke ColorSync/ICM-locaties én extra mappen uit `--icc-dirs` of `config.yaml`.
2. **Bestanden verzamelen** — `find_tiff_files()` geeft `(tiff_file, base_dir)` tuples terug. `base_dir` is de opgegeven invoermap en wordt gebruikt om de mappenstructuur te spiegelen in de outputmap.
3. **Parallelle conversie** — `convert_icc()` verdeelt het werk via `ProcessPoolExecutor`.
4. **Per bestand** — `process_file()` heeft twee paden:
   - *Mét embedded ICC-profiel*: kleurconversie via `ImageCms.buildTransform` + `applyTransform`, output met doelprofiel ingebed.
   - *Zonder embedded profiel*: pixels ongewijzigd, doelprofiel ingebed via ExifTool (`-icc_profile<=`). Fallback naar Pillow re-save als ExifTool ontbreekt.
5. **Metadata** — `preserve_metadata()` roept ExifTool aan na de conversie (`smart` / `all` / `xmp`).

## Configuratie

`config.yaml` biedt standaardwaarden voor `target_icc`, `outdir`, `preserve_metadata`, `icc_dirs` en `log`. CLI-argumenten hebben altijd voorrang.

## ExifTool

ExifTool is een externe dependency (geen pip-package). Op Windows: pas `EXIFTOOL_PATH` bovenin `icc_convert.py` aan naar het juiste pad. Op macOS/Linux wordt `exiftool` uit `PATH` gebruikt.
