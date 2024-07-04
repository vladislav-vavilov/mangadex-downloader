from search import select_manga
from downloader import MangaDownloader


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
