import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Int32, String
from px4_msgs.msg import VehicleStatus
from cv_bridge import CvBridge
import cv2
import os
from ultralytics import YOLO
from rclpy.qos import QoSProfile, ReliabilityPolicy

class CinematicMockAI(Node):
    def __init__(self):
        super().__init__('cinematic_ai_node')
        self.bridge = CvBridge()

        self.get_logger().info('Loading YOLOv8 model...')
        self.model = YOLO('yolov8n.pt')
        self.is_flying = False
        self.active_feed = 0  # 0 = Empty Video, 1 = People Video

        # Video File Paths
        self.video_paths = {
            0: os.path.expanduser('~/videos/empty.mp4'),
            1: os.path.expanduser('~/videos/people.mp4')
        }

        self.caps = {
            0: cv2.VideoCapture(self.video_paths[0]),
            1: cv2.VideoCapture(self.video_paths[1])
        }

        # PX4 Telemetry Subscription
        qos_profile = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, depth=10)
        self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v4', self.status_cb, qos_profile)
        self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status', self.status_cb, qos_profile)

        # Video Switcher Subscription
        self.create_subscription(Int32, '/drone/video_feed_select', self.switch_cb, 10)

        # Output Publishers
        self.img_pub = self.create_publisher(CompressedImage, '/ai/annotated_image/compressed', 10)
        self.status_pub = self.create_publisher(String, '/ai/status', 10)

        # 30 FPS Processing Loop
        self.timer = self.create_timer(1.0 / 30.0, self.process_loop)
        self.get_logger().info('Cinematic AI Ready. Arm/Takeoff in QGroundControl to begin streaming.')

    def status_cb(self, msg):
        was_flying = self.is_flying
        self.is_flying = (msg.arming_state == 2)
        if self.is_flying and not was_flying:
            self.get_logger().info('TAKEOFF DETECTED! Unlocking video feed.')
        elif not self.is_flying and was_flying:
            self.get_logger().info('LANDING DETECTED! Video feed paused.')

    def switch_cb(self, msg):
        if msg.data in self.caps:
            self.active_feed = msg.data
            mode_str = "PEOPLE FEED" if self.active_feed == 1 else "EMPTY FEED"
            self.get_logger().info(f'VIDEO SWITCH: Switched to {mode_str}')

    def process_loop(self):
        if not self.is_flying:
            return

        cap = self.caps[self.active_feed]
        ret, frame = cap.read()

        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                return

        frame = cv2.resize(frame, (640, 480))
        results = self.model(frame, classes=[0], verbose=False)
        boxes = results[0].boxes
        
        # Prepare status message
        status_msg = String()

        if len(boxes) > 0:
            output_img = results[0].plot()
            status_msg.data = f"[ALERT] ACTION CAM ACTIVE: Tracking {len(boxes)} person(s)."
        else:
            output_img = frame.copy()
            status_msg.data = "[STANDBY] CINEMATIC CAM ACTIVE: Scanning area. Zero targets detected."
            
            text = "TRACKING..."
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.3
            thickness = 3
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = (output_img.shape[1] - text_size[0]) // 2
            text_y = (output_img.shape[0] + text_size[1]) // 2
            cv2.putText(output_img, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 2)
            cv2.putText(output_img, text, (text_x, text_y), font, font_scale, (0, 255, 0), thickness)

        # Publish frame and text status
        self.status_pub.publish(status_msg)
        compressed_msg = self.bridge.cv2_to_compressed_imgmsg(output_img)
        self.img_pub.publish(compressed_msg)

def main(args=None):
    rclpy.init(args=args)
    node = CinematicMockAI()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
