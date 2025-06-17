from google.cloud import storage
import logging
import json
import os
import requests
from datetime import datetime, timezone, time, timedelta
import time as t
from decimal import Decimal
import pytz
import sys

project_id = "" # PROJECT ID GCP
baseurl = "" # BASE URL i.e. https://api.vicarius.cloud
endpoint = "vicarius-external-data-api/incidentEvent/filter" # API ENDPOINT
BUCKET_NAME = "" # BUCKET NAME
TIMESTAMP_OBJECT = "state/timestamp.txt"
time_window = 4 # Hours
timezone = "" # i.e. "America/Chicago"

VRX_API_URL = baseurl + endpoint
event_quantity_request = 500

def get_gcp_secret(secret_id, version_id="latest"):
    """
    Retrieves a secret from Google Secret Manager.
    """
    # Return API Key, set as env vars from secrets.
    secret = os.environ[secret_id]
    return secret

# Establish secrets globally:
VICARIUS_API_KEY = get_gcp_secret("VICARIUS_API_KEY")
SLACK_WEBHOOK_URL = get_gcp_secret("SLACK_WEBHOOK_URL")

# Configuracion inicial de logging - formato.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_time_data(hours_ago=time_window, timezone_str=timezone): # EL NUEVO
    """
    Centralized function to get all required timestamps.
    
    Args:
        hours_ago (int): How many hours before now to calculate.
        timezone_str (str): Timezone string (default: "America/Mexico_City").

    Returns:
        dict: A dictionary containing multiple time formats:
            - `current_time` (datetime): Current timestamp (timezone-aware).
            - `past_time` (datetime): Timestamp `hours_ago` before now.
            - `folder_date_str` (str): `YYYY/MM/DD/` for folder naming.
            - `log_timestamp_str` (str): Readable log timestamp.
            - `epoch_ns` (int): Nanoseconds for current time.
            - `past_epoch_ns` (int): Nanoseconds for past time.
            - `start_time` (float): Timestamp for execution time tracking.
    """
    # Load timezone
    local_tz = pytz.timezone(timezone_str)
    
    # Get current time
    current_time = datetime.now(local_tz)
    
    # Get past time (X hours ago)
    past_time = current_time - timedelta(hours=hours_ago)
    
    # Format different representations
    folder_date_str = f"{current_time.year}/{current_time.month:02d}/{current_time.day:02d}/"
    log_timestamp_str = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')
    
    # Convert to epoch timestamps
    epoch_ns = int(current_time.timestamp() * 1_000_000_000)
    past_epoch_ns = int(past_time.timestamp() * 1_000_000_000)

    start_hour_str = past_time.strftime("%H_%M")
    end_hour_str   = current_time.strftime("%H_%M")
    
    # Execution start time (for duration tracking)
    start_time = t.time()

    return {
        "current_time": current_time,
        "past_time": past_time,
        "folder_date_str": folder_date_str,
        "log_timestamp_str": log_timestamp_str,
        "epoch_ns": epoch_ns,
        "past_epoch_ns": past_epoch_ns,
        "start_time": start_time,
        "start_hour_str": start_hour_str, 
        "end_hour_str": end_hour_str
    }

# Diccionario con valores de tiempos:
time_data = get_time_data()
    # 2025-02-18 19:50:10.609019-06:00 - RFC 3339 (ISO 8601)
current_time = time_data["current_time"]
    # 2025-02-18 19:15:12 CST (Antes)
past_time = time_data["past_time"]
    # Ej. 2025/02/18/
folder_date_str = time_data["folder_date_str"]
    # 2025-02-18 19:15:12 CST (Ahora)
log_timestamp_str = time_data["log_timestamp_str"]
    # nanoseconds - 1739927712033682176 (Ahora)
epoch_ns = time_data["epoch_ns"]
    # nanoseconds - 1739927712033682176 (Antes)
past_epoch_ns = time_data["past_epoch_ns"]
    # Ej. 16_00 (Antes)
start_hour_str = time_data["start_hour_str"]
    # Ej. 16_00 (Ahora)
end_hour_str = time_data["end_hour_str"]


start_time = time_data["start_time"]


def save_timestamp(ts_str):
    """
    Overwrites the file 'gs://BUCKET_NAME/TIMESTAMP_OBJECT' with the string `ts_str`.
    """
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(TIMESTAMP_OBJECT)

    blob.upload_from_string(str(ts_str))
    print_logs(f"Saved timestamp \"{ts_str}\" to gs://{BUCKET_NAME}/{TIMESTAMP_OBJECT}", 1)



def load_timestamp() -> str:
    """
    Returns the timestamp as a string from 'gs://BUCKET_NAME/TIMESTAMP_OBJECT'.
    If no file exists, returns None.
    """
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(TIMESTAMP_OBJECT)

    if not blob.exists():
        return None

    ts_str = blob.download_as_text().strip()
    print_logs(f"Loaded timestamp \"{ts_str}\" from gs://{BUCKET_NAME}/{TIMESTAMP_OBJECT}", 1)
    return ts_str


