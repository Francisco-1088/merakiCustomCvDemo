from tkinter import *
from PIL import Image,ImageTk
import config

import paho.mqtt.client as mqtt
import json
from collections import Counter

# Parse label_map.pbtxt into classes variable
f = open('label_map.pbtxt')
lines = f.readlines()
new_lines = []
for line in lines:
    line = line.replace(" ","")
    line = line.replace("\n","")
    line = line.replace("}", "")
    line = line.replace("name:","")
    line = line.replace("id:", "")
    line = line.replace("'", "")
    line = line.replace("item{","")
    if line != "":
        new_lines.append(line)

if len(new_lines)%2 == 0:
    keys = new_lines[::2]
    values = new_lines[1::2]
    classes = dict(zip(keys, values))
    print(classes)

# Parameters
max_classes = config.max_classes
mqtt_server = config.mqtt_server
det_threshold = config.app_det_threshold

#Have to run these in computer
#docker pull ecplipse-mosquitto:1.6
#docker run -p 1883:1883 eclipse-mosquitto:1.6

# Set up GUI
window = Tk()
window.title("Meraki Custom CV Dashboard")
window.geometry('395x600')
window.resizable(False, False)
window.configure(bg="white")
canvas = Canvas(window, bg="white", width=395, height=135)
canvas.place(x=0, y=0)
img = (Image.open("logo.png"))

resized_image = img.resize((400, 162), Image.ANTIALIAS)
new_image = ImageTk.PhotoImage(resized_image)
canvas.create_image(0, 0, anchor=NW, image=new_image)

canvas2 = Canvas(window, width=250, height=218)
canvas2.place(x=5, y=165)
img2 = (Image.open("cam.png"))
resized_image2 = img2.resize((156, 125), Image.ANTIALIAS)
new_image2 = ImageTk.PhotoImage(resized_image2)
canvas2.create_image(20, 20, anchor=NW, image=new_image2)


gui_label_dict = {}
title = Label(window,text="MV Custom CV Detections:", bg="white", fg="black", font=("Helvetica, 32"))
title.place(x=0, y=140)

for i in range(max_classes):
    gui_label_dict[f"label_{i}"] = [Label(window,
       text=f" label {i}",
       bg="white",
       fg="black",
       font=("Helvetica", 32)),"blank"]
    gui_label_dict[f"label_{i}"][0].place(x=185, y=200+(50*i))


def on_connect(client, userdata, flags, rc):
    """
    The callback for when the client receives a CONNACK response from the server.
    """
    print("Connected with result code " + str(rc))
    client.subscribe("/merakimv/Q2NV-47D4-38T2/custom_analytics/#")


def on_disconnect(client, userdata, flags, rc=0):
    """
    MQTT disconnect
    """
    print("DISconnected with result code " + str(rc))


def on_log(client, userdata, level, buf):
    """
    MQTT logs
    """
    print("log: " + buf)


def on_message(client, userdata, msg):
    """
    The callback for when a PUBLISH message is received from the server.
    """
    data = json.loads(msg.payload.decode('utf-8'))
    split_topic = msg.topic.split("/", 3)
    mqtt_topic = str(split_topic[3])

    # based on the MQTT topic, output the parameters

    print(data)

    counter = Counter((x['class']) for x in data['outputs'] if x['score']>=det_threshold)
    #print(Counter((x['class']) for x in data['outputs']))
    #print(data)
    i = 0
    existing_labels = [gui_label_dict[f"label_{x}"][1] for x in range(max_classes)]
    print("Labels tracked: ", existing_labels)
    labels_in_msg = list(counter.keys())
    print("Labels seen: ",labels_in_msg)

    for label in labels_in_msg:
        if label not in existing_labels:
            for i in range(len(existing_labels)):
                if existing_labels[i]=="blank":
                    existing_labels[i]=label
                    gui_label_dict[f"label_{i}"][1]=label
                    gui_label_dict[f"label_{i}"][0].config(
                        text=str(counter[label]) + f" {classes[str(label)]}",
                        fg="black")
                    break
        elif label in existing_labels:
            x = existing_labels.index(label)
            gui_label_dict[f"label_{x}"][0].config(
                text=str(counter[label]) + f" {classes[str(label)]}",
                fg="black")

    for label in existing_labels:
        if (label not in labels_in_msg) and (label != "blank"):
            x = existing_labels.index(label)
            gui_label_dict[f"label_{x}"][0].config(
                text=str(0) + f" {classes[str(label)]}",
                fg="black")


if __name__ == "__main__":

    try:
        print("Start MQTT")
        client = mqtt.Client(client_id="pythonscript", protocol=mqtt.MQTTv311)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        # client.on_log = on_log
        client.on_message = on_message
        client.connect(mqtt_server, port=1883)

        # run the MQTT connection forever
        client.loop_start()
        window.mainloop()
        client.loop_stop()

    except Exception as e:
        print("MQTT Connection error: {}".format(e))

