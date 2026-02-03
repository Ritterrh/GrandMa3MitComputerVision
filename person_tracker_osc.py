#!/usr/bin/env python3
"""
Person Tracker with OSC Output for grandMA3
Tracks the closest person using MediaPipe Pose and sends coordinates via OSC
Updated for MediaPipe 0.10.32+ API
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import numpy as np
from pythonosc import udp_client
import time
import argparse


class PersonTrackerOSC:
    def __init__(self, osc_ip="127.0.0.1", osc_port=8000, camera_id=0):
        """
        Initialize the person tracker with OSC communication
        
        Args:
            osc_ip: IP address of the grandMA3 console
            osc_port: OSC port (default 8000)
            camera_id: Camera device ID (default 0)
        """
        # Download the pose landmarker model if needed
        model_path = 'pose_landmarker_lite.task'
        
        # Initialize MediaPipe Pose Landmarker
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.detector = vision.PoseLandmarker.create_from_options(options)
        
        # Initialize OSC client
        self.osc_client = udp_client.SimpleUDPClient(osc_ip, osc_port)
        self.osc_ip = osc_ip
        self.osc_port = osc_port
        
        # Initialize camera
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera {camera_id}")
        
        # Set camera resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Tracking state
        self.last_x = 0.5
        self.last_y = 0.5
        self.person_detected = False
        
        # FPS calculation
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.timestamp_ms = 0
        
        print(f"✓ Person Tracker initialized")
        print(f"✓ OSC target: {osc_ip}:{osc_port}")
        print(f"✓ Camera resolution: {int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
        print(f"✓ Press 'q' to quit")
    
    def get_closest_person_position(self, landmarks):
        """
        Extract the position of the closest person based on nose landmark
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            tuple: (x, y) normalized coordinates (0.0 to 1.0)
        """
        # Use nose landmark (index 0) as the tracking point
        nose = landmarks[0]  # NOSE landmark
        
        # Normalize coordinates (MediaPipe already provides normalized coords)
        x = nose.x  # 0.0 to 1.0 (left to right)
        y = nose.y  # 0.0 to 1.0 (top to bottom)
        
        # Clamp values to ensure they're in valid range
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        
        return x, y
    
    def send_osc_data(self, x, y):
        """
        Send normalized coordinates via OSC to grandMA3
        
        Args:
            x: Normalized X coordinate (0.0 to 1.0)
            y: Normalized Y coordinate (0.0 to 1.0)
        """
        try:
            # Send X coordinate
            self.osc_client.send_message("/stage/person1/x", x)
            # Send Y coordinate
            self.osc_client.send_message("/stage/person1/y", y)
        except Exception as e:
            print(f"OSC Error: {e}")
    
    def draw_landmarks_on_image(self, rgb_image, detection_result):
        """
        Draw pose landmarks on the image
        
        Args:
            rgb_image: RGB image
            detection_result: MediaPipe detection result
            
        Returns:
            Annotated image
        """
        if not detection_result.pose_landmarks:
            return rgb_image
            
        pose_landmarks_list = detection_result.pose_landmarks
        annotated_image = np.copy(rgb_image)

        # Loop through the detected poses to visualize
        for idx in range(len(pose_landmarks_list)):
            pose_landmarks = pose_landmarks_list[idx]

            # Draw the pose landmarks
            pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            pose_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) 
                for landmark in pose_landmarks
            ])
            
            solutions.drawing_utils.draw_landmarks(
                annotated_image,
                pose_landmarks_proto,
                solutions.pose.POSE_CONNECTIONS,
                solutions.drawing_styles.get_default_pose_landmarks_style()
            )
        
        return annotated_image
    
    def draw_info_overlay(self, image, x, y):
        """
        Draw information overlay on the image
        
        Args:
            image: OpenCV image
            x: Current X coordinate
            y: Current Y coordinate
        """
        height, width = image.shape[:2]
        
        # Semi-transparent overlay for info panel
        overlay = image.copy()
        cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)
        
        # Draw info text
        font = cv2.FONT_HERSHEY_SIMPLEX
        y_offset = 35
        
        cv2.putText(image, f"FPS: {self.fps:.1f}", (20, y_offset), 
                    font, 0.6, (0, 255, 0), 2)
        y_offset += 30
        
        status_color = (0, 255, 0) if self.person_detected else (0, 0, 255)
        status_text = "TRACKING" if self.person_detected else "NO PERSON"
        cv2.putText(image, f"Status: {status_text}", (20, y_offset), 
                    font, 0.6, status_color, 2)
        y_offset += 30
        
        cv2.putText(image, f"X: {x:.3f} | Y: {y:.3f}", (20, y_offset), 
                    font, 0.6, (255, 255, 255), 2)
        y_offset += 30
        
        cv2.putText(image, f"OSC: {self.osc_ip}:{self.osc_port}", (20, y_offset), 
                    font, 0.5, (200, 200, 200), 1)
        
        # Draw crosshair at tracked position if person detected
        if self.person_detected:
            center_x = int(x * width)
            center_y = int(y * height)
            
            # Draw crosshair
            cv2.drawMarker(image, (center_x, center_y), (0, 255, 255), 
                          cv2.MARKER_CROSS, 30, 2)
            
            # Draw circle
            cv2.circle(image, (center_x, center_y), 15, (0, 255, 255), 2)
    
    def update_fps(self):
        """Update FPS calculation"""
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()
    
    def run(self):
        """Main tracking loop"""
        print("\n=== Starting Person Tracking ===\n")
        
        try:
            while self.cap.isOpened():
                success, image = self.cap.read()
                if not success:
                    print("Failed to read from camera")
                    break
                
                # Flip image horizontally for mirror view
                image = cv2.flip(image, 1)
                
                # Convert to RGB for MediaPipe
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Create MediaPipe Image
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
                
                # Process pose detection
                self.timestamp_ms += 33  # Approximate 30 FPS
                detection_result = self.detector.detect_for_video(mp_image, self.timestamp_ms)
                
                # Extract position if person detected
                if detection_result.pose_landmarks:
                    self.person_detected = True
                    
                    # Get position from first detected person
                    landmarks = detection_result.pose_landmarks[0]
                    x, y = self.get_closest_person_position(landmarks)
                    
                    # Update last known position
                    self.last_x = x
                    self.last_y = y
                    
                    # Send OSC data
                    self.send_osc_data(x, y)
                    
                    # Draw pose landmarks
                    image_rgb = self.draw_landmarks_on_image(image_rgb, detection_result)
                    image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                else:
                    self.person_detected = False
                
                # Draw info overlay
                self.draw_info_overlay(image, self.last_x, self.last_y)
                
                # Update FPS
                self.update_fps()
                
                # Display image
                cv2.imshow('Person Tracker - Press Q to quit', image)
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nQuitting...")
                    break
                    
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up...")
        self.cap.release()
        cv2.destroyAllWindows()
        self.detector.close()
        print("✓ Cleanup complete")


def main():
    parser = argparse.ArgumentParser(description='Person Tracker with OSC output for grandMA3')
    parser.add_argument('--ip', type=str, default='127.0.0.1',
                        help='IP address of grandMA3 console (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000,
                        help='OSC port (default: 8000)')
    parser.add_argument('--camera', type=int, default=0,
                        help='Camera device ID (default: 0)')
    
    args = parser.parse_args()
    
    try:
        tracker = PersonTrackerOSC(
            osc_ip=args.ip,
            osc_port=args.port,
            camera_id=args.camera
        )
        tracker.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
