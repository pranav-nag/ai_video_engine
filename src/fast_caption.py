class SubtitleGenerator:
    STYLES = {
        "Hormozi": {
            "Fontname": "The Bold Font",
            "PrimaryColour": "&H00FFFFFF",  # White
            "HighlightColour": "&H0000FFFF",  # Yellow
            "OutlineColour": "&H00000000",  # Black
            "BackColour": "&H80000000",
            "BorderStyle": 1,
            "Outline": 3,
            "Shadow": 0,
            "Alignment": 5,
            "MarginV": 250,
        },
        "Minimal": {
            "Fontname": "Montserrat",
            "PrimaryColour": "&H00FFFFFF",  # White
            "HighlightColour": "&H00CCCCCC",  # Light Grey
            "OutlineColour": "&H00000000",
            "BackColour": "&H60000000",
            "BorderStyle": 1,
            "Outline": 1,
            "Shadow": 0,
            "Alignment": 2,
            "MarginV": 50,
        },
        "Neon": {
            "Fontname": "Arial Black",
            "PrimaryColour": "&H00FFFFFF",  # White
            "HighlightColour": "&H00FFFF00",  # Cyan
            "OutlineColour": "&H00FF0080",  # Purple Glow
            "BackColour": "&H00000000",
            "BorderStyle": 1,
            "Outline": 2,
            "Shadow": 2,
            "Alignment": 5,
            "MarginV": 250,
        },
        "Boxed": {
            "Fontname": "Arial",
            "PrimaryColour": "&H00000000",  # Black Text
            "HighlightColour": "&H000000FF",  # Red Text
            "OutlineColour": "&H00FFFFFF",  # White Box (Outline)
            "BackColour": "&H80FFFFFF",  # White Box Background
            "BorderStyle": 3,  # Opaque Box
            "Outline": 0,
            "Shadow": 0,
            "Alignment": 2,
            "MarginV": 50,
        },
        "Beast": {
            "Fontname": "Komika Axis",
            "PrimaryColour": "&H00FFFFFF",  # White
            "HighlightColour": "&H000000FF",  # Red
            "OutlineColour": "&H00000000",  # Black
            "BackColour": "&H40000000",
            "BorderStyle": 1,
            "Outline": 5,
            "Shadow": 2,
            "Alignment": 5,
            "MarginV": 300,
        },
        "Gaming": {
            "Fontname": "Lilita One",
            "PrimaryColour": "&H0000FF00",  # Green
            "HighlightColour": "&H00FFFFFF",  # White
            "OutlineColour": "&H00000000",  # Black
            "BackColour": "&H80000000",
            "BorderStyle": 1,
            "Outline": 4,
            "Shadow": 0,
            "Alignment": 5,
            "MarginV": 200,
        },
        "Bold Shadow": {
            "Fontname": "Impact",
            "PrimaryColour": "&H00FFFFFF",
            "HighlightColour": "&H0000FFFF",  # Yellow
            "OutlineColour": "&H00000000",
            "BackColour": "&H80000000",
            "BorderStyle": 1,
            "Outline": 0,
            "Shadow": 4,  # Heavy Shadow
            "Alignment": 5,
            "MarginV": 250,
        },
        "Outline Glow": {
            "Fontname": "The Bold Font",
            "PrimaryColour": "&H00FFFFFF",
            "HighlightColour": "&H00FFFF00",  # Cyan Glow
            "OutlineColour": "&H00FF00FF",  # Purple Outline
            "BackColour": "&H80000000",
            "BorderStyle": 1,
            "Outline": 2,
            "Shadow": 0,
            "Alignment": 5,
            "MarginV": 250,
        },
        "Gradient Vibrant": {
            "Fontname": "Arial Black",
            "PrimaryColour": "&H0000FFFF",  # Yellow (Start)
            "HighlightColour": "&H00FF00FF",  # Magenta (Active)
            "OutlineColour": "&H00FFFFFF",  # White Outline
            "BackColour": "&H80000000",
            "BorderStyle": 1,
            "Outline": 2,
            "Shadow": 0,
            "Alignment": 5,
            "MarginV": 250,
        },
        "Glass Morphism": {
            "Fontname": "Roboto",
            "PrimaryColour": "&H00FFFFFF",
            "HighlightColour": "&H0000FFFF",
            "OutlineColour": "&H40000000",  # Semi-transparent outline
            "BackColour": "&H60000000",  # Semi-transparent box (Alpha 60)
            "BorderStyle": 3,  # Box
            "Outline": 0,
            "Shadow": 0,
            "Alignment": 5,
            "MarginV": 250,
        },
        "Minimal Elegant": {
            "Fontname": "Helvetica",
            "PrimaryColour": "&H00DDDDDD",  # Light Grey
            "HighlightColour": "&H00FFFFFF",  # White
            "OutlineColour": "&H00000000",
            "BackColour": "&H00000000",
            "BorderStyle": 1,
            "Outline": 0,
            "Shadow": 0,
            "Alignment": 5,
            "MarginV": 250,
        },
    }

    def __init__(
        self,
        style_name="Hormozi",
        font_size=60,
        position="center",
        custom_config=None,  # NEW: Allow full custom override
    ):
        # 1. Select Base Style
        base_style = self.STYLES.get(style_name, self.STYLES["Hormozi"])
        self.style_config = base_style.copy()

        self.font_size = font_size

        # 2. Apply Custom Overrides
        if custom_config:
            self.style_config.update(custom_config)

        # Override position if needed
        if position == "top":
            self.style_config = self.style_config.copy()
            self.style_config["Alignment"] = 8
            self.style_config["MarginV"] = 50
        elif position == "bottom":
            self.style_config = self.style_config.copy()
            self.style_config["Alignment"] = 2
            self.style_config["MarginV"] = 50
        # If center, use default from style or 5

        self.play_res_x = 1080
        self.play_res_y = 1920

    def generate_header(self):
        s = self.style_config
        # Note: ASS Header uses PrimaryColour as the default text color
        return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {self.play_res_x}