def print_logs(message, level=1):

    """
    Centralized logging function.

    Sends BOTH a stdout message for GCP Logging AND a Slack notification

    Exits if a critical error occurred, preventing further execution.
    
    Args:
        message (str): The message to log.
        level (int): Logging level (1=INFO, 2=WARNING, 3=ERROR, 4=CRITICAL, 5=GLOBAL_ERROR).

    """
    if level == 1:
        logging.info(message)
    elif level == 2:
        logging.warning(message)
    elif level == 3:
        logging.error(message)
    
    # Falla conocida; paro total
    elif level == 4:    
        logging.critical(message)
        send_slack_notification(
                f" [CRITICAL] [{current_time}] | Cloud Run Job Failed.", 
                error_message=str(message)
                )
        print_logs("-------------------- END ---------------------",1)
        sys.exit(1)

    # Falla desconocida; paro total
    elif level == 5:
        logging.exception(message)
        send_slack_notification(
                f"🟪 [CRITICAL/GLOBAL] [{current_time}] Cloud Run Job failed in an unexpected way.",
                error_message=str(message)
                )
        print_logs("-------------------- END ---------------------",1)
        sys.exit(1)  # If it's a critical failure, stop execution
    else:
        logging.debug(message)  # Default to debug

def upload_to_gcs(trailing_count, processed_events):
    
    """
        Uploads the raw NDJSON string to GCS.
    """

    client = storage.Client()

    file_name = f"events_{start_hour_str}-{end_hour_str}-{trailing_count}.json"  # Use `.json` to be safe for SIEM
    gcs_path = folder_date_str + file_name

    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)

    try:
        # Storing the NDJSON to the bucket, from string:
        blob.upload_from_string(processed_events.encode("utf-8"), content_type="application/json")

        bucket_full_path = f"gs://{BUCKET_NAME}/{gcs_path}"
        print_logs(f" [INFO] Logs uploaded to {bucket_full_path}", 1)
        e = None
        return "SUCCESS", bucket_full_path, e
    except Exception as e:
        return "FAILURE", None, e

def fetch_vicarius_events(VICARIUS_API_KEY, event_quantity_request, past_epoch_ns, max_retries=5, timeout=10):
    """Fetch 500 events from API starting from the given timestamp with error handling."""

    headers = {
        "Accept": "application/json",
        "Vicarius-Token":  VICARIUS_API_KEY
    }
    params = {
    "size": f"{event_quantity_request}",
    "metricActionName": "IncidentEvent",
    "metricAnalyticsEventAction": "IncidentEvent",
    "sort": "+analyticsEventCreatedAtNano",
    "q": f"incidentEventIncidentEventType==DetectedVulnerability;analyticsEventCreatedAtNano>{past_epoch_ns}",
    "from": "0",
    "includeFields": (
        "incidentEventIncidentEventType;"
        "incidentEventEndpoint.endpointId;"
        "incidentEventVulnerability.vulnerabilityId;"
        "incidentEventEndpoint.endpointName;"
        "incidentEventEndpoint.endpointOrganization.organizationName;"
        "incidentEventOrganizationPublisherProducts.organizationPublisherProductsPublisher.publisherName;"
        "incidentEventVulnerability.vulnerabilityExternalReference.externalReferenceExternalId;"
        "incidentEventVulnerability.vulnerabilityExternalReference.externalReferenceUniqueIdentifier;"
        "incidentEventOrganizationPublisherProducts.organizationPublisherProductsProduct.productName;"
        "incidentEventVulnerability.vulnerabilitySensitivityLevel.sensitivityLevelName;"
        "incidentEventEndpoint.endpointHash;"
        "_id;"
        "analyticsEventUpdatedAt;"
        "analyticsEventCreatedAt;"
        "incidentEventEndpoint.operatingSystemId;"
        "incidentEventEndpoint.endpointOrganization.organizationUniqueIdentifier;"
        "incidentEventOrganizationPublisherProducts.organizationPublisherProductsPublisher.publisherUniqueIdentifier;"
        "incidentEventOrganizationPublisherProducts.organizationPublisherProductsProduct.productUniqueIdentifier;"
        "incidentEventVulnerability.vulnerabilityId;"
        "incidentEventVulnerability.sensitivityLevelId;"
        "incidentEventVulnerability.vulnerabilitySummary;"
        "incidentEventVulnerability.vulnerabilitySensitivityLevel.sensitivityLevelUpdatedAt;"
        "incidentEventVulnerability.vulnerabilitySensitivityLevel.sensitivityLevelCreatedAt;"
        "incidentEventVulnerability.vulnerabilityV3ExploitabilityLevel;"
        "incidentEventVulnerability.vulnerabilityV3BaseScore;"
        "analyticsEventCreatedAtNano"
            )
        }

    print_logs(f" [INFO] Fetching events from Vicarius API starting at timestamp [{past_time}] - (Timestamp in nanoseconds: {past_epoch_ns})", 1)

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(VRX_API_URL, headers=headers, params=params, timeout=timeout)

            if response.status_code == 429:  # API rate limit hit
                print_logs(f"[WARNING] API rate limited (HTTP 429). Waiting 60 sec before retry... (Attempt {attempt}/{max_retries})", 2)
                t.sleep(60)  # Just wait 60 seconds and try again
                continue

            response.raise_for_status()  # Raise error if status is not 2xx

            response_data = response.json()
            return response_data, None  # Success

        except requests.exceptions.RequestException as e:
            print_logs(f"[WARNING] API request error: {e} (Attempt {attempt}/{max_retries})", 2)
            if attempt == max_retries:
                return None, e  # Max retries reached → fail

            t.sleep(2)  # Short sleep before retrying (for non-429 errors)

    return None, "Failed after max retries"  # If loop exits without success
    
