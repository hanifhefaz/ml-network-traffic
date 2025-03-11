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
    csv_file = 'updated_file.csv'
    last_line_count = 0

    while True:
        current_line_count = sum(1 for line in open(csv_file))
        if current_line_count > last_line_count:
            # Read the CSV file with proper delimiter and quoting
            new_data = pd.read_csv(csv_file, delimiter=',', quotechar='"')

            # Debugging line to check columns
            print("Columns in new_data:", new_data.columns)

            # Strip whitespace from column names
            new_data.columns = new_data.columns.str.strip()

            # Check if required columns exist
            required_columns = ['Time', 'Length', 'Class']
            if not all(col in new_data.columns for col in required_columns):
                print(f"Missing columns: {set(required_columns) - set(new_data.columns)}")
                last_line_count = current_line_count
                time.sleep(10)
                continue  # Skip this iteration if required columns are missing

            # Prepare the data for prediction
            new_data_cleaned = new_data[['Time', 'Length']]  # Only use Time and Length for prediction

            # Standardize and predict
            X_new = scaler.transform(new_data_cleaned)
            predictions = model.predict(X_new)

            # Print predictions for debugging
            print("Predictions:", predictions)

            # Add predictions to the DataFrame
            new_data['Predicted_Class'] = np.where(predictions == 1, 'Normal', 'Anomaly')  # Adjust based on your model's output

            # Check for anomalies and create alerts
            anomalies = new_data[new_data['Predicted_Class'] == 'Anomaly']
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
    traffic_data = pd.read_csv('updated_file.csv')  # Load your traffic data

    # Preprocess the data if necessary (e.g., scaling)
    X = traffic_data[['Time', 'Length']]  # Select relevant features

    # Standardize the data
    X_scaled = scaler.transform(X)

    # Predict using the trained model
    predictions = model.predict(X_scaled)

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