import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    pkg_custom_nodes = 'action_recognition' 
    
    # Obtener el directorio share del paquete para localizar los archivos YAML
    pkg_share = get_package_share_directory(pkg_custom_nodes)
    
    # Rutas absolutas a los archivos de parámetros de configuración
    arc_params_path = os.path.join(pkg_share, 'config', 'arc_params.yaml')
    tracking_params_path = os.path.join(pkg_share, 'config', 'tracking_params.yaml')


    usb_cam_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        output='screen',
        parameters=[{
            'video_device': '/dev/video0',
            'image_width': 640,
            'image_height': 480,
            'pixel_format': 'yuyv',
            'io_method': 'mmap',
            'frame_id': 'camera_link'
        }]
    )

    tracking_node = Node(
        package=pkg_custom_nodes,
        executable='tracking_node',
        name='tracking_node',
        output='screen',
        parameters=[tracking_params_path]
    )

    action_recognition_core_node = Node(
        package=pkg_custom_nodes,
        executable='action_recognition_core',
        name='action_recognition_core',
        output='screen',
        parameters=[arc_params_path]
    )

    hri_node = Node(
        package=pkg_custom_nodes,
        executable='hri_node',
        name='hri_node',
        output='screen'
    )

    # -------------------------------------------------------------------------
    # LANZAMIENTO
    # -------------------------------------------------------------------------
    return LaunchDescription([
        usb_cam_node,
        tracking_node,
        action_recognition_core_node,
        hri_node
    ])