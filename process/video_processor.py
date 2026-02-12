import cv2
import json
import os
from process.achievement_title_matcher import AchievementTitleMatcher

class AchievementVideoProcessor:
    def __init__(self, template_path, ocr, threshold=0.8, json_path="achievements.json"):
        self.template = cv2.imread(template_path, 0)
        self.template_w, self.template_h = self.template.shape[::-1]
        self.threshold = threshold
        self.ocr = ocr
        self.json_path = json_path

        # Load existing JSON if exists
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.results = json.load(f)
        else:
            self.results = []

        # Faster lookup set
        self.detected_titles = {
            item.get("title") for item in self.results if item.get("title")
        }
        
        with open("all_achievements.json", "r", encoding="utf-8") as f:
            all_achievements = json.load(f)

        self.matcher = AchievementTitleMatcher(all_achievements)

    def _detect_popup(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(gray, self.template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= self.threshold:
            x, y = max_loc

            popup_width = 1050
            popup_height = 110

            return frame[y:y+popup_height, x:x+popup_width]

        return None

    def _save_json(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=4, ensure_ascii=False)

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            popup = self._detect_popup(frame)
            if popup is None:
                continue

            # OCR extraction
            data = self.ocr.extract_from_image_array(popup)

            ocr_title = data.get("title")

            matched_title = self.matcher.match(ocr_title)

            if matched_title:
                data["title"] = matched_title
            else:
                print("Could not confidently match:", ocr_title)
                continue

            if matched_title in self.detected_titles:
                continue

            print("New achievement detected:", data)

            self.results.append(data)
            self.detected_titles.add(matched_title)

            self._save_json()

        cap.release()
        return self.results

if __name__ == "__main__":
    from process.image_processor import AchievementOCR

    ocr = AchievementOCR(debug=False)

    processor = AchievementVideoProcessor(
        template_path="template.png",
        ocr=ocr,
        json_path="achievements.json"
    )

    processor.process_video("genshin_capture.mp4")
