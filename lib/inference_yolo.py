import os
import gc
import tensorflow as tf
tfconfig = tf.ConfigProto()
tfconfig.gpu_options.allow_growth = True
session = tf.Session(config=tfconfig)
import keras
from keras.callbacks import EarlyStopping, ModelCheckpoint, TensorBoard
import models
from reader import dataset_filepath, dir_reader
import config as conf
from sklearn.model_selection import train_test_split
from utils import normalize
from generators import YOLO_BatchGenerator

yolo_model = models.get_yolo_model()
yolo_model.summary()
print('Loading trained weights...')
yolo_model.load_weights(conf.YOLO_CKPT)

print('Generating metadata...')
imgs_meta  = dataset_filepath(conf.TEST_PATH, get_masks=False)
imgs_batch, imgs_original, imgs_path = dir_reader(imgs_meta)

netouts = yolo_model.predict([imgs_batch, imgs_meta], batch_size=conf.YOLO_BATCH_SIZE)
del imgs_batch
gc.collect() # release memory

if not os.path.exists(conf.YOLO_OUT_DIR):
    os.makedirs(conf.YOLO_OUT_DIR)

for i, netout in tqdm(enumerate(netouts), total=len(netouts)):
    boxes = decode_netout(netout,
                      obj_threshold=conf.OBJECT_THRESHOLD,
                      nms_threshold=conf.NMS_THRESHOLD,
                      anchors=conf.ANCHORS)
    image = draw_boxes(imgs_original[i], boxes)[...,::-1] # RGB -> BGR
    _ , filename = os.path.split(imgs_path[i])
    newpath = os.path.join(conf.YOLO_OUT_DIR , filename)
    cv2.imwrite(newpath, image)
