#!/usr/bin/env python3

import cv2
import json
import torch
import os
import re
import time
import rclpy
import numpy as np
from cv_bridge import CvBridge
from ultralytics import YOLO
from rclpy.node import Node 
from sensor_msgs.msg import Image
from std_msgs.msg import String



class TrackingNode(Node):

    def __init__(self):
        super().__init__("tracking_node") 
        self.bridge = CvBridge()

        # --- Mode parameters ---
        self.mode = self.declare_parameter('mode', 'dataset').value
        self.dataset_path = self.declare_parameter('dataset_path', '/robotics-action-recognition-system/test/dataset').value
        
         # --- Wait time between frames ---
        self.max_frames = self.declare_parameter('max_frames_per_video',5).value
        self.delay_between_videos = self.declare_parameter('delay_between_videos',30).value

        
        # --- YOLO parameters ---
        self.MODEL = self.declare_parameter('yolo_model',"yolov8s.pt").value 
        self.CONFIDENCE = self.declare_parameter('confidence',0.4).value
        self.CLASSES = self.declare_parameter('classes',[0]).value
        self.TRACKER = self.declare_parameter('tracker',"bytetrack.yaml").value
        self.PERSIST = self.declare_parameter('persist',True).value
        self.IOU = self.declare_parameter('iou',0.45).value
        self.VERBOSE = self.declare_parameter('verbose',False).value

        # --- YOLO initialization ---
        self.model = YOLO(self.MODEL)

         # --- Publishers ---
        self.publisher_image = self.create_publisher(Image, '/detected_person_image', 10)
        self.publisher_id_match = self.create_publisher(String, '/person_id_match', 10)

        self.get_logger().info(f"Tracking node initiated in mode: {self.mode}")

        if self.mode == 'camera':
            self.subscription = self.create_subscription(Image, '/image_raw', self.image_callback, 5)
            self.frame_counter = 0
            self.WAIT_TIME = 5
        else:
            # Dataset mode
            self.timer = self.create_timer(2.0, self.process_dataset)


    #Tracking model function
    def image_callback(self,msg):

        self.frame_counter += 1

        #Analyze frames every 0,5s (30fps camera)
        if self.frame_counter % self.WAIT_TIME == 0: 
            self.frame_counter = 0

            try:
                frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
                self.process_frame_logic(frame)
            except Exception as e:
                self.get_logger().error(f"Error reading image: {e}")
                return
            

    def process_frame_logic(self, frame):       

        #Make a copy of the frame so we can send it without bounding boxes
        original_frame = frame.copy()

        tracking_results = self.model.track(frame, persist=self.PERSIST, tracker=self.TRACKER, classes= self.CLASSES,
                                                 conf= self.CONFIDENCE, iou=self.IOU, verbose=self.VERBOSE)
        
       
        if tracking_results[0].boxes is not None and len(tracking_results[0].boxes) > 0 and tracking_results[0].boxes.id is not None:

                #boundingbox_frame = tracking_results[0].plot()  Just in case we need to check the bounding boxes

            boundingbox_frame = tracking_results[0].plot()
            num_persons = len(tracking_results[0].boxes)
            out_image_msg = self.bridge.cv2_to_imgmsg(boundingbox_frame, "bgr8") #Transform again into ROS2 image.  


            if(num_persons == 1):
                id_match = "1 persona detectada con id " + str(tracking_results[0].boxes.id.int().cpu().tolist()) + "."
            else:
                id_match = str(num_persons) + " personas detectadas con id" + str(tracking_results[0].boxes.id.int().cpu().tolist()) + "."
                

            id_match_msg = String()
            id_match_msg.data = id_match

            # --- Publish both image and id_match ---
            self.publisher_image.publish(out_image_msg)
            self.publisher_id_match.publish(id_match_msg)
            info_msg = "Frame sent to /detected_person_image : " + str(num_persons) + " person/persons detected with id"+ str(tracking_results[0].boxes.id.int().cpu().tolist()) + "."
            self.get_logger().info(info_msg)

            return True
        return False     


    def process_dataset(self):
        self.timer.cancel() 
        
        if not os.path.exists(self.dataset_path):
            self.get_logger().error(f"Path not valid: {self.dataset_path}")
            return

        videos = [f for f in os.listdir(self.dataset_path) if f.endswith(('.mp4', '.avi'))]
        
        for video_name in videos:
            video_path = os.path.join(self.dataset_path, video_name)
            cap = cv2.VideoCapture(video_path)
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps == 0:
                fps = 30.0 # Fallback value
                
           
            self.get_logger().info(f"--- Video: {video_name} (FPS: {fps}) ---")
            time.sleep(2.0)
            frame_idx = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                self.process_frame_logic(frame)
                frame_idx += 1

            cap.release()
            
            # Wait till system full prediction ends
            self.get_logger().info(f"Video {video_name} fully read. Waiting for model prediction...")
            time.sleep(self.delay_between_videos)
            
            torch.cuda.empty_cache()

        self.get_logger().info("All videos had been procesed.")


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
