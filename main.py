# -*- coding: utf-8 -*-
"""Copy of fcc_sms_text_classification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1f_61s-GIrT8OMFu77AO55llZknrFKxzx
"""

# import libraries
try:
  # %tensorflow_version only exists in Colab.
  !pip install tf-nightly
except Exception:
  pass
import tensorflow as tf
import pandas as pd
from tensorflow import keras
!pip install tensorflow-datasets
import tensorflow_datasets as tfds
import numpy as np
import matplotlib.pyplot as plt

print(tf.__version__)

# get data files
!wget https://cdn.freecodecamp.org/project-data/sms/train-data.tsv
!wget https://cdn.freecodecamp.org/project-data/sms/valid-data.tsv

train_file_path = "train-data.tsv"
test_file_path = "valid-data.tsv"

#get data
df_train = pd.read_csv(train_file_path, sep='\t', header=None, names=['type','message'])
df_train.dropna()
df_test = pd.read_csv(test_file_path, sep='\t', header=None, names=['type','message'])
df_test.dropna()
df_train['type'] = pd.factorize(df_train['type'])[0]
df_test['type'] = pd.factorize(df_test['type'])[0]

train_labels = df_train['type'].values
ds_train = tf.data.Dataset.from_tensor_slices(
    (df_train['message'].values, train_labels)
)

test_labels = df_test['type'].values
ds_test = tf.data.Dataset.from_tensor_slices(
    (df_test['message'].values, test_labels)
)
ds_test.element_spec

BUFFER_SIZE = 100
BATCH_SIZE = 32
ds_train = ds_train.shuffle(BUFFER_SIZE).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
ds_test = ds_test.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

for example, label in ds_train.take(1):
  print('texts: ', example.numpy()[:3])
  print()
  print('labels: ', label.numpy()[:3])

#Create the text encoder
enc = tf.keras.layers.TextVectorization(
    output_mode='int',
    max_tokens=1000,
    output_sequence_length=1000,
)

enc.adapt(ds_train.map(lambda text, label: text))

vocab = np.array(enc.get_vocabulary())
vocab[:20]

#create the model
model = tf.keras.Sequential([
    enc,
    tf.keras.layers.Embedding(
        len(enc.get_vocabulary()),
        64,
        mask_zero=True,
    ),
    tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64,  return_sequences=True)),
    tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(32)),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(1)
])

#compile the model
model.compile(loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
              optimizer=tf.keras.optimizers.Adam(1e-4),
              metrics=['accuracy'])

#train the model
history = model.fit(ds_train, epochs=10,
                    validation_data=ds_test,
                    validation_steps=30)

test_loss, test_acc = model.evaluate(ds_test)

print('Test Loss:', test_loss)
print('Test Accuracy:', test_acc)

#vizualisation

def plot_graphs(history, metric):
  plt.plot(history.history[metric])
  plt.plot(history.history['val_'+metric], '')
  plt.xlabel("Epochs")
  plt.ylabel(metric)
  plt.legend([metric, 'val_'+metric])
  
plt.figure(figsize=(16, 8))
plt.subplot(1, 2, 1)
plot_graphs(history, 'accuracy')
plt.ylim(None, 1)
plt.subplot(1, 2, 2)
plot_graphs(history, 'loss')
plt.ylim(0, None)

# function to predict messages based on model
# (should return list containing prediction and label, ex. [0.008318834938108921, 'ham'])
def predict_message(pred_text):
  res = model.predict([pred_text])
  print(res)
  prediction = [res[0][0], "ham" if res[0][0] < 0.1 else "spam"]
  return (prediction)

pred_text = "how are you doing today?"

prediction = predict_message(pred_text)
print(prediction)

# Run this  to test your function and model.
def test_predictions():
  test_messages = ["how are you doing today",
                   "sale today! to stop texts call 98912460324",
                   "i dont want to go. can we try it a different day? available sat",
                   "our new mobile video service is live. just install on your phone to start watching.",
                   "you have won £1000 cash! call to claim your prize.",
                   "i'll bring it tomorrow. don't forget the milk.",
                   "wow, is your arm alright. that happened to me one time too"
                  ]

  test_answers = ["ham", "spam", "ham", "spam", "spam", "ham", "ham"]
  passed = True

  for msg, ans in zip(test_messages, test_answers):
    prediction = predict_message(msg)
    if prediction[1] != ans:
      passed = False

  if passed:
    print("You passed the challenge. Great job!")
  else:
    print("You haven't passed yet. Keep trying.")

test_predictions()