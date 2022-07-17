# split into train and test set
import os
from os import listdir
from xml.etree import ElementTree
from numpy import zeros
from numpy import asarray
from mrcnn.utils import Dataset
from mrcnn.config import Config
from mrcnn.model import MaskRCNN
from numpy import zeros
from numpy import asarray
from matplotlib import pyplot
import argparse

parser = argparse.ArgumentParser(description='be my slave bitch')
parser.add_argument('--epoch', type=int, nargs=1, default=25)
parser.add_argument('--samples', type=int, nargs=1, default=64)
args = parser.parse_args()
samples = args.samples
epoch = args.epoch


# class that defines and loads the kangaroo dataset
class Galaxy_Ore_Detection(Dataset):
    # load the dataset definitions
    def load_dataset(self, dataset_dir, is_train=True):
        # define one class
        self.add_class("dataset", 1, "Silicate")
        self.add_class("dataset", 2, "Carbon")
        self.add_class("dataset", 3, "Iridium")
        # define data locations
        images_dir = dataset_dir + '/images/'
        annotations_dir = dataset_dir + '/annots/'
        # find all images
        for filename in listdir(images_dir):
            # extract image id
            image_id = filename[:-4]
            # skip bad images
            if image_id in ['00090']:
                continue
            # skip all images after 60 if we are building the train set
            if is_train and int(image_id) >= 60:
                continue
            # skip all images before 60 if we are building the test/val set
            if not is_train and int(image_id) < 60:
                continue
            img_path = images_dir + filename
            ann_path = annotations_dir + image_id + '.xml'
            # add to dataset
            self.add_image('dataset', image_id=image_id, path=img_path, annotation=ann_path)

    # extract bounding boxes from an annotation file
    def extract_boxes(self, filename):
        # load and parse the file
        tree = ElementTree.parse(filename)
        # get the root of the document
        root = tree.getroot()
        # extract each bounding box
        boxes = list()
        for box in root.findall('.//bndbox'):
            xmin = int(box.find('xmin').text)
            ymin = int(box.find('ymin').text)
            xmax = int(box.find('xmax').text)
            ymax = int(box.find('ymax').text)
            coors = [xmin, ymin, xmax, ymax]
            boxes.append(coors)
        # extract image dimensions
        width = int(root.find('.//size/width').text)
        height = int(root.find('.//size/height').text)
        label = root.find('.//object/name').text
        return boxes, width, height, label

    # load the masks for an image
    def load_mask(self, image_id):
        # get details of image
        info = self.image_info[image_id]
        # define box file location
        path = info['annotation']
        # load XML
        boxes, w, h, l = self.extract_boxes(path)
        # create one array for all masks, each on a different channel
        masks = zeros([h, w, len(boxes)], dtype='uint8')
        # create masks
        class_ids = list()
        for i in range(len(boxes)):
            box = boxes[i]
            row_s, row_e = box[1], box[3]
            col_s, col_e = box[0], box[2]
            masks[row_s:row_e, col_s:col_e, i] = 1
            class_ids.append(self.class_names.index(l))
        return masks, asarray(class_ids, dtype='int32')

    # load an image reference
    def image_reference(self, image_id):
        info = self.image_info[image_id]
        return info['path']


# define a configuration for the model
class GalaxyConfig(Config):
    # define the name of the configuration
    NAME = "galaxy_cfg"
    # number of classes (background + kangaroo)
    NUM_CLASSES = 1 + 3
    # number of training steps per epoch
    STEPS_PER_EPOCH = samples


# train set
train_set = Galaxy_Ore_Detection()
train_set.load_dataset(os.getcwd(), is_train=True)
train_set.prepare()
print('Train: %d' % len(train_set.image_ids))

# test/val set
test_set = Galaxy_Ore_Detection()
test_set.load_dataset(os.getcwd(), is_train=False)
test_set.prepare()
print('Test: %d' % len(test_set.image_ids))

# prepare config
config = GalaxyConfig()
config.display()
# define the model
model = MaskRCNN(mode='training', model_dir='./', config=config)
# load weights (mscoco) and exclude the output layers
model.load_weights('mask_rcnn_coco.h5', by_name=True, exclude=["mrcnn_class_logits", "mrcnn_bbox_fc",  "mrcnn_bbox", "mrcnn_mask"])
# train weights (output layers or 'heads')
model.train(train_set, test_set, learning_rate=config.LEARNING_RATE, epochs=epoch, layers='heads')
"""
# load an image
image_id = 0
image = test_set.load_image(image_id)
print(image.shape)
# load image mask
mask, class_ids = test_set.load_mask(image_id)
print(mask.shape)
# plot image
pyplot.imshow(image)
# plot mask
pyplot.imshow(mask[:, :, 0], cmap='gray', alpha=0.5)
pyplot.show()
"""
