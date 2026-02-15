import re


class CaptionEnhancer:
    """
    Analyzes transcript words to identify 'Power Words' and assign colors/emojis.
    Dictionary-based for O(1) performance.
    """

    # BGR Colors for ASS (BBGGRR)
    COLOR_MAP = {
        "MONEY": "&H0000FFFF",  # Yellow (00FFFF) -> BGR: 00FFFF
        "DANGER": "&H000000FF",  # Red (FF0000) -> BGR: 0000FF
        "GROWTH": "&H0000FF00",  # Green (00FF00) -> BGR: 00FF00
        "TECH": "&H00FFFF00",  # Cyan (00FFFF) -> BGR: FFFF00
        "LOVE": "&H00FF00FF",  # Magenta (FF00FF) -> BGR: FF00FF
    }

    # Keyword Categories
    KEYWORDS = {
        # MONEY / SUCCESS (Yellow)
        "MONEY": "MONEY",
        "CASH": "MONEY",
        "DOLLAR": "MONEY",
        "PROFIT": "MONEY",
        "RICH": "MONEY",
        "WEALTH": "MONEY",
        "MILLION": "MONEY",
        "BILLION": "MONEY",
        "SALES": "MONEY",
        "REVENUE": "MONEY",
        "INCOME": "MONEY",
        "PAID": "MONEY",
        # DANGER / NEGATIVE (Red)
        "DIE": "DANGER",
        "KILL": "DANGER",
        "DEATH": "DANGER",
        "FAIL": "DANGER",
        "LOSE": "DANGER",
        "LOST": "DANGER",
        "BROKEN": "DANGER",
        "WRONG": "DANGER",
        "BAD": "DANGER",
        "HATE": "DANGER",
        "STOP": "DANGER",
        "WARNING": "DANGER",
        "CRAZY": "DANGER",
        "SCARY": "DANGER",
        "FEAR": "DANGER",
        "DANGEROUS": "DANGER",
        # GROWTH / POSITIVE (Green)
        "GROW": "GROWTH",
        "WIN": "GROWTH",
        "SUCCESS": "GROWTH",
        "BEST": "GROWTH",
        "GOOD": "GROWTH",
        "GREAT": "GROWTH",
        "AMAZING": "GROWTH",
        "EASY": "GROWTH",
        "FAST": "GROWTH",
        "SMART": "GROWTH",
        "GENIUS": "GROWTH",
        "SOLVE": "GROWTH",
        "GOAL": "GROWTH",
        "BUILD": "GROWTH",
        "CREATE": "GROWTH",
        # TECH / FUTURE (Cyan)
        "AI": "TECH",
        "TECH": "TECH",
        "ROBOT": "TECH",
        "FUTURE": "TECH",
        "DATA": "TECH",
        "CODE": "TECH",
        "DIGITAL": "TECH",
        "ONLINE": "TECH",
        "APP": "TECH",
        "SOFTWARE": "TECH",
        "SYSTEM": "TECH",
        "AUTOMATION": "TECH",
        # EMOTIONAL / LOVE (Magenta)
        "LOVE": "LOVE",
        "HEART": "LOVE",
        "PASSION": "LOVE",
        "HAPPY": "LOVE",
        "DREAM": "LOVE",
        "FEEL": "LOVE",
        "LIFE": "LOVE",
        "SOUL": "LOVE",
        "FRIEND": "LOVE",
        "FAMILY": "LOVE",
        "TRUST": "LOVE",
        "TRUTH": "LOVE",
    }

    EMOJI_MAP = {
        "MONEY": "💰",
        "CASH": "💵",
        "DOLLAR": "💲",
        "RICH": "🤑",
        "PRICE": "🏷️",
        "FIRE": "🔥",
        "HOT": "🥵",
        "BURN": "🎇",
        "HAPPY": "😊",
        "LAUGH": "😂",
        "FUNNY": "🤣",
        "SMILE": "😁",
        "SAD": "😢",
        "CRY": "😭",
        "PAIN": "🤕",
        "LOVE": "❤️",
        "HEART": "💖",
        "LIKE": "👍",
        "ANGRY": "😡",
        "MAD": "🤬",
        "HATE": "😤",
        "SCARY": "😱",
        "FEAR": "😨",
        "SHOCK": "🤯",
        "OMG": "🙀",
        "WOW": "🤩",
        "STOP": "🛑",
        "WAIT": "✋",
        "NO": "❌",
        "TIME": "⏰",
        "CLOCK": "🕰️",
        "NOW": "⏳",
        "GOAL": "🎯",
        "WIN": "🏆",
        "VICTORY": "✌️",
        "TOP": "🔝",
        "BRAIN": "🧠",
        "THINK": "🤔",
        "IDEA": "💡",
        "KNOW": "🎓",
        "DEAL": "🤝",
        "TEAM": "👥",
        "WORLD": "🌎",
        "GLOBAL": "🌐",
        "KING": "👑",
        "QUEEN": "👸",
        "STAR": "⭐",
        "MAGIC": "✨",
        "ROCKET": "🚀",
        "FAST": "⚡",
        "SKULL": "💀",
        "DEAD": "⚰️",
        "GHOST": "👻",
        "PHONE": "📱",
        "CALL": "📞",
        "COMPUTER": "💻",
        "AI": "🤖",
        "CAMERA": "📷",
        "VIDEO": "📹",
    }

    def enhance_word(self, word_data):
        """
        Input: {'word': 'string', 'start': float, 'end': float}
        Output: Same dict with 'color' and 'emoji' keys added if applicable.
        """
        text = word_data["word"]
        # Strip punctuation for lookup
        clean_text = re.sub(r"[^\w\s]", "", text).upper()

        if not clean_text:
            return word_data

        # 1. Color Lookup
        category = self.KEYWORDS.get(clean_text)
        if category:
            word_data["color"] = self.COLOR_MAP.get(category)

        # 2. Emoji Lookup
        emoji = self.EMOJI_MAP.get(clean_text)
        if emoji:
            word_data["emoji"] = emoji

        return word_data

    def enhance_transcript(self, words_list):
        """Process entire list of word dicts."""
        return [self.enhance_word(w) for w in words_list]
