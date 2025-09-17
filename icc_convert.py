import argparse
import platform
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageCms
from tqdm import tqdm

# 🔧 Pad naar ExifTool afhankelijk van OS
if platform.system() == "Windows":
    EXIFTOOL_PATH = r"C:\Tools\exiftool-13.36_64\exiftool.exe"
else:
    EXIFTOOL_PATH = ""  # leeg = gebruik 'exiftool' uit PATH


def get_default_icc_dirs():
    """Geef standaard ICC-directories terug afhankelijk van OS."""
    system = platform.system()
    if system == "Darwin":  # macOS
        return [
            Path("/System/Library/ColorSync/Profiles"),
            Path("/Library/ColorSync/Profiles"),
            Path.home() / "Library/ColorSync/Profiles",
        ]
    elif system == "Windows":
        return [Path("C:/Windows/System32/spool/drivers/color")]
    else:  # Linux/unix
        return [
            Path("/usr/share/color/icc"),
            Path("/usr/local/share/color/icc"),
            Path.home() / ".color/icc",
        ]


def build_icc_map(extra_dirs=None):
    """Zoek ICC-profielen in standaard + extra directories en maak een map {bestandsnaam: pad}."""
    icc_map = {}
    search_dirs = get_default_icc_dirs()
    if extra_dirs:
        search_dirs.extend([Path(d) for d in extra_dirs])

    for d in search_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.is_file() and f.suffix.lower() in [".icc", ".icm"]:
                icc_map[f.name] = f
    return icc_map


def find_tiff_files(paths):
    """Geef alle TIFF-bestanden uit een mix van bestanden en mappen terug."""
    files = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"⚠️ Pad bestaat niet: {path}")
            continue
        if path.is_dir():
            files.extend(path.rglob("*.tif"))
            files.extend(path.rglob("*.tiff"))
        elif path.is_file() and path.suffix.lower() in [".tif", ".tiff"]:
            files.append(path)
    return files


def exiftool_available():
    """Geef pad naar ExifTool (via global of PATH), of None als niet gevonden."""
    if EXIFTOOL_PATH and Path(EXIFTOOL_PATH).exists():
        return EXIFTOOL_PATH
    found = shutil.which("exiftool")
    if found:
        return found
    return None


def preserve_metadata(src, dst, mode="smart"):
    """Kopieer metadata met ExifTool in de gekozen mode."""
    exiftool = exiftool_available()
    if not exiftool:
        tqdm.write(
            "⚠️ ExifTool niet gevonden. Installeer ExifTool of pas EXIFTOOL_PATH aan.")
        return

    try:
        if mode == "all":
            tqdm.write("ℹ️ Let op: metadata wordt volledig gekopieerd, "
                       "maar sommige waarden kunnen door ExifTool genormaliseerd worden.")

            # 1. kopieer alle metadata
            cmd1 = [exiftool, "-TagsFromFile",
                    str(src), "-all:all", "-overwrite_original", str(dst)]
            subprocess.run(cmd1, check=True, capture_output=True)

            # 2. update alleen ModifyDate en MetadataDate naar nu
            cmd2 = [exiftool, "-overwrite_original",
                    "-ModifyDate=now", "-MetadataDate=now", str(dst)]
            subprocess.run(cmd2, check=True, capture_output=True)

        elif mode == "xmp":
            cmd = [exiftool, "-TagsFromFile",
                   str(src), "-xmp", "-overwrite_original", str(dst)]
            subprocess.run(cmd, check=True, capture_output=True)

        else:  # smart
            cmd = [exiftool, "-TagsFromFile",
                   str(src), "-overwrite_original", str(dst)]
            subprocess.run(cmd, check=True, capture_output=True)

    except subprocess.CalledProcessError as e:
        tqdm.write(f"❌ Fout bij ExifTool: {e.stderr.decode().strip()}")


def process_file(tiff_file, source_icc, target_icc, overwrite, preserve):
    """Verwerk één bestand: ICC conversie + optioneel metadata preservatie."""
    try:
        with Image.open(tiff_file) as im:
            transform = ImageCms.buildTransform(
                str(source_icc), str(target_icc), "RGB", "RGB")
            im_converted = ImageCms.applyTransform(im, transform)
            out_path = tiff_file if overwrite else tiff_file.with_name(
                tiff_file.stem + "_converted.tif"
            )
            with open(target_icc, "rb") as f:
                target_profile = f.read()
            im_converted.save(out_path, format="TIFF",
                              icc_profile=target_profile)

            if preserve and out_path != tiff_file:
                preserve_metadata(tiff_file, out_path, preserve)

        return (tiff_file, True, None)
    except Exception as e:
        return (tiff_file, False, str(e))


