import pickle
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


def save_images():
    with open('images.pickle', 'wb') as f:
        pickle.dump(images, f)

def load_images():
    try:
        with open('images.pickle', 'rb') as f:
            return pickle.load(f)
    except Exception:
        return {}

images = load_images()
previous_value = -1

def get_people_at_the_gym():
    response = requests.get(url, headers=headers)
    if response.content in images:
        #print(f'{datetime.datetime.now()}: {response.content} already in cache')
        return images[response.content]
    gif = io.BytesIO(response.content)
    image = Image.open(gif)

    # Create a new image with a white background
    new_image = Image.new('RGB', (image.width + 20, image.height + 20), 'white')
    # Paste the original image into the center of the new image
    new_image.paste(image, (10, 10))
    
    text = pytesseract.image_to_string(new_image, config='--oem 3 --psm 6  outputbase digits')
    people_at_the_gym = int(text)
    images[response.content] = people_at_the_gym
    save_images()
    return people_at_the_gym

def save_people_at_the_gym():
    people_at_the_gym = get_people_at_the_gym()
    global previous_value
    if people_at_the_gym == previous_value:
        #print(f'{datetime.datetime.now()}: {people_at_the_gym} same as previous value, skipping...')
        return
    previous_value = people_at_the_gym
    if not 0 <= people_at_the_gym <= 200:
        print(f'{datetime.datetime.now()}: {people_at_the_gym} this seems suspicious, skipping...')
        return
    c.execute("INSERT INTO gym VALUES (datetime('now','localtime'), ?)", (people_at_the_gym,))
    conn.commit()
    print(f'{datetime.datetime.now()}: {people_at_the_gym}')
    
if __name__ == '__main__':
    conn = sqlite3.connect('people_at_the_gym.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gym
            (timestamp DATETIME, people integer)''')
    save_people_at_the_gym()
    schedule.every().second.do(save_people_at_the_gym)
    try:
        while True:
            try:
                schedule.run_pending()
                next_job_time = schedule.next_run() - datetime.datetime.now()
                time.sleep(next_job_time.total_seconds())
            except Exception as e:
                print(e)
                time.sleep(50)
    finally:
        conn.close()