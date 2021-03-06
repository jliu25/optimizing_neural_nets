batch_size = 100
num_classes = 10
epochs = 100
import keras
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dense, Flatten, Conv2D, SeparableConv2D, DepthwiseConv2D, ZeroPadding2D, Concatenate
from keras.layers import MaxPooling2D, AveragePooling2D, GlobalMaxPooling2D, GlobalAveragePooling2D
from keras import regularizers
from keras.regularizers import l2
from keras import metrics
from keras import callbacks
from apscheduler.schedulers.background import BackgroundScheduler
import pickle
import psutil

from pool_helper import PoolHelper
from lrn import LRN

process = psutil.Process()

mcpu = 0
mmem = 0

def get_info():
    global mmem
    mem = process.memory_info().rss
    if mmem < mem:
        mmem = mem

scheduler = BackgroundScheduler()
scheduler.add_job(get_info, 'interval', seconds=1)


data_augmentation = True

#load saved data
pkl_file = open('/exports/home/j_liu21/projects/genetic_algorithms/x_train.pkl', 'rb')
x_train = pickle.load(pkl_file, encoding='latin1')
pkl_file.close()

############################################################
x_data_len = len(x_train)
#end = int(.2*x_data_len)
#x_train_train = x_train[0:end]
#x_train_valid = x_train[end:]
print(x_data_len)
x_train_train = x_train[0:40000]
x_train_valid = x_train[40000:50000]
############################################################

pkl_file = open('/exports/home/j_liu21/projects/genetic_algorithms/y_train.pkl', 'rb')
y_train = pickle.load(pkl_file, encoding='latin1')
pkl_file.close()

############################################################
#y_train_train = y_train[0:end]
#y_train_valid = y_train[end:]
y_train_train = y_train[0:40000]
y_train_valid = y_train[40000:50000]
############################################################

pkl_file = open('/exports/home/j_liu21/projects/genetic_algorithms/x_test.pkl', 'rb')
x_test = pickle.load(pkl_file, encoding='latin1')
pkl_file.close()

pkl_file = open('/exports/home/j_liu21/projects/genetic_algorithms/y_test.pkl', 'rb')
y_test = pickle.load(pkl_file, encoding='latin1')
pkl_file.close()

