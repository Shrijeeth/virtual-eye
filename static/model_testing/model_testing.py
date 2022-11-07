import torch
import glob
import cv2
import matplotlib.pyplot as plt


model = torch.hub.load("ultralytics/yolov5", "yolov5m")


def load_image(image_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image

def detect_person(image):
    detection_results = model(image)
    persons = []
    for detections in detection_results.xyxy[0]:
        if detections[-1] == 0:
            persons.append(detections[:-1])
    return persons


if __name__ == "__main__":
    for ind, img_path in enumerate(glob.glob("./*.jpg")):
        img = load_image(image_path=img_path)
        persons = detect_person(img)
        for person in persons:
            person = list(map(int, person.cpu().numpy().round().tolist()))
            start_point = (person[0], person[1])
            end_point = (person[2], person[3])
            color = (255, 0, 0)
            thickness = 2
            img = cv2.rectangle(img, start_point, end_point, color, thickness)
        plt.imshow(img)
        plt.savefig(str(ind)+"_testing.png")