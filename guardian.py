import cv2
import pyautogui
import time
import sqlite3
import os
from datetime import datetime
from collections import deque
from PIL import Image, ImageTk, ImageFilter
import numpy as np
import config  # Import configuration

class ZeroTrustGuardian:
    def __init__(self):
        # Initialize database
        self.init_database()
        
        # Load face detector (single, most reliable one)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Open webcam with configured settings
        self.cap = cv2.VideoCapture(config.PERFORMANCE['camera_index'])
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.PERFORMANCE['frame_width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.PERFORMANCE['frame_height'])
        
        # State management from config
        self.face_history = deque(maxlen=config.STABILIZATION['face_history_length'])
        self.phone_history = deque(maxlen=config.STABILIZATION['phone_history_length'])
        self.privacy_mode = False
        self.last_action_time = 0
        self.ACTION_COOLDOWN = config.SHOULDER_SURFING['cooldown_seconds']
        self.threat_count = 0
        self.user_absent_time = None
        self.ABSENCE_THRESHOLD = config.USER_ABSENCE['threshold_seconds']
        self.last_threat_type = None
        self.consecutive_threats = 0
        self.THREAT_CONFIRMATION_THRESHOLD = config.SHOULDER_SURFING['confirmation_threshold']
        
        # Additional tracking for stability
        self.last_known_face_count = 1  # Assume user starts alone
        self.face_lost_time = None
        self.FACE_LOST_GRACE_PERIOD = 2.0  # seconds before considering face truly lost
        
        # Test mode
        self.test_mode = config.ADVANCED['test_mode']
        
        # Create screenshots directory
        os.makedirs('threat_logs', exist_ok=True)
        
        print("🛡️  ZeroTrust Workspace Guardian Active")
        print(f"📊 Monitoring: Shoulder Surfing | Screen Recording | User Absence")
        print(f"🔒 Privacy Mode: Local Processing Only")
        print(f"⚙️  Preset: {config.ACTIVE_PRESET}")
        if self.test_mode:
            print("🧪 TEST MODE: Actions simulated only")
        
    def init_database(self):
        """Initialize SQLite database for threat logging"""
        self.conn = sqlite3.connect('security_log.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                threat_type TEXT,
                face_count INTEGER,
                action_taken TEXT,
                screenshot_path TEXT,
                location TEXT
            )
        ''')
        self.conn.commit()
    
    def log_threat(self, threat_type, face_count, action_taken, screenshot_path=None):
        """Log security threat to database"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO threats (timestamp, threat_type, face_count, action_taken, screenshot_path, location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, threat_type, face_count, action_taken, screenshot_path, 'Unknown'))
        self.conn.commit()
        self.threat_count += 1
        print(f"🚨 THREAT #{self.threat_count}: {threat_type} detected at {timestamp}")
    
    def capture_threat_screenshot(self, frame, threat_type):
        """Save screenshot of threat"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'threat_logs/{threat_type}_{timestamp}.jpg'
        cv2.imwrite(filename, frame)
        return filename
    
    def remove_overlapping_faces(self, faces):
        """Remove duplicate/overlapping face detections using non-maximum suppression"""
        if len(faces) == 0:
            return []
        
        # Convert to numpy array
        boxes = np.array(faces)
        
        # Calculate areas
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 0] + boxes[:, 2]
        y2 = boxes[:, 1] + boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)
        
        # Sort by area (larger boxes first)
        order = areas.argsort()[::-1]
        
        keep = []
        while len(order) > 0:
            i = order[0]
            keep.append(i)
            
            if len(order) == 1:
                break
            
            # Calculate IoU with remaining boxes
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            
            intersection = w * h
            iou = intersection / (areas[i] + areas[order[1:]] - intersection + 1e-5)
            
            # Keep only boxes with IoU < 0.5 (not overlapping much)
            order = order[1:][iou < 0.5]
        
        return [tuple(boxes[i]) for i in keep]
    
    def detect_phone_camera(self, frame):
        """Detect rectangular objects that might be phones/cameras - improved accuracy"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Preprocessing for better edge detection
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 100)
        
        # Morphological operations to connect edges
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        edges = cv2.erode(edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        phone_detected = False
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by size
            if config.CAMERA_DETECTION['min_area'] < area < config.CAMERA_DETECTION['max_area']:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h > 0 else 0
                
                # Check aspect ratios
                portrait_min, portrait_max = config.CAMERA_DETECTION['aspect_ratios']['portrait']
                landscape_min, landscape_max = config.CAMERA_DETECTION['aspect_ratios']['landscape']
                
                is_portrait = portrait_min < aspect_ratio < portrait_max
                is_landscape = landscape_min < aspect_ratio < landscape_max
                
                if is_portrait or is_landscape:
                    # Verify it's rectangular (4-8 corners)
                    perimeter = cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
                    
                    if 4 <= len(approx) <= 8:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(frame, "CAMERA", (x, y-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        phone_detected = True
        
        # Stabilization: require consistent detection
        self.phone_history.append(1 if phone_detected else 0)
        stable_detection = sum(self.phone_history) >= len(self.phone_history) * 0.5
        
        return stable_detection
    
    def blur_screen(self):
        """Apply blur overlay to screen (simulated)"""
        if self.test_mode:
            print("   [TEST MODE] Would minimize screen")
            return
        # In production, this would overlay a blur on the actual screen
        # For demo, we'll just minimize
        pyautogui.hotkey('win', 'd')
    
    def lock_screen(self):
        """Lock the computer"""
        if self.test_mode:
            print("   [TEST MODE] Would lock screen")
            return
        pyautogui.hotkey('win', 'l')
    
    def run(self):
        """Main monitoring loop"""
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Enhance image quality for better detection
            gray = cv2.equalizeHist(gray)  # Improve contrast
            
            # Primary face detection (most reliable)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1,
                minNeighbors=6,  # Higher = fewer false positives
                minSize=(80, 80),  # Larger minimum to avoid small false detections
                maxSize=(400, 400),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Remove overlapping detections (non-maximum suppression)
            if len(faces) > 0:
                faces = self.remove_overlapping_faces(list(faces))
            
            face_count = len(faces)
            
            # Add to history for stabilization
            self.face_history.append(face_count)
            
            # Use median instead of average for better stability
            sorted_history = sorted(self.face_history)
            median_idx = len(sorted_history) // 2
            stable_face_count = sorted_history[median_idx]
            
            # Calculate confidence based on consistency
            face_consistency = sum(1 for f in self.face_history if f == stable_face_count) / len(self.face_history)
            
            # Draw face boxes with labels
            for i, (x, y, w, h) in enumerate(faces):
                color = (0, 255, 0) if face_count == 1 else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                
                # Label each face
                label = "USER" if i == 0 and face_count == 1 else f"PERSON {i+1}"
                cv2.putText(frame, label, (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            current_time = time.time()
            
            # THREAT 1: Multiple faces (Shoulder Surfing) - with confirmation
            if config.SHOULDER_SURFING['enabled'] and stable_face_count > 1 and face_consistency > config.STABILIZATION['consistency_threshold']:
                if self.last_threat_type == "shoulder_surfing":
                    self.consecutive_threats += 1
                else:
                    self.last_threat_type = "shoulder_surfing"
                    self.consecutive_threats = 1
                
                if not self.privacy_mode and self.consecutive_threats >= self.THREAT_CONFIRMATION_THRESHOLD:
                    if (current_time - self.last_action_time) > self.ACTION_COOLDOWN:
                        print(f"🚨 SHOULDER SURFING CONFIRMED! ({face_count} faces detected)")
                        screenshot = self.capture_threat_screenshot(frame, "shoulder_surfing")
                        self.log_threat("Shoulder Surfing", face_count, "Screen Minimized", screenshot)
                        self.blur_screen()
                        self.privacy_mode = True
                        self.last_action_time = current_time
                        self.consecutive_threats = 0
                    
                cv2.putText(frame, f"THREAT: SHOULDER SURFING ({self.consecutive_threats}/{self.THREAT_CONFIRMATION_THRESHOLD})", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                if self.last_threat_type == "shoulder_surfing":
                    self.consecutive_threats = 0
                    self.last_threat_type = None
            
            # THREAT 2: Phone/Camera detection - with confirmation
            if config.CAMERA_DETECTION['enabled']:
                phone_detected = self.detect_phone_camera(frame)
            if phone_detected and not self.privacy_mode:
                if self.last_threat_type == "camera":
                    self.consecutive_threats += 1
                else:
                    self.last_threat_type = "camera"
                    self.consecutive_threats = 1
                
                if self.consecutive_threats >= self.THREAT_CONFIRMATION_THRESHOLD:
                    if (current_time - self.last_action_time) > self.ACTION_COOLDOWN:
                        print("🚨 CAMERA/PHONE RECORDING CONFIRMED!")
                        screenshot = self.capture_threat_screenshot(frame, "camera_detected")
                        self.log_threat("Camera/Phone Recording", face_count, "Screen Minimized", screenshot)
                        self.blur_screen()
                        self.privacy_mode = True
                        self.last_action_time = current_time
                        self.consecutive_threats = 0
                
                cv2.putText(frame, f"THREAT: CAMERA DETECTED ({self.consecutive_threats}/{self.THREAT_CONFIRMATION_THRESHOLD})", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif not phone_detected and self.last_threat_type == "camera":
                self.consecutive_threats = 0
                self.last_threat_type = None
            
            # SAFE: Exactly 1 face with good consistency
            if stable_face_count == 1 and face_consistency > config.STABILIZATION['consistency_threshold']:
                self.user_absent_time = None  # Reset absence timer
                self.face_lost_time = None  # Reset face lost timer
                self.last_known_face_count = 1
                
                # Reset threat counters when safe
                if self.last_threat_type in ["shoulder_surfing", "camera"]:
                    self.consecutive_threats = max(0, self.consecutive_threats - 1)
                
                if self.privacy_mode and (current_time - self.last_action_time) > self.ACTION_COOLDOWN:
                    print("✅ Safe - Resuming (1 face detected consistently)")
                    pyautogui.hotkey('win', 'd')
                    self.privacy_mode = False
                    self.last_action_time = current_time
                    self.last_threat_type = None
                    self.consecutive_threats = 0
            
            # Handle temporary face loss (movement, rotation)
            elif stable_face_count == 0:
                if self.last_known_face_count == 1:
                    # Face was just detected, might be temporary loss
                    if self.face_lost_time is None:
                        self.face_lost_time = current_time
                        print("⚠️  Face temporarily lost - grace period active...")
                    
                    time_lost = current_time - self.face_lost_time
                    
                    # Within grace period - don't trigger absence
                    if time_lost < self.FACE_LOST_GRACE_PERIOD:
                        cv2.putText(frame, f"Face Lost: {time_lost:.1f}s / {self.FACE_LOST_GRACE_PERIOD}s grace", 
                                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
                        # Don't start absence timer yet
                        continue_to_absence = False
                    else:
                        # Grace period expired, now consider truly absent
                        continue_to_absence = True
                else:
                    continue_to_absence = True
                
                if continue_to_absence and config.USER_ABSENCE['enabled'] and face_consistency > config.STABILIZATION['consistency_threshold']:
                    if self.user_absent_time is None:
                        self.user_absent_time = current_time
                        print("⚠️  User absence detected - monitoring...")
                    
                    absent_duration = int(current_time - self.user_absent_time)
                    
                    if absent_duration > self.ABSENCE_THRESHOLD:
                        if not self.privacy_mode:
                            print(f"🚨 USER ABSENT FOR {absent_duration}s - AUTO LOCKING")
                            self.log_threat("User Absence", 0, "Screen Locked (Simulated)", None)
                            self.blur_screen()
                            self.privacy_mode = True
                            self.last_action_time = current_time
                    
                    # Visual warning
                    warning_color = (0, 165, 255) if absent_duration < self.ABSENCE_THRESHOLD else (0, 0, 255)
                    cv2.putText(frame, f"User Absent: {absent_duration}s / {self.ABSENCE_THRESHOLD}s", 
                               (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, warning_color, 2)
                    
                    # Progress bar
                    progress = min(absent_duration / self.ABSENCE_THRESHOLD, 1.0)
                    bar_width = int(300 * progress)
                    cv2.rectangle(frame, (10, 130), (310, 145), (100, 100, 100), -1)
                    cv2.rectangle(frame, (10, 130), (10 + bar_width, 145), warning_color, -1)
            else:
                # Multiple faces or other count
                self.face_lost_time = None
                if stable_face_count > 0:
                    self.last_known_face_count = stable_face_count
                    self.user_absent_time = None
                    self.last_action_time = current_time
                    self.last_threat_type = None
                    self.consecutive_threats = 0
            
            # THREAT 3: User absence - with grace period
            if config.USER_ABSENCE['enabled'] and stable_face_count == 0 and face_consistency > config.STABILIZATION['consistency_threshold']:
                if continue_to_absence:
                    # THREAT 3: User absence - with grace period
                    if config.USER_ABSENCE['enabled'] and face_consistency > config.STABILIZATION['consistency_threshold']:
                        if self.user_absent_time is None:
                            self.user_absent_time = current_time
                            print("⚠️  User absence detected - monitoring...")
                        
                        absent_duration = int(current_time - self.user_absent_time)
                        
                        if absent_duration > self.ABSENCE_THRESHOLD:
                            if not self.privacy_mode:
                                print(f"🚨 USER ABSENT FOR {absent_duration}s - AUTO LOCKING")
                                self.log_threat("User Absence", 0, "Screen Locked (Simulated)", None)
                                # Uncomment to actually lock:
                                # self.lock_screen()
                                self.blur_screen()  # For demo, just minimize
                                self.privacy_mode = True
                                self.last_action_time = current_time
                        
                        # Visual warning
                        warning_color = (0, 165, 255) if absent_duration < self.ABSENCE_THRESHOLD else (0, 0, 255)
                        cv2.putText(frame, f"User Absent: {absent_duration}s / {self.ABSENCE_THRESHOLD}s", 
                                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, warning_color, 2)
                        
                        # Progress bar
                        progress = min(absent_duration / self.ABSENCE_THRESHOLD, 1.0)
                        bar_width = int(300 * progress)
                        cv2.rectangle(frame, (10, 130), (310, 145), (100, 100, 100), -1)
                        cv2.rectangle(frame, (10, 130), (10 + bar_width, 145), warning_color, -1)
            else:
                # Multiple faces or other count
                self.face_lost_time = None
                if stable_face_count > 0:
                    self.last_known_face_count = stable_face_count
                    self.user_absent_time = None
            
            # Display status with confidence
            status_color = (0, 255, 0) if stable_face_count == 1 else (0, 0, 255)
            confidence_pct = int(face_consistency * 100)
            cv2.putText(frame, f"Faces: {face_count} | Stable: {stable_face_count} | Confidence: {confidence_pct}%", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
            
            # Privacy mode indicator
            if self.privacy_mode:
                # Flashing red banner
                if int(current_time * 2) % 2 == 0:
                    cv2.rectangle(frame, (0, 160), (frame.shape[1], 200), (0, 0, 255), -1)
                    cv2.putText(frame, "PRIVACY MODE ACTIVE - SCREEN PROTECTED", (10, 185),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Threat counter
            cv2.putText(frame, f"Total Threats Logged: {self.threat_count}", (10, 220),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # System status
            status_text = "MONITORING" if not self.privacy_mode else "PROTECTED"
            status_bg_color = (0, 100, 0) if not self.privacy_mode else (0, 0, 100)
            cv2.rectangle(frame, (frame.shape[1]-200, 10), (frame.shape[1]-10, 50), status_bg_color, -1)
            cv2.putText(frame, status_text, (frame.shape[1]-190, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show feed if configured
            if config.DISPLAY['show_feed']:
                cv2.imshow(config.DISPLAY['window_name'], frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.cap.release()
        cv2.destroyAllWindows()
        self.conn.close()
        print("🛡️  Guardian deactivated")

if __name__ == "__main__":
    guardian = ZeroTrustGuardian()
    guardian.run()
