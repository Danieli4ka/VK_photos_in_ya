import json
import logging
from tqdm import tqdm
import configparser
from vk_api import VK
from yandex_api import YandexAPI
from datetime import datetime
import requests
from pprint import pprint

logging.basicConfig(level=logging.INFO, filename='photo_upload.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')


def load_config(filename='settings.ini'):
    config = configparser.ConfigParser()

    try:
        config.read(filename)
        access_token = config.get('VK', 'access_token')
        OAuth_token = config.get('Yandex', 'OAuth_token')

    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.error(f'Error in settings file: {e}')
        access_token = input('Enter access_token: ')
        OAuth_token = input('Enter OAuth_token: ')

        config['VK'] = {'access_token': access_token}
        config['Yandex'] = {'OAuth_token': OAuth_token}

        with open(filename, 'w') as configfile:
            config.write(configfile)

    return access_token, OAuth_token

def user_info():
    identifier = input('Enter users id or screen name: ')
    count = input('Enter count photo: ')

    while not count.isdigit():
        print('Please, enter numeric')
        count = input('Enter count photo: ')

    return identifier, int(count)


def save_photos(vk, yandex_api):
    vk.resolve_user_id()
    folder_name = f'photos{vk.id}'
    json_filename = 'photo_data.json'

    if not yandex_api.create_folder(folder_name):
        return

    photo_data = []
    photos = vk.get_profile_photos(count)
    photos_by_likes = {}

    for photo in photos['response']['items']:
        likes_count = photo['likes']['count']
        max_size_url = photo['sizes'][-1]['url']
        photo_date = datetime.fromtimestamp(photo['date']).strftime('%Y-%m-%d')

        if likes_count not in photos_by_likes:
            photos_by_likes[likes_count] = {}

        if photo_date not in photos_by_likes[likes_count]:
            photos_by_likes[likes_count][photo_date] = []

        photos_by_likes[likes_count][photo_date].append({
            'id': photo['id'],
            'url': max_size_url,
            'type': photo['sizes'][-1]['type']
        })

    for likes, date_dict in tqdm(photos_by_likes.items(), desc="Uploading photos to Yandex Disk", unit="like"):
        for date_str, photo_list in date_dict.items():
            for photo in photo_list:
                if len(photo_list) == 1:
                    filename = f'likes_{likes}.jpg'
                elif len(photo_list) > 1 and len(date_dict) == 1:
                    filename = f'likes_{likes}_{date_str}.jpg'
                else:
                    filename = f'likes_{likes}_{date_str}_{photo["id"]}.jpg'

                full_path = f'{folder_name}/{filename}'

                if yandex_api.check_file_exists(full_path):
                    logging.info(f'Photo {filename} already exists on Yandex Disk, skipping upload.')
                    continue

                response = requests.get(photo['url'])
                if response.status_code == 200:
                    upload_link = yandex_api.get_upload_link(full_path)
                    if upload_link:
                        if yandex_api.upload_file(upload_link, response.content):
                            logging.info(f'Photo {filename} saved to Yandex Disk.')
                            photo_info = {'file_name': filename, 'size': photo['type']}
                            photo_data.append(photo_info)
                        else:
                            logging.error(f'Error uploading photo {filename}.')
                    else:
                        logging.error('Error retrieving upload link.')
                else:
                    logging.error(f'Error downloading photo {photo["id"]}.')

    with open(json_filename, 'w') as json_file:
        json.dump(photo_data, json_file, indent=4, ensure_ascii=False)
        logging.info(f'Saved photo information to JSON: {json_filename}')

if __name__ == '__main__':
    access_token, OAuth_token = load_config()
    user_id, count = user_info()
    vk = VK(access_token, str(user_id))
    yandex_api = YandexAPI(OAuth_token)
    save_photos(vk, yandex_api)