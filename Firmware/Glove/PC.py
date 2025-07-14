import sys
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder, StandardScaler
from keras.utils import to_categorical
import time
import serial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer

classes = []
arduino_port = "COM13"

dataset = pd.read_csv('Firmware/Dataset.csv')
X = dataset.iloc[:, :-1].values 
y = dataset.iloc[:, -1].values

for label in y:
    if label not in classes:
        classes.append(label)
numClasses = len(classes)
print(classes)

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
y_encoded = to_categorical(y_encoded)

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=0)

sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

ann = tf.keras.models.Sequential([
    tf.keras.layers.Dense(units=10, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(units=128, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(units=numClasses, activation='softmax')
])

ann.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
ann.fit(X_train, y_train, batch_size=256, epochs=25, validation_split=0.2)

ser = serial.Serial(arduino_port, 9600)
print("Connected to Arduino port: " + arduino_port)

max_samples = 100000
time.sleep(5)

class PredictionWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gesture Classifier")
        self.setGeometry(100, 100, 400, 350)

        self.layout = QVBoxLayout()

        self.prediction_label = QLabel("Prediction: ", self)
        self.layout.addWidget(self.prediction_label)

        self.progress_bars = []
        self.labels = []

        for i in range(numClasses):
            bar = QProgressBar(self)
            bar.setMinimum(0)
            bar.setMaximum(100)
            self.progress_bars.append(bar)

            label = QLabel(f"{classes[i]}", self)
            self.labels.append(label)

            h_layout = QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(bar)

            self.layout.addLayout(h_layout)
        
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start", self)
        self.data_button = QPushButton("Add Gesture", self)
        self.data_button.clicked.connect(self.collect)
        self.start_button.clicked.connect(self.toggle_progress)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.data_button)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)

        self.progress_values = [0] * numClasses

    def collect(self):
        if self.start_button.text() == "Stop":
            self.toggle_progress()
        self.hide()
        collection_window.show()
        
    def toggle_progress(self):
        if self.start_button.text() == "Start":
            self.start_button.setText("Stop")
            self.timer.start(10)
        else:
            self.start_button.setText("Start")
            self.timer.stop()

    def update_progress(self):
        try:
            ser.flushInput()
            getData = ser.readline()

            if not getData:
                return

            dataString = getData.decode('utf-8').rstrip()
            readings = dataString.split(",")

            if len(readings) == 10 and readings[0] != '':
                readings = np.array(readings, dtype=float).reshape(1, -1)
                readings = sc.transform(readings)

                detection = ann.predict(readings)
                prediction_class_index = np.argmax(detection)

                for i in range(numClasses):
                    progress = int(detection[0][i] * 100)
                    self.progress_values[i] = progress

                    self.progress_bars[i].setValue(self.progress_values[i])

                    self.labels[i].setText(f"{classes[i]}")

                final_prediction = classes[prediction_class_index]
                final_probability = detection[0][prediction_class_index] * 100
                self.prediction_label.setText(f"Prediction: {final_prediction} ({final_probability:.2f}%)")

                if all(value == 100 for value in self.progress_values):
                    self.timer.stop()

        except Exception as e:
            print(f"Error reading or processing data: {e}")

class CollectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Gesture")
        self.setGeometry(100, 100, 400, 350)

        self.layout = QVBoxLayout()

        text = "Current Gestures: "
        for i in classes:
            text = text + i + ", "
        self.classes_label = QLabel(text, self)
        self.layout.addWidget(self.classes_label)
        self.info_label = QLabel("The program will quit after collecting 5000 samples in 5 rounds. Slightly change how the gesture is done between rounds.", self)
        self.layout.addWidget(self.info_label)
        
        input_layout = QHBoxLayout()
        self.new_gesture_input = QLineEdit(self)
        self.new_gesture_input.setPlaceholderText("Enter new gesture name")
        input_layout.addWidget(self.new_gesture_input)
        
        self.start_sampling_button = QPushButton("Start Sampling", self)
        self.start_sampling_button.clicked.connect(self.startSample)
        input_layout.addWidget(self.start_sampling_button)
        
        self.layout.addLayout(input_layout)
        
        self.sample_label = QLabel("Round 1/5: Samples collected 0/1000", self)
        self.layout.addWidget(self.sample_label)
        
        self.status_label = QLabel("Status: Waiting to start", self)
        self.layout.addWidget(self.status_label)
        
        button_layout = QHBoxLayout()
        self.back_button = QPushButton("Back to Prediction Window", self)
        self.back_button.clicked.connect(self.go_back)
        button_layout.addWidget(self.back_button)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sample)
        self.sample_count = 0
        self.round_count = 1
        self.gesture_name = ""
        self.sampling = False
        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.start_round)

    def go_back(self):
        self.hide()
        prediction_window.show()
        
    def startSample(self):
        self.gesture_name = self.new_gesture_input.text().strip()
        if not self.gesture_name:
            return
        self.sample_count = 0
        self.round_count = 1
        self.status_label.setText("Status: Waiting 10 seconds before round 1")
        self.delay_timer.start(10000)

    def start_round(self):
        self.sample_count = 0
        self.status_label.setText(f"Status: Collecting samples for round {self.round_count}")
        self.sampling = True
        self.timer.start(1)

    def sample(self):
        if not self.sampling:
            return
            
        try:
            ser.flushInput()
            getData = ser.readline()
            
            if not getData:
                return
                
            dataString = getData.decode('utf-8').rstrip()
            readings = dataString.split(",")
            
            if len(readings) == 16 and readings[0] != '':
                readings.append(self.gesture_name)
                with open('Main/Dataset2.csv', 'a') as f:
                    f.write(','.join(readings) + '\n')
                    
                self.sample_count += 1
                self.sample_label.setText(f"Round {self.round_count}/5: Samples collected {self.sample_count}/1000")
                
                if self.sample_count >= 1000:
                    if self.round_count < 5:
                        self.sampling = False
                        self.timer.stop()
                        self.round_count += 1
                        self.status_label.setText(f"Status: Waiting 5 seconds before round {self.round_count}")
                        self.delay_timer.start(5000)
                    else:
                        self.sampling = False
                        self.timer.stop()
                        self.status_label.setText("Finished all rounds. Quitting program...")
                        classes.append(self.gesture_name)
                        self.close()
                        QApplication.quit()
                    
        except Exception as e:
            print(f"Error during sampling: {e}")


app = QApplication(sys.argv)
prediction_window = PredictionWindow()
collection_window = CollectionWindow()
collection_window.hide()
prediction_window.show()
sys.exit(app.exec_())