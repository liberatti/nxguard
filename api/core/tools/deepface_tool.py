import os
import numpy as np
import cv2
import logging
from deepface import DeepFace
from api.core.tools.image_tool import ImageTool

class DeepFaceTool:
    def __init__(self):
        logging.getLogger('deepface').setLevel(logging.ERROR)
        logging.getLogger('tensorflow').setLevel(logging.ERROR)
        logging.getLogger('numpy').setLevel(logging.ERROR)
        logging.getLogger('PIL').setLevel(logging.ERROR)
        
        self.current_model = 'VGG-Face'
        self.current_threshold = 0.5
        self.current_align = True
        self.current_enforce_detection = False
        self.current_detector_backend = 'retinaface'
        #self.current_db_path = f"/app/data/{account_id}"
        self.current_db_path = f"data/facedb"
        os.makedirs(self.current_db_path, exist_ok=True)

    def get_person_id(self, path,account_id):
        """
        Extract the person's ID from a full path.
        """
        if path is None:
            return None
        relative_path = path.replace(f"{self.current_db_path}/{account_id}")
        return relative_path.split('/')[0]

    def identify_faces(self, img_input,account_id):
        """
        Identify faces in an image, accepting either a file path or image bytes.
        
        Args:
            img_input: Either a string path to an image file or bytes containing image data
        """

        if isinstance(img_input, bytes):
                nparr = np.frombuffer(img_input, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    return
                img_path = img
        else:
                img_path = img_input
        try:
            dfs = DeepFace.find(
                img_path = img_path,
                db_path = f"{self.current_db_path}/{account_id}", 
                model_name = self.current_model,
                enforce_detection=self.current_enforce_detection,
                detector_backend=self.current_detector_backend
            )
            if not isinstance(dfs, list):
                    dfs = [dfs]
            for idx, df in enumerate(dfs):
                    if not df.empty:
                        for _, row in df.iterrows():
                            if row['threshold'] >= self.current_threshold:
                                return self.get_person_id(row['identity'],account_id)
                    return None
        except Exception as e:
            return None

    
    
    def extract_faces(self,img_input):
            """
            Extract faces from an image byte array and return them as an array of bytearrays.
            
            Args:
                image_bytes (bytes): Image data as bytes
                
            Returns:
                list: List of bytearrays, each containing a face image
            """
            result = []


            if isinstance(img_input, bytes):
                    nparr = np.frombuffer(img_input, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        return
                    img_path = img
            else:
                    img_path = img_input
                            
            faces = DeepFace.extract_faces(
                img_path=img_path,
                detector_backend='retinaface',
                enforce_detection=True,
                align=True
                )
            
            if not faces:
                return []
            
            result = []
            for idx, face in enumerate(faces):
                if face['confidence'] >= self.current_threshold:
                    face_img = face['face']               
                    if face_img.dtype != np.uint8:
                        face_img = np.clip(face_img, 0, 1)
                        face_img = (face_img * 255).astype(np.uint8)
                    else:
                        face_img = np.clip(face_img, 0, 255).astype(np.uint8)
                    face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
                    face_img = cv2.resize(face_img, (224, 224))
                    meta={
                        'face': face_img,
                        'area': {
                            "h":face['facial_area']['h'],
                            "w":face['facial_area']['w'],
                            "x":face['facial_area']['x'],
                            "y":face['facial_area']['y']
                        },
                        'hash': ImageTool._gen_hash(face_img)
                    }
                    result.append(meta)
            return result
    def save_face(self,people_id,face,account_id):
        output_path =  f"{self.current_db_path}/{account_id}/{people_id}"
        os.makedirs(output_path, exist_ok=True)
        if "face_b64" in face:
            face_img = ImageTool._from_64(face['face_b64'])
        else:
            face_img = face['face']
        
        cv2.imwrite(f"{output_path}/{face['hash']}.png", face_img)
        return output_path

    def get_face(self, person_id, face_hash,account_id):
        """
        Read a face image from disk and return it as base64.
        
        Args:
            person_id (str): The ID of the person
            face_hash (str): The hash of the face image
            
        Returns:
            str: Base64 encoded face image or None if not found
        """
        face_path = f"{self.current_db_path}/{account_id}/{person_id}/{face_hash}.png"
        if not os.path.exists(face_path):
            return None
            
        img = cv2.imread(face_path)
        if img is None:
            return None
            
        return img