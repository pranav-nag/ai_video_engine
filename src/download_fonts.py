import os
import requests
import zipfile
import io

# Fonts to download (Direct Links)
FONT_URLS = {
    "TheBoldFont": "https://dl.dafont.com/dl/?f=the_bold_font",
    "LilitaOne": "https://fonts.google.com/download?family=Lilita%20One",
}

DEST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts"
)


def download_and_extract(name, url):
    print(f"⬇️  Downloading {name}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        r = requests.get(url, allow_redirects=True, headers=headers)
        r.raise_for_status()

        content_io = io.BytesIO(r.content)

        # Robust ZIP check
        if zipfile.is_zipfile(content_io):
            with zipfile.ZipFile(content_io) as z:
                # Extract only .ttf or .otf
                for file_info in z.infolist():
                    if file_info.filename.lower().endswith((".ttf", ".otf")):
                        # Remove path garbage, just get filename
                        filename = os.path.basename(file_info.filename)
                        if not filename:
                            continue

                        target = os.path.join(DEST_DIR, filename)
                        with open(target, "wb") as f:
                            f.write(z.read(file_info))
                        print(f"   ✅ Extracted: {filename}")
        else:
            print(f"⚠️  Not a ZIP file. Content-Type: {r.headers.get('Content-Type')}")

    except Exception as e:
        print(f"❌ Failed to download {name}: {e}")


def main():
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"SYSCALL: Created {DEST_DIR}")

    print(f"📂 Downloading fonts to: {DEST_DIR}\n")

    for name, url in FONT_URLS.items():
        download_and_extract(name, url)

    print("\n✨ Download Complete.")
    print(
        "⚠️  IMPORTANT: You must manually install these fonts (Right-Click -> Install) for them to work!"
    )

    # Open the folder
    os.startfile(DEST_DIR)


if __name__ == "__main__":
    main()
