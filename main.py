import requests
import inquirer
from config import BASE_URL
import os


def search_manga(search_query):
    manga_response = requests.get(
        f'{BASE_URL}/manga', params={'title': search_query})
    return manga_response.json()['data']


def get_manga_title(manga):
    return list(manga['attributes']['title'].values())[0]


def select_manga():
    search_query = input("Enter manga's title: ")
    manga_data = search_manga(search_query=search_query)

    manga_choices = list(map(get_manga_title, manga_data))
    questions = [
        inquirer.List('title', message='Select exact title',
                      choices=manga_choices)
    ]

    selected_manga_title = inquirer.prompt(questions)['title']
    selected_manga_data = list(filter(
        lambda manga: get_manga_title(
            manga) == selected_manga_title, manga_data
    ))[0]

    return selected_manga_title, selected_manga_data['id']


class MangaDownloader:
    def __init__(self, title, id, step):
        self.title = title
        self.id = id
        self.step = step

    def get_chapters(self, limit=100, offset=0):
        chapters_request_params = {
            'limit': limit,
            'offset': offset,
            'manga': self.id
        }

        chapters_response = requests.get(
            f'{BASE_URL}/chapter', params=chapters_request_params)
        return chapters_response.json()

    def get_chapter_path(self, chapter_title):
        if (not chapter_title):
            raise ValueError('Invalid chapter title')

        return os.path.join(os.getcwd(), 'manga', self.title, chapter_title)

    def get_chapter_images_data(self, chapter_id):
        chapter_images_response = requests.get(
            f'{BASE_URL}/at-home/server/{chapter_id}')
        return chapter_images_response.json()

    def download_chapter_images(self, chapter_id, chapter_path):
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
                self.download_chapter_images(chapter['id'], chapter_path)
                print(f'Downloaded: "{chapter_title}"')
            except Exception as e:
                print(f'Failed to retrieve a chapter: {e}')

    def get_chapters_amount(self):
        return self.get_chapters(limit=1, offset=0)['total']

    def download_manga(self):
        total_chapters = self.get_chapters_amount()

        for i in range(0, total_chapters + self.step, self.step):
            self.download_chapters(offset=i)


def main():
    try:
        manga_title, manga_id = select_manga()

        downloader = MangaDownloader(title=manga_title, id=manga_id, step=100)
        downloader.download_manga()
    except KeyboardInterrupt:
        print('\nDownload interrupted')
    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    main()
