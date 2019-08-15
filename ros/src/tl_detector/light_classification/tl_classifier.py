from styx_msgs.msg import TrafficLight
from PIL import Image
import tensorflow as tf
import numpy as np
import time
import os

from filters import *
from utils import *

class TLClassifier(object):
    def __init__(self):
        #TODO load classifier
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)

        self.config = tf.ConfigProto(gpu_options = gpu_options,
                                     Log_device_placement = False)
        dir_path = os.path.dirname(os.path.abspath(__file__))
        self.classes = load_coco_names(os.path.join(dir_path, "coco.names"))

        self.forzenGraph = load_graph(os.path.join(dir_path, "frozen_darknet_yolov3.pb"))

        self.sess = tf.Session(graph=self.frozenGraph, config=self.config)
        print("Graph loaded successfully!")

    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        #TODO implement light color prediction
        image = Image.fromarray(cv_image)
        img_resized = letter_box_image(image, 416, 416, 128)
        img_resized = img_resized.astype(np.float32)

        boxes, inputs = get_boxes_and_inputs_pb(self.frozenGraph)

        detected_boxes = self.sess.run(boxes, feed_dict = {inputs : [img_resized]})
        filtered_boxes = nms(detected_boxes, confidence_threshold=0.5,
                             iou_threshold = 0.4)
        inp = filtered_boxes.get(9)         # Get detected traffic light boxes
        inp_new = dict()
        inp_new[9] = inp

        if inp_new[9] != None:
            if len(inp_new[9]) > 0:
                for cls, bboxes in inp_new.items():
                    for box, score in bboxes:
                        box = convert_to_original_size(box, 416, 416, np.array(image.size), True)

                a = analyze_color(inp_new, cv_image)

                color = state_predict(a)
                print("Detect %s light"%color)
                if color == "YELLOW":
                    return TrafficLight.YELLOW
                elif color == "RED":
                    return TrafficLight.RED
                elif color == "GREEN":
                    return TrafficLight.GREEN
        return TrafficLight.UNKNOWN
