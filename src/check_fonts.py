from matplotlib import font_manager
import sys


def check_fonts():
    required_fonts = [
        "The Bold Font",
        "Montserrat",
        "Komika Axis",
        "Lilita One",
        "Roboto",
        "Arial Black",
        "Impact",
        "Helvetica",
    ]

    print("🔍 Scanning System Fonts...")
    system_fonts = {f.name for f in font_manager.fontManager.ttflist}

    missing = []
    found = []

    for font in required_fonts:
        if font in system_fonts:
            found.append(font)
        else:
            missing.append(font)

    print("\n✅ FOUND:")
    for f in found:
        print(f"  - {f}")

    print("\n❌ MISSING (Action Required):")
    for f in missing:
        print(f"  - {f}")

    if missing:
        sys.exit(1)


if __name__ == "__main__":
    check_fonts()
