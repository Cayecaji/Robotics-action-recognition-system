#!/usr/bin/env python3

import cv2
import json
import torch
import time
import re
import rclpy
import numpy as np

from ollama import chat
from cv_bridge import CvBridge
from ultralytics import YOLO
from rclpy.node import Node 
from sensor_msgs.msg import Image
from std_msgs.msg import String



class TrackingNode(Node):

    def __init__(self):
        super().__init__("tracking_node") 
        self.bridge = CvBridge()

        #Initialise model YOLO one time only
        self.model = YOLO('yolov8m.pt')

        #Subcriptions and publishers.
        self.subscription         =   self.create_subscription(Image, '/image_raw', self.image_callback, 5)
        self.publisher_image      =   self.create_publisher(Image, '/detected_person_image', 10)
        self.publisher_id_match   =   self.create_publisher(String, '/person_id_match', 10)

        #Define the wait time between frames and the frame counter
        self.WAIT_TIME = 5
        self.frame_counter = 0

        #Model parameters
        self.PERSIST = True 
        self.TRACKER = "bytetrack.yaml"
        self.CLASSES = [0]
        self.CONFIDENCE = 0.75
        self.IOU = 0.45
        self.VERBOSE = False 

        #Image correction (low bright and contrast)
        self.CONTRAST   = 1.2
        self.BRIGHTNESS = 80
        
        
        #Node info
        self.get_logger().info("Tracking node running...")


    #Tracking model function
    def image_callback(self,msg):

        self.frame_counter += 1

        #Analyze frames every 0,5s (30fps camera)
        if self.frame_counter % self.WAIT_TIME == 0: 
            self.frame_counter = 0

            try:
                frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            except Exception as e:
                self.get_logger().error(f"Error reading image: {e}")
                return
            

            #Pre-process the image
            #frame = cv2.convertScaleAbs(frame, alpha=self.CONTRAST, beta=self.BRIGHTNESS)

            #Make a copy of the frame so we can send it without bounding boxes
            original_frame = frame.copy()

            tracking_results = self.model.track(frame, persist=self.PERSIST, tracker=self.TRACKER, classes= self.CLASSES,
                                                 conf= self.CONFIDENCE, iou=self.IOU, verbose=self.VERBOSE)

            if tracking_results[0].boxes is not None and len(tracking_results[0].boxes) > 0 and tracking_results[0].boxes.id is not None:
                #if tracking_results[0].boxes.id is not None: ¿?

                #boundingbox_frame = tracking_results[0].plot()  Just in case we need to check the bounding boxes


                num_persons = len(tracking_results[0].boxes)
                out_image_msg = self.bridge.cv2_to_imgmsg(original_frame, "bgr8") #Transform again into ROS2 image.
                out_image_msg.header = msg.header    
                

                if(num_persons == 1):
                    id_match = "1 persona detectada con id " + str(tracking_results[0].boxes.id.int().cpu().tolist()) + "."
                
                else:
                    id_match = str(num_persons) + " personas detectadas con id" + str(tracking_results[0].boxes.id.int().cpu().tolist()) + "."
                


                id_match_msg = String()
                id_match_msg.data = id_match

                #Publish both image and id_match
                self.publisher_image.publish(out_image_msg)
                self.publisher_id_match.publish(id_match_msg)
                info_msg = "Frame sent to /detected_person_image : " + str(num_persons) + " person/persons detected with id"+ str(tracking_results[0].boxes.id.int().cpu().tolist()) + "."
                self.get_logger().info(info_msg)


            #Empty cache so node doesnt explode
            del tracking_results
            torch.cuda.empty_cache()


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
