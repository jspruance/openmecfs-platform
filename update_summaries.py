# update_summaries.py
import json
import time
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Paper

INPUT_PATH = "data/mecfs_papers_summarized_2025-10-12.json"

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

updated = 0
batch_size = 20  # commit every 20 records


def update_batch(batch):
    global updated
    db: Session = SessionLocal()
    for paper in batch:
        pmid = str(paper.get("pmid"))
        tech = paper.get("technical_summary")
        patient = paper.get("patient_summary")

        if not pmid:
            continue

        db_paper = db.query(Paper).filter(Paper.pmid == pmid).first()
        if db_paper:
            db_paper.technical_summary = tech
            db_paper.patient_summary = patient
            updated += 1

    db.commit()
    db.close()


# Process in chunks to prevent timeout
for i in range(0, len(data), batch_size):
    batch = data[i:i + batch_size]
    update_batch(batch)
    print(f"✅ Committed batch {i//batch_size + 1}, total updated: {updated}")
    time.sleep(0.2)  # tiny delay between batches

print(f"🎉 Finished. Total updated: {updated}")
