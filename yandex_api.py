import requests
import logging

class YandexAPI:
    def __init__(self, oauth_token):
        self.oauth_token = oauth_token
        self.base_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.headers = {'Authorization': f'OAuth {self.oauth_token}'}
        self.logger = logging.getLogger(__name__)

    def create_folder(self, folder_name):
        params = {'path': folder_name}
        response = requests.put(self.base_url, headers=self.headers, params=params)
        if response.status_code == 201:
            logging.info(f'Folder {folder_name} created on Yandex Disk.')
        elif response.status_code == 409:
            logging.info(f'Folder {folder_name} already exists on Yandex Disk.')
        else:
            logging.error(f'Error creating folder on Yandex Disk: {response.json()}')
        return response.status_code

    def check_file_exists(self, file_path):
        params = {'path': file_path}
        response = requests.get(self.base_url, headers=self.headers, params=params)
        return response.status_code == 200

    def get_upload_link(self, file_path):
        upload_url = f'{self.base_url}/upload'
        upload_params = {'path': file_path, 'overwrite': 'true'}
        response = requests.get(upload_url, headers=self.headers, params=upload_params)
        return response.json().get('href')

    def upload_file(self, upload_link, file_content):
        response = requests.put(upload_link, files={'file': file_content})
        return response.status_code == 201