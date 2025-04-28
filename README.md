# 📊 Automating QuickSight Dataset Refresh with Python, S3, and Task Scheduler

This guide takes you from raw daily CSV to fully automated, up-to-date QuickSight dashboards — with no manual intervention after setup.

---

## 🎯 Business Use Case

You run a daily sales reporting dashboard for leadership. Each morning:

1. **5:45 AM**: A Python script cleans and uploads the latest sales CSV to S3.  
2. **5:47 AM**: The script updates `manifest.json` in S3 to point to the new file.  
3. **6:00 AM**: QuickSight automatically refreshes the dataset via the manifest URL.  
4. **6:05 AM**: Dashboards show the night’s sales — ready before business hours.

---

## 📂 Folder Structure (Local)

```text
C:\Users\Win10\Desktop\schedule_refresh\
│
├── 2025-04-30.csv            # Raw daily data files, autopopulated or dropped in
├── manifest.json             # Template/updated by script
├── refresh_upload.py         # Main Python script
└── README.md                 # This guide
```

---

## 🔑 Prerequisites

1. **AWS Credentials**  
   - Create an IAM user with `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` and QuickSight permissions.  
   - Store them as environment variables:
     ```bash
     setx AWS_ACCESS_KEY_ID    "YOUR_ACCESS_KEY"
     setx AWS_SECRET_ACCESS_KEY "YOUR_SECRET_KEY"
     ```
2. **Python 3.8+**  
   ```bash
   pip install pandas boto3
   ```
3. **AWS S3 Bucket** in `eu-north-1` (e.g., `quicksight-data-nanda`)  
4. **Amazon QuickSight** subscription (Standard or Enterprise)

---

## 1. Setup S3 Bucket

- Create bucket `quicksight-data-nanda` in `eu-north-1`.  
- Grant your IAM user **PutObject**, **GetObject**, **ListBucket** permissions.  
- (Optional) Create a subfolder, but root is simplest.

---

## 2. `manifest.json` Explained

QuickSight uses a `manifest.json` file to know which CSV to load. It must live in S3 at:

```text
s3://quicksight-data-nanda/manifest.json
```

**Structure**:

```json
{
  "fileLocations": [
    {
      "URIs": [
        "s3://quicksight-data-nanda/CLEANED_YYYY-MM-DD.csv"
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
```

- **fileLocations**: array; each entry has `URIs` (exactly one `s3://` link).  
- Do *not* include the HTTPS URL here — QuickSight treats each URI as a separate source and will double-ingest if you include both.  
- **globalUploadSettings**:  
  - `format`: file format (`CSV`)  
  - `delimiter`: field separator (`,`)  
  - `textqualifier`: quoting character (`"`)  
  - `containsHeader`: `"true"` if the first row is header  

**QuickSight Connection URL** (for dataset creation):

```text
https://quicksight-data-nanda.s3.eu-north-1.amazonaws.com/manifest.json
```

---

## 3. Python Script: `refresh_upload.py`

Automates:

1. Find latest `YYYY-MM-DD.csv` in the local folder  
2. Clean `OrderDate` into `YYYY-MM-DD` text  
3. Upload cleaned CSV as `CLEANED_YYYY-MM-DD.csv` to S3  
4. Update `manifest.json` to point at the new S3 URI  
5. Overwrite the manifest in S3  

To run:

```bash
python refresh_upload.py
```

Check your console logs for original rows, cleaned rows, S3 upload, and manifest update.

---

## 4. Create QuickSight Dataset via Manifest

1. In QuickSight, go to **Datasets → New dataset → S3**  
2. Choose **Manifest file**  
3. Paste the HTTPS manifest URL:
   ```
   https://quicksight-data-nanda.s3.eu-north-1.amazonaws.com/manifest.json
   ```
4. Name it (e.g., `DailySalesData`), import into SPICE for better performance  
5. In the **Fields** panel, find `OrderDate`, click ⋮ → **Change data type → String** (to strip `T00:00:00Z`)  
6. Save dataset

---

## 5. Automate with Windows Task Scheduler (5:45 AM)

1. Open **Task Scheduler**  
2. Create **Basic Task**  
   - **Name**: `DailySalesRefresh`  
3. **Trigger**: Daily at **5:45 AM**  
4. **Action**: Start a program  
   - **Program/script**: `python`  
   - **Arguments**:  
     ```
     "C:\Users\Win10\Desktop\schedule_refresh\refresh_upload.py"
     ```
5. Finish  

Now, every day at **5:45 AM**, your script will run automatically, updating S3 and the manifest.

---

## 6. Schedule QuickSight Refresh (6:00 AM)

1. In QuickSight, navigate to your dataset `DailySalesData`  
2. Click ⋮ → **Schedule refresh**  
3. Add a daily refresh at **6:00 AM** (your local timezone)  
4. Save  

**Timeline**

| Time    | Action                                                       |
| ------- | ------------------------------------------------------------ |
| 5:45 AM | Python script uploads fresh data and manifest to S3         |
| 6:00 AM | QuickSight auto-refreshes dataset via `manifest.json`       |

---

## 7. Build and Share Dashboards

- Use `DailySalesData` fields to create visuals (charts, tables, KPIs).  
- Dashboards now auto-update daily without manual steps.

---

## ✅ Conclusion

You’ve configured:

- Environment variables for AWS credentials  
- Automated Python upload & manifest updates  
- S3 storage of cleaned CSV and manifest  
- QuickSight dataset via manifest URL  
- Windows & QuickSight scheduling at 5:45 AM and 6:00 AM  

Enjoy your automated BI pipeline! 🎉
