import requests
import datetime
from PIL import Image
import pytesseract
import io
import time
import schedule
import sqlite3

url = 'https://buchung.hsz.rwth-aachen.de/cgi/studio.cgi?size=30'
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Accept': 'image/avif,image/webp,*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://buchung.hsz.rwth-aachen.de/angebote/aktueller_zeitraum/_Auslastung.html',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
    'TE': 'trailers'
}

def get_people_at_the_gym():
    response = requests.get(url, headers=headers)
    gif = io.BytesIO(response.content)
    image = Image.open(gif)
    text = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
    people_at_the_gym = int(text)
    return people_at_the_gym

def save_people_at_the_gym():
    people_at_the_gym = get_people_at_the_gym()
    c.execute("INSERT INTO gym VALUES (datetime('now'), ?)", (people_at_the_gym,))
    conn.commit()
    print(f'{datetime.datetime.now()}: {people_at_the_gym}')

if __name__ == '__main__':
    conn = sqlite3.connect('people_at_the_gym.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gym
            (timestamp DATETIME, people integer)''')
    schedule.every().minute.do(save_people_at_the_gym)
    try:
        while True:
            schedule.run_pending()
            next_job_time = schedule.next_run() - datetime.datetime.now()
            time.sleep(next_job_time.total_seconds())
    finally:
        conn.close()