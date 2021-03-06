#!/usr/bin/env python

"""Load and analyze a Keras model."""

import os

from keras.utils import np_utils
from keras.models import load_model
from keras import backend as K
import hasy_tools as ht
from hasy_tools import load_data
import yaml

batch_size = 128
nb_classes = 369
nb_epoch = 1

# input image dimensions
img_rows, img_cols = 32, 32
# number of convolutional filters to use
nb_filters = 32
# size of pooling area for max pooling
pool_size = (2, 2)
# convolution kernel size
kernel_size = (3, 3)

dataset_path = os.path.join(os.path.expanduser("~"), 'hasy')

# Translation
symbol_id2index = ht.generate_index("%s/symbols.csv" % dataset_path)
symbolid2latex = ht._get_symbolid2latex("%s/symbols.csv" % dataset_path)
index2symbol_id = {}
for index, symbol_id in symbol_id2index.items():
    index2symbol_id[symbol_id] = index
index2latex = lambda n: symbolid2latex[index2symbol_id[n]]

with open("confusable-classes.yml", 'r') as stream:
    merge_classes = yaml.load(stream)

print("Load model")
model = load_model('../keras-models/my_keras_model.h5')

print("Load data")
hasy_data = load_data(normalize=True, dataset_path=dataset_path)

print("edit data")
X_train = hasy_data['train']['X']
y_train = hasy_data['train']['y']
s_train = hasy_data['train']['source']
X_test = hasy_data['test']['X']
y_test = hasy_data['test']['y']
s_test = hasy_data['test']['source']

if K.image_dim_ordering() == 'th':
    X_train = X_train.reshape(X_train.shape[0], 1, img_rows, img_cols)
    X_test = X_test.reshape(X_test.shape[0], 1, img_rows, img_cols)
    input_shape = (1, img_rows, img_cols)
else:
    X_train = X_train.reshape(X_train.shape[0], img_rows, img_cols, 1)
    X_test = X_test.reshape(X_test.shape[0], img_rows, img_cols, 1)
    input_shape = (img_rows, img_cols, 1)


def is_confusable(merge_classes, el1, el2):
    """Check if two symbols belong to the same 'confuscation class'."""
    for cl in merge_classes:
        if el1 in cl and el2 in cl:
            return True
    return False


print("Evaluate model")
out = model.predict_classes(X_test)
wrongs = []
for el in zip(out, y_test, s_test):
    el1 = index2latex(el[0])
    el2 = index2latex(el[1])
    if el[0] != el[1] and not is_confusable(merge_classes, el1, el2):
        wrongs.append(el)
wrongs = sorted(wrongs, key=lambda n: (n[1], n[0], n[2]))
with open("index.html", "w") as f:
    for pred, true_c, source in wrongs:
        source = source.replace(dataset_path, '')
        f.write(('<img src="{source}" /> '
                 'true={true}, Predicted={pred}, {source}</a>'
                 '<br/>\n').format(source=source,
                                   pred=index2latex(pred),
                                   true=index2latex(true_c)))

y_test = np_utils.to_categorical(y_test, nb_classes)
score = model.evaluate(X_test, y_test, verbose=0)
print('Test score:', score[0])
print('Test accuracy:', score[1])
