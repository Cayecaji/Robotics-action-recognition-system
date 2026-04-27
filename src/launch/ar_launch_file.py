from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        #action_recognition_core
        Node(
            package='action_recognition',
            executable='action_recognition_core',
            name='action_recognition_core',
            output='screen'
        ),
        #tracking_node
        Node(
            package='action_recognition',
            executable='tracking_node',
            name='tracking_node',
            output='screen'
        ),
        #usb_cam
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='usb_cam',
            parameters=[{
                'brightness': 150
            }],
            output='screen'
        )
    ])