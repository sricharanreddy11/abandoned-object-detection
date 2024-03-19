import cv2
import numpy as np
import time
import sys
import winsound
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from twilio.rest import Client


CONFIDENCE = 0.5
SCORE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5
config_path = "./yolov3-tiny.cfg"
weights_path = "./yolov3-tiny.weights"
font_scale = 1
thickness = 1
labels = open("./coco.names").read().strip().split("\n")
colors = np.random.randint(0, 255, size=(len(labels), 3), dtype="uint8")

net = cv2.dnn.readNetFromDarknet(config_path, weights_path)

ln = net.getLayerNames()
try:
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
except IndexError:
    # in case getUnconnectedOutLayers() returns 1D array when CUDA isn't available
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]
# read the file from the command line
# video_file = sys.argv[1]
cap = cv2.VideoCapture(0)
cap.set(3, 720)
cap.set(4, 640)
_, image = cap.read()
h, w = image.shape[:2]
fourcc = cv2.VideoWriter_fourcc(*"XVID")
out = cv2.VideoWriter("output_live.avi", fourcc, 20.0, (w, h))


# Define the path to the sound file
sound_file = "alert.wav"


def store_image():
    image_filename = f"static/abandoned_object_{time.strftime('%Y%m%d%H%M%S')}.jpg"
    cv2.imwrite(image_filename, image)

    return image_filename


def play_buzzer():
    winsound.PlaySound(sound_file, winsound.SND_ASYNC)


def sms_alert(to, body):
    account_sid = "AC9073349faa6c452b183145f47dxxxxxx"
    auth_token = "3cf0be99e4359c68028aba5a09xxxxxx"
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=body,
        from_="+19165128xxx",
        to=to
    )
    print(message.sid)


def email_alert(subject, body, to, image_path=None):
    msg = MIMEMultipart()
    msg.attach(MIMEText(body, 'plain'))
    msg['subject'] = subject
    msg['to'] = to
    user = "noreply.alertabandonedbag@gmail.com"
    msg['from'] = user
    password = "umtquekarfsoaudi"

    if image_path:
        with open(image_path, 'rb') as fp:
            img_data = fp.read()
        image = MIMEImage(img_data, name=image_path.split('/')[-1])
        msg.attach(image)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(user, password)
    server.send_message(msg)
    server.quit()


abandoned_objects = {}
threshold_for_abandonment = 30  # in sec
new_object_threshold = 50  # in px
threshold_for_person = 500  # in px


# Function to calculate distance between two boxes
def box_distance(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    # Calculate distance based on center points of the boxes
    distance = np.sqrt(((x1 + w1 / 2) - (x2 + w2 / 2)) ** 2 + ((y1 + h1 / 2) - (y2 + h2 / 2)) ** 2)
    return distance


while True:
    _, image = cap.read()

    h, w = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    start = time.perf_counter()
    layer_outputs = net.forward(ln)
    time_took = time.perf_counter() - start
    print("Time took:", time_took)
    boxes, confidences, class_ids = [], [], []

    # loop over each of the layer outputs
    for output in layer_outputs:
        # loop over each of the object detections
        for detection in output:
            # extract the class id (label) and confidence (as a probability) of
            # the current object detection
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            # discard weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if labels[class_id] in ("handbag", "suitcase", "backpack", "person") and confidence > CONFIDENCE:
                # play_buzzer()
                # image_name = store_image()
                # email_alert("Abandoned object detected!", "Immediate Attention Needed!!!",
                #             "charanreddy5611@gmail.com", f"./static/{image_name}")
                # sms_alert("+917288004377", "Abandoned Object Detected, Immediate Attention Needed")
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[:4] * np.array([w, h, w, h])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # perform the non maximum suppression given the scores defined before
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, SCORE_THRESHOLD, IOU_THRESHOLD)

    font_scale = 1
    thickness = 1

    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates
            x, y = boxes[i][0], boxes[i][1]
            w, h = boxes[i][2], boxes[i][3]
            # draw a bounding box rectangle and label on the image
            color = [int(c) for c in colors[class_ids[i]]]
            cv2.rectangle(image, (x, y), (x + w, y + h), color=color, thickness=thickness)
            text = f"{labels[class_ids[i]]}: {confidences[i]:.2f}"
            # calculate text width & height to draw the transparent boxes as background of the text
            (text_width, text_height) = \
            cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontScale=font_scale, thickness=thickness)[0]
            text_offset_x = x
            text_offset_y = y - 5
            box_coords = ((text_offset_x, text_offset_y), (text_offset_x + text_width + 2, text_offset_y - text_height))
            overlay = image.copy()
            cv2.rectangle(overlay, box_coords[0], box_coords[1], color=color, thickness=cv2.FILLED)
            # add opacity (transparency to the box)
            image = cv2.addWeighted(overlay, 0.6, image, 0.4, 0)
            # now put the text (label: confidence %)
            cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=font_scale, color=(0, 0, 0), thickness=thickness)

            # Check if the object is handbag, suitcase, or backpack
            if labels[class_ids[i]] in ("handbag", "suitcase", "backpack"):
                obj_id = None
                min_distance = float('inf')
                # Find the closest existing object to the current detection
                for key, val in abandoned_objects.items():
                    distance = box_distance(key, boxes[i])
                    if distance < min_distance:
                        min_distance = distance
                        obj_id = key

                if obj_id is not None and min_distance < new_object_threshold and obj_id in abandoned_objects:
                    # Object found within threshold distance, update properties
                    abandoned_objects[obj_id]['last_seen'] = time.time()
                    if abandoned_objects[obj_id]['abandoned'] and (
                            time.time() - abandoned_objects[obj_id]['abandoned_time']) > threshold_for_abandonment:
                        print("Abandoned object detected!")
                        play_buzzer()
                        image_name = store_image()
                        if len(sys.argv) > 1:
                            email_str = sys.argv[1]
                            trigger_emails = email_str.split(',')
                            print(trigger_emails)
                            # sms_alert("+917288004377", "Abandoned Object Detected, Immediate Attention Needed")
                            email_alert("Abandoned object detected!", "Immediate Attention Needed!!!",
                                        "charanreddy5611@gmail.com", f"./{image_name}")
                            for email in trigger_emails:
                                email_alert("Abandoned object detected!", "Immediate Attention Needed!!!",
                                            email, f"./{image_name}")
                else:
                    abandoned_objects[tuple(boxes[i])] = {'last_seen': time.time(), 'abandoned': False}

                # Check if the object is surrounded by a person
                surrounded_by_person = False
                for j in idxs.flatten():
                    if j != i and labels[class_ids[j]] == "person":
                        person_x, person_y = boxes[j][0], boxes[j][1]
                        person_w, person_h = boxes[j][2], boxes[j][3]
                        # Calculate distance between object and person
                        distance = np.sqrt((x - person_x) ** 2 + (y - person_y) ** 2)
                        # If person is within certain distance, object is not abandoned
                        if distance < threshold_for_person:
                            surrounded_by_person = True
                            # print("person_detected")
                            break

                if obj_id is not None and not surrounded_by_person:
                    if not abandoned_objects[obj_id]['abandoned']:
                        abandoned_objects[obj_id]['abandoned'] = True
                        abandoned_objects[obj_id]['abandoned_time'] = time.time()
    out.write(image)
    cv2.imshow("image", image)

    if ord("q") == cv2.waitKey(1):
        break

cap.release()
cv2.destroyAllWindows()