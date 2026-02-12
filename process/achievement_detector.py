import cv2
import os


class AchievementDetector:
    def __init__(self, template_path, threshold=0.8):
        self.template = cv2.imread(template_path, 0)

        if self.template is None:
            raise ValueError(f"Could not load template image: {template_path}")

        self.template_w, self.template_h = self.template.shape[::-1]
        self.threshold = threshold

    # -------------------------------------------------
    # Detect popup from full video frame
    # -------------------------------------------------
    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(gray, self.template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= self.threshold:
            x, y = max_loc

            popup_width = 1050
            popup_height = 110

            cropped = frame[y:y + popup_height, x:x + popup_width]

            if cropped.size == 0:
                return None

            return cropped

        return None

    # -------------------------------------------------
    # Build OCR-style regions INSIDE popup
    # -------------------------------------------------
    def build_regions(self, popup):
        h, w = popup.shape[:2]

        return {
            "title": (
                int(0 * h),
                int(0.5 * h),
                int(0 * w),
                int(0.75 * w),
            ),
            "description": (
                int(0.5 * h),
                int(1 * h),
                int(0 * w),
                int(0.75 * w),
            ),
            "reward": (
                int(0 * h),
                int(1 * h),
                int(0.75 * w),
                int(0.85 * w),
            ),
            "progress": (
                int(0 * h),
                int(1 * h),
                int(0.85 * w),
                int(1 * w),
            ),
        }

    # -------------------------------------------------
    # Save overlay image FROM POPUP
    # -------------------------------------------------
    def save_region_overlay(self, popup, regions, save_path):
        debug_img = popup.copy()

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1

        for key, (y1, y2, x1, x2) in regions.items():
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            cv2.putText(
                debug_img,
                key.upper(),
                (x1, y1 - 5 if y1 - 5 > 10 else y1 + 15),
                font,
                font_scale,
                (0, 255, 0),
                thickness,
                cv2.LINE_AA
            )

        cv2.imwrite(save_path, debug_img)


# =====================================================
# Video Processing
# =====================================================

def process_video(video_path, template_path):
    detector = AchievementDetector(template_path)

    cap = cv2.VideoCapture(video_path)

    os.makedirs("detected", exist_ok=True)
    os.makedirs("debug", exist_ok=True)

    count = 0
    last_saved_frame = -100
    frame_index = 0
    cooldown_frames = 30  # prevent duplicate saves

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        popup = detector.detect(frame)

        if popup is not None:
            # Cooldown protection
            if frame_index - last_saved_frame > cooldown_frames:

                popup_path = f"detected/achievement_{count}.png"
                debug_path = f"debug/achievement_debug_{count}.png"

                # Save cropped popup
                cv2.imwrite(popup_path, popup)

                # Build and save region overlay FROM POPUP
                regions = detector.build_regions(popup)
                detector.save_region_overlay(popup, regions, debug_path)

                print(f"Saved achievement_{count}.png")

                count += 1
                last_saved_frame = frame_index

        frame_index += 1

    cap.release()
    print("Processing complete.")


if __name__ == "__main__":
    process_video("genshin_capture.mp4", "template.png")
