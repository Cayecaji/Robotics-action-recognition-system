#!/usr/bin/env python3

import rclpy
from rclpy.node import Node 


class TrackingNode(Node):

    def __init__(self):
        super().__init__("tracking_node") 
        self.get_logger().info("Testing node...")


def main():

    rclpy.init()

    node = TrackingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
