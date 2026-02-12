import re
from difflib import get_close_matches


class AchievementTitleMatcher:
    def __init__(self, all_achievements):
        """
        all_achievements = list of dict from all-achievements.json
        """
        self.raw_titles = [a["Achievement"] for a in all_achievements]
        self.normalized_map = {
            self._normalize(title): title
            for title in self.raw_titles
        }

    # -----------------------------
    # Normalize text
    # -----------------------------
    def _normalize(self, text):
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # -----------------------------
    # Match OCR title
    # -----------------------------
    def match(self, ocr_title):
        if not ocr_title:
            return None

        normalized_input = self._normalize(ocr_title)

        matches = get_close_matches(
            normalized_input,
            self.normalized_map.keys(),
            n=1,
            cutoff=0.6  # Adjust sensitivity (0.6–0.8)
        )

        if matches:
            best_normalized = matches[0]
            return self.normalized_map[best_normalized]

        return None
