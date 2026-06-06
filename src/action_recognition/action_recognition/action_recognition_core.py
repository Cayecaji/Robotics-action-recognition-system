#!/usr/bin/env python3

import cv2
import json
import time
import re
import os
import base64
import rclpy
import numpy as np

from ollama import chat
from ollama import Client
from ollama import list as list_models
from cv_bridge import CvBridge
from rclpy.node import Node 
from sensor_msgs.msg import Image
from std_msgs.msg import String
from rclpy.executors import MultiThreadedExecutor
from collections import Counter
from rclpy.callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup
from .prompts import PROMPT_SCENE_DESCRIPTION, PROMPT_ACTION_PREDICTION, PROMPT_VOTING



class ActionRecognitionNode(Node):

    def __init__(self):
        super().__init__("action_recognition_node") 
        self.bridge = CvBridge()

       # --- Params read from .yaml ---
        
        # Routes and predictions for models
        self.frames_route = self.declare_parameter('frames_route', '/home/cayecaji/image_frames').value
        self.nPrediccionesLVLM = self.declare_parameter('n_predicciones_lvlm', 3).value
        self.nPrediccionesLLM = self.declare_parameter('n_predicciones_llm', 5).value

        # Model selection and return format
        self.LVLM_MODEL = self.declare_parameter('lvlm_model', 'qwen2.5vl:7b').value
        self.LLM_MODEL  = self.declare_parameter('llm_model', 'llama3.2:3b').value
        self.FORMAT     = self.declare_parameter('format', 'json').value

        #LVLM configuration
        self.LVLM_TEMPERATURE = self.declare_parameter('lvlm_temperature', 0.7).value
        self.LVLM_TOP_P       = self.declare_parameter('lvlm_top_p', 0.85).value
        self.LVLM_NUM_PREDICT = self.declare_parameter('lvlm_num_predict', 175).value

        #LLM configuration (Action prediction)
        self.LLM_ACTION_TEMP        = self.declare_parameter('llm_action_temperature', 0.4).value
        self.LLM_ACTION_TOP_P       = self.declare_parameter('llm_action_top_p', 0.5).value
        self.LLM_ACTION_NUM_PREDICT = self.declare_parameter('llm_action_num_predict', 175).value

        #LLM configuration (Voting)
        self.LLM_VOTING_TEMP        = self.declare_parameter('llm_voting_temperature', 0.1).value
        self.LLM_VOTING_TOP_P       = self.declare_parameter('llm_voting_top_p', 0.5).value
        self.LLM_VOTING_NUM_PREDICT = self.declare_parameter('llm_voting_num_predict', 175).value

        # --- MultiThread config ---
        self.sensor_cb_group = ReentrantCallbackGroup()
        self.ai_cb_group = MutuallyExclusiveCallbackGroup()

        # --- Debug mode ---
        self.DEBUG_MODE = self.declare_parameter('debugging', False).value

        # --- Prompts for models ---
        self.promptLVLM = PROMPT_SCENE_DESCRIPTION
        self.promptLLM_SD = PROMPT_ACTION_PREDICTION
        self.promptLLM_Voting = PROMPT_VOTING

        # --- Utils ---
        self.idle_timeout = self.declare_parameter('idle_timeout', 3.0).value
        self.predict_frames_list = []
        self.id_match_list = []
        self.image_route_list = []
        self.json_files    = []
        self.final_actions = []
        self.all_predictions = []
        self.id_count = 1
        self.frame_id = 1
        self.ai_busy = False
        self.timeout_timer = None
        self.current_id = "No ID"
        

        # --- Subcriptions and publishers ---
        self.image_subscriber = self.create_subscription(Image, '/detected_person_image', self.image_callback, 1, callback_group=self.sensor_cb_group)
        self.id_subscriber    = self.create_subscription(String, '/person_id_match', self.id_callback, 1, callback_group=self.sensor_cb_group)
        self.action_publisher =   self.create_publisher(String, '/action_prediction', 1) 



        # --- Check if Ollama is available ---
        if not self.check_ollama_server():
            self.get_logger().fatal("Ollama server is not currently working. Shutting down node...")
            raise RuntimeError("Ollama Service Unavailable")
           

        # --- Running node info ---
        self.get_logger().info("Core node running...")


    def id_callback(self, msg):
        self.current_id = msg.data


    def image_callback(self, img_msg):

        #Check if action recognition is being processed
        if self.ai_busy:
            return
        self.recognition_core(img_msg, self.current_id)


    def recognition_core(self,img_msg, id_msg):
        
        #We want to predict the action of the first person captured by camera.
        if len(self.predict_frames_list) == 0:
            self.target_id = id_msg

        #Check if we have enough frame and if person id of frame is valid
        if(len(self.predict_frames_list) < 5):
            try:
                    frame = self.bridge.imgmsg_to_cv2(img_msg, "bgr8")
                    self.predict_frames_list.append(frame)
                    self.id_match_list.append("Frame " + str(self.id_count) + ": " + id_msg)
                    self.get_logger().info("    Image recieved...")
                    self.reset_idle_timer()
                    self.id_count +=1

            except Exception as e:
                    self.get_logger().error(f"Error reading image: {e}")
                    return
            
        

        if(len(self.predict_frames_list) == 5):


           # primary_id, id_consistency = self.validate_id_consistency()

            #if not id_consistency:
            #    self.get_logger().error("Couldn't predict action due to ID inconsistency.")
            #    self.reset_utils()
            #    return
            
            if self.timeout_timer is not None:
                self.timeout_timer.cancel()
                if self.DEBUG_MODE: self.get_logger().info("Starting predictions, timer canceled.")


            start_time = time.perf_counter()
            if self.DEBUG_MODE :self.get_logger().info("Iniciating prediction timer (s)...")
            #if self.DEBUG_MODE: self.get_logger().info("Predicting action of person with id["+ str(primary_id) + "].")

            self.ai_busy = True #Block incoming images
            self.id_count = 1
            if(self.DEBUG_MODE): print(self.id_match_list)
            for image in self.predict_frames_list:
                    
                    image_name = f"frame{self.frame_id}.jpg"
                    path = os.path.join(self.frames_route, image_name)
                    self.image_route_list.append(path)
                    cv2.imwrite(path, image)
                    self.frame_id +=1

            #Reset counter for future predictions
            self.frame_id = 1


            #Update prompt adding the ids info extracted from YOLO
            frame_id_info = get_frame_id_info(self.id_match_list)
            updatedLVLMprompt = self.promptLVLM.replace("INPUT_LVLM", frame_id_info)


            #Store images in variables instead of reading from drive
            frame_list = [self.frame_to_base64(f) for f in self.predict_frames_list]

            if self.DEBUG_MODE: self.debug_base64_image(frame_list)

            if(self.DEBUG_MODE): print(updatedLVLMprompt)
            print("------------------------------------------")


            #LVLM predictions
            for n in range (self.nPrediccionesLVLM):
                
                print("(LVLM): Prediction", n+1, "in course...")
                responseQwen = chat(
                    model= self.LVLM_MODEL,
                    messages=[{
                        'role': 'user',
                        'content': updatedLVLMprompt,
                        'images': [self.image_route_list[0],self.image_route_list[1],self.image_route_list[2],self.image_route_list[3],self.image_route_list[4]]
                    }],
                    format = self.FORMAT,
                    options={
                        'temperature': self.LVLM_TEMPERATURE,       
                        'top_p':  self.LVLM_TOP_P,                         
                        'num_predict': self.LVLM_NUM_PREDICT,     
                    },
                )
                
                #In case direct parse to JSON doesnt work
                """descripcion = re.findall(r'"descripcion_secuencia":\s*"([^"]+)"', responseQwen.message.content)
                acciones = re.findall(r'"accion":\s*"([^"]+)"', responseQwen.message.content)
                confianza = re.findall(r'"confianza":\s*"([^"]+)"', responseQwen.message.content)
                resultados = list(zip(descripcion,acciones, confianza))
                key = "Predicción " + str(v+1)
                results.update({key : resultados})"""


                #String to JSON parser
                try:
                    data = json.loads(responseQwen.message.content)
                    self.json_files.append(data)
                except:

                    if responseQwen.message.content == None:
                        self.error_empty_output(self.LLM_MODEL)
                    self.get_logger().info("Model didn't return clean JSON file:")
                    
                #Prediction end
                print(" Prediction" ,n+1 , "ended.")
                



        #********OUT OF LOOP**********

            lvlm_predictions = get_scene_descriptions(self.json_files)
            promptLLM = self.promptLLM_SD.replace("INPUT_LLM", lvlm_predictions)


            print("------------------------------------------")
            if(self.DEBUG_MODE): print(promptLLM)

            for n in range(self.nPrediccionesLLM):

                print("(LLM): Prediction" ,n+1, "in course...")
                responseLlava = chat(
                model=self.LLM_MODEL,
                messages=[{'role': 'user', 'content': promptLLM}],

                format=self.FORMAT,  

                options={
                    'temperature': self.LLM_ACTION_TEMP,  
                    'top_p': self.LLM_ACTION_TOP_P,
                    'num_predict': self.LLM_ACTION_NUM_PREDICT,
                },
            )
                

                #String to JSON parser
                try:
                    data = json.loads(responseLlava.message.content)
                    self.final_actions.append(data)
                except:
                    if responseLlava.message.content == None:
                        self.error_empty_output(self.LVLM_MODEL)
                    self.get_logger().info("Model didn't return clean JSON file:")
                    
                #Prediction end
                print(" Prediction", n+1 , "ended.")
                print(responseLlava.message.content)

            #Get final predictions
            actions_predictions = get_action_predictions(self.final_actions)
            promptVote = self.promptLLM_Voting.replace("INPUT_VOTING", actions_predictions)

            print("------------------------------------------")
            if(self.DEBUG_MODE): print(promptVote)

            print("(Voting Model): Predicting final decision...")
            responseVoting = chat(
            model=self.LLM_MODEL,
            messages=[{'role': 'user', 'content': promptVote}],

            format=self.FORMAT,  

            options={
                    'temperature': self.LLM_VOTING_TEMP,  
                    'top_p': self.LLM_VOTING_TOP_P,
                    'num_predict': self.LLM_VOTING_NUM_PREDICT,
            },
            )



            """#String to JSON parser
            try:
                    data = json.loads(responseVoting.message.content)
            except:
                    self.get_logger().info("Model didn't return clean JSON file:")"""
            

            if responseVoting.message.content == None:
                        self.error_empty_output(self.LLM_MODEL)



            print("------------------------------------------")

            end_time = time.perf_counter()
            total_duration = end_time - start_time
            self.get_logger().info(f"Full processing time: {total_duration:.3f}s.")

            print("------------------------------------------")
            print("Final prediction:")
           

            final_prediction = self.confidence_filter(responseVoting.message.content)
            print(final_prediction)

            data   = json.loads(final_prediction)
            action = data.get("accion_final", "unknown")
            self.all_predictions.append(action)
            print("------------------------------------------")
            print("Predictions made so far: ", self.all_predictions)
            print("------------------------------------------")
            #Publish final prediction
            msg = String()
            msg.data = final_prediction
            self.action_publisher.publish(msg)

            #Clear the lists and reset vars for other predictions
            self.reset_utils()

    # ---- Some useful functions ----

    def confidence_filter(self,llm_voting_pred):
        try:
            data = json.loads(llm_voting_pred)
            votos_raw = str(data.get("conteo_votos", "0"))
            match = re.search(r'\d+', votos_raw)
            conteo_mayoritario = int(match.group()) if match else 0
            
            if conteo_mayoritario <= 2:
                self.get_logger().info(f"Mayoritary decision was not reached ("+ str(conteo_mayoritario) +"/5). Unknown action.")
                data["accion_final"] = "unknown"

            return json.dumps(data, ensure_ascii=False)

        except Exception as e:
            self.get_logger().error(f"Error processing JSON : {e}")
            return json.dumps({"accion_final": "unknown", "error": "fallo_en_parseo"})
        
    def check_ollama_server(self):
        try:
            list_models()
            self.get_logger().info("Conection established with Ollama server.")
            return True
        except Exception as e:
            self.get_logger().error(f"Couldn't connect to Ollama: {e}")
            return False
        

    def validate_id_consistency(self):
        if not self.id_match_list:
            return None, False

        ids = [msg.split(": ")[1] for msg in self.id_match_list]
        
        conteo = Counter(ids)
        id_dominante, num_apariciones = conteo.most_common(1)[0]
        
        if num_apariciones >= 4:
            if self.DEBUG_MODE: self.get_logger().info(f"At least 4 IDs where equal: " + str(id_dominante) + " (" + str(num_apariciones) +"/5)")
            return id_dominante, True
        else:
            self.get_logger().warn(f"There where not enough equal IDs: {conteo}. Aborting prediction.")
            return None, False
        
    def reset_idle_timer(self):
        
        #Check if predicting
        if self.ai_busy:
            return
        
        #Check an existing timer
        if self.timeout_timer is not None:
            self.timeout_timer.cancel()
        
        self.timeout_timer = self.create_timer(self.idle_timeout, self.reset_utils)
        if self.DEBUG_MODE: self.get_logger().info("Inactivity timer iniciated:"+ str(self.idle_timeout) +  ".")

    def  error_empty_output(self,model):
        self.get_logger.info("The model " + model + " returned an empty message, aborting prediction...")
        self.reset_utils()
        return
    
    def frame_to_base64(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')
    


    def debug_base64_image(self, b64_list):
        self.get_logger().info(f"Guardando {len(b64_list)} imágenes de debug desde Base64...")
        for i, b64_string in enumerate(b64_list):
            try:
               
                img_data = base64.b64decode(b64_string)
                nparr = np.frombuffer(img_data, np.uint8)
                img_check = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img_check is not None:
                    debug_path = os.path.join(self.frames_route, f"debug_b64_frame_{i}.jpg")
                    cv2.imwrite(debug_path, img_check)
                else:
                    self.get_logger().error(f"No se pudo decodificar la imagen de debug {i}")
                    
            except Exception as e:
                self.get_logger().error(f"Error en debug_base64_image al procesar el frame {i}: {e}")

        
    def reset_utils(self):
        
        if self.DEBUG_MODE:  self.get_logger().info("Clearing all lists an resetting utils...")
        self.get_logger().info("Resetting images due to INACTIVITY...")
        

        self.ai_busy = False
        self.predict_frames_list.clear()
        self.image_route_list.clear()
        self.json_files.clear()
        self.final_actions.clear()
        self.id_match_list.clear()


# ---- Some getters ----

def get_frame_id_info(id_info):
    frame_info_index = 1
    result = ""
    for frame_info in id_info:
        result += str(frame_info_index) + ". " + frame_info + "\n"
        frame_info_index +=1

    return result

def get_scene_descriptions(lvlm_outputs):
    prediction_index = 1
    result = ""
    for file in lvlm_outputs:
        result += "Predicción " + str(prediction_index) + ":\n"
        result += str(file) + "\n"
        prediction_index += 1

    return result


def get_action_predictions(action_predictions):
    pred_string = ""
    i=1
    for action in action_predictions:
        pred_string += str(i) + ". " + action['accion_final'] + ".\n"
        i+=1
    return pred_string


def main():
    rclpy.init()
    node = ActionRecognitionNode()
    
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