# Convert class vectors to binary class matrices.
y_train_train = keras.utils.to_categorical(y_train_train, num_classes)
y_train_valid = keras.utils.to_categorical(y_train_valid, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()

model.add(ZeroPadding2D(padding=(3, 3)))
model.add(Conv2D(64, (7,7), strides=(2,2), padding='valid', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(ZeroPadding2D(padding=(1, 1)))
model.add(PoolHelper())
model.add(MaxPooling2D(pool_size=(3,3), strides=(2,2), padding='valid'))
model.add(LRN())

model.add(Conv2D(64, (1,1), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(Conv2D(192, (3,3), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(LRN())
model.add(ZeroPadding2D(padding=(1, 1)))
model.add(PoolHelper())
model.add(MaxPooling2D(pool_size=(3,3), strides=(2,2), padding='valid'))

inception_3a_1x1 = model.add(Conv2D(64, (1,1), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(Conv2D(96, (1,1), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(ZeroPadding2D(padding=(1, 1)))
inception_3a_3x3 = model.add(Conv2D(128, (3,3), padding='valid', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(Conv2D(16, (1,1), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(ZeroPadding2D(padding=(2, 2)))
inception_3a_5x5 = model.add(Conv2D(32, (5,5), padding='valid', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(MaxPooling2D(pool_size=(3,3), strides=(1,1), padding='same'))
inception_3a_pool_proj = model.add(Conv2D(32, (1,1), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
inception_3a_output = Concatenate(axis=1)([inception_3a_1x1,inception_3a_3x3,inception_3a_5x5,inception_3a_pool_proj])

inception_3b_1x1 = model.add(Conv2D(128, (1,1), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(Conv2D(128, (1,1), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(ZeroPadding2D(padding=(1, 1)))
inception_3b_3x3 = model.add(Conv2D(192, (3,3), padding='valid', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(Conv2D(32, (1,1), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(ZeroPadding2D(padding=(2, 2)))
inception_3b_5x5 = model.add(Conv2D(96, (5,5), padding='valid', activation='relu', kernel_regularizer=l2(0.0002)))
model.add(MaxPooling2D(pool_size=(3,3), strides=(1,1), padding='same'))
inception_3b_pool_proj = model.add(Conv2D(64, (1,1), padding='same', activation='relu', kernel_regularizer=l2(0.0002)))
inception_3b_output = Concatenate(axis=1)([inception_3b_1x1,inception_3b_3x3,inception_3b_5x5,inception_3b_pool_proj])

inception_3b_output_zero_pad = ZeroPadding2D(padding=(1, 1))(inception_3b_output)
pool3_helper = PoolHelper()(inception_3b_output_zero_pad)
pool3_3x3_s2 = MaxPooling2D(pool_size=(3,3), strides=(2,2), padding='valid', name='pool3/3x3_s2')(pool3_helper)

inception_4a_1x1 = Conv2D(192, (1,1), padding='same', activation='relu', name='inception_4a/1x1', kernel_regularizer=l2(0.0002))(pool3_3x3_s2)
inception_4a_3x3_reduce = Conv2D(96, (1,1), padding='same', activation='relu', name='inception_4a/3x3_reduce', kernel_regularizer=l2(0.0002))(pool3_3x3_s2)
inception_4a_3x3_pad = ZeroPadding2D(padding=(1, 1))(inception_4a_3x3_reduce)
inception_4a_3x3 = Conv2D(208, (3,3), padding='valid', activation='relu', name='inception_4a/3x3' ,kernel_regularizer=l2(0.0002))(inception_4a_3x3_pad)
inception_4a_5x5_reduce = Conv2D(16, (1,1), padding='same', activation='relu', name='inception_4a/5x5_reduce', kernel_regularizer=l2(0.0002))(pool3_3x3_s2)
inception_4a_5x5_pad = ZeroPadding2D(padding=(2, 2))(inception_4a_5x5_reduce)
inception_4a_5x5 = Conv2D(48, (5,5), padding='valid', activation='relu', name='inception_4a/5x5', kernel_regularizer=l2(0.0002))(inception_4a_5x5_pad)
inception_4a_pool = MaxPooling2D(pool_size=(3,3), strides=(1,1), padding='same', name='inception_4a/pool')(pool3_3x3_s2)
inception_4a_pool_proj = Conv2D(64, (1,1), padding='same', activation='relu', name='inception_4a/pool_proj', kernel_regularizer=l2(0.0002))(inception_4a_pool)
inception_4a_output = Concatenate(axis=1, name='inception_4a/output')([inception_4a_1x1,inception_4a_3x3,inception_4a_5x5,inception_4a_pool_proj])

loss1_ave_pool = AveragePooling2D(pool_size=(5,5), strides=(3,3), name='loss1/ave_pool')(inception_4a_output)
loss1_conv = Conv2D(128, (1,1), padding='same', activation='relu', name='loss1/conv', kernel_regularizer=l2(0.0002))(loss1_ave_pool)
loss1_flat = Flatten()(loss1_conv)
loss1_fc = Dense(1024, activation='relu', name='loss1/fc', kernel_regularizer=l2(0.0002))(loss1_flat)
loss1_drop_fc = Dropout(rate=0.7)(loss1_fc)
loss1_classifier = Dense(1000, name='loss1/classifier', kernel_regularizer=l2(0.0002))(loss1_drop_fc)
loss1_classifier_act = Activation('softmax')(loss1_classifier)

inception_4b_1x1 = Conv2D(160, (1,1), padding='same', activation='relu', name='inception_4b/1x1', kernel_regularizer=l2(0.0002))(inception_4a_output)
inception_4b_3x3_reduce = Conv2D(112, (1,1), padding='same', activation='relu', name='inception_4b/3x3_reduce', kernel_regularizer=l2(0.0002))(inception_4a_output)
inception_4b_3x3_pad = ZeroPadding2D(padding=(1, 1))(inception_4b_3x3_reduce)
inception_4b_3x3 = Conv2D(224, (3,3), padding='valid', activation='relu', name='inception_4b/3x3', kernel_regularizer=l2(0.0002))(inception_4b_3x3_pad)
inception_4b_5x5_reduce = Conv2D(24, (1,1), padding='same', activation='relu', name='inception_4b/5x5_reduce', kernel_regularizer=l2(0.0002))(inception_4a_output)
inception_4b_5x5_pad = ZeroPadding2D(padding=(2, 2))(inception_4b_5x5_reduce)
inception_4b_5x5 = Conv2D(64, (5,5), padding='valid', activation='relu', name='inception_4b/5x5', kernel_regularizer=l2(0.0002))(inception_4b_5x5_pad)
inception_4b_pool = MaxPooling2D(pool_size=(3,3), strides=(1,1), padding='same', name='inception_4b/pool')(inception_4a_output)
inception_4b_pool_proj = Conv2D(64, (1,1), padding='same', activation='relu', name='inception_4b/pool_proj', kernel_regularizer=l2(0.0002))(inception_4b_pool)
inception_4b_output = Concatenate(axis=1, name='inception_4b/output')([inception_4b_1x1,inception_4b_3x3,inception_4b_5x5,inception_4b_pool_proj])

inception_4c_1x1 = Conv2D(128, (1,1), padding='same', activation='relu', name='inception_4c/1x1', kernel_regularizer=l2(0.0002))(inception_4b_output)
inception_4c_3x3_reduce = Conv2D(128, (1,1), padding='same', activation='relu', name='inception_4c/3x3_reduce', kernel_regularizer=l2(0.0002))(inception_4b_output)
inception_4c_3x3_pad = ZeroPadding2D(padding=(1, 1))(inception_4c_3x3_reduce)
inception_4c_3x3 = Conv2D(256, (3,3), padding='valid', activation='relu', name='inception_4c/3x3', kernel_regularizer=l2(0.0002))(inception_4c_3x3_pad)
inception_4c_5x5_reduce = Conv2D(24, (1,1), padding='same', activation='relu', name='inception_4c/5x5_reduce', kernel_regularizer=l2(0.0002))(inception_4b_output)
inception_4c_5x5_pad = ZeroPadding2D(padding=(2, 2))(inception_4c_5x5_reduce)
inception_4c_5x5 = Conv2D(64, (5,5), padding='valid', activation='relu', name='inception_4c/5x5', kernel_regularizer=l2(0.0002))(inception_4c_5x5_pad)
inception_4c_pool = MaxPooling2D(pool_size=(3,3), strides=(1,1), padding='same', name='inception_4c/pool')(inception_4b_output)
inception_4c_pool_proj = Conv2D(64, (1,1), padding='same', activation='relu', name='inception_4c/pool_proj', kernel_regularizer=l2(0.0002))(inception_4c_pool)
inception_4c_output = Concatenate(axis=1, name='inception_4c/output')([inception_4c_1x1,inception_4c_3x3,inception_4c_5x5,inception_4c_pool_proj])

inception_4d_1x1 = Conv2D(112, (1,1), padding='same', activation='relu', name='inception_4d/1x1', kernel_regularizer=l2(0.0002))(inception_4c_output)
inception_4d_3x3_reduce = Conv2D(144, (1,1), padding='same', activation='relu', name='inception_4d/3x3_reduce', kernel_regularizer=l2(0.0002))(inception_4c_output)
inception_4d_3x3_pad = ZeroPadding2D(padding=(1, 1))(inception_4d_3x3_reduce)
inception_4d_3x3 = Conv2D(288, (3,3), padding='valid', activation='relu', name='inception_4d/3x3', kernel_regularizer=l2(0.0002))(inception_4d_3x3_pad)
inception_4d_5x5_reduce = Conv2D(32, (1,1), padding='same', activation='relu', name='inception_4d/5x5_reduce', kernel_regularizer=l2(0.0002))(inception_4c_output)
inception_4d_5x5_pad = ZeroPadding2D(padding=(2, 2))(inception_4d_5x5_reduce)
inception_4d_5x5 = Conv2D(64, (5,5), padding='valid', activation='relu', name='inception_4d/5x5', kernel_regularizer=l2(0.0002))(inception_4d_5x5_pad)
inception_4d_pool = MaxPooling2D(pool_size=(3,3), strides=(1,1), padding='same', name='inception_4d/pool')(inception_4c_output)
inception_4d_pool_proj = Conv2D(64, (1,1), padding='same', activation='relu', name='inception_4d/pool_proj', kernel_regularizer=l2(0.0002))(inception_4d_pool)
inception_4d_output = Concatenate(axis=1, name='inception_4d/output')([inception_4d_1x1,inception_4d_3x3,inception_4d_5x5,inception_4d_pool_proj])

loss2_ave_pool = AveragePooling2D(pool_size=(5,5), strides=(3,3), name='loss2/ave_pool')(inception_4d_output)
loss2_conv = Conv2D(128, (1,1), padding='same', activation='relu', name='loss2/conv', kernel_regularizer=l2(0.0002))(loss2_ave_pool)
loss2_flat = Flatten()(loss2_conv)
loss2_fc = Dense(1024, activation='relu', name='loss2/fc', kernel_regularizer=l2(0.0002))(loss2_flat)
loss2_drop_fc = Dropout(rate=0.7)(loss2_fc)
loss2_classifier = Dense(1000, name='loss2/classifier', kernel_regularizer=l2(0.0002))(loss2_drop_fc)
loss2_classifier_act = Activation('softmax')(loss2_classifier)

inception_4e_1x1 = Conv2D(256, (1,1), padding='same', activation='relu', name='inception_4e/1x1', kernel_regularizer=l2(0.0002))(inception_4d_output)
inception_4e_3x3_reduce = Conv2D(160, (1,1), padding='same', activation='relu', name='inception_4e/3x3_reduce', kernel_regularizer=l2(0.0002))(inception_4d_output)
inception_4e_3x3_pad = ZeroPadding2D(padding=(1, 1))(inception_4e_3x3_reduce)
inception_4e_3x3 = Conv2D(320, (3,3), padding='valid', activation='relu', name='inception_4e/3x3', kernel_regularizer=l2(0.0002))(inception_4e_3x3_pad)
inception_4e_5x5_reduce = Conv2D(32, (1,1), padding='same', activation='relu', name='inception_4e/5x5_reduce', kernel_regularizer=l2(0.0002))(inception_4d_output)
inception_4e_5x5_pad = ZeroPadding2D(padding=(2, 2))(inception_4e_5x5_reduce)
inception_4e_5x5 = Conv2D(128, (5,5), padding='valid', activation='relu', name='inception_4e/5x5', kernel_regularizer=l2(0.0002))(inception_4e_5x5_pad)
inception_4e_pool = MaxPooling2D(pool_size=(3,3), strides=(1,1), padding='same', name='inception_4e/pool')(inception_4d_output)
inception_4e_pool_proj = Conv2D(128, (1,1), padding='same', activation='relu', name='inception_4e/pool_proj', kernel_regularizer=l2(0.0002))(inception_4e_pool)
inception_4e_output = Concatenate(axis=1, name='inception_4e/output')([inception_4e_1x1,inception_4e_3x3,inception_4e_5x5,inception_4e_pool_proj])

inception_4e_output_zero_pad = ZeroPadding2D(padding=(1, 1))(inception_4e_output)
pool4_helper = PoolHelper()(inception_4e_output_zero_pad)
pool4_3x3_s2 = MaxPooling2D(pool_size=(3,3), strides=(2,2), padding='valid', name='pool4/3x3_s2')(pool4_helper)

inception_5a_1x1 = Conv2D(256, (1,1), padding='same', activation='relu', name='inception_5a/1x1', kernel_regularizer=l2(0.0002))(pool4_3x3_s2)
inception_5a_3x3_reduce = Conv2D(160, (1,1), padding='same', activation='relu', name='inception_5a/3x3_reduce', kernel_regularizer=l2(0.0002))(pool4_3x3_s2)
inception_5a_3x3_pad = ZeroPadding2D(padding=(1, 1))(inception_5a_3x3_reduce)
inception_5a_3x3 = Conv2D(320, (3,3), padding='valid', activation='relu', name='inception_5a/3x3', kernel_regularizer=l2(0.0002))(inception_5a_3x3_pad)
inception_5a_5x5_reduce = Conv2D(32, (1,1), padding='same', activation='relu', name='inception_5a/5x5_reduce', kernel_regularizer=l2(0.0002))(pool4_3x3_s2)
inception_5a_5x5_pad = ZeroPadding2D(padding=(2, 2))(inception_5a_5x5_reduce)
inception_5a_5x5 = Conv2D(128, (5,5), padding='valid', activation='relu', name='inception_5a/5x5', kernel_regularizer=l2(0.0002))(inception_5a_5x5_pad)
inception_5a_pool = MaxPooling2D(pool_size=(3,3), strides=(1,1), padding='same', name='inception_5a/pool')(pool4_3x3_s2)
inception_5a_pool_proj = Conv2D(128, (1,1), padding='same', activation='relu', name='inception_5a/pool_proj', kernel_regularizer=l2(0.0002))(inception_5a_pool)
inception_5a_output = Concatenate(axis=1, name='inception_5a/output')([inception_5a_1x1,inception_5a_3x3,inception_5a_5x5,inception_5a_pool_proj])

inception_5b_1x1 = Conv2D(384, (1,1), padding='same', activation='relu', name='inception_5b/1x1', kernel_regularizer=l2(0.0002))(inception_5a_output)
inception_5b_3x3_reduce = Conv2D(192, (1,1), padding='same', activation='relu', name='inception_5b/3x3_reduce', kernel_regularizer=l2(0.0002))(inception_5a_output)
inception_5b_3x3_pad = ZeroPadding2D(padding=(1, 1))(inception_5b_3x3_reduce)
inception_5b_3x3 = Conv2D(384, (3,3), padding='valid', activation='relu', name='inception_5b/3x3', kernel_regularizer=l2(0.0002))(inception_5b_3x3_pad)
inception_5b_5x5_reduce = Conv2D(48, (1,1), padding='same', activation='relu', name='inception_5b/5x5_reduce', kernel_regularizer=l2(0.0002))(inception_5a_output)
inception_5b_5x5_pad = ZeroPadding2D(padding=(2, 2))(inception_5b_5x5_reduce)
inception_5b_5x5 = Conv2D(128, (5,5), padding='valid', activation='relu', name='inception_5b/5x5', kernel_regularizer=l2(0.0002))(inception_5b_5x5_pad)
inception_5b_pool = MaxPooling2D(pool_size=(3,3), strides=(1,1), padding='same', name='inception_5b/pool')(inception_5a_output)
inception_5b_pool_proj = Conv2D(128, (1,1), padding='same', activation='relu', name='inception_5b/pool_proj', kernel_regularizer=l2(0.0002))(inception_5b_pool)
inception_5b_output = Concatenate(axis=1, name='inception_5b/output')([inception_5b_1x1,inception_5b_3x3,inception_5b_5x5,inception_5b_pool_proj])

pool5_7x7_s1 = AveragePooling2D(pool_size=(7,7), strides=(1,1), name='pool5/7x7_s2')(inception_5b_output)
loss3_flat = Flatten()(pool5_7x7_s1)
pool5_drop_7x7_s1 = Dropout(rate=0.4)(loss3_flat)
loss3_classifier = Dense(1000, name='loss3/classifier', kernel_regularizer=l2(0.0002))(pool5_drop_7x7_s1)
loss3_classifier_act = Activation('softmax', name='prob')(loss3_classifier)





print(model.summary())

opt = keras.optimizers.rmsprop(lr=0.001, decay=1e-6)
#opt = keras.optimizers.SGD(learning_rate = .01, decay=1e-6)

es = keras.callbacks.EarlyStopping(monitor = 'val_loss', patience = 10, verbose = 1)

scheduler.start()

model.compile(loss = 'categorical_crossentropy',
              optimizer = opt,
              metrics = ['accuracy'])

x_train_train = x_train_train.astype('float32')
x_train_valid = x_train_valid.astype('float32')
x_test = x_test.astype('float32')
x_train_train /= 255
x_train_valid /= 255
x_test /= 255

if not data_augmentation:
    print('Not using data augmentation.')
    model.fit(x_train_train, y_train_train,
              batch_size = batch_size,
              epochs = epochs,
              validation_data = (x_train_valid, y_train_valid),
              shuffle = True)
else:
    print('Using real-time data augmentation.')
                   # This will do preprocessing and realtime data augmentation:
    datagen = ImageDataGenerator(
        featurewise_center = False,             # set input mean to 0 over the dataset
        samplewise_center = False,              # set each sample mean to 0
        featurewise_std_normalization = False,  # divide inputs by std of the dataset
        samplewise_std_normalization = False,   # divide each input by its std
        zca_whitening = False,                  # apply ZCA whitening
        zca_epsilon = 1e-06,                    # epsilon for ZCA whitening
        rotation_range = 0,                     # randomly rotate images in the range (degrees, 0 to 180)
        width_shift_range = 0.1,                # randomly shift images horizontally (fraction of total width)
        height_shift_range = 0.1,               # randomly shift images vertically (fraction of total height)
        shear_range = 0.,                       # set range for random shear
        zoom_range = 0.,                        # set range for random zoom
        channel_shift_range = 0.,               # set range for random channel shifts
        fill_mode = 'nearest',                  # set mode for filling points outside the input boundaries
        cval = 0.,                              # value used for fill_mode = "constant"
        horizontal_flip = True,                 # randomly flip images
        vertical_flip = False,                  # randomly flip images
        rescale = None,                         # set rescaling factor (applied before any other transformation)
        preprocessing_function = None,          # set function that will be applied on each input
        data_format = None,                     # image data format, either "channels_first" or "channels_last"
        validation_split = 0.0 )                # fraction of images reserved for validation (strictly between 0 and 1)


    # Compute quantities required for feature-wise normalization
    # (std, mean, and principal components if ZCA whitening is applied).

    datagen.fit(x_train_train)

    # Fit the model on the batches generated by datagen.flow().

    model.fit_generator(datagen.flow(x_train_train, y_train_train, batch_size = batch_size),
                                     steps_per_epoch = 100,
                                     epochs = epochs,
                                     validation_data = (x_train_valid, y_train_valid),
                                     workers = 8,
                                     callbacks = [es] )

    #model.fit_generator(datagen.flow(x_train_train, y_train_train, batch_size = batch_size),
    #                                 steps_per_epoch = 100,
    #                                 epochs = epochs,
    #                                 validation_data = (x_train_valid, y_train_valid),
    #                                 workers = 8 )


# Score trained model.
scores_train_train = model.evaluate(x_train_train, y_train_train, verbose = 0)
scores_test = model.evaluate(x_test, y_test, verbose = 0)
scheduler.shutdown()
cpu_time = process.cpu_times().user

print('Training_loss: {} Test_accuracy: {} Mem: {} CPU: {}'.format(scores_train_train[0], scores_test[1], mmem, cpu_time) )

