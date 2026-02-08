import cv2
import os

# DO NOT CHANGE THIS ORDER
import mediapipe as mp

# Access solutions through the main module to avoid direct sub-module import issues
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils


class SmartCropper:
    def __init__(self):
        # We use the explicitly imported sub-module here
        self.face_detection = mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )

    def get_face_center(self, image):
        """
        Returns the X coordinate (0.0 to 1.0) of the primary face.
        """
        try:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(image_rgb)

            if results.detections:
                # Get the first face detected
                detection = results.detections[0]
                bbox = detection.location_data.relative_bounding_box

                # Calculate center X (0.0 to 1.0)
                center_x = bbox.xmin + (bbox.width / 2)
                return center_x
        except Exception as e:
            print(f"⚠️ Face Detection Error: {e}")

        return None

    def analyze_video(self, video_path, progress_callback=None):
        """
        Analyzes the video to determine the crop coordinates for 9:16 aspect ratio.
        Uses multi-threading to speed up face detection.
        """
        import concurrent.futures

        if not os.path.exists(video_path):
            print(f"❌ Error: Video not found at {video_path}")
            return {}, 1, 1

        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        print(f"📐 Dimensions: {width}x{height} | Frames: {total_frames} | FPS: {fps}")

        target_width = int(height * (9 / 16))
        if target_width > width:
            target_width = width

        # Config
        stride = 2  # Process every 2nd frame
        # Use more threads for the Ryzen 7 (8 cores / 16 threads)
        max_workers = 12

        frame_mapping = {}

        # We'll batch process frames to utilitze CPU better
        batch_size = 64

        def process_batch(frames_data):
            results = []
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                # MediaPipe can be picky with many threads sharing one instance
                # but for simple FaceDetection it usually works if we don't recreate it.
                # However, for MAX performance, we might need a pool of detectors.
                # Let's try regular first.
                future_to_idx = {
                    executor.submit(self.get_face_center, f): idx
                    for f, idx in frames_data
                }
                for future in concurrent.futures.as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        res = future.result()
                        results.append((idx, res))
                    except Exception as e:
                        print(f"Error processing frame {idx}: {e}")
            return results

        print(f"🚀 Analyzing with {max_workers} threads...")

        frame_idx = 0
        all_results = []

        while cap.isOpened():
            batch_frames = []
            for _ in range(batch_size):
                ret, frame = cap.read()
                if not ret:
                    break

                # Only add if it's a stride frame
                if frame_idx % stride == 0:
                    batch_frames.append((frame.copy(), frame_idx))

                frame_idx += 1

            if not batch_frames:
                break

            # Process batch
            batch_results = process_batch(batch_frames)
            all_results.extend(batch_results)

            # Progress reporting
            if progress_callback:
                progress = min(1.0, frame_idx / total_frames)
                progress_callback(progress)
            else:
                print(f"   Progress: {frame_idx}/{total_frames} frames...", end="\r")

        cap.release()

        # Sort results by index
        all_results.sort(key=lambda x: x[0])

        # State-based smoothing (Hysteresis)
        alpha = 0.1
        hysteresis_threshold = 0.10
        current_x = width / 2
        smoothed_x = current_x
        last_stable_x = current_x

        # Map processed results back to coordinates
        processed_indices = [r[0] for r in all_results]
        processed_centers = [r[1] for r in all_results]

        for idx, face_rel_x in zip(processed_indices, processed_centers):
            if face_rel_x is not None:
                target_center_x = face_rel_x * width
            else:
                target_center_x = width / 2

            smoothed_x = (alpha * target_center_x) + ((1 - alpha) * smoothed_x)

            diff = abs(smoothed_x - last_stable_x)
            if diff > (width * hysteresis_threshold):
                last_stable_x = smoothed_x

            crop_x = int(last_stable_x - (target_width / 2))
            crop_x = max(0, min(crop_x, width - target_width))
            frame_mapping[idx] = crop_x

        # Interpolate missing frames
        for i in range(total_frames):
            if i not in frame_mapping:
                # Find nearest neighbor for simplicity, or interpolate
                # Let's find neighbors
                prev_idx = max([idx for idx in frame_mapping.keys() if idx < i] or [0])
                next_idx = min(
                    [idx for idx in frame_mapping.keys() if idx > i]
                    or [total_frames - 1]
                )

                if prev_idx == next_idx:
                    frame_mapping[i] = frame_mapping.get(prev_idx, 0)
                else:
                    t = (i - prev_idx) / (next_idx - prev_idx)
                    p_val = frame_mapping[prev_idx]
                    n_val = frame_mapping[next_idx]
                    frame_mapping[i] = int(p_val + t * (n_val - p_val))

        print(
            f"\n✅ Crop Analysis Complete. Generated {len(frame_mapping)} coordinates."
        )
        return frame_mapping, target_width, height


# --- Test Block ---
if __name__ == "__main__":
    # Create a dummy test if specific video not present,
    # or point to a known video for testing.
    # Note: Requires a real video file to work properly.

    # Check if a test file exists in temp, otherwise ask user
    test_video = r"E:\AI_Video_Engine\temp\input_video.mp4"  # Default from processor.py

    if os.path.exists(test_video):
        cropper = SmartCropper()
        crop_data, w, h = cropper.analyze_video(test_video)

        print(f"Sample Frame 0 Crop X: {crop_data.get(0)}")
        print(f"Sample Frame 100 Crop X: {crop_data.get(100)}")
    else:
        print(f"ℹ️ No test video found at {test_video}.")
        print("   Run 'python src/processor.py' first to download a video.")
