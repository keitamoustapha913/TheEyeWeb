#!/usr/bin/env python3



"""
import numpy as np

import os

import tensorflow as tf
from tensorflow.keras import layers, metrics , optimizers , losses
from tensorflow.keras.models import Sequential

import pathlib

AUTOTUNE = tf.data.AUTOTUNE


def compile_fit( data_dir = '', batch_size = 2 , img_height = 256 , img_width = 256):
    train_ds = tf.keras.preprocessing.image_dataset_from_directory(
                                directory = data_dir,
                                labels='inferred',
                                validation_split=0.2,
                                subset="training",
                                seed=123,
                                image_size=(img_height, img_width),
                                batch_size=batch_size,
                        )

    val_ds = tf.keras.preprocessing.image_dataset_from_directory(
                                directory = data_dir,
                                labels='inferred',
                                validation_split=0.2,
                                subset="validation",
                                seed=123,
                                image_size=(img_height, img_width),
                                batch_size=batch_size,
                        )

    class_names = train_ds.class_names
    for image_batch, labels_batch in train_ds:
        print(image_batch.shape)
        print(labels_batch.shape)
        break
        
    # You can see the length of each dataset as follows:
    print(f"\n\n len of training set: { len(train_ds) }")
    print(f" \n\n len of validation set : { len(val_ds) }")

    print(f"\n\n Number of training set: {tf.data.experimental.cardinality(train_ds).numpy()}")
    print(f" \n\n Number of validation set : {tf.data.experimental.cardinality(val_ds).numpy()}")

    print(f"Number of classes are : {class_names}")

    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    #train_ds = configure_for_performance( ds = train_ds, batch_size = batch_size )
    #val_ds = configure_for_performance( ds = val_ds, batch_size = batch_size)


    
  

    model = tf.keras.Sequential([
            layers.experimental.preprocessing.Rescaling(1./255, input_shape=(img_height, img_width, 3)),
            #layers.experimental.preprocessing.Rescaling(1./255),
            layers.experimental.preprocessing.RandomFlip("horizontal_and_vertical"),
            layers.experimental.preprocessing.RandomRotation(0.2),
            layers.experimental.preprocessing.RandomZoom(0.1),

            layers.Conv2D(32, (3,3), activation='relu'),
            layers.MaxPooling2D(),

            layers.Conv2D(32,  (3,3), activation='relu'),
            layers.MaxPooling2D(),

            layers.Conv2D(64, (3,3), activation='relu'),
            layers.MaxPooling2D(),


            layers.Flatten(),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(1, activation='sigmoid'),
            #layers.Dense(2)
    ])

    METRICS = [
        metrics.BinaryAccuracy(name="accuracy"),
        #metrics.Precision(name="precision"),
        #metrics.Recall(name="recall"),
        #metrics.AUC(name="auc"),
    ]

    #model.build( image_batch.shape )
    print(model.summary())
    
    model.compile(
        optimizer = optimizers.Adam(lr=3e-4),
        loss=[losses.BinaryCrossentropy(from_logits=True)],
        metrics=METRICS,
    )
       

    model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=50,
            batch_size =batch_size,
        )

        


def configure_for_performance(ds , batch_size = 32):
    ds = ds.cache()
    ds = ds.shuffle(buffer_size=1000)
    ds = ds.batch(batch_size)
    ds = ds.prefetch(buffer_size=AUTOTUNE)
    return ds


"""