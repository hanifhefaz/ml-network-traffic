from flask import Flask, render_template, jsonify
import pandas as pd
import joblib
import numpy as np
import time
import threading

app = Flask(__name__)

# Load the model and scaler
model = joblib.load('anomaly_detection_model.pkl')
scaler = joblib.load('scaler.pkl')

# Global variable to hold alerts
alerts = []

def monitor_traffic():
    global alerts
    csv_file = 'traffic.csv'
    last_line_count = 0

    while True:
        current_line_count = sum(1 for line in open(csv_file))
        if current_line_count > last_line_count:
            new_data = pd.read_csv(csv_file)
            print(new_data.columns)  # Debugging line to check columns

            # Only drop existing columns
            columns_to_drop = ['Timestamp', 'Source IP', 'Destination IP', 'Protocol']
            existing_columns = [col for col in columns_to_drop if col in new_data.columns]
            new_data.drop(existing_columns, axis=1, inplace=True)

            # Standardize and predict
            X_new = scaler.transform(new_data)
            predictions = model.predict(X_new)

            # Print predictions for debugging
            print("Predictions:", predictions)

            # Add predictions to the DataFrame
            new_data['Anomaly'] = predictions
            new_data['Anomaly'] = np.where(new_data['Anomaly'] == -1, 'Anomaly', 'Normal')

            # Check for anomalies and create alerts
            anomalies = new_data[new_data['Anomaly'] == 'Anomaly']
            if not anomalies.empty:
                alerts.extend(anomalies.to_dict(orient='records'))

            last_line_count = current_line_count

        time.sleep(10)

@app.route('/')
def index():
    return render_template('index.html', alerts=alerts)

@app.route('/alerts')
def get_alerts():
    return jsonify(alerts)

@app.route('/normal_traffic')
def get_normal_traffic():
    # Load the current traffic data
    traffic_data = pd.read_csv('traffic.csv')  # Load your traffic data

    # Preprocess the data if necessary (e.g., scaling)
    X = traffic_data.drop(['Timestamp', 'Source IP', 'Destination IP', 'Protocol'], axis=1)

    # Standardize the data
    X_scaled = scaler.transform(X)

    # Predict using the trained model
    predictions = model.predict(X_scaled)  # Assuming 'model' is your trained model

    # Add predictions to the DataFrame
    traffic_data['Anomaly'] = predictions

    # Filter normal traffic (assuming 1 indicates normal traffic)
    normal_traffic = traffic_data[traffic_data['Anomaly'] == 1]  # Adjust based on your model's output

    # Convert to list of dictionaries for JSON response
    normal_list = normal_traffic.to_dict(orient='records')
    
    return jsonify(normal_list)
if __name__ == '__main__':
    threading.Thread(target=monitor_traffic, daemon=True).start()
    app.run(debug=True)