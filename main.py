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
    '''Select language and exact title'''
    search_query = input("Enter manga's title: ")
    manga_data = search_manga(search_query)

    title_choices = list(map(get_manga_title, manga_data))
    title_questions = [inquirer.List(
        'title', message='Select exact title', choices=title_choices)]

    selected_manga_title = inquirer.prompt(title_questions)['title']
    selected_manga_data = list(filter(
        lambda manga: get_manga_title(
            manga) == selected_manga_title, manga_data
    ))[0]

    language_choices = selected_manga_data['attributes']['availableTranslatedLanguages']
    language_questions = [inquirer.List(
        'language', message='Select language', choices=language_choices)]
    selected_language = inquirer.prompt(language_questions)['language']

    return selected_manga_title, selected_language, selected_manga_data['id']


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

        return chapters_response.json()

    def get_chapter_path(self, chapter_title):
        '''Get chapter's path in system'''
        if (not chapter_title):
            raise ValueError('Invalid chapter title')

        return os.path.join(os.getcwd(), 'manga', self.title, chapter_title)

    def get_chapter_images(self, chapter_id):
        '''Get chapter's images data'''
        chapter_images_response = requests.get(
            f'{BASE_URL}/at-home/server/{chapter_id}')
        return chapter_images_response.json()

    def download_chapter_images(self, chapter_id, chapter_path):
        '''Request chapter's images and download it'''
        os.makedirs(chapter_path)
        chapter_images_data = self.get_chapter_images(chapter_id)

        for image in chapter_images_data['chapter']['data']:
            base_url = chapter_images_data['baseUrl']
            hash = chapter_images_data['chapter']['hash']
            image_url = f'{base_url}/data/{hash}/{image}'
            image_response = requests.get(image_url)

            with open(f'{chapter_path}/{image}', 'wb') as file:
                file.write(image_response.content)

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
                print(f'Failed to retrieve a chapter: {e}')

    def download_manga(self):
        '''Download all manga's chapters'''
        chapters = self.get_chapters()
        total_chapters = chapters['total']
        print(f'Available {total_chapters} chapters in selected language')

        '''Get all chapters by chunks'''
        chapters_data = chapters['data']
        # Range starts with self.step instead of 0 because first chunk (which is equal to step) was fetched above
        for i in range(self.step, total_chapters + self.step, self.step):
            chapters_data.extend(self.get_chapters(offset=i)['data'])

        print(len(chapters_data))
        self.download_chapters(chapters_data)


def main():
    try:
        title, language, id = select_manga()

        downloader = MangaDownloader(title, language, id, step=100)
        downloader.download_manga()
    except KeyboardInterrupt:
        print('\nDownload interrupted')
    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    main()
