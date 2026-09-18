import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage # NEW: Importing Compressed Video
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO

class DroneYOLODetector(Node):
    def __init__(self):
        super().__init__('drone_yolo_detector')
        
        self.subscription = self.create_subscription(Image, '/camera', self.image_callback, 10)
        self.target_pub = self.create_publisher(Point, '/ai/target_pixel', 10)
        
        # FIX: Switched to CompressedImage and restored 'Reliable' (10) QoS for Foxglove!
        self.image_pub = self.create_publisher(CompressedImage, '/ai/annotated_image', 10)
        
        self.bridge = CvBridge()
        self.get_logger().info('Loading YOLO model...')
        self.model = YOLO('yolov8n.pt') 
        self.get_logger().info('Vision Node Online. Waiting for camera frames...')

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            return

        # Run AI Inference (classes=[0] strictly filters for 'person' only)
        results = self.model(frame, classes=[0], verbose=False)
        annotated_frame = results[0].plot()

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf > 0.10: 
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    u_center = int((x1 + x2) / 2)
                    v_center = int((y1 + y2) / 2)
                    
                    # Updated the text to explicitly state PERSON DETECTED
                    self.get_logger().warn(f'PERSON DETECTED! Confidence: {conf:.2f} | Pixel Center: ({u_center}, {v_center})')
                    
                    msg_out = Point()
                    msg_out.x = float(u_center)
                    msg_out.y = float(v_center)
                    msg_out.z = float(conf)
                    self.target_pub.publish(msg_out)

        # NEW: Compress the video stream by 98% to prevent network crashes
        try:
            success, encoded_image = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if success:
                compressed_msg = CompressedImage()
                compressed_msg.header = msg.header
                compressed_msg.format = "jpeg"
                compressed_msg.data = encoded_image.tobytes()
                self.image_pub.publish(compressed_msg)
        except Exception as e:
            self.get_logger().error(f"Publishing compressed frame failed: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = DroneYOLODetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
