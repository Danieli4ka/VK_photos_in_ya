import requests
import logging

class VK:
    def __init__(self, access_token, identifier, version='5.131'):
        self.token = access_token
        self.id = identifier # без разницы число или screen_name
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}
        self.logger = logging.getLogger(__name__)

    def get_base_url(self):
        return 'https://api.vk.com/method/'

    def users_info(self):
        url = f"{self.get_base_url()}users.get"
        params = {'user_ids': self.id, 'fields': 'photo_max'}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def resolve_user_id(self):
        if not self.id.isdigit():
            user_info = self.users_info()
            if 'response' in user_info:
                self.id = str(user_info['response'][0]['id'])
                logging.info(f'Resolved screen_name to user ID: {self.id}')
            else:
                logging.error('User not found or error retrieving user information.')
                raise ValueError('User not found or error retrieving user information.')

    def get_profile_photos(self, count=5):
        url = f"{self.get_base_url()}photos.get"
        self.resolve_user_id()
        params = {'owner_id': self.id, 'album_id': 'profile', 'extended': 1, 'count': count}
        response = requests.get(url, params={**self.params, **params})

        if response.status_code != 200:
            logging.error(f'Error fetching photos: {response.json()}')
            return {'error': 'User not found or error retrieving user information.'}
        return response.json()