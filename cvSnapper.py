import meraki
import requests
import os
import random
from PIL import Image
from io import BytesIO
import time
import psutil
import shutil
import config

api_key = config.api_key
camera_serial = config.camera_serial

win_or_mac = "mac" # Set to win if on windows
if win_or_mac == 'mac':
  img_close = 'Preview'
elif win_or_mac == 'win':
  img_close = 'display'

dashboard = meraki.DashboardAPI(api_key)

# Import config and set up environment
desired_snaps = config.desired_snaps
train_test_split = config.train_test_split
dataset_name = config.dataset_name
snap_count = 0
path = f"./{dataset_name}/images"

# Make directory structure
if not os.path.exists(dataset_name):
  os.makedirs(dataset_name)
if not os.path.exists(f"{dataset_name}/images"):
  os.makedirs(f"{dataset_name}/images")
if not os.path.exists(f"{dataset_name}/images/train"):
  os.makedirs(f"{dataset_name}/images/train")
if not os.path.exists(f"{dataset_name}/images/test"):
  os.makedirs(f"{dataset_name}/images/test")

# Keep taking snapshots until you accumulate a total equal to desired snaps
while snap_count < desired_snaps:
  enter = input("Press Enter to capture snapshot:")
  if enter == "":
    snapshot = dashboard.camera.generateDeviceCameraSnapshot(serial=camera_serial)
    time.sleep(5)
    response = requests.get(snapshot['url'])
    img = Image.open(BytesIO(response.content))
    img.show()
    keep = input("Keep image? (Y/N): ")

    if keep == 'Y':
      snap_count = snap_count + 1
      img.convert('RGB')
      img.save(f"./{dataset_name}/images/snap_{snap_count}.jpg")
      for proc in psutil.process_iter():
        if proc.name() == img_close:
          proc.kill()
    elif keep == 'N':
      for proc in psutil.process_iter():
        if proc.name() == img_close:
          proc.kill()
      cont = input("Do you wish to continue taking snapshots? (Y/N): ")
      if cont =='Y':
        continue
      elif cont =='N':
        exit()
  else:
    exit()

# Split captured images into train, test sets
f = []
for (dirpath, dirnames, filenames) in os.walk(path):
    f.extend(filenames)
    break
f.sort()

random.seed(42)
random.shuffle(f) # shuffles the ordering of filenames (deterministic given the chosen seed)

split_1 = int(train_test_split * len(f))
train_filenames = f[:split_1]
test_filenames = f[split_1:]

for image in train_filenames:
    os.rename(f"{path}/{image}",f"{path}/train/{image}")

for image in test_filenames:
    os.rename(f"{path}/{image}",f"{path}/test/{image}")
