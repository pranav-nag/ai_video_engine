import cv2
import os

# DO NOT CHANGE THIS ORDER
# Suppress MediaPipe/TensorFlow C++ warnings (0 = all, 1 = info, 2 = warning, 3 = error)
os.environ["GLOG_minloglevel"] = "2"

import mediapipe as mp

# Access solutions through the main module to avoid direct sub-module import issues
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils


class SmartCropper:
    def __init__(self):
        # We use the explicitly imported sub-module here
        self.face_detection = mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.65
        )

    def get_face_center(self, image, prior_x=None, focus_region="auto"):
        """
        Returns the X coordinate (0.0 to 1.0) of the best face based on focus_region.
        """
        try:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            with mp_face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.6
            ) as face_detection:
                results = face_detection.process(image_rgb)

                if results.detections:
                    best_face = None
                    best_score = -1

                    for detection in results.detections:
                        bbox = detection.location_data.relative_bounding_box
                        center_x = bbox.xmin + (bbox.width / 2)
                        box_area = bbox.width * bbox.height

                        # --- SCORING LOGIC ---
                        score = 0

                        if focus_region == "left":
                            # Bonus for being on the left (0.0 - 0.45)
                            # We use 0.45 to be slightly generous
                            score = box_area * (3.0 if center_x < 0.45 else 0.5)
                        elif focus_region == "right":
                            # Bonus for being on the right (0.55 - 1.0)
                            score = box_area * (3.0 if center_x > 0.55 else 0.5)
                        elif focus_region == "center":
                            # Bonus for being in center (0.35 - 0.65)
                            score = box_area * (3.0 if 0.35 < center_x < 0.65 else 0.5)
                        else:  # "auto"
                            # Weighted: Size is King, but Center is Queen.
                            # Size^1.2 makes large faces significantly better.
                            # Bias against extreme edges using dist_from_center.
                            dist_from_center = abs(0.5 - center_x)
                            center_bias = (1 - dist_from_center) ** 0.8
                            score = (box_area**1.2) * center_bias

                        # Stickiness Bonus (Process Continuity)
                        if prior_x is not None:
                            dist_to_prior = abs(center_x - prior_x)
                            # If very close to prior, huge bonus (maintain lock)
                            if dist_to_prior < 0.1:
                                score *= 2.0
                            elif dist_to_prior > 0.3:
                                score *= 0.5

                        if score > best_score:
                            best_score = score
                            best_face = detection

                    if best_face:
                        bbox = best_face.location_data.relative_bounding_box
                        return bbox.xmin + (bbox.width / 2)

        except Exception:
            pass

        return None

    def analyze_video(
        self, video_path, progress_callback=None, logger=None, focus_region="auto"
    ):
        """
        Analyzes video for face centering with Sticky Focus and Region Preference.
        """
        import concurrent.futures

        if not os.path.exists(video_path):
            if logger:
                logger.error(f"Video not found: {video_path}")
            return {}, 1, 1

        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Calculate target crop width (9:16)
        target_width = int(height * (9 / 16))
        if target_width > width:
            target_width = width

        # Config - Optimized for speed without sacrificing quality
        stride = 4  # Analyze every 4th frame (~6fps @ 24fps source)
        batch_size = 32

        cpu_count = os.cpu_count() or 4
        max_workers = max(1, cpu_count - 2)
        if max_workers > 16:
            max_workers = 16

        def process_batch(frames_data):
            results = []
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                # pass None for prior_x in parallel, but pass focus_region!
                future_to_idx = {
                    executor.submit(self.get_face_center, f, None, focus_region): idx
                    for f, idx in frames_data
                }
                for future in concurrent.futures.as_completed(future_to_idx):
                    try:
                        results.append((future_to_idx[future], future.result()))
                    except:
                        pass
            return results

        if logger:
            logger.log(f"🚀 Analyzing with {max_workers} threads...", "INFO")

        frame_idx = 0
        all_results = []

        while cap.isOpened():
            batch_frames = []
            for _ in range(batch_size):
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % stride == 0:
                    batch_frames.append((frame.copy(), frame_idx))
                frame_idx += 1

            if not batch_frames:
                break

            batch_results = process_batch(batch_frames)
            all_results.extend(batch_results)

            if progress_callback:
                progress_callback(min(1.0, frame_idx / total_frames))

        cap.release()
        all_results.sort(key=lambda x: x[0])

        # --- POST-PROCESSING (The "Stickiness" & "Hold" Logic) ---
        frame_mapping = {}

        # Initialize state
        current_rel_x = 0.5
        last_valid_rel_x = 0.5

        # Smoothing factors (0.2 = faster response, less lag)
        alpha = 0.2  # Increased from 0.1 for better face movement tracking

        for idx, detected_rel_x in all_results:
            target_rel_x = last_valid_rel_x  # Default to HOLD

            if detected_rel_x is not None:
                # If we found a face, update our target
                target_rel_x = detected_rel_x
                last_valid_rel_x = detected_rel_x

            # Apply Exponential Smoothing
            current_rel_x = (alpha * target_rel_x) + ((1 - alpha) * current_rel_x)

            # Convert to absolute pixels
            center_pix = int(current_rel_x * width)

            # Calculate Crop X (Top-Left corner)
            crop_x = int(center_pix - (target_width / 2))

            # Boundary Checks
            crop_x = max(0, min(crop_x, width - target_width))

            frame_mapping[idx] = crop_x

        if logger:
            logger.log(
                f"✅ Crop Analysis Complete. Generated {len(frame_mapping)} coordinates.",
                "INFO",
            )

        # OPTIMIZATION: Free memory after face detection
        import gc

        gc.collect()

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
