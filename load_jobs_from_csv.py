import csv
from shared.db_config import get_db_connection

def load_jobs_from_csv(csv_path):
    conn = get_db_connection()
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['title']
            description = row['description']
            cursor.execute("""
                INSERT INTO jobs (title, description)
                VALUES (%s, %s)
            """, (title, description))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Jobs loaded successfully.")

if __name__ == '__main__':
    load_jobs_from_csv('data/job_dataset.csv')
