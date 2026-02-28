"""
Test script to verify detection accuracy
"""
import cv2
import time

# Load face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Open webcam
cap = cv2.VideoCapture(0)

print("🧪 Testing Detection Accuracy")
print("=" * 50)
print("\nInstructions:")
print("1. Sit alone in front of camera - should detect 1 face")
print("2. Have someone join you - should detect 2+ faces")
print("3. Walk away - should detect 0 faces")
print("4. Press 'q' to quit\n")
print("=" * 50)

face_counts = []
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Test with same parameters as guardian
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(60, 60),
        maxSize=(400, 400)
    )
    
    face_count = len(faces)
    face_counts.append(face_count)
    
    # Draw boxes
    for i, (x, y, w, h) in enumerate(faces):
        color = (0, 255, 0) if face_count == 1 else (0, 0, 255) if face_count > 1 else (255, 0, 0)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
        
        # Calculate face size
        face_size = w * h
        cv2.putText(frame, f"Face {i+1} ({face_size}px)", (x, y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Statistics
    elapsed = int(time.time() - start_time)
    avg_faces = sum(face_counts[-30:]) / min(len(face_counts), 30)  # Last 30 frames
    
    # Display info
    cv2.putText(frame, f"Current: {face_count} faces", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Average (30f): {avg_faces:.1f}", (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Runtime: {elapsed}s", (10, 90),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Status
    if face_count == 0:
        status = "NO USER DETECTED"
        status_color = (0, 165, 255)
    elif face_count == 1:
        status = "SAFE - 1 USER"
        status_color = (0, 255, 0)
    else:
        status = f"THREAT - {face_count} PEOPLE"
        status_color = (0, 0, 255)
    
    cv2.rectangle(frame, (0, frame.shape[0]-50), (frame.shape[1], frame.shape[0]), (50, 50, 50), -1)
    cv2.putText(frame, status, (10, frame.shape[0]-15),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2)
    
    cv2.imshow('Accuracy Test - Press Q to quit', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Final statistics
print("\n" + "=" * 50)
print("📊 Test Results")
print("=" * 50)
print(f"Total frames: {len(face_counts)}")
print(f"Average faces detected: {sum(face_counts)/len(face_counts):.2f}")
print(f"0 faces: {face_counts.count(0)} frames ({face_counts.count(0)/len(face_counts)*100:.1f}%)")
print(f"1 face: {face_counts.count(1)} frames ({face_counts.count(1)/len(face_counts)*100:.1f}%)")
print(f"2+ faces: {sum(1 for f in face_counts if f >= 2)} frames ({sum(1 for f in face_counts if f >= 2)/len(face_counts)*100:.1f}%)")
print("=" * 50)
