"""
CNN image classifier for the photo editor.

Uses MobileNetV2, a convolutional neural network pretrained on ImageNet
(1000 classes), run through OpenCV's DNN module, so no extra deep-learning
framework is needed beyond the OpenCV the app already uses.

The model (~14 MB) and the class labels are downloaded automatically into
the "models" folder the first time a photo is classified. You can also
download them ahead of time with:  python cnn_classifier.py --download
"""

import os
import sys
import urllib.request

import cv2
import numpy as np

MODEL_DIR = "models"
MODEL_FILE = os.path.join(MODEL_DIR, "mobilenetv2-12.onnx")
LABELS_FILE = os.path.join(MODEL_DIR, "synset.txt")

MODEL_URL = ("https://media.githubusercontent.com/media/onnx/models/main/"
             "validated/vision/classification/mobilenet/model/mobilenetv2-12.onnx")
LABELS_URL = ("https://raw.githubusercontent.com/onnx/models/main/"
              "validated/vision/classification/synset.txt")

INPUT_SIZE = 224
# ImageNet normalisation used when MobileNetV2 was trained
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def download_model_files():
    """Download the ONNX model and the label list if they are missing."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    for url, path in ((MODEL_URL, MODEL_FILE), (LABELS_URL, LABELS_FILE)):
        if not os.path.exists(path):
            print("Downloading", url)
            tmp_path = path + ".part"
            urllib.request.urlretrieve(url, tmp_path)
            os.replace(tmp_path, path)


class CNNClassifier:
    def __init__(self):
        self.net = None
        self.labels = None

    def load(self):
        """Load the network once (lazily, on first use)."""
        if self.net is not None:
            return
        download_model_files()
        self.net = cv2.dnn.readNetFromONNX(MODEL_FILE)
        with open(LABELS_FILE, encoding="utf-8") as f:
            # each line looks like: "n01440764 tench, Tinca tinca"
            # keep only the first readable name ("tench")
            self.labels = [line.strip().split(" ", 1)[1].split(",")[0]
                           for line in f if line.strip()]

    def preprocess(self, img_rgb):
        """RGB uint8 image (H, W, 3) -> network input blob (1, 3, 224, 224)."""
        img = cv2.resize(img_rgb, (INPUT_SIZE, INPUT_SIZE), interpolation=cv2.INTER_AREA)
        img = img.astype(np.float32) / 255.0
        img = (img - MEAN) / STD
        blob = img.transpose(2, 0, 1)[np.newaxis, ...]  # HWC -> NCHW
        return np.ascontiguousarray(blob, dtype=np.float32)

    @staticmethod
    def softmax(x):
        e = np.exp(x - np.max(x))
        return e / e.sum()

    def classify(self, img_rgb, top_k=3):
        """Return a list of (label, probability) for the top_k classes."""
        self.load()
        if img_rgb.ndim == 2:  # grayscale -> 3 channels
            img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_GRAY2RGB)
        elif img_rgb.shape[2] == 4:  # drop alpha channel
            img_rgb = img_rgb[:, :, :3]
        self.net.setInput(self.preprocess(img_rgb))
        logits = self.net.forward().flatten()
        probs = self.softmax(logits)
        best = np.argsort(probs)[::-1][:top_k]
        return [(self.labels[i], float(probs[i])) for i in best]


if __name__ == "__main__":
    if "--download" in sys.argv:
        download_model_files()
        print("Model files are in", MODEL_DIR)
    else:
        # quick test: python cnn_classifier.py path/to/image.jpg
        image = cv2.cvtColor(cv2.imread(sys.argv[1]), cv2.COLOR_BGR2RGB)
        for name, p in CNNClassifier().classify(image):
            print(f"{name}: {p * 100:.1f}%")