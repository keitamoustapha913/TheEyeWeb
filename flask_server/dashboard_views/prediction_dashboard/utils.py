#!/usr/bin/env python3

import os

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, metrics , optimizers , losses , models
#from sklearn.metrics import confusion_matrix
from ..training_dashboard.compile_fit_train import make_or_restore_model, configure_for_performance
import time

# Allow memory growth for the GPU
physical_devices = tf.config.experimental.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)



def prediction( data_dir = '', batch_size = 2 , img_height = 256 , img_width = 256 , ml_model = None):
    t1 = time.time()
    test_ds = tf.keras.preprocessing.image_dataset_from_directory(
                                directory = data_dir,
                                labels='inferred',
                                seed=123,
                                image_size=(img_height, img_width),
                                batch_size=batch_size,
                        )

    

    class_names = test_ds.class_names
    #for image_batch, labels_batch in test_ds:
    #    print(f"\n\n First image_batch.shape : {image_batch.shape}\n")
    #    print( f" First labels_batch.shape : {labels_batch.shape}\n\n")
    #    break
        

    #print(f"\n\n Number of testing batches: {tf.data.experimental.cardinality(test_ds).numpy()}")

    #print(f"\n\nClasses names are : {class_names}\n\n")
    #print(f"\n\ntf.data.AUTOTUNE : {tf.data.AUTOTUNE}\n\n")

    test_ds = configure_for_performance(test_ds)

    if  ml_model is None:
        raise f"Model Path ERROR : \n\t{ml_model_dir} does not exists \n Please train your model first"

    """
    t2 = time.time()
    model = make_or_restore_model(checkpoint_dir = ml_model_dir, 
                                  img_height = img_height, 
                                  img_width = img_height,
                                  )
    print(f"\n\ntime to loaded the model : {time.time()-t2}")
    """
    #Retrieve a batch of images from the test set
    #image_batch, label_batch = test_ds.as_numpy_iterator().next()
    #for img in image_batch:
    #    print(f"image_batch[0] : {img} ")
    #    break

    t2 = time.time()
    for image_batch, label_batch in test_ds:
        t3 = time.time()
        predictions = ml_model.predict_on_batch(image_batch).flatten()
        predictions = tf.where(predictions < 0.5, 0, 1)
        print(f"\n\ntime to make one batch loop : {time.time()-t3}")
        print('Predictions:\n', predictions.numpy())
        print('Labels:\n', label_batch.numpy())

    print(f"\n\ntime to make all batch loop : {time.time()-t2}")
    #predictions = model.predict_on_batch(image_batch).flatten()

    # Apply a sigmoid since our model returns logits
    #predictions = tf.nn.sigmoid(predictions)
    #predictions = tf.where(predictions < 0.5, 0, 1)

    #print('Predictions:\n', predictions.numpy())
    #print('Predictions:\n', predictions )
    #print('Labels:\n', label_batch)
    print(f"\n\n\ntime to make all predictions : {time.time()-t1}\n\n\n")
    




"""
labels = os.listdir(self.ml_testing_path)
for label in labels:
    root_ext = os.path.splitext(label)
    if root_ext =='.csv':
        trash_delete(imgs_main_dir = '' , img_thumb_path = os.path.join(self.ml_testing_path , f"{label}")  )
        continue
    trash_delete(imgs_main_dir = os.path.join(self.ml_testing_path , f"{label}") , img_thumb_path = '' )
"""