import uuid
import time
from threading import Thread 
from flask import Flask, request, jsonify

app = Flask(__name__)
jobs = {}
def simulate_processing(job_id):
    jobs[job_id]["status"] = "RUNNING"
    # Simulate a task that takes several seconds.
    time.sleep(8)
    jobs[job_id]["result"] = {
        "message": "Simulated analytics completed successfully.",
        "records_processed": 1000
    }

    jobs[job_id]["status"] = "SUCCEEDED"


@app.route("/",methods=["GET"])
def home():
    return "Hello COM3033"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "UP"
    }), 200


@app.route("/metadata", methods=["GET"])
def metadata():
    return jsonify({
        "service_id": "week2-demo-service",
        "name": "COM3033 Week 2 Analytics Service",
        "version": "1.0",
        "supported_tasks": [
            "regional-summary"
        ],
        "supported_engines": [
            "mapreduce",
            "spark"
        ]
    }), 200


@app.route("/jobs", methods=["POST"])
def create_job():
    if not request.is_json:
        return jsonify({
            "error": "INVALID_REQUEST",
            "message": "Request body must be JSON."
        }), 400
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "INVALID_JSON",
            "message": "The JSON body could not be parsed."
        }), 400
    required_fields = ["task", "engine", "input_reference"]
    missing_fields = [
        field for field in required_fields
        if field not in data
    ]

    if missing_fields:
        return jsonify({
            "error": "MISSING_FIELDS",
            "message": "One or more required fields are missing.",
            "missing_fields": missing_fields
        }), 400
    if not isinstance(data["task"], str) or not data["task"].strip():
        return jsonify({
            "error": "INVALID_TASK",
            "message": "task must be a non-empty string."
        }), 400
    if data["engine"] not in ["mapreduce", "spark"]:
        return jsonify({
            "error": "INVALID_ENGINE",
            "message": "engine must be either mapreduce or spark."
        }), 400
    if not isinstance(data["input_reference"], str) or not data["input_reference"].strip():
        return jsonify({
            "error": "INVALID_INPUT_REFERENCE",
            "message": "input_reference must be a non-empty string."
        }), 400
    if "parameters" in data and not isinstance(data["parameters"], dict):
        return jsonify({
            "error": "INVALID_PARAMETERS",
            "message": "parameters must be a JSON object."
        }), 400
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "task": data["task"],
        "engine": data["engine"],
        "input_reference": data["input_reference"],
        "parameters": data.get("parameters", {}),
        "status": "QUEUED",
        "result": None
    }
    Thread(
        target=simulate_processing,
        args=(job_id,),
        daemon=True
    ).start()
    return jsonify({
        "job_id": job_id,
        "status": "QUEUED"
    }), 202


@app.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    job = jobs.get(job_id)
    
    if job is None:
        return jsonify({
            "error": "JOB_NOT_FOUND",
            "message": "No job exists with the supplied job_id."
        }), 404
    return jsonify({
        "job_id": job["job_id"],
        "task": job["task"],
        "engine": job["engine"],
        "status": job["status"]
    }), 200


@app.route("/jobs/<job_id>/results", methods=["GET"])
def get_job_results(job_id):
    job = jobs.get(job_id)
    
    if job is None:
        return jsonify({
            "error": "JOB_NOT_FOUND",
            "message": "No job exists with the supplied job_id."
        }), 404
    if job["status"] != "SUCCEEDED":
        return jsonify({
            "error": "RESULT_NOT_READY",
            "message": "The job has not completed yet.",
            "status": job["status"]
        }), 409
    return jsonify({
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"]
    }), 200

if __name__ == "__main__":
    app.run(debug=True)

