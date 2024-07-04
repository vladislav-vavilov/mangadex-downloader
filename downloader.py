from config import BASE_URL
import requests
import os


class MangaDownloader:
    def __init__(self, title, language, id, step):
        self.title = title
        self.language = language
        self.id = id
        self.step = step

    def get_chapters(self, offset=0):
        '''Request chunk of chapters'''
        chapters_request_params = {
            'limit': self.step,
            'offset': offset,
            'manga': self.id,
            'translatedLanguage[]': self.language
        }

        chapters_response = requests.get(
            f'{BASE_URL}/chapter', params=chapters_request_params)
        if chapters_response.ok:
            return chapters_response.json()

        raise Exception(
            f'Unable to get chapters from {offset} to {offset + self.step}'
        )

    def get_chapter_path(self, chapter_title):
        '''Get chapter's path in system'''
        if (not chapter_title):
            raise ValueError('Invalid chapter title')

        return os.path.join(os.getcwd(), 'manga', self.title, chapter_title)

    def get_chapter_images(self, chapter_id):
        '''Get chapter's images data'''
        chapter_images_response = requests.get(
            f'{BASE_URL}/at-home/server/{chapter_id}')
        if (chapter_images_response.ok):
            return chapter_images_response.json()

        raise Exception(f'Unable to get images for chapter {chapter_id}')

    def download_chapter_images(self, chapter_id, chapter_path):
        '''Request chapter's images and download it'''
        os.makedirs(chapter_path)
        chapter_images_data = self.get_chapter_images(chapter_id)

        for image in chapter_images_data['chapter']['data']:
            base_url = chapter_images_data['baseUrl']
            hash = chapter_images_data['chapter']['hash']
            image_url = f'{base_url}/data/{hash}/{image}'
            image_response = requests.get(image_url)

            if (image_response.ok):
                with open(f'{chapter_path}/{image}', 'wb') as file:
                    file.write(image_response.content)
            else:
                raise Exception(f'Unable to download image {image}')

    def download_chapters(self, chapters):
        '''Download all chapters'''
        for i, chapter in enumerate(chapters):
            try:
                chapter_title = f'{i + 1}. {chapter['attributes']['title']}'
                chapter_path = self.get_chapter_path(chapter_title)
                is_chapter_exist = os.path.exists(chapter_path)

                if is_chapter_exist:
                    print(f'"{chapter_title}" already exist')
                    continue

                print(f'Download started: "{chapter_title}"')
                self.download_chapter_images(chapter['id'], chapter_path)
                print(f'Downloaded: "{chapter_title}"')
            except Exception as e:
                print(f'Error: {e}')

    def download_manga(self):
        '''Download all manga's chapters'''
        chapters = self.get_chapters()
        total_chapters = chapters['total']
        print(f'Available {total_chapters} chapters in selected language')

        '''Get all chapters by chunks'''
        chapters_data = chapters['data']
        # Range starts with self.step instead of 0 because first 100 chapters (which is equal to 1 step) was fetched above
        for i in range(self.step, total_chapters + self.step, self.step):
            chapters_data.extend(self.get_chapters(offset=i)['data'])

        self.download_chapters(chapters_data)
