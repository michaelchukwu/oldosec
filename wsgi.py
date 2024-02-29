from flask import Flask, render_template, Response
import cv2
import cloudinary
import cloudinary.uploader
from datetime import datetime
import uuid
import requests
import numpy as np
import textwrap

app = Flask(__name__)

# Configure Cloudinary
cloudinary.config(
  cloud_name="dycfnmgfi",
  api_key="916318845173418",
  api_secret="8mNWugQCEm3iMWI3eiYYjRZqO1U"
)

# Initialize OpenCV face recognizer and cascade classifier
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer.yml')
cascadePath = "Cascades/haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)

font = cv2.FONT_HERSHEY_SIMPLEX

id=0
# find a way to automate this to be dynamic 
names = ['None', 'Emeka', 'Nnamdi', 'Ilza', 'Z', 'W'] 
# Define min window size to be recognized as a face
minW = 0.1 * 640
minH = 0.1 * 480

# Underdog API endpoint for minting CNFTs
underdog_api_url = "https://devnet.underdogprotocol.com/v2/projects/1/nfts"

def generate_frames():
    # Initialize webcam
    cam = cv2.VideoCapture(0)

    while True:
        # Capture frame-by-frame
        ret, frame = cam.read()

        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(int(minW), int(minH)))

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            id, confidence = recognizer.predict(gray[y:y + h, x:x + w])

            # Check if confidence is less than 100 ==> "0" is perfect match
            if confidence < 100:
                id = names[id]
                confidence = "  {0}%".format(round(100 - confidence))
            else:
                # Take a photo of the face when confidence level is low
                face_image = frame[y:y + h, x:x + w]

                # Generate unique ID and timestamp
                unique_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                file_name = f"possible_intruder_{timestamp}_{unique_id}.jpg"

                # Save the photo to a temporary file
                cv2.imwrite(file_name, face_image)

                # Upload the image to Cloudinary
                upload_result = cloudinary.uploader.upload(file_name)

                # Get the URL of the uploaded image
                image_url = upload_result['url']

                print("Uploaded image URL:", image_url)
                payload = {
                    "name": "Intruder-"+textwrap.shorten(unique_id, 5),
                    "symbol": "CNFT",
                    "description": "CNFT created using face recognition",
                    "image": image_url,
                    "attributes": {
                        "confidence": round(100 - confidence),
                        "timestamp": timestamp,
                        "unique_id": unique_id
                    },
                    "receiver": {
                        "address": "7px1aXrdcySNHEF8aQ12iHBW5a2MVsqQU1ELkTdYAgjN",
                        "namespace": "public",
                        "identifier": "kevin@underdogprotocol.com"
                    },
                    "receiverAddress": "dustFPTV7dujoJjgkKtf6is3bYaFEy1nswS23vxHfvt",
                    "delegated": True,
                    "upsert": True
                }
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "authorization": "Bearer 4143d54b376531.47b23e99a32d48329f2f9e24e32ad6ee"
                }

                response = requests.post(underdog_api_url, json=payload, headers=headers)
                print(response.text)

            cv2.putText(frame, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
            cv2.putText(frame, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the frame in the response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # Release the webcam when finished
    cam.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)
