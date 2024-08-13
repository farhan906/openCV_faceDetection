import cv2
import os
import numpy as np
from pathlib import Path

# Path to the dataset
dataset_path = Path("C:/Users/FARHAN/Desktop/vscode@/captureimgopcv/dataset/dataset2")

# Create the LBPH face recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Prepare the training data
def prepare_training_data(data_folder_path):
    faces = []
    labels = []
    label_dict = {}
    label_id = 0
    total_files = sum(len(files) for _, _, files in os.walk(data_folder_path))
    processed_files = 0

    for root, dirs, files in os.walk(data_folder_path):
        for file in files:
            if file.endswith(".jpg"):
                path = os.path.join(root, file)
                label = os.path.basename(root)
                if label not in label_dict:
                    label_dict[label] = label_id
                    label_id += 1
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                faces.append(img)
                labels.append(label_dict[label])
                processed_files += 1
                if processed_files % 100 == 0:
                    print(f"Processed {processed_files}/{total_files} images")

    return faces, labels, label_dict

faces, labels, label_dict = prepare_training_data(dataset_path)

# Train the recognizer
print("Training the recognizer. This might take a while...")
recognizer.train(faces, np.array(labels))

# Save the trained model and label dictionary
recognizer.save("face_recognizer_model.yml")

with open("label_dict.npy", "wb") as f:
    np.save(f, label_dict)

print("Training complete and model saved.")
