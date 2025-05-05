from utils.face_recognition_utils import encode_faces
from utils.voice_recognition_utils import encode_voices
from utils.face_recognition_utils import recognize_face
from utils.voice_recognition_utils import recognize_voice
from utils.attendance_utils import mark_attendance

# Step 1: Recognize Face
print("[STEP 1] Please show your face to the camera and press 'q' when recognized.")
recognized_name = recognize_face()

# Step 2: Recognize Voice
print("[STEP 2] Please say 'Present' into the mic.")
recognized_voice = recognize_voice()

# Step 3: Verify Both
if recognized_name == recognized_voice and recognized_name != "Unknown":
    print("[SUCCESS] Face and Voice matched!")
    mark_attendance(recognized_name)
else:
    print("[FAILED] Face and Voice did not match.")

encode_faces()
encode_voices()
