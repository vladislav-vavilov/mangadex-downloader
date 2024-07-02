from config import BASE_URL
import requests
import inquirer
import os

search_query = input("Enter manga's title: ")
manga_response = requests.get(f'{BASE_URL}/manga', params={'title': search_query})
manga_data = manga_response.json()['data']

def get_manga_title(manga):
  return list(manga['attributes']['title'].values())[0]

def get_manga_by_title(title):
  for manga in manga_data:
    if get_manga_title(manga) == title: return manga

manga_choices = list(map(get_manga_title, manga_data))
questions = [
  inquirer.List('title', message='Select exact title', choices=manga_choices)
]

selected_manga_title = inquirer.prompt(questions)['title']
selected_manga_data = get_manga_by_title(selected_manga_title)

def get_chapters(limit = 100, offset = 0):
  chapters_request_params = {
    'limit': limit,
    'offset': offset,
    'manga': selected_manga_data['id']
  }

  chapters_response =  requests.get(f'{BASE_URL}/chapter', params=chapters_request_params)
  return chapters_response.json()

def get_chapters(limit = 100, offset = 0):
  chapters_request_params = {
    'limit': limit,
    'offset': offset,
    'manga': selected_manga_data['id']
  }

  chapters_response =  requests.get(f'{BASE_URL}/chapter', params=chapters_request_params)
  return chapters_response.json()


def get_chapter_path(chapter_title):
  if (not chapter_title):
    raise ValueError('Invalid chapter title')

  return os.path.join(os.getcwd(), selected_manga_title, chapter_title)

def get_chapter_images_data(chapter_id):
    chapter_images_response = requests.get(f'{BASE_URL}/at-home/server/{chapter_id}')
    return chapter_images_response.json()

def download_images(chapter_id, chapter_path):
    os.makedirs(chapter_path)
    chapter_images_data = get_chapter_images_data(chapter_id)

    for image in chapter_images_data['chapter']['data']:
      base_url = chapter_images_data['baseUrl']
      hash = chapter_images_data['chapter']['hash']
      image_url = f'{base_url}/data/{hash}/{image}'
      image_response = requests.get(image_url)

      with open(f'{chapter_path}/{image}', 'wb') as file:
        file.write(image_response.content)

def download_chapters(limit = 100, offset = 0):
  chapters = get_chapters(limit, offset)['data']

  for chapter in chapters:
    try:
      if chapter['attributes']['translatedLanguage'] != 'en':
        continue

      chapter_title = chapter['attributes']['title']
      chapter_path = get_chapter_path(chapter_title)
      is_chapter_exist = os.path.exists(chapter_path)

      if is_chapter_exist:
        print(f'"{chapter_title}" already exist')
        continue

      print(f'Download started: "{chapter_title}"')
      download_images(chapter['id'], chapter_path)
      print(f'Downloaded: "{chapter_title}"')
    except Exception as e:
      print(f'Failed to retrieve a chapter: {e}')

def download_manga():
  total_chapters = get_chapters(limit=1, offset=0)['total']

  step = 100
  for i in range(0, total_chapters + step, step):
    download_chapters(offset=i)

download_manga()
