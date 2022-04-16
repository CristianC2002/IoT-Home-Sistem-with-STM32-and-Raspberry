import os
import pickle
import cv2
import numpy as np
import time
# Utilidades de la API de Gmail
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# codificar/decodificar mensajes en base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.encoders import encode_base64
# para tratar con tipos MIME adjuntos
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#from email.mime.image import MIMEImage
#from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

#--------------DATOS GRABACION--------------
EMPIEZA_CONTEO = time.time()   # conteo para finalizar grabacion
TEMPORIZADOR_GRABACION = 20    # tiempo de ejecucion del programa

URL = 'rtsp://192.168.0.7:8080/h264_ulaw.sdp' # URL camara IP
CAPTURA = cv2.VideoCapture(URL)

FPS = CAPTURA.get(cv2.CAP_PROP_FPS)
ANCHO = int(CAPTURA.get(cv2.CAP_PROP_FRAME_WIDTH))
ALTO = int(CAPTURA.get(cv2.CAP_PROP_FRAME_HEIGHT))
FORMATO = cv2.VideoWriter_fourcc('X','2','6','4')
VIDEO_SALIDA = cv2.VideoWriter('GRABACION.avi', FORMATO, FPS, (ANCHO,ALTO))

#-----------DATOS ENVIO CORREO------------------

SCOPES = ['https://mail.google.com/']

RUTA_GRABACION = "/home/pi/Desktop/MAESTRO/GRABACION.avi"

CORREO_MAESTRO = 'iot.e.bot21@gmail.com'
CORREO_DESTINO = "dgomezbernal24@gmail.com"
ASUNTO_MSG = "PRUEBA DE ENVIO"
CUERPO_MSG = "PRUEBA ENVIO DE VIDEO AL CORREO MEDIANTE A API GMAIL"

#-------------------------------------------------

def gmail_authenticate():
    creds = None
    # el archivo token.pickle almacena los tokens de acceso y actualización del usuario, y es
    # creado automáticamente cuando el flujo de autorización se completa por primera vez
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # si no hay credenciales disponibles, permita que el usuario inicie sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('CREDENCIALES.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # guardar las credenciales para la próxima ejecución
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# obtener el servicio API de Gmail
service = gmail_authenticate()

# Agrega el archivo adjunto con el nombre de archivo dado al mensaje dado
def add_attachment(message, filename):

    content_type, encoding = guess_mime_type(filename)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)

    fp = open(filename, 'rb')
    msg = MIMEBase(main_type, sub_type)

    msg.set_payload(fp.read())
    fp.close()
    encode_base64(msg)#super importante esta joda o se manda el video corrompido (verde todo)

    msg.add_header('Content-Disposition', 'attachment', filename ='VIDEO GRABADO.mp4' )
    message.attach(msg)

def build_message(CORREO_DESTINO, ASUNTO, body, attachments=[]):

    message = MIMEMultipart()

    message['to'] = CORREO_DESTINO
    message['from'] = CORREO_MAESTRO
    message['subject'] = ASUNTO

    message.attach(MIMEText(body))

    for filename in attachments:
        add_attachment(message, filename)

    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

def ENVIO_CORREO(service, CORREO_DESTINO, ASUNTO, body, attachments=[]):
    return service.users().messages().send(
      userId="me",
      body=build_message(CORREO_DESTINO, ASUNTO, body, attachments)
    ).execute()

def CAP_VIDEO():
   
    DETENER = False
    EMPIEZA_CONTEO = 0.0
    EMPIEZA_CONTEO = time.time() 
    
    while True:
              
        ret, FRAME = CAPTURA.read()
        
        if (ret == 1):         
            print("GRABANDO")       
            print("FPS = "   + str(FPS))
            print("ANCHO = " + str(ANCHO))
            print("ALTO = "  + str(ALTO))            
        
            VIDEO_SALIDA.write(FRAME)
            cv2.imshow('VIDEO', FRAME)               
            TRASCURRIDO = time.time() - EMPIEZA_CONTEO
            
            if TRASCURRIDO > TEMPORIZADOR_GRABACION:
                DETENER = True
                print("PASARON " + str(TRASCURRIDO) + " SEGUNDOS")
                
        else:
            break
        
        if (cv2.waitKey(1) & DETENER == True):
            
            print("CAPTURA DE VIDEO FINALIZADO ")
            DETENER = False
            EMPIEZA_CONTEO = 0.0
            EMPIEZA_CONTEO = time.time()
            ret = True
            TRASCURRIDO = 0.0                  
            break
    
    CAPTURA.release()
    VIDEO_SALIDA.release()
    cv2.destroyAllWindows()    

if __name__ == '__main__':

    CAP_VIDEO()
    print("SE CERRO PROGRAMA DE GRABACION EMPEZANDO ENVIO DE CORREO ") 
    ENVIO_CORREO(service, CORREO_DESTINO, ASUNTO_MSG, CUERPO_MSG, [RUTA_GRABACION])
    exit(1)
