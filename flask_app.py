from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_cors import CORS
import os
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow access from other websites

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

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/set-threshold', methods=['POST'])
def set_threshold():
    try:
        threshold = request.json.get('temperature')
        if threshold is None:
            return jsonify({"error": "Temperature threshold missing"}), 400
            
        app.config['TEMP_THRESHOLD'] = float(threshold)
        return jsonify({"status": "success", "threshold": app.config['TEMP_THRESHOLD']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
# Route to receive sensor data
@app.route('/data', methods=['POST'])
def receive_data():
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
        # Get ALL data without filtering
        data = SensorData.query.all()
        
        result = []
        for entry in data:
            result.append({
                "timestamp": entry.timestamp.isoformat(),
                "temperature": entry.temperature,
                "humidity": entry.humidity
            })
            
        return jsonify(result)
    except Exception as e:
        app.logger.exception("❌ Failed in GET /data")
        return jsonify({"error": str(e)}), 500

# Route for prediction
@app.route('/predict', methods=['GET'])
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
            "message": "Average temperature prediction"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Test endpoint
@app.route('/test-endpoint')
def test_endpoint():
    return "CI/CD Test Successful! Deployment is working.", 200

if __name__ == '__main__':
    app.run()