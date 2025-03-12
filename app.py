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
    csv_file = 'updated_data_net.csv'
    last_line_count = 0

    while True:
        current_line_count = sum(1 for line in open(csv_file))
        if current_line_count > last_line_count:
            new_data = pd.read_csv(csv_file, delimiter=',', quotechar='"')
            print("Columns in new_data:", new_data.columns)

            new_data.columns = new_data.columns.str.strip()

            required_columns = ['Time', 'Length']
            if not all(col in new_data.columns for col in required_columns):
                print(f"Missing columns: {set(required_columns) - set(new_data.columns)}")
                last_line_count = current_line_count
                time.sleep(10)
                continue

            new_data_cleaned = new_data[['Time', 'Length']]
            X_new = scaler.transform(new_data_cleaned)
            predictions = model.predict(X_new)

            print("Predictions:", predictions)

            new_data['Predicted_Class'] = np.where(predictions == 1, 'Normal', 'Anomaly')

            anomalies = new_data[new_data['Predicted_Class'] == 'Anomaly']
            if not anomalies.empty:
                alerts.extend(anomalies.to_dict(orient='records'))

            last_line_count = current_line_count

        time.sleep(10)
# def send_slack_notification(message):
#     webhook_url = 'https://hooks.slack.com/services/your/app/hook/url'
#     payload = {'text': message}
#     requests.post(webhook_url, json=payload)

# # Usage
# anomaly_message = "Anomaly detected in the system at 12:00 PM."
# send_slack_notification(anomaly_message)
@app.route('/')
def index():
    return render_template('index.html', alerts=alerts)

@app.route('/alerts')
def get_alerts():
    global alerts

    # Filter alerts for only "Anomaly" type
    anomaly_alerts = [alert for alert in alerts if alert.get('Predicted_Class') == 'Anomaly']

    alerts_df = pd.DataFrame(anomaly_alerts)
    alerts_df.fillna('', inplace=True)

    return jsonify(alerts_df.to_dict(orient='records'))

@app.route('/normal_traffic')
def get_normal_traffic():
    traffic_data = pd.read_csv('updated_data_net.csv')
    X = traffic_data[['Time', 'Length']]
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)

    traffic_data['Anomaly'] = predictions
    normal_traffic = traffic_data[traffic_data['Anomaly'] == 1]

    normal_traffic.fillna('', inplace=True)
    normal_list = normal_traffic.to_dict(orient='records')
    
    return jsonify(normal_list)

if __name__ == '__main__':
    threading.Thread(target=monitor_traffic, daemon=True).start()
    app.run(debug=True)