def convert_icc(tiff_files, source_icc, target_icc, overwrite=False, preserve=None):
    """Converteer TIFFs parallel met multiprocessing + progressbar."""
    results = []
    with ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(process_file, t, source_icc, target_icc, overwrite, preserve): t
            for t in tiff_files
        }

        with tqdm(as_completed(futures), total=len(futures), desc="Converting", unit="file") as pbar:
            for f in pbar:
                tiff_file, ok, err = f.result()
                if ok:
                    tqdm.write(f"✅ {tiff_file}")
                else:
                    tqdm.write(f"❌ {tiff_file}: {err}")
                results.append((tiff_file, ok, err))

    # Samenvatting
    success = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"\n✔ Klaar: {success} succesvol, {failed} mislukt")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Converteer TIFF bestanden van een bron-ICC naar een doel-ICC (optioneel metadata behouden)."
    )
    parser.add_argument("paths", nargs="*",
                        help="Pad(en) naar TIFF bestand(en) of map(pen).")
    parser.add_argument("-s", "--source-icc",
                        help="Bestandsnaam van bron ICC-profiel (bijv. CNN8083DA.ICC).")
    parser.add_argument("-t", "--target-icc",
                        help="Bestandsnaam van doel ICC-profiel (bijv. AdobeRGB1998.icc).")
    parser.add_argument("--icc-dirs", nargs="*", default=[],
                        help="Extra directories om ICC-profielen in te zoeken.")
    parser.add_argument("--list-icc", action="store_true",
                        help="Toon alle gevonden ICC-profielen en stop daarna.")
    parser.add_argument("-o", "--overwrite", action="store_true",
                        help="Overschrijf originele bestanden (anders wordt '_converted.tif' aangemaakt).")
    parser.add_argument(
        "--preserve-metadata",
        choices=["smart", "all", "xmp"],
        help=(
            "Kopieer metadata met ExifTool:\n"
            "  smart – merge metadata (default gedrag)\n"
            "  all   – volledige kopie (waarden kunnen genormaliseerd worden; "
            "ModifyDate/MetadataDate worden bijgewerkt)\n"
            "  xmp   – alleen XMP-secties"
        ),
    )

    args = parser.parse_args()

    # Bouw ICC-map
    icc_map = build_icc_map(args.icc_dirs)

    # Alleen lijst tonen
    if args.list_icc:
        if not icc_map:
            print("⚠️ Geen ICC-profielen gevonden.")
        else:
            print("📂 Beschikbare ICC-profielen:")
            for name, path in sorted(icc_map.items(), key=lambda x: x[0].lower()):
                print(f"  {name:<40} {path}")
        return

    # Normale workflow
    if not args.source_icc or not args.target_icc:
        parser.error(
            "Je moet zowel --source-icc als --target-icc opgeven (tenzij je --list-icc gebruikt).")

    if args.source_icc not in icc_map:
        print(f"❌ Bronprofiel '{args.source_icc}' niet gevonden.")
        print(f"Beschikbare profielen: {', '.join(sorted(icc_map.keys()))}")
        return
    if args.target_icc not in icc_map:
        print(f"❌ Doelprofiel '{args.target_icc}' niet gevonden.")
        print(f"Beschikbare profielen: {', '.join(sorted(icc_map.keys()))}")
        return

    # Controleer ExifTool
    if args.preserve_metadata and not exiftool_available():
        print("⚠️ Optie --preserve-metadata genegeerd: ExifTool is niet gevonden.")
        args.preserve_metadata = None

    source_icc = icc_map[args.source_icc]
    target_icc = icc_map[args.target_icc]

    # Verzamel TIFFs
    tiff_files = find_tiff_files(args.paths)
    if not tiff_files:
        print("⚠️ Geen TIFF-bestanden gevonden.")
        return

    convert_icc(tiff_files, source_icc, target_icc,
                args.overwrite, args.preserve_metadata)


if __name__ == "__main__":
    main()
