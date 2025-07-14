import sys
import numpy as np
import pandas as pd
import tensorflow as tf
import pyautogui
import time
import serial

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, QDateTime

arduino_port = "COM13"
dataset = pd.read_csv('CrazyControllers/Firmware/Dataset.csv')
X = dataset.iloc[:, :-1].values 
y = dataset.iloc[:, -1].values

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
classes = list(label_encoder.classes_)
y_encoded = to_categorical(y_encoded)
numClasses = len(classes)

X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=0)
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

ann = tf.keras.models.Sequential([
    tf.keras.layers.Dense(units=7, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(units=128, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(units=numClasses, activation='softmax')
])
ann.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
ann.fit(X_train, y_train, batch_size=256, epochs=25, validation_split=0.2)

ser = serial.Serial(arduino_port, 9600)
time.sleep(5)

class ConfigWindow(QWidget):
    def __init__(self, gesture_action_map, gestures, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Gesture Actions")
        self.setGeometry(150, 150, 400, 300)
        self.layout = QVBoxLayout()
         
        self.dropdown_map = {}   
        actions = ["None", "left", "right", "click", "space", "scroll_up", "scroll_down"]

        for gesture in gestures:
            h_layout = QHBoxLayout()
            label = QLabel(f"{gesture}:")
            dropdown = QComboBox()
            dropdown.addItems(actions)
            dropdown.setCurrentText(gesture_action_map.get(gesture, "None"))
            self.dropdown_map[gesture] = dropdown
            h_layout.addWidget(label)
            h_layout.addWidget(dropdown)
            self.layout.addLayout(h_layout)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_config)
        self.layout.addWidget(save_button)

        self.setLayout(self.layout)
        self.gesture_action_map = gesture_action_map

    def save_config(self):
        for gesture, dropdown in self.dropdown_map.items():
            self.gesture_action_map[gesture] = dropdown.currentText()
        self.close()

# GUI: Real-time Prediction
class PredictionWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gesture Classifier")
        self.setGeometry(100, 100, 400, 400)
        self.layout = QVBoxLayout()

        self.prediction_label = QLabel("Neural Network Prediction: ", self)
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

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.toggle_progress)
        self.layout.addWidget(self.start_button)

        self.data_button = QPushButton("Add Gesture", self)
        self.data_button.clicked.connect(self.collect)
        self.layout.addWidget(self.data_button)

        self.automation_button = QPushButton("Enable Control", self)
        self.automation_button.clicked.connect(self.toggle_automation)
        self.layout.addWidget(self.automation_button)

        self.config_button = QPushButton("Configure Gesture Actions", self)
        self.config_button.clicked.connect(self.open_config_window)
        self.layout.addWidget(self.config_button)

        self.setLayout(self.layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.progress_values = [0] * numClasses

        self.automation_enabled = False
        self.last_action_time = 0
        self.action_cooldown = 1000  # ms

        self.gesture_action_map = {
            "rest": "None",
            "Left": "left",
            "Right": "right",
            "Click": "click",
            "Space": "space",
            "Scroll Up": "scroll_up",
            "Scroll Down": "scroll_down"
        }

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

    def toggle_automation(self):
        self.automation_enabled = not self.automation_enabled
        self.automation_button.setText("Disable Control" if self.automation_enabled else "Enable Control")

    def open_config_window(self):
        self.config_window = ConfigWindow(self.gesture_action_map, classes, self)
        self.config_window.show()

    def update_progress(self):
        try:
            ser.flushInput()
            getData = ser.readline()

            if not getData:
                return

            dataString = getData.decode('utf-8').rstrip()
            readings = dataString.split(",")

            if len(readings) == 7 and readings[0] != '':
                readings = np.array(readings, dtype=float).reshape(1, -1)
                readings = sc.transform(readings)

                detection = ann.predict(readings)
                prediction_class_index = np.argmax(detection)

                for i in range(numClasses):
                    self.progress_bars[i].setValue(int(detection[0][i] * 100))
                    self.labels[i].setText(f"{classes[i]}")

                final_prediction = classes[prediction_class_index]
                final_probability = detection[0][prediction_class_index] * 100
                self.prediction_label.setText(f"Neural Network Prediction: {final_prediction} ({final_probability:.2f}%)")

                if self.automation_enabled:
                    self.perform_automation(final_prediction)

        except Exception as e:
            print(f"Error reading or processing data: {e}")

    def perform_automation(self, gesture):
        current_time = QDateTime.currentMSecsSinceEpoch()
        if current_time - self.last_action_time < self.action_cooldown:
            return

        self.last_action_time = current_time
        action = self.gesture_action_map.get(gesture)

        try:
            if action == "left":
                pyautogui.press("left")
            elif action == "right":
                pyautogui.press("right")
            elif action == "click":
                pyautogui.click()
            elif action == "space":
                pyautogui.press("space")
            elif action == "scroll_up":
                pyautogui.scroll(300)
            elif action == "scroll_down":
                pyautogui.scroll(-300)
        except Exception as e:
            print(f"Automation error: {e}")

class CollectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Gesture")
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout()

        current_gesture_text = "Current Gestures: " + ", ".join(classes)
        self.classes_label = QLabel(current_gesture_text, self)
        self.info_label = QLabel("Collects 5 rounds of 1000 samples. Slightly vary gestures.", self)
        self.sample_label = QLabel("Round 1/5: Samples collected 0/1000", self)
        self.status_label = QLabel("Status: Waiting to start", self)

        self.layout.addWidget(self.classes_label)
        self.layout.addWidget(self.info_label)

        input_layout = QHBoxLayout()
        self.new_gesture_input = QLineEdit(self)
        self.new_gesture_input.setPlaceholderText("Enter new gesture name")
        input_layout.addWidget(self.new_gesture_input)

        self.start_sampling_button = QPushButton("Start Sampling", self)
        self.start_sampling_button.clicked.connect(self.startSample)
        input_layout.addWidget(self.start_sampling_button)

        self.layout.addLayout(input_layout)
        self.layout.addWidget(self.sample_label)
        self.layout.addWidget(self.status_label)

        self.back_button = QPushButton("Back to Prediction Window", self)
        self.back_button.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_button)

        self.setLayout(self.layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sample)

        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.start_round)

        self.sample_count = 0
        self.round_count = 1
        self.gesture_name = ""
        self.sampling = False

    def go_back(self):
        self.hide()
        prediction_window.show()

    def startSample(self):
        self.gesture_name = self.new_gesture_input.text().strip()
        if not self.gesture_name:
            return
        self.sample_count = 0
        self.round_count = 1
        self.status_label.setText("Waiting 10 seconds before round 1")
        self.delay_timer.start(10000)

    def start_round(self):
        self.sample_count = 0
        self.status_label.setText(f"Collecting samples for round {self.round_count}")
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

            if len(readings) == 7 and readings[0] != '':
                readings.append(self.gesture_name)
                with open('CrazyControllers/Firmware/Dataset.csv', 'a') as f:
                    f.write(','.join(readings) + '\n')

                self.sample_count += 1
                self.sample_label.setText(f"Round {self.round_count}/5: Samples collected {self.sample_count}/1000")

                if self.sample_count >= 1000:
                    if self.round_count < 5:
                        self.sampling = False
                        self.timer.stop()
                        self.round_count += 1
                        self.status_label.setText(f"Waiting 5 seconds before round {self.round_count}")
                        self.delay_timer.start(5000)
                    else:
                        self.sampling = False
                        self.timer.stop()
                        self.status_label.setText("Finished all rounds. Restart to train again.")
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
