from hmac import new
import pickle

import re
from tkinter import filedialog
from typing import ByteString

def load_images():
    filename = filedialog.askopenfilename(filetypes=[("Pickle files", "*.pickle")])
    with open(filename, 'rb') as f:
        images = pickle.load(f)
    return images

def save_images(images):
    with open('modified_images.pickle', 'wb') as f:
        pickle.dump(images, f)

import tkinter as tk
from PIL import Image, ImageTk
from io import BytesIO


def load_next_image():
    global current_image_key
    current_image_key = next(image_keys)
    image_data = images[current_image_key]
    try:
        image = Image.open(BytesIO(current_image_key))
    except:
        print("Error loading image:")
        print(current_image_key)
        images.pop(current_image_key)
        return

    # Update the image label
    tk_image = ImageTk.PhotoImage(image)
    image_label.config(image=tk_image)
    image_label.image = tk_image

    # Update the text entry
    text_entry.delete(0, tk.END)
    text_entry.insert(0, image_data)

def save_current_label():
    new_label = int(text_entry.get())
    images[current_image_key] = new_label

# Load the images
images = load_images()
for img in list(images.keys()):
    if type(img) != bytes:
        print("Removed image")
        print(img, type(img))
        print(images[img])
        images.pop(img)

keys=list(images.keys())
keys.sort(key=lambda k: images[k])
image_keys = iter(keys)

# Create the GUI
root = tk.Tk()

image_label = tk.Label(root)
image_label.pack()

text_entry = tk.Entry(root)
text_entry.pack()

next_button = tk.Button(root, text="Next", command=load_next_image)
next_button.pack()

save_button = tk.Button(root, text="Save", command=lambda: [save_current_label(), save_images(images)])
save_button.pack()

# Load the first image
load_next_image()

# Start the GUI
root.mainloop()