import cv2
import numpy as np
import mss
import pygetwindow as gw
import time


class ScreenRecorder:
    def __init__(self, output="output.mp4", fps=30):
        self.output = output
        self.fps = fps
        self.recording = False

    def start(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor

            width = monitor["width"]
            height = monitor["height"]

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(self.output, fourcc, self.fps, (width, height))

            print("Recording started... Press 'q' to stop.")
            self.recording = True

            while self.recording:
                start_time = time.time()

                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)

                # Convert BGRA → BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                out.write(frame)

                cv2.imshow("Recording", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                # Maintain FPS
                elapsed = time.time() - start_time
                time.sleep(max(0, (1 / self.fps) - elapsed))

            out.release()
            cv2.destroyAllWindows()
            print("Recording saved:", self.output)


class WindowRecorder:
    def __init__(self, window_title, output="window_record.mp4", fps=30):
        self.window_title = window_title
        self.output = output
        self.fps = fps
        self.recording = False

    def _get_window_rect(self):
        windows = gw.getWindowsWithTitle(self.window_title)

        if not windows:
            raise Exception(f"Window not found: {self.window_title}")

        window = windows[0]

        if window.isMinimized:
            raise Exception("Window is minimized. Restore it first.")

        return {
            "top": window.top,
            "left": window.left,
            "width": window.width,
            "height": window.height,
        }

    def start(self):
        monitor = self._get_window_rect()

        with mss.mss() as sct:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(
                self.output,
                fourcc,
                self.fps,
                (monitor["width"], monitor["height"])
            )

            print(f"Recording window: {self.window_title}")
            print("Press 'q' to stop.")

            self.recording = True

            while self.recording:
                start_time = time.time()

                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)

                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                out.write(frame)
                cv2.imshow("Window Recording", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                elapsed = time.time() - start_time
                time.sleep(max(0, (1 / self.fps) - elapsed))

            out.release()
            cv2.destroyAllWindows()
            print("Recording saved:", self.output)

if __name__ == "__main__":
    # recorder = WindowRecorder(
    #     window_title="Genshin Impact",
    #     output="genshin_window.mp4",
    #     fps=30
    # )
    recorder = ScreenRecorder(output="genshin_capture.mp4", fps=60)
    recorder.start()
