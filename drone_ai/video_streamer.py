import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os

class VideoPlayer(Node):
    def __init__(self):
        super().__init__('video_streamer')
        self.publisher = self.create_publisher(Image, '/camera', 10)
        self.bridge = CvBridge()
        
        video_path = '/home/n_harsha/ros2_ws/rescue.mp4'
        
        self.cap = cv2.VideoCapture(video_path)
        self.timer = self.create_timer(0.1, self.timer_cb) 
        self.get_logger().info("Video Injector Online! Broadcasting rescue.mp4 to AI...")

    def timer_cb(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret: return
            
        frame = cv2.resize(frame, (640, 480)) 
        
        # FIX: Bypass the ROS 2 cv_bridge KeyError 16 bug
        msg = self.bridge.cv2_to_imgmsg(frame)
        msg.encoding = "bgr8" # Manually attach the encoding label
        msg.header.stamp = self.get_clock().now().to_msg()
        
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = VideoPlayer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
