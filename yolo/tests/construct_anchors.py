import json
import os
from utils import ConstructAnchors

annote_file_path = os.path.join(
    os.environ['HOME'], 'Datasets', 'flir', 'images_thermal_train' , 'coco.json'
)
with open(annote_file_path, 'r') as oj:
    annotations = json.load(oj)

construct_anchors = ConstructAnchors(annotations['annotations'], 640, 512)
construct_anchors.cluster_centers[:, 1:]
