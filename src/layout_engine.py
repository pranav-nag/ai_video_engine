import cv2
import numpy as np
import os

class LayoutEngine:
    """
    Analyzes video content to determine the best layout (Solo vs Split Screen).
    Uses OpenCV Haar Cascades for face detection.
    """
    
    def __init__(self):
        # Load Haar Cascade for Face Detection
        # We need to find the xml file. Usually it's in cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def detect_faces(self, frame):
        """Returns list of (x, y, w, h) for detected faces."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50), # Ignore tiny faces
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        return faces

    def analyze_layout(self, video_path, sample_interval=1.0, logger=None):
        """
        Scans video to determine if it's a multi-speaker podcast.
        
        Returns:
            layout_mode (str): "active_speaker" (default) or "split_screen"
            regions (dict): { "top": (x,y,w,h), "bottom": (x,y,w,h) } if split
        """
        if logger:
            logger.log(f"📐 Analyzing layout for {os.path.basename(video_path)}...", "INFO", "BLUE")

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        frame_interval = int(fps * sample_interval)
        count = 0
        
        frames_with_2_faces = 0
        total_samples = 0
        
        # Accumulators for face positions (to find stable regions)
        # We'll split the screen horizontally and track faces in Left vs Right (or Top/Bottom)
        # Assuming Podcasts are usually Left/Right in 16:9
        left_faces = []
        right_faces = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if count % frame_interval == 0:
                total_samples += 1
                faces = self.detect_faces(frame)
                
                if len(faces) >= 2:
                    # Sort faces by size (largest first) to ignore background noise
                    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[:2]
                    
                    # Sort by X coordinate to distinguish Left/Right
                    faces_x = sorted(faces, key=lambda f: f[0])
                    
                    f1 = faces_x[0] # Left
                    f2 = faces_x[1] # Right
                    
                    # Check if they are distinct (avoid double detection of same face)
                    # If x centers are far apart
                    c1 = f1[0] + f1[2]/2
                    c2 = f2[0] + f2[2]/2
                    
                    if abs(c1 - c2) > width * 0.2: # At least 20% width separation
                        frames_with_2_faces += 1
                        left_faces.append(f1)
                        right_faces.append(f2)

            count += 1
            
        cap.release()
        
        # Decide Layout
        # If > 30% of sampled frames have 2 faces, we assume podcast mode
        is_podcast = total_samples > 5 and (frames_with_2_faces / total_samples) > 0.3
        
        result = {
            "layout_mode": "active_speaker", # Default
            "coords": {}
        }

        if is_podcast:
            msg = f"🎙️ Dual-Speaker Podcast Detected ({frames_with_2_faces}/{total_samples} samples)"
            print(msg)
            if logger:
                logger.log(msg, "INFO", "PURPLE")
            
            result["layout_mode"] = "split_screen"
            
            # Calculate average crop regions
            # Helper to get avg rect
            def get_avg_rect(face_list):
                if not face_list: return (0,0,0,0)
                # Weighted average? No, simple average is fine for crop center
                avg_x = int(np.mean([f[0] for f in face_list]))
                avg_y = int(np.mean([f[1] for f in face_list]))
                avg_w = int(np.mean([f[2] for f in face_list]))
                avg_h = int(np.mean([f[3] for f in face_list]))
                return (avg_x, avg_y, avg_w, avg_h)

            result["coords"]["top"] = get_avg_rect(left_faces) # Detect Left -> Map to Top
            result["coords"]["bottom"] = get_avg_rect(right_faces) # Detect Right -> Map to Bottom
            
        else:
            if logger:
                logger.log("👤 Single Speaker / Dynamic Mode Detected", "INFO")

        return result

if __name__ == "__main__":
    # Test
    # le = LayoutEngine()
    # print(le.analyze_layout("test_podcast.mp4"))
    pass
