from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from flask_cors import CORS
import os
import pytz
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity
)
from prophet import Prophet
import pandas as pd

MANILA = pytz.timezone("Asia/Manila")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow access from other websites


app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY","super-secret")
jwt = JWTManager(app)
# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/raiceen/mysite/sensor_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Sensor data model
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)

class Threshold(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float, nullable=False)

# Create database tables
with app.app_context():
    db.create_all()
    if Threshold.query.first() is None:
        db.session.add(Threshold(value=30.0))
        db.session.commit()

@app.route('/auth/device', methods=['POST'])
def device_login():
    device_id = request.json.get('device_id')
    # in prod you’d validate against a table of valid devices
    if not device_id:
        return jsonify({"error":"Missing device_id"}), 400
    token = create_access_token(identity=device_id)
    return jsonify(access_token=token), 200


@app.route('/set-threshold', methods=['POST'])
def set_threshold():
    t = Threshold.query.first()
    new_val = request.json.get('temperature', None)
    if new_val is None:
        return jsonify({"error":"Missing temperature"}), 400
    t.value = float(new_val)
    db.session.commit()
    return jsonify({"threshold": t.value}), 200

@app.route('/threshold', methods=['GET'])
def get_threshold():
    return jsonify({"threshold": Threshold.query.first().value})

# Route to receive sensor data
@app.route('/data', methods=['POST'])
@jwt_required()
def receive_data():
    device_id = get_jwt_identity()
    payload = request.json
    new_entry = SensorData(
        device_id=device_id,
        temperature=payload['temperature'],
        humidity=payload['humidity']
    )
    try:
        data = request.json
        new_entry = SensorData(
            device_id=data['device_id'],
            temperature=data['temperature'],
            humidity=data['humidity']
        )

        # Alert check moved inside the function
        if new_entry.temperature > app.config.get('TEMP_THRESHOLD', 30):
            app.logger.warning(f"ALERT: Temperature {new_entry.temperature} exceeds threshold!")

        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get historical data
@app.route('/data', methods=['GET'])
def get_data():
    try:
        data = SensorData.query.all()
        result = []

        for entry in data:
            # Treat your stored timestamp as UTC…
            utc_dt = entry.timestamp.replace(tzinfo=timezone.utc)
            # …then convert it into Manila time
            local_dt = utc_dt.astimezone(MANILA)

            result.append({
                "timestamp": local_dt.isoformat(),  # e.g. '2025-06-29T19:52:30+08:00'
                "temperature": entry.temperature,
                "humidity":    entry.humidity
            })

        return jsonify(result), 200

    except Exception as e:
        app.logger.exception("❌ Failed in GET /data")
        return jsonify({"error": str(e)}), 500

# Route for prediction
@app.route('/predict', methods=['GET'])
def predict():
    data = SensorData.query.order_by(SensorData.timestamp).all()
    if len(data) < 10:
        return jsonify({"error":"Not enough data"}), 400

    # Prepare DataFrame
    df = pd.DataFrame([{
        "ds": d.timestamp,
        "y": d.temperature
    } for d in data])

    m = Prophet(daily_seasonality=False, yearly_seasonality=False)
    m.fit(df)

    hours = int(request.args.get('hours', 6))
    future = m.make_future_dataframe(periods=hours, freq='H')
    forecast = m.predict(future)
    point = forecast.iloc[-1]

    return jsonify({
        "future_time": point['ds'].isoformat(),
        "prediction": round(point['yhat'], 1)
    })

# Test endpoint
@app.route('/test-endpoint')
def test_endpoint():
    return "CI/CD Test Successful! Deployment is working.", 200

@app.route('/healthz')
def healthz():
    return "OK", 200

if __name__ == '__main__':
    app.run()