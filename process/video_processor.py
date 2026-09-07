import cv2
import json
import os
from typing import Callable, Optional
from process.achievement_title_matcher import AchievementTitleMatcher

class AchievementVideoProcessor:
    def __init__(self, template_path, ocr, threshold=0.8,
                 json_path="achievements.json", catalogue_path="all_achievements.json"):
        self.template = cv2.imread(template_path, 0)
        if self.template is None:
            raise ValueError(f"Could not load template: {template_path}")
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
        
        with open(catalogue_path, "r", encoding="utf-8") as f:
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

    def process_video(self, video_path, progress_callback: Optional[Callable[[str, Optional[float]], None]] = None):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_number = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_number += 1

            if progress_callback and (frame_number == 1 or frame_number % 25 == 0):
                progress = (frame_number / total_frames * 100) if total_frames else None
                progress_callback(f"Processing video frame {frame_number}…", progress)

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
        if progress_callback:
            progress_callback("Video processing finished.", 100.0)
        return self.results


def process_video_file(
    video_path,
    *,
    template_path="template.png",
    json_path="achievements.json",
    catalogue_path="all_achievements.json",
    progress_callback=None,
):
    """Create the OCR processor and process one video file."""
    from process.image_processor import AchievementOCR

    if progress_callback:
        progress_callback("Loading OCR engine…", None)
    ocr = AchievementOCR(debug=False)
    processor = AchievementVideoProcessor(
        template_path=template_path,
        ocr=ocr,
        json_path=json_path,
        catalogue_path=catalogue_path,
    )
    return processor.process_video(video_path, progress_callback=progress_callback)

if __name__ == "__main__":
    from process.text_processor import update_catalogue

    update_catalogue()
    process_video_file("genshin_capture.mp4")
