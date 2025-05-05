import face_recognition
import cv2
import os
import pickle
#creating encoding function
def encode_faces(dataset_path='dataset/faces',model_save_path='model/face_encodings.pkl'):
    known_encodings=[]
    known_names=[]

    for filename in os.listdir(dataset_path):
        if filename.endswith('.jpg') or filename.endswith('png'):
            # Load the image file from the dataset folder for face recognition processing
            image = face_recognition.load_image_file(os.path.join(dataset_path,filename))
            #Gets face encoding
            encoding = face_recognition.face_encoding(image)[0]
            #add face encoding to list of encoding
            known_encodings.append(encoding)
            #extract name from the filename and add to list of known list
            known_names.append(filename.split('.')[0])

    #saving encoding
    with open(model_save_path, 'wb') as f:
        pickle.dump((known_encodings, known_names),f)
    print("[INFO] face encodings saved!")
def recognize_face():
    # Load encodings
    with open('models/face_encodings.pkl', 'rb') as f:
        known_encodings, known_names = pickle.load(f)

        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            boxes = face_recognition.face_locations(rgb_frame)
            encodings = face_recognition.face_encodings(rgb_frame, boxes)

            for encoding, box in zip(encodings, boxes):
                matches = face_recognition.compare_faces(known_encodings, encoding)
                name = "Unknown"

                if True in matches:
                    matchedIdx = matches.index(True)
                    name = known_names[matchedIdx]

                # Draw box and name
                top, right, bottom, left = box
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            cv2.imshow("Face Recognition", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

