import os
import cv2
from paddleocr import PaddleOCR
import numpy as np


class AchievementOCR:

    def __init__(self, lang="en", debug=False):
        self.debug = debug

        self.ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang=lang
        )

    # -----------------------------
    # Build regions dynamically
    # -----------------------------
    def _build_regions(self, img):
        h, w = img.shape[:2]

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
                int(0.80 * w),
                int(1 * w),
            ),
        }

    def _crop_region(self, image, region):
        y1, y2, x1, x2 = region
        return image[y1:y2, x1:x2]

    def _preprocess(self, image):
        if image is None or image.size == 0:
            return None

        h, _ = image.shape[:2]

        # Only upscale small regions
        if h < 80:
            image = cv2.resize(image, None, fx=2, fy=2)

        return image

    def _extract_text(self, image):
        if image is None:
            return ""

        results = self.ocr.predict(image)

        return " ".join(results[0]['rec_texts'])

    def _save_region_overlay(self, image, regions):
        """
        Draw rectangles around all regions on original image
        """
        debug_img = image.copy()

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1

        for key, (y1, y2, x1, x2) in regions.items():
            # Draw rectangle
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw label
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

        os.makedirs("debug", exist_ok=True)
        cv2.imwrite("debug/regions_overlay.png", debug_img)

    # -----------------------------
    # Main function
    # -----------------------------
    def extract_from_image(self, image_path):
        img = cv2.imread(image_path)

        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        regions = self._build_regions(img)
        data = {}

        # Create debug folder
        if self.debug:
            os.makedirs("debug", exist_ok=True)

        for key, region in regions.items():
            cropped = self._crop_region(img, region)
            processed = self._preprocess(cropped)
            text = self._extract_text(processed)
            data[key] = text

        if self.debug:
            self._save_region_overlay(img, regions)

        return data

    def extract_from_image_array(self, img, debug_name=None):
        regions = self._build_regions(img)
        data = {}

        for key, region in regions.items():
            cropped = self._crop_region(img, region)
            processed = self._preprocess(cropped)
            text = self._extract_text(processed)
            data[key] = text

        # Save debug overlay FROM POPUP
        if self.debug and debug_name is not None:
            os.makedirs("debug", exist_ok=True)
            debug_path = f"debug/{debug_name}.png"
            self._save_region_overlay(img, regions)
            cv2.imwrite(debug_path, img)

        return data



if __name__ == "__main__":
    ocr = AchievementOCR(debug=True)

    result = ocr.extract_from_image("Screenshot 2026-02-12 033015.png")
    print(result)
