import requests
import inquirer
from config import BASE_URL
import os


class MangaDownloader:
    def __init__(self, step):
        self.step = step
        self.selected_manga_title = None
        self.selected_manga_id = None

    def search_manga(self, search_query):
        manga_response = requests.get(
            f'{BASE_URL}/manga', params={'title': search_query})
        return manga_response.json()['data']

    def get_manga_title(self, manga):
        return list(manga['attributes']['title'].values())[0]

    def select_manga(self):
        search_query = input("Enter manga's title: ")
        manga_data = self.search_manga(search_query=search_query)

        manga_choices = list(map(self.get_manga_title, manga_data))
        questions = [
            inquirer.List('title', message='Select exact title',
                          choices=manga_choices)
        ]

        selected_manga_title = inquirer.prompt(questions)['title']
        selected_manga_data = list(filter(
            lambda manga: self.get_manga_title(
                manga) == selected_manga_title, manga_data
        ))[0]

        self.selected_manga_title = selected_manga_title
        self.selected_manga_id = selected_manga_data['id']

    def get_chapters(self, limit=100, offset=0):
        chapters_request_params = {
            'limit': limit,
            'offset': offset,
            'manga': self.selected_manga_id
        }

        chapters_response = requests.get(
            f'{BASE_URL}/chapter', params=chapters_request_params)
        return chapters_response.json()

    def get_chapter_path(self, chapter_title):
        if (not chapter_title):
            raise ValueError('Invalid chapter title')

        return os.path.join(os.getcwd(), 'manga', self.selected_manga_title, chapter_title)

    def get_chapter_images_data(self, chapter_id):
        chapter_images_response = requests.get(
            f'{BASE_URL}/at-home/server/{chapter_id}')
        return chapter_images_response.json()

    def download_images(self, chapter_id, chapter_path):
        os.makedirs(chapter_path)
        chapter_images_data = self.get_chapter_images_data(chapter_id)

        for image in chapter_images_data['chapter']['data']:
            base_url = chapter_images_data['baseUrl']
            hash = chapter_images_data['chapter']['hash']
            image_url = f'{base_url}/data/{hash}/{image}'
            image_response = requests.get(image_url)

            with open(f'{chapter_path}/{image}', 'wb') as file:
                file.write(image_response.content)

    def download_chapters(self, limit=100, offset=0):
        chapters = self.get_chapters(limit, offset)['data']

        for chapter in chapters:
            try:
                if chapter['attributes']['translatedLanguage'] != 'en':
                    continue

                chapter_title = chapter['attributes']['title']
                chapter_path = self.get_chapter_path(chapter_title)
                is_chapter_exist = os.path.exists(chapter_path)

                if is_chapter_exist:
                    print(f'"{chapter_title}" already exist')
                    continue

                print(f'Download started: "{chapter_title}"')
                self.download_images(chapter['id'], chapter_path)
                print(f'Downloaded: "{chapter_title}"')
            except Exception as e:
                print(f'Failed to retrieve a chapter: {e}')

    def get_chapters_amount(self):
        return self.get_chapters(limit=1, offset=0)['total']

    def download_manga(self):
        self.select_manga()
        total_chapters = self.get_chapters_amount()

        for i in range(0, total_chapters + self.step, self.step):
            self.download_chapters(offset=i)


def main():
    downloader = MangaDownloader(step=100)

    try:
        downloader.download_manga()
    except KeyboardInterrupt:
        print('\nDownload interrupted')
    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    main()
