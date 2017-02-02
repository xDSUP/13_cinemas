import requests
import random
import argparse
import logging

from bs4 import BeautifulSoup


LOGGER = logging.getLogger('info')
logging.basicConfig(format = u'[%(asctime)s] %(levelname)s %(message)s', 
                    level = logging.DEBUG, filename = 'cinemas.log')


def fetch_afisha_page():
    afisha_url = 'http://www.afisha.ru/bryansk/schedule_cinema/'
    afisha_page = requests.get(afisha_url).text
    return afisha_page


def parse_afisha_list(raw_html):
    html = BeautifulSoup(raw_html, "lxml")
    movies_list = html.findAll(class_='object s-votes-hover-area collapsed')
    movies_info = []
    for movie in movies_list:
        movie_title = movie.find(class_='usetags').text
        count_cinemas = len(movie.findAll(class_="b-td-item"))
        proxies_list = get_proxy()
        html_rating_page = multiconnection(movie_title, proxies_list)
        rating_ball, rating_count = map(str, (parse_rating_page(html_rating_page)))
        movies_info.append({
            "movie_title" : movie_title,
            "count_cinemas" : count_cinemas,
            "rating_ball" : rating_ball,
            "rating_count" : rating_count
            })
    return movies_info


def get_proxy():
    url_proxy = 'http://www.freeproxy-list.ru/api/proxy'
    params = {'token': 'demo'}
    html = requests.get(url_proxy, params=params).text
    proxies_list = html.split('\n')
    return proxies_list


def multiconnection(movie_title, proxies_list):
    while True:
        html = fetch_rating_page(movie_title, proxies_list)
        if html is not None:
            return html
        else:
            LOGGER.info("reconnect")


def get_random_user_agent():
    user_agent_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0',
    'Mozilla/5.0 (X11; Linux i686; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
    'Opera/9.80 (Windows NT 6.2; WOW64) Presto/2.12.388 Version/12.17',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
                       ] 
    user_agent = random.sample(user_agent_list, 1)[0]
    return user_agent


def fetch_rating_page(title, proxies_list):
    LOGGER.info("parse : %s" % title)
    try:
        url = "https://www.kinopoisk.ru/index.php"
        params = {'kp_query': title,
                  'first': 'yes'}
        proxy = {"http": random.choice(proxies_list)}
        timeout = random.randrange(3,6)
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Agent:%s'.format(get_random_user_agent())}
        movie_page = requests.session().get(url, 
                                           params=params,
                                           proxies=proxy,
                                           timeout=timeout,
                                           headers=headers)
    except (requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ProxyError,
            requests.exceptions.ReadTimeout):
        return None
    else:
        return movie_page.text


def parse_rating_page(movie_page):
    html = BeautifulSoup(movie_page, "lxml")
    rating_ball = html.find(class_="rating_ball")
    rating_ball = 0 if not rating_ball else rating_ball.text
    rating_count = html.find(class_="ratingCount")
    rating_count = 0 if not rating_count else rating_count.text
    return rating_ball, rating_count


def sort_movies(movies_info, count, cinemas_min):
    movies_info = [movie for movie in movies_info if movie['count_cinemas'] >= cinemas_min]
    sorted_movie =  sorted(movies_list,
                          key=lambda movie: movie["rating_ball"],
                          reverse=True)
    return sorted_movie[:count]


def output_movies_to_console(movies):
    print('movie title - count cinemas - rating ball - rating count')
    for movie in movies:
        print('%s - %s - %s - %s' % (movie['movie_title'],
                                     movie['count_cinemas'],
                                     movie['rating_ball'],
                                     movie['rating_count']))        


def get_args():
    parser = argparse.ArgumentParser(
        description=(
        'The script obtains movies,sorts them by rating and count of cinemas, and outputs the result')
        )
    parser.add_argument('-m', '--movies', default=10, 
                        help="Counts movies", type=int)
    parser.add_argument('-c', '--count', default=0, 
                        help="minimum count of cinemas", type=int)
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    html = fetch_afisha_page()
    movies_list = parse_afisha_list(html)
    sorted_movies = sort_movies(movies_list, args.movies, args.count)
    output_movies_to_console(sorted_movies)
