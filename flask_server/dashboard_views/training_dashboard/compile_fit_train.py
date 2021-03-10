#!/usr/bin/env python3

import numpy as np

import os

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, metrics , optimizers , losses , models
from tensorflow.keras.models import Sequential

from matplotlib import pyplot as plt
import pathlib

# Allow memory growth for the GPU
#physical_devices = tf.config.experimental.list_physical_devices('GPU')
#tf.config.experimental.set_memory_growth(physical_devices[0], True)
# from https://www.tensorflow.org/guide/gpu
gpus = tf.config.list_physical_devices('GPU')
if gpus:
  # Restrict TensorFlow to only allocate 1GB of memory on the first GPU
  try:
    tf.config.experimental.set_virtual_device_configuration(
        gpus[0],
        [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=1024)])
    logical_gpus = tf.config.experimental.list_logical_devices('GPU')
    print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
  except RuntimeError as e:
    # Virtual devices must be set before GPUs have been initialized
    print(e)


AUTOTUNE = tf.data.AUTOTUNE


def compile_fit( data_dir = '', batch_size = 2 , img_height = 256 , img_width = 256 , checkpoint_dir = ''):
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
        print(f"\n\n First image_batch.shape : {image_batch.shape}\n")
        print( f" First labels_batch.shape : {labels_batch.shape}\n\n")
        break
        

    print(f"\n\n Number of training batches: {tf.data.experimental.cardinality(train_ds).numpy()}")
    print(f" \n\n Number of validation batches : {tf.data.experimental.cardinality(val_ds).numpy()}")

    print(f"\n\nClasses names are : {class_names}\n\n")

    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    #train_ds = configure_for_performance( ds = train_ds, batch_size = batch_size )
    #val_ds = configure_for_performance( ds = val_ds, batch_size = batch_size)
    global model_directory
    model_directory = checkpoint_dir
    # Prepare a directory to store all the checkpoints.
    #checkpoint_dir = "./ckpt"
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)



    model = make_or_restore_model(checkpoint_dir = checkpoint_dir, 
                                  img_height = img_height, 
                                  img_width = img_height,
                                  )


    callbacks = [
        # This callback saves a SavedModel every 20 batches.
        # We include the training loss in the saved model name.
        keras.callbacks.ModelCheckpoint(
                            filepath=checkpoint_dir + "/ckpt-val_accuracy-{epoch:02d}-{val_accuracy:.2f}",
                            monitor='val_accuracy',
                            mode='max',
                           ) ,

        keras.callbacks.CSVLogger(filename = os.path.join( os.path.dirname(checkpoint_dir), "logs","ml_train_log.csv" ), separator=",", append=False),

        #PlotLearning(filename= os.path.join( checkpoint_dir,"ml_plot_learning_{val_accuracy:.2f}.png" ) ),
        
        keras.callbacks.EarlyStopping( monitor="val_accuracy",
                            min_delta=0.00001,
                            patience=10,
                            verbose=1,
                            mode="max",
                            baseline=None,
                            restore_best_weights=True,
                        ),

    ]
       

    history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=1000,
            batch_size = batch_size,
            callbacks=callbacks,
        )
    
    
    ###2 conv and pool layers. with some normalization and drops in between.
    
    INPUT_SHAPE = (img_height, img_width, 3)   #change to (SIZE, SIZE, 3)

    model = Sequential()
    model.add(Conv2D(32, (3, 3), input_shape=INPUT_SHAPE))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Conv2D(32, (3, 3)))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Conv2D(64, (3, 3)))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Flatten())
    model.add(Dense(64))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(1))
    model.add(Activation('sigmoid'))
    




def configure_for_performance(ds):
    ds = ds.cache()
    ds = ds.shuffle(buffer_size=1000)
    ds = ds.prefetch(buffer_size=AUTOTUNE)
    return ds




def make_or_restore_model(checkpoint_dir = '', img_height = 256, img_width = 256):
    # Either restore the latest model, or create a fresh one
    # if there is no checkpoint available.
    checkpoints = [checkpoint_dir + "/" + name for name in os.listdir(checkpoint_dir)]
    if checkpoints:
        latest_checkpoint = max(checkpoints, key=os.path.getctime)
        print("Restoring from", latest_checkpoint)
        return models.load_model(latest_checkpoint)
    print("Creating a new model")
    return get_compiled_model( img_height = img_height, img_width = img_height )


def get_compiled_model(img_height = 256, img_width = 256 ):
    model = tf.keras.Sequential([
            layers.experimental.preprocessing.Rescaling(1./255, input_shape=(img_height, img_width, 3)),
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
        metrics.Precision(name="precision"),
        metrics.Recall(name="recall"),
        metrics.AUC(name="auc"),
    ]

    #model.build( image_batch.shape )
    print(model.summary())
    
    model.compile(
        optimizer = optimizers.Adam(lr=3e-4),
        loss=[losses.BinaryCrossentropy(from_logits=True)],
        metrics=METRICS,
    )

    return model



class PlotLearning(keras.callbacks.Callback):
    def __init__(self, *args, **kargs):
        self.filename = kargs.get('filename', 'model_training')

    def on_train_begin(self, logs={}):
        self.i = 0
        self.x = []
        self.losses = []
        self.val_losses = []
        self.acc = []
        self.val_acc = []
        self.fig = plt.figure()
        self.logs = []
        self.t1 = time.time()
        # ani = animation.FuncAnimation(self.fig, self.animate_plot(), interval=1000)

    def on_epoch_end(self, epoch, logs={}):
        self.logs.append(logs)
        self.x.append(self.i)
        self.losses.append(logs.get('loss'))
        self.val_losses.append(logs.get('val_loss'))
        self.acc.append(logs.get('acc'))
        self.val_acc.append(logs.get('val_acc'))
        self.i += 1


    def on_train_end(self, epoch, logs={}):
        print('end')
        global model_directory
        print(model_directory)
        print("[DL TRAIN] Top training done in %ds" % (time.time() - self.t1))

        f, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

        plt.title(self.filename)
        plt.xlabel('epoch [total:%ds]' % (time.time() - self.t1))

        # clear_output(wait=True)
        ax1.set_yscale('log')
        ax1.set_ylabel('log(loss)')
        ax1.plot(self.x, self.losses, label="loss")
        ax1.plot(self.x, self.val_losses, label="val_loss")
        ax1.legend()

        ax2.set_ylabel('accuracy')
        ax2.plot(self.x, self.acc, label="accuracy")
        ax2.plot(self.x, self.val_acc, label="validation accuracy")
        ax2.legend()

        plt.savefig( self.filename , bbox_inches='tight', dpi=250)
        print("  %s saved " % (self.filename) )
        
        plt.close()








def configure_for_performance(ds , batch_size = 32):
    ds = ds.cache()
    ds = ds.shuffle(buffer_size=1000)
    ds = ds.prefetch(buffer_size=AUTOTUNE)
    return ds



