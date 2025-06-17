# Vicarius vRx Event Processor

This project is a **serverless ETL** designed to run as a **Cloud Run Job** every **4 hours**.  
It extracts events from **Vicarius vRx**, processes them, and stores them in **Google Cloud Storage (GCS)** in **NDJSON** format.  
Execution alerts (only key events) are sent to Slack, and detailed step-by-step logs are sent to Cloud Run Jobs Events/Logs for full verbosity.

## Additional Variables & Data

- GCP bucket name  
- Vicarius vRx base URL (e.g. `api.vicarius.com`)  
- GCP project name  

The variable `time_window` defines the time diff from which logs will be pulled (Every `$time_window` hours)

## Description

The main script (`main.py`) performs the following tasks:

1. **Load the last timestamp** from `gs://BUCKET_NAME/state/timestamp.txt`.  
2. **Call the Vicarius vRx API** to fetch vulnerability events since that timestamp.  
3. **Process the events**, clean them, and save them as **NDJSON** under `gs://BUCKET_NAME/`.  
4. **Update the timestamp** in `timestamp.txt` only if events were successfully processed.  
5. **Send notifications to Slack** for errors or successful runs.  
6. **Log to GCP** at extra-verbose level so that Cloud Run Jobs show full execution logs, while Slack only shows overall success or failure.

## Project Structure

```
│── main.py              # Main script that runs the ETL process
│── requirements.txt     # Python dependencies for Cloud Run
│── Procfile             # Necessary for GCP CR to treat this as a non-web application
```

# How It Works

- **Automatic Execution:** Scheduled via Cloud Scheduler to run every 4 hours as a Cloud Run Job.
- **Serverless ETL:** No dedicated servers; Google Cloud handles everything.
- **Persistent Timestamp:** Reads and writes the last-processed timestamp in `gs://BUCKET_NAME/state/timestamp.txt` to prevent duplicates.
- **Data Format:** Events are stored in NDJSON, optimized for ingestion by Google SecOps.
- **Error Handling:** API or execution failures trigger Slack alerts.

# Dependencies

Python packages:

- `google-cloud-storage`
- `google-cloud-secret-manager`
- `requests`
- `datetime`
- `pytz`

# Final Notes

- Built to run as a Cloud Run Job.
- If the API returns no events, the timestamp is not updated—ensuring the next run covers the same time window.
- Execution logs are available in Cloud Logging; run history is in Cloud Run Jobs > Executions.
