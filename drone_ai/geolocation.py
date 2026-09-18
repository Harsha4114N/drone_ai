import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from px4_msgs.msg import VehicleGlobalPosition, VehicleOdometry
from rclpy.qos import qos_profile_sensor_data
import math

class GeolocationNode(Node):
    def __init__(self):
        super().__init__('geolocation_node')
        
        self.create_subscription(Point, '/ai/target_pixel', self.target_cb, 10)
        self.create_subscription(VehicleGlobalPosition, '/fmu/out/vehicle_global_position', self.global_pos_cb, qos_profile_sensor_data)
        
        # FIX: Switched to VehicleOdometry for reliable altitude telemetry
        self.create_subscription(VehicleOdometry, '/fmu/out/vehicle_odometry', self.odom_cb, qos_profile_sensor_data)
        
        self.drone_lat = 0.0
        self.drone_lon = 0.0
        self.drone_alt = 0.0
        self.targets_received = 0
        
        self.c_x, self.c_y = 320.0, 240.0
        self.f_x, self.f_y = 554.0, 554.0
        
        self.create_timer(2.0, self.debug_timer)
        self.get_logger().info("LoRa Geolocation Transmitter Online. Waiting for telemetry...")

    def debug_timer(self):
        self.get_logger().info(f"[DEBUG] Alt: {self.drone_alt:.2f}m | Lat: {self.drone_lat:.4f} | AI Targets Rx: {self.targets_received}")

    def global_pos_cb(self, msg):
        self.drone_lat = msg.lat
        self.drone_lon = msg.lon

    def odom_cb(self, msg):
        # Odometry position[2] is the Z axis (Down is positive, so we invert it)
        self.drone_alt = -msg.position[2]

    def target_cb(self, msg):
        self.targets_received += 1
        if self.drone_lat == 0.0 or self.drone_alt < 1.0:
            return 
            
        u, v = msg.x, msg.y
        
        offset_x_meters = (u - self.c_x) * self.drone_alt / self.f_x
        offset_y_meters = (v - self.c_y) * self.drone_alt / self.f_y
        
        lat_offset = offset_y_meters / 111320.0
        lon_offset = offset_x_meters / (111320.0 * math.cos(math.radians(self.drone_lat)))
        
        victim_lat = self.drone_lat + lat_offset
        victim_lon = self.drone_lon + lon_offset
        
        self.get_logger().warn(f"\n[LORA TRANSMISSION] OVERRIDE! VICTIM DETECTED!")
        self.get_logger().warn(f"Drone GPS:   {self.drone_lat:.6f}, {self.drone_lon:.6f}")
        self.get_logger().warn(f"Victim GPS:  {victim_lat:.6f}, {victim_lon:.6f}")
        self.get_logger().warn(f"Distance:    Target is {offset_x_meters:.1f}m East, {offset_y_meters:.1f}m North\n")

def main():
    rclpy.init()
    node = GeolocationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