PlayResY: {self.play_res_y}
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{s["Fontname"]},{self.font_size},{s["PrimaryColour"]},&H000000FF,{s["OutlineColour"]},{s["BackColour"]},-1,0,0,0,100,100,0,0,{s["BorderStyle"]},{s["Outline"]},{s["Shadow"]},{s["Alignment"]},10,10,{s["MarginV"]},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def time_to_ass(self, seconds):
        """Convert float seconds to ASS timecode format: H:MM:SS.CC"""
        if seconds < 0:
            seconds = 0
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int(round((seconds % 1) * 100))
        if cs >= 100:
            cs = 99
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    def generate_karaoke_line(self, word_list, line_start, line_end):
        """
        Generates word-by-word karaoke events with gap-free timing.
        Each word displays from slightly before it's spoken until the next word begins.
        word_list: list of dicts {'word': str, 'start': float, 'end': float}
        """
        events = []
        if not word_list:
            return events

        # Extract highlight color from config (default to yellow if missing)
        hl_color = self.style_config.get("HighlightColour", "&H0000FFFF")

        for i, w in enumerate(word_list):
            word_text = w["word"].upper()
            w_start = w["start"]

            # --- GAP-FREE TIMING ---
            # Each word stays on screen until the next word starts.
            # This eliminates blank frames between words.
            if i + 1 < len(word_list):
                w_end = word_list[i + 1]["start"]
            else:
                # Last word: use its own end + 200ms buffer
                w_end = w["end"] + 0.2

            # Pre-display buffer: show word 50ms early so it's already
            # visible the instant the speaker begins
            display_start = max(0, w_start - 0.05)

            start_tc = self.time_to_ass(display_start)
            end_tc = self.time_to_ass(w_end)

            # Pop animation: scale up 115% in 100ms + Color override
            # \c&H...& sets the fill color to HighlightColour
            # \3c&H...& sets the outline color (Glow)
            hl_outline = self.style_config.get("OutlineColour", "&H00000000")

            anim_tags = rf"{{\c{hl_color}\3c{hl_outline}\fad(50,50)\t(0,100,\fscx115\fscy115)\t(100,200,\fscx100\fscy100)}}"

            # NOTE: Emoji injection disabled — libass cannot render colored
            # Unicode emoji via standard fonts.
            final_text = f"{anim_tags}{word_text}"

            events.append(
                f"Dialogue: 0,{start_tc},{end_tc},Default,,0,0,0,,{final_text}"
            )

        return events

    def get_emoji(self, word):
        EMOJI_MAPPING = {
            "MONEY": "💰",
            "CASH": "💵",
            "DOLLAR": "💲",
            "RICH": "🤑",
            "FIRE": "🔥",
            "HOT": "🥵",
            "BURN": "🎇",
            "HAPPY": "😊",
            "LAUGH": "😂",
            "FUNNY": "🤣",
            "SMILE": "😁",
            "SAD": "😢",
            "CRY": "😭",
            "LOVE": "❤️",
            "HEART": "💖",
            "LIKE": "👍",
            "ANGRY": "😡",
            "MAD": "🤬",
            "SCARY": "😱",
            "FEAR": "😨",
            "SHOCK": "😱",
            "OMG": "🙀",
            "WOW": "🤯",
            "STOP": "🛑",
            "WAIT": "✋",
            "TIME": "⏰",
            "CLOCK": "🕰️",
            "GOAL": "🎯",
            "KICK": "🦶",
            "WIN": "🏆",
            "VICTORY": "✌️",
            "BRAIN": "🧠",
            "THINK": "🤔",
            "IDEA": "💡",
            "DEAL": "🤝",
            "WORLD": "🌎",
            "KING": "👑",
            "QUEEN": "👸",
            "STAR": "⭐",
            "ROCKET": "🚀",
            "SKULL": "💀",
            "DEAD": "⚰️",
        }
        clean = word.strip(",.!?").upper()
        return EMOJI_MAPPING.get(clean)

    def generate_ass_file(self, words, output_path):
        header = self.generate_header()
        events = self.generate_karaoke_line(words, 0, 0)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            for e in events:
                f.write(e + "\n")
