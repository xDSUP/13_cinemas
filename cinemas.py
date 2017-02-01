import requests
import random
import argparse

from bs4 import BeautifulSoup


def fetch_afisha_page():
    afisha_url = 'http://www.afisha.ru/bryansk/schedule_cinema/'
    afisha_page = requests.get(afisha_url).text
    return afisha_page


def parse_afisha_list(raw_html):
    html = BeautifulSoup(raw_html, "lxml")
    films_list = html.findAll(class_='object s-votes-hover-area collapsed')
    films_info = []
    for film in films_list:
        title = film.find(class_='usetags').text
        count_cinemas = len(film.findAll(class_="b-td-item"))
        proxies_list = get_proxy()
        html_kinopoisk = multiconnection(title, proxies_list)
        rating_ball, rating_count = map(str, (get_rating(html_kinopoisk)))
        films_info.append({
            "movie_title" : title,
            "count_cinemas" : count_cinemas,
            "rating_ball" : rating_ball,
            "rating_count" : rating_count
            })
    return films_info


def get_proxy():
    url_proxy = 'http://www.freeproxy-list.ru/api/proxy'
    params = {'token': 'demo'}
    html = requests.get(url_proxy, params=params).text
    proxies_list = html.split('\n')
    return proxies_list


def multiconnection(title, proxies_list):
    while True:
        html = connect_to_kinopoisk(title, proxies_list)
        if html is not None:
            return html
        else:
            print("reconnect")


def get_random_user_agent():
    user_agent_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0',
    'Mozilla/5.0 (X11; Linux i686; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
    'Opera/9.80 (Windows NT 6.2; WOW64) Presto/2.12.388 Version/12.17',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
                       ] 
    user_agent = random.sample(user_agent_list, 1)[0]
    return user_agent


def connect_to_kinopoisk(title, proxies_list):
    print("get info %s" % title)
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
        film_page = requests.session().get(url, 
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
        return film_page.text


def get_rating(film_page):
    html = BeautifulSoup(film_page, "lxml")
    rating_ball = html.find(class_="rating_ball")
    rating_ball = 0 if not rating_ball else rating_ball.text
    rating_count = html.find(class_="ratingCount")
    rating_count = 0 if not rating_count else rating_count.text
    return rating_ball, rating_count


def sort_films(movies, count, cinemas_min):
    films_list = [film for film in movies if film['count_cinemas'] >= cinemas_min]
    sorted_film =  sorted(films_list,
                          key=lambda film: film["rating_ball"],
                          reverse=True)
    return sorted_film[:count]


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
    films_list = parse_afisha_list(html)
    sorted_films = sort_films(films_list, args.movies, args.count)
    output_movies_to_console(sorted_films)
