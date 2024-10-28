import requests
import json
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, filename='photo_upload.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# объявление класса V, получение информации о юзере и о фотографиях
class VK:
    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id, 'fields': 'photo_max'}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_profile_photos(self, count = 5):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id, 'album_id': 'profile', 'extended': 1, 'count': count}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

# Функция загрузки файла с доступами или ввода необходимых ключей
def load_config(filename):
    config = {}
    try:
        with open(filename, 'r') as file:
            for line in file:
                key, value = line.strip().split('=')
                config[key] = value
    except FileNotFoundError:
        logging.error(f'File {filename} not found. Input need info')
        config['access_token'] = input('Input access_token: ')
        config['user_id'] = input('Input user_id: ')
        config['OAuth_token'] = input('Input OAuth_token: ')
        return config
    return config

#Функци для загрузки фото из ВК на Я.диск
def save_photos(photos):
    folder_name = f'photos_{user_id}'
    json_filename = 'photo_data.json'
    folder_yandex_url = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Authorization': f'OAuth {OAuth_token}'}
    params = {'path': folder_name}

    response = requests.put(folder_yandex_url, headers=headers, params=params)
    if response.status_code == 201:
        logging.info(f'Folder {folder_name} created on Yandex Disk.')
    elif response.status_code == 409:
        logging.info(f'Folder {folder_name} already exists on Yandex Disk.')
    else:
        logging.error(f'Error creating folder on Yandex Disk: {response.json()}')
        return

    photo_data = []

    for photo in tqdm(photos, desc="Uploading photos to Yandex Disk", unit="photo"):
        photo_id = str(photo['id'])
        max_size_url = photo['sizes'][-1]['url']
        likes = photo['likes']['count']
        filename = f'photo_{photo_id}_likes_{likes}.jpg'
        full_path = f'{folder_name}/{filename}'

        # Проверка существования фото на Яндекс.Диске
        params = {'path': full_path}
        check_response = requests.get(folder_yandex_url, headers=headers, params=params)
        if check_response.status_code == 200:
            logging.info(f'Photo {filename} already exists on Yandex Disk, skipping upload.')
            continue

        # Скачивание фото
        response = requests.get(max_size_url)
        if response.status_code == 200:
            upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            upload_params = {'path': full_path, 'overwrite': 'true'}
            upload_link = requests.get(upload_url, headers=headers, params=upload_params).json().get('href')
            if upload_link:
                upload_response = requests.put(upload_link, files={'file': response.content})
                if upload_response.status_code == 201:
                    logging.info(f'Photo {filename} save to Yandex Disk.')
                    photo_info = {'file_name': filename, 'size': photo['sizes'][-1]['type']}
                    photo_data.append(photo_info)
                else:
                    logging.error(f'Error uploading photo {filename}: {upload_response.json()}')
            else:
                logging.error(f'Error retrieving upload link: {upload_response.json()}')

    # Сохранение данных о фото на Яндекс.Диске
    with open(json_filename, 'w') as json_file:
        json.dump(photo_data, json_file, indent=4, ensure_ascii=False)
        logging.info(f'Saved photo information to JSON: {json_filename}')



config = load_config('config.txt')

access_token = config.get('access_token')
user_id = config.get('user_id')
OAuth_token = config.get('OAuth_token')

vk = VK(access_token, user_id)
user_info = vk.users_info()
profile_photos = vk.get_profile_photos(count = 2)

if 'response' in user_info:
    photos = profile_photos['response']['items']
    save_photos(photos)
else:
    logging.error('Error retrieving user information:', user_info.get('error', {}).get('error_msg', 'Unknown Error'))

