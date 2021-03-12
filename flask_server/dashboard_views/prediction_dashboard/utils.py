#!/usr/bin/env python3

import os

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, metrics , optimizers , losses , models
from sklearn.metrics import classification_report, confusion_matrix ,accuracy_score
from ..training_dashboard.compile_fit_train import make_or_restore_model, configure_for_performance
import time

# Allow memory growth for the GPU
physical_devices = tf.config.experimental.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)
"""
gpus = tf.config.list_physical_devices('GPU')
if gpus:
  # Restrict TensorFlow to only allocate 1GB of memory on the first GPU
  try:
    tf.config.experimental.set_virtual_device_configuration(
        gpus[0],
        [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=512)])
    logical_gpus = tf.config.experimental.list_logical_devices('GPU')
    print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
  except RuntimeError as e:
    # Virtual devices must be set before GPUs have been initialized
    print(e)
"""

def prediction( data_dir = '', batch_size = 2 , img_height = 256 , img_width = 256 , ml_model = None, class_names_list = []):
    t1 = time.time()
    test_ds = tf.keras.preprocessing.image_dataset_from_directory(
                                directory = data_dir,
                                labels='inferred',
                                seed=123,
                                image_size=(img_height, img_width),
                                batch_size=batch_size,
                        )


    if len(class_names_list) <= 1 :
        class_names = test_ds.class_names
    else:
        class_names = class_names_list

    #for image_batch, labels_batch in test_ds:
    #    print(f"\n\n First image_batch.shape : {image_batch.shape}\n")
    #    print( f" First labels_batch.shape : {labels_batch.shape}\n\n")
    #    break
        

    #print(f"\n\n Number of testing batches: {tf.data.experimental.cardinality(test_ds).numpy()}")

    print(f"\n\nClasses names are : {class_names}\n\n")
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

    t2 = time.time()

    predictions_list = []
    labels_list = []
    for image_batch, label_batch in test_ds:
        t3 = time.time()
        predictions_batch = ml_model.predict_on_batch(image_batch).flatten()
        predictions_batch = tf.where(predictions_batch < 0.5, 0, 1)
        print(f"\n\ntime to make one batch loop : {time.time()-t3}")
        print('Predictions:\n', predictions_batch.numpy())
        print('Labels:\n', label_batch.numpy())
        predictions_list.extend( list ( predictions_batch.numpy() ) )
        labels_list.extend( list( label_batch.numpy() ) )
    
    #confusion =  confusion_matrix( labels_list  , predictions_list)
    #print(f"\n\n Confusion Matrix:\n {confusion}")
    #report =  classification_report( labels_list, predictions_list, target_names=class_names) 
    #print(f"\n\n Classification Report:\n {report }")

    accuracy = accuracy_score( labels_list , predictions_list)
    print(f"\n\n accuracy :\n {accuracy }")
    
    
    class_pred = [0 if accuracy > 0.5 else 1]
    if len(class_names) == 1 :
        class_pred = [ class_names[0] if accuracy > 0.5 else 'Not'][0]
    elif len(class_names) > 1 :
        class_pred = class_names[class_pred[0]]

    print(f"\n\n class_pred :\n {class_pred }")

    print(f"\n\ntime to make all batch loop : {time.time()-t2}")

    print(f"\n\n\ntime to make all predictions : {time.time()-t1}\n\n\n")

    return accuracy, class_pred
    

def show_bin_confusion_matrix(accuracies_list = [] , class_preds_list = []):
    y_true_list = []
    for accuracy , y_pred in zip ( accuracies_list , class_preds_list ):
        if accuracy > 0.5 :
            y_true_list.append(f"Hot")
        else:
            y_true_list.append(f"Cold")
    
    confusion =  confusion_matrix( y_true_list  , class_preds_list)
    print(f"\n\n Confusion Matrix:\n {confusion}")    

    return confusion
    
    


"""
labels = os.listdir(self.ml_testing_path)
for label in labels:
    root_ext = os.path.splitext(label)
    if root_ext =='.csv':
        trash_delete(imgs_main_dir = '' , img_thumb_path = os.path.join(self.ml_testing_path , f"{label}")  )
        continue
    trash_delete(imgs_main_dir = os.path.join(self.ml_testing_path , f"{label}") , img_thumb_path = '' )
"""
