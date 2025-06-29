from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_cors import CORS
import os
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow access from other websites

# Configure SQLite database - SIMPLIFIED PATH
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sensor_data.db'  # 3 slashes for relative path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)  # Simplified initialization

API_KEYS = {
    "iot_device": "DEVICE_SECRET_123",
    "dashboard": "DASHBOARD_SECRET_456"
}

if 'DEFAULT' in API_KEYS['iot_device']:
    print("WARNING: Using default API keys - not secure!")

# Authentication decorator
def api_key_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            if not api_key or api_key != API_KEYS.get(role):
                return jsonify({"error": "Unauthorized"}), 401
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Sensor data model
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Use DateTime type
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)

# Create database tables within app context
with app.app_context():
    db.create_all()


@app.route('/env-test')
def env_test():
    return jsonify({
        "IOT_API_KEY": os.getenv('IOT_API_KEY'),
        "DASHBOARD_API_KEY": os.getenv('DASHBOARD_API_KEY')
    })

# Route to create database manually
@app.route('/create-db')
def create_db():
    try:
        db.create_all()
        return "Database tables created successfully!"
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/data', methods=['POST'])
@api_key_required('iot_device')
def receive_data():
    try:
        data = request.json

        # Create new entry WITHOUT timestamp (auto-generated)
        new_entry = SensorData(
            device_id=data['device_id'],
            temperature=data['temperature'],
            humidity=data['humidity']
        )

        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data', methods=['GET'])
@api_key_required('dashboard')
def get_data():
    try:
        # Get ALL data without filtering
        data = SensorData.query.all()

        result = []
        for entry in data:
            result.append({
                "id": entry.id,
                "timestamp": entry.timestamp.isoformat(),
                "temperature": entry.temperature,
                "humidity": entry.humidity
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/predict', methods=['GET'])
@api_key_required('dashboard')
def predict():
    try:
        # Get last 6 hours of data
        time_threshold = datetime.utcnow() - timedelta(hours=6)

        data = SensorData.query.filter(
            SensorData.timestamp >= time_threshold
        ).all()

        # Simple average prediction
        temps = [entry.temperature for entry in data]
        avg_temp = sum(temps) / len(temps) if temps else 0

        return jsonify({
            "prediction": round(avg_temp, 1),
            "message": "Average temperature prediction",
            "data_points": len(temps)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()