def send_slack_notification(status, **details):
    """Send formatted message to Slack webhook."""

    if "SUCCESS" in status: 
        COLOR = "#36a64f"
    elif "FAILURE" in status:
        COLOR = "#ff0000"
    elif "INFO" in status:
        COLOR = "#808080"
    else:
        COLOR = "#808080"

    message = {
        "text": status,
        "attachments": [
            {
                "color": COLOR,
                "fields": [{"title": key.replace("_", " ").title(), "value": str(value), "short": False} for key, value in details.items()]
            }
        ]
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=message)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print_logs(f"❌ [ERROR] Failed to send Slack notification: {e}", 3)


def convert_to_rfc3339(nano_timestamp):
    """Convert nanoseconds since epoch to RFC 3339 format."""
    seconds = nano_timestamp // 1_000_000_000
    nanoseconds = nano_timestamp % 1_000_000_000
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=nanoseconds // 1_000)
    return dt.isoformat().replace('+00:00', 'Z')


def process_event(event):
    """Process a single event and return a formatted dictionary."""

    timestamp_ns = event.get('analyticsEventCreatedAtNano')

    processed_event = {
        'timestamp': convert_to_rfc3339(timestamp_ns) if timestamp_ns else "Unknown",
        'event_type': event.get('incidentEventIncidentEventType'),
        'asset_id': event.get('incidentEventEndpoint', {}).get('endpointId'),
        'hostname': event.get('incidentEventEndpoint', {}).get('endpointName'),
        'organization': event.get('incidentEventEndpoint', {}).get('endpointOrganization', {}).get('organizationName'),
        'software_name': event.get('incidentEventOrganizationPublisherProducts', {}).get('organizationPublisherProductsProduct', {}).get('productName'),
        'software_vendor': event.get('incidentEventOrganizationPublisherProducts', {}).get('organizationPublisherProductsPublisher', {}).get('publisherName'),
        'cve_id': event.get('incidentEventVulnerability', {}).get('vulnerabilityExternalReference', {}).get('externalReferenceExternalId'),
        'cve_summary': event.get('incidentEventVulnerability', {}).get('vulnerabilitySummary'),
        'cve_severity': event.get('incidentEventVulnerability', {}).get('vulnerabilitySensitivityLevel', {}).get('sensitivityLevelName'),
        'exploitability_score': event.get('incidentEventVulnerability', {}).get('vulnerabilityV3ExploitabilityLevel'),
        'risk_score': event.get('incidentEventVulnerability', {}).get('vulnerabilityV3BaseScore')
    }
    # Remove keys with None values
    return {k: v for k, v in processed_event.items() if v is not None}

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON Encoder to handle Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def main():
    """Process events from the input JSON file and write formatted events to the output file."""

    print_logs("-------------------- START ---------------------",1)
    global past_epoch_ns
    loaded_ts = load_timestamp() # str
    start_time = t.time()  
    log_count = 0
    trailing_count = 1

    if loaded_ts is not None:
        # This is first run, fallback to "past_time" from your time_data (or any default)
        # e.g., your time_data's "past_epoch_ns" is a fallback
        past_epoch_ns = loaded_ts
    else:
        print_logs("⭐ [FIRST_RUN] No timestamp file found. Likely first run.", 1)
        # Explicitly set the past_epoch_ns
        past_epoch_ns = time_data["past_epoch_ns"]


    while True:
        
        """Iterate in time increments until all events from the last 24 hours are exhausted."""

        # Fetch events from the API
        response_data, failure = fetch_vicarius_events(VICARIUS_API_KEY, event_quantity_request, past_epoch_ns)

        if failure is None:
            if response_data.get('serverResponseResult', {}).get('serverResponseResultCode') == "SUCCESS":
                
                # List of events from the JSON "response_data"
                events = response_data.get('serverResponseObject', [])

                if not events:
                    if log_count == 0:  # Case 1: First call, no logs at all
                        print_logs(f"[INFO] Zero Events [{current_time}] | No new events since: {past_time}", 1)
                        
                        send_slack_notification(f"[INFO] Zero Events [{current_time}] | No new events since: {past_time}", error_message="Got zero events today")
                    else:  # Case 2: No more logs left, but we retrieved at least one batch
                        
                        print_logs(f"[INFO] Reached final API call. No more events left to process. Last successful batch was at {past_time}. Stopping.", 1)
                    break  #  Stop the loop in both cases
                
                # Process each event individually and append to a list.
                # list_of_processed_events is a list of processed dictionaries
                list_of_processed_events = [process_event(event) for event in events]

                # processed_event_data is a string with NDJSON format, ready for GCS:
                processed_event_data = "\n".join(json.dumps(evt) for evt in list_of_processed_events)

                if len(events) == 500: 
                    log_count += len(events)
                    events_stored, bucket_full_path, error = upload_to_gcs(trailing_count, processed_event_data)

                    if events_stored == "FAILURE":
                        print_logs(f"❌ [ERROR] Upload failed for batch {trailing_count}. Stopping execution.", 4)
                        send_slack_notification(f"❌ [ERROR] Upload failed to bucket for batch {trailing_count}.", error_message=f"{error}")
                        break  # Stop execution if upload fails

                    # Ensure the timestamp is explicitly re-assigned globally
                    if events:
                        new_epoch_ns = events[-1].get('analyticsEventCreatedAtNano')
                        if new_epoch_ns:
                            
                            # +1 para evitar el edge case en que hay 2 eventos con el mismo TS y caer en loops
                            past_epoch_ns = int(new_epoch_ns) + 1  # Normal case
                        else:

                            # +1 para evitar el edge case en que hay 2 eventos con el mismo TS y caer en loops
                            past_epoch_ns = int(past_epoch_ns + 1)
                            print_logs(f" [INFO] Warning: Last event missing timestamp. Using incremented past_epoch_ns={past_epoch_ns}.", 2)

                    trailing_count += 1

                elif len(events) < 500:
                    #  Last batch (less than 500) → Stop
                    new_epoch_ns = events[-1].get('analyticsEventCreatedAtNano')
                    # -1 para evitar el edge case en que hay 2 eventos con el mismo TS y caer en loops
                    past_epoch_ns = int(new_epoch_ns) + 1
                    log_count += len(events)
                    events_stored, bucket_full_path, error = upload_to_gcs(trailing_count, processed_event_data)
                    if events_stored == "FAILURE":
                        print_logs(f"❌ [ERROR] Upload failed for batch {trailing_count}. Stopping execution.", 4)
                        send_slack_notification(f"❌ [ERROR] Upload failed to bucket for batch {trailing_count}.", error_message=f"{error}")
                        break  #  Stop execution if upload fails

                    if error is not None:
                        print_logs(f"❌ [ERROR] {current_time} | Aborted. Error uploading to GCP CS. Upload failed to bucket for batch {trailing_count}.", 4)
                        send_slack_notification(
                            f"❌ [ERROR] [{current_time}] | Aborted. Error uploading to GCP CS. Upload failed to bucket for batch {trailing_count}.",
                            error_message=f"{error}"
                            )
                        break  #  Stop execution if upload fails
                    break
        else:
            print_logs(f" [CRITICAL] API Vicarius Failed. Error: [{failure}]" ,4)

    save_timestamp(past_epoch_ns)

    end_time = t.time()
    execution_duration = end_time - start_time

    # FINAL STEP - LOGGING SUCCESS
    if log_count > 0 and events_stored:

        # 1. Logging
        print_logs(
            f" [SUCCESS] [{current_time}] | Event processing completed! "
            f"time_of_execution={current_time}, total_events_retrieved={log_count}, "
            f"execution_time={execution_duration:.2f} seconds, "
            f"bucket_prefix=gs://{bucket_full_path}, "
            f"number_of_files_created={trailing_count}",
            1  # INFO level
                )
        # 2. Send Slack
        send_slack_notification(
            f" [SUCCESS] [{current_time}] | Event processing completed!",
            time_of_execution=current_time,
            total_events_retrieved=log_count,
            execution_time=f"{execution_duration:.2f} seconds",
            bucket_prefix=f"gs://{bucket_full_path}/",
            number_of_files_created=trailing_count
        )
    print_logs("-------------------- END ---------------------",1)


if __name__ == '__main__':
    try:
        main()
    except Exception as error_message:
        print_logs(error_message, 5)
