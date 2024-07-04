import requests
import inquirer
from config import BASE_URL


def search_manga(search_query):
    manga_response = requests.get(
        f'{BASE_URL}/manga', params={'title': search_query})
    return manga_response.json()['data']


def get_manga_title(manga):
    return list(manga['attributes']['title'].values())[0]


def select_exact_manga(manga):
    title_choices = list(map(get_manga_title, manga))
    title_questions = [inquirer.List(
        'title', message='Select exact title', choices=title_choices)]

    selected_manga_title = inquirer.prompt(title_questions)['title']
    return list(filter(lambda manga: get_manga_title(manga) == selected_manga_title, manga))[0]


def select_language(manga):
    available_languages = manga['attributes']['availableTranslatedLanguages']
    language_questions = [inquirer.List(
        'language', message='Select language', choices=available_languages)]
    return inquirer.prompt(language_questions)['language']


def select_manga():
    '''Select language and exact title'''
    search_query = input("Enter manga's title: ")
    manga_data = search_manga(search_query)

    if (not len(manga_data)):
        print('No manga was found')
        exit()

    selected_manga = None
    if (len(manga_data) == 1):
        selected_manga = manga_data[0]
    else:
        selected_manga = select_exact_manga(manga_data)

    selected_language = select_language(selected_manga)

    return get_manga_title(selected_manga), selected_language, selected_manga['id']
