#!/usr/bin/env python3

import os
import json
import time
import asyncio
import rclpy
import numpy as np
from collections import deque

from ollama import chat
from rclpy.node import Node 
from std_msgs.msg import String
from gtts import gTTS
from pygame import mixer




class HRINode(Node):

    def __init__(self):
        super().__init__("hri_node")


        #Temporary route for robot response audio file
        self.audio_dir = "/tmp/caji_audio"
        self.audio_path = os.path.join(self.audio_dir, "caji_reply.mp3")

        #Start audio player
        mixer.pre_init(24000, -16, 2, 4096)
        mixer.init()

        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
            self.get_logger().info(f"Directorio creado: {self.audio_dir}")

        #Inicialize list of 3 actions 
        self.actions = []

        #Inicialize State machine mode to PASIVE
        self.MODE = "PASIVE"
        
        #Create a String to concatenate messages to create a virtual memory for agent
        self.CHAT_HISTORY = ""

        #Create timer to check inactivity in conversations
        self.timeout_timer = None
        self.idle_timeout = 60.0


        #Subcriptions and publishers.
        self.action_predict_subscription = self.create_subscription(String, '/action_prediction', self.pasive_interaction, 1)
        self.user_speech_subscription = self.create_subscription(String,'/user_speach',self.active_interaction,1)

        self.chat_publisher = self.create_publisher(String, '/chat_history',10)

        #Node info
        self.get_logger().info("HRI node running...")


        #Configuration of LLM model
        self.LLM_MODEL  = 'gemma3:4b'
        self.LLM_FORMAT = 'json'

        #Options of model
        self.LLM_TEMPERATURE = 0.7
        self.LLM_TOP_P       = 0.9
        self.LLM_NUM_PREDICT = 175 

        #Prompt for the robot:

        self.promptRobot = """
### ROL
Eres Caji, un robot asistente inteligente, curioso y muy amable. Tu voz debe sonar natural y cercana, como la de un compañero que está en la misma habitación que el usuario.

### INSTRUCCIONES DE CONTEXTO
Para generar tu respuesta, debes realizar este proceso mental:
1. **Analiza el HISTORIAL**: Identifica de qué estáis hablando para no repetir saludos y mantener el hilo.
2. **Observa las ACCIONES RECIENTES**: Úsalas como contexto visual. Si el usuario cambia de actividad, puedes comentarlo de forma natural.
3. **Responde al MENSAJE DEL USUARIO**: Es tu prioridad actual, pero debe estar influenciada por los dos puntos anteriores.

### DATOS DE ENTRADA
- [HISTORIAL DE CHAT (Memoria)]: 
CLAVE_HISTORIAL

- [ACCIONES QUE VEO AHORA]: 
CLAVE_ACCIONES

- [MENSAJE DEL USUARIO A RESPONDER]: 
CLAVE_USUARIO

### REGLAS DE ORO (SALIDA ESTRICTA)
- Genera EXCLUSIVAMENTE el texto que dirás en voz alta.
- Máximo 2 frases cortas.
- NO uses etiquetas como "Caji:", "Robot:" ni "[ROBOT]".
- NO expliques por qué respondes eso ni des introducciones.
- Si el historial está vacío, preséntate brevemente; si ya hay charla, ve directo al grano.

RESPUESTA DE CAJI:
"""


    #Prompt for iniciating conversation:

        self.promptrobotInit = """ ### ROL
Eres Caji, un robot asistente curioso y muy amable. Tu función es iniciar conversaciones de forma natural, utilizando lo que observas como un "rompehielo" para conectar con el usuario.

### INSTRUCCIONES
1. **ANALIZA LA ACCIÓN**: Observa qué está haciendo el usuario.
2. **GENERA UN ROMPEHIELO**: Utiliza esa acción como pretexto para iniciar una interacción.
3. **TONO**: Debes sonar cercano y espontáneo, nunca robótico ni descriptivo.

### DATO DE ENTRADA
- [ACCIÓN DETECTADA]: 
CLAVE_ACCION_USUARIO

### REGLAS DE ORO
- Genera EXCLUSIVAMENTE el texto que dirás en voz alta.
- Máximo 2 frases cortas.
- NO describas la acción de forma clínica (evita decir "he detectado que estás...").
- Enfócate en el usuario (ej: "¿Cómo te va con eso?", "¿Necesitas ayuda con...?", "¡Qué interesante lo que haces!").
- NUNCA uses etiquetas de personaje ni introducciones.

"""


    #Create timer and send to change mode function / also used to reset timer every time a robot-send text is published in topic
    def reset_idle_timer(self):
        
        #Check an existing timer
        if self.timeout_timer is not None:
            self.timeout_timer.cancel()
        
        self.timeout_timer = self.create_timer(self.idle_timeout, self.go_to_pasive)
        self.get_logger().info("Timer de inactividad iniciado:"+ str(self.idle_timeout) +  ".")

    #Change mode to pasive if specified time has elapsed
    def go_to_pasive(self):

        
        self.get_logger().info("Tiempo de espera agotado. Volviendo a modo PASIVE.")
        self.MODE = "PASIVE"
        
        # Clean chat history could be good?
        self.CHAT_HISTORY = "" 
        
        
        if self.timeout_timer is not None:
            self.timeout_timer.cancel()


    #Tracking model function
    def pasive_interaction(self,msg):
 
        data   = json.loads(msg.data)
        accion = data.get("accion_final", "sin accion") 

        if (len(self.actions) == 3): 
            self.actions.pop(0)

        self.actions.append(accion)

        print("Acciones más actuales: ", self.actions)

        if self.MODE == "PASIVE":
            responseLlava = chat(
                model=self.LLM_MODEL,
                messages=[{'role': 'user', 'content': self.promptrobotInit}], 

                options={
                    'temperature': self.LLM_TEMPERATURE,  
                    'top_p': self.LLM_TOP_P,
                    'num_predict': self.LLM_NUM_PREDICT,
                },
            )

            robot_speach = responseLlava.message.content
            actual_message = "[ROBOT]: " + robot_speach + "\n"
            self.CHAT_HISTORY += actual_message
            
            self.get_logger().info("[ROBOT]:" + robot_speach)
            self.MODE = "ACTIVE"
            print("Actual mode: " + self.MODE)


            self.speak(robot_speach)

            #Reset timer
            self.reset_idle_timer()

    def active_interaction(self,msg):


        if self.MODE == "ACTIVE":
            user_speach = "[HUMAN]: " + msg.data + "\n"
            self.CHAT_HISTORY += user_speach
            print("Message recieved...") 



            #Change prompt including chat history, user message and actions
            promptFinal = self.promptRobot.replace("CLAVE_ACCIONES",str(self.actions))
            promptFinal = promptFinal.replace("CLAVE_HISTORIAL",self.CHAT_HISTORY)
            promptFinal = promptFinal.replace("CLAVE_USUARIO",msg.data)
            

            responseLlava = chat(
                model=self.LLM_MODEL,
                messages=[{'role': 'user', 'content': promptFinal}], 

                options={
                    'temperature': self.LLM_TEMPERATURE,  
                    'top_p': self.LLM_TOP_P,
                    'num_predict': self.LLM_NUM_PREDICT,
                },
            )


            robot_speach = responseLlava.message.content
            print("----------------------------------")
            print("[ROBOT]: " +robot_speach)
            print("----------------------------------")
            self.CHAT_HISTORY += "[ROBOT]" + robot_speach + "\n"


            self.speak(robot_speach)

            #Reset timer
            self.reset_idle_timer()
            


def main():

    rclpy.init()

    node = HRINode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
