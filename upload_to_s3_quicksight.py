import boto3
from botocore.exceptions import NoCredentialsError
import pandas as pd
import os
import json
import re
from datetime import datetime

# CONFIGURATION
AWS_ACCESS_KEY = os.getenv('Amazon.ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('Amazon.SECRET_KEY')
BUCKET_NAME = 'quicksight-data-nanda'
REGION = 'eu-north-1'

FOLDER_PATH = r"C:\Users\Win10\Desktop\schedule refresh"
MANIFEST_PATH = os.path.join(FOLDER_PATH, 'manifest.json')


# STEP 1: Find the latest CSV file
def find_latest_csv(folder_path):
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}\.csv$")
    csv_files = [f for f in os.listdir(folder_path) if date_pattern.match(f)]
    if not csv_files:
        raise FileNotFoundError("No date-based CSV files found (yyyy-mm-dd.csv).")
    latest_csv = max(csv_files, key=lambda f: datetime.strptime(f.split('.')[0], "%Y-%m-%d"))
    return os.path.join(folder_path, latest_csv), latest_csv


# STEP 2: Clean the CSV (fix OrderDate)
def clean_csv_dates(input_path, output_path):
    try:
        # Read CSV without parsing dates
        df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
        print(f"Original file rows (before cleaning): {len(df)}")

        # Parse OrderDate carefully
        df['OrderDate'] = pd.to_datetime(
            df['OrderDate'],
            format='%d/%m/%Y',  # Based on your samples
            dayfirst=True,
            errors='coerce'
        )

        bad_dates = df['OrderDate'].isna().sum()
        print(f"⚡ Bad OrderDate rows after parsing: {bad_dates}")

        if bad_dates > 0:
            raise ValueError(f"{bad_dates} invalid OrderDate values found. Fix source file!")

        # Format OrderDate to string (keep only YYYY-MM-DD)
        df['OrderDate'] = df['OrderDate'].dt.strftime('%Y-%m-%d')

        # VERY IMPORTANT: Cast OrderDate BACK to string
        df['OrderDate'] = df['OrderDate'].astype(str)

        # Save cleaned CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✅ CSV cleaned and saved successfully: {output_path}")

    except Exception as e:
        raise Exception(f"❌ Error cleaning CSV: {e}")




# STEP 3: Upload a file to S3
def upload_to_aws(local_file, bucket, s3_file_key):
    try:
        s3 = boto3.client('s3', region_name=REGION,
                          aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_KEY)

        with open(local_file, 'rb') as file:
            s3.upload_fileobj(file, bucket, s3_file_key)
            print(f"✅ Upload Successful: {s3_file_key}")
        return True
    except Exception as e:
        raise Exception(f"Error uploading to AWS: {e}")


# STEP 4: Update manifest.json locally
def update_manifest(bucket, s3_file, manifest_path):
    manifest_content = {
        "fileLocations": [
            {
                "URIs": [
                    f"s3://{bucket}/{s3_file}"
                ]
            }
        ],
        "globalUploadSettings": {
            "format": "CSV",
            "delimiter": ",",
            "textqualifier": "\"",
            "containsHeader": "true"
        }
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest_content, f, indent=2)
    print(f"✅ Manifest updated locally: {manifest_path}")


# MAIN LOGIC
if __name__ == "__main__":
    try:
        latest_csv_path, latest_csv_name = find_latest_csv(FOLDER_PATH)
        print(f"📂 Latest CSV found: {latest_csv_name}")

        cleaned_csv_name = "CLEANED_" + latest_csv_name
        cleaned_csv_path = os.path.join(FOLDER_PATH, cleaned_csv_name)

        # Step 1: Clean CSV
        clean_csv_dates(latest_csv_path, cleaned_csv_path)

        # Step 2: Upload cleaned CSV
        upload_success = upload_to_aws(cleaned_csv_path, BUCKET_NAME, cleaned_csv_name)

        if upload_success:
            # Step 3: Update manifest.json locally
            update_manifest(BUCKET_NAME, cleaned_csv_name, MANIFEST_PATH)

            # Step 4: Upload manifest.json (overwrite in S3)
            upload_to_aws(MANIFEST_PATH, BUCKET_NAME, "manifest.json")

        print("🎯 All steps completed successfully.")

    except Exception as e:
        print(f"❌ Process failed: {e}")
