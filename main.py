import csv
import datetime
import re
import requests
import unicodedata
from bs4 import BeautifulSoup

csv_filename = 'news_data.csv'

def check_href_is_section(href):
    return href and re.compile("^(https://punchng.com/topics)").search(href)


def check_href_is_tag(href):
    return href and re.compile("^(https://punchng.com/tags)").search(href)


def get_all_sections(soup: BeautifulSoup) -> list:
    # Id of primary-menu
    # All children with class menu-item-object-category
    # The child.a['href'] of that tag
    primary_menu = soup.find(id='primary-menu')
    sections = primary_menu.find_all(href=check_href_is_section)
    # sections = [section['href'] for section in sections]
    return sections


def check_date_less_than_30days(date_str: str) -> bool:
    date_time_obj = datetime.datetime.strptime(date_str, '%d %B %Y')
    return date_str and (datetime.datetime.utcnow() - datetime.timedelta(30)) < date_time_obj


def convert_to_int(string: str) -> int:
    try:
        return int(string)
    except ValueError:
        return 0


def get_article_links_on_pages(page_url: str, article_limit=10, page_limit=5) -> list:
    # Open a request to that page
    all_articles = []
    def main(soup: BeautifulSoup):
        articles = soup.find_all(class_='entry-title', limit=article_limit)
        articles = [article.find('a')['href'] for article in articles]
        all_articles.extend(articles)
    
    r = requests.get(page_url)
    soup = BeautifulSoup(r.text, 'lxml')
    main(soup)

    for tag in soup.find_all(lambda x: x.get('class') == ['page-numbers'] and 1 < convert_to_int(x.string) <= page_limit):
        if tag['href']:
            r = requests.get(tag['href'])
            new_soup = BeautifulSoup(r.text, 'lxml')
            main(new_soup)

    return all_articles


def get_data_from_article(article_url: str) -> dict:
    """
    Extract the tag, date_published, author, title
    """
    r = requests.get(article_url)
    soup = BeautifulSoup(r.text, 'lxml')

    date_published = soup.find(class_='entry-date').span.string
    # 9 April 2022
    if not check_date_less_than_30days(date_published):
        return

    title = soup.find(id='huge_trend_title_count').string
    author = soup.find(class_='entry-author').string

    tags = soup.find(class_='entry-tags').find_all(href=check_href_is_tag)
    tags = [tag.string.strip() for tag in tags]

    data = {'title': title, 'author': author, 'tags': tags,
            'date_published': date_published}

    return data


def write_to_csv(data: dict):
    with open(csv_filename, 'a', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, data.keys())
        if f.tell() == 0:
            w.writeheader()
            w.writerow(data)
        else:
            w.writerow(data)


def main():
    # 1. Clear the file if it exists
    open(csv_filename, 'w').close()
    # 2. Getting the html content of the page
    page_url = 'https://punchng.com/'
    r = requests.get(page_url)
    soup = BeautifulSoup(r.text, 'lxml')
    sections = get_all_sections(soup)
    for section in sections:
        print(section)
        articles = get_article_links_on_pages(section['href'], article_limit=100)
        for article in articles:
            print(article)
            data = get_data_from_article(article)
            if data:
                data['section'] = section.string
                write_to_csv(data)
        print('\n\n')


if __name__ == '__main__':
    main()
# Steps
# 10 Get the page
# 20 Get all section urls
# 30 Loop through the next 5 pages in that section, get all articles from the pages
# 40 For each article, if date is less than 30 days ago then 50;
# 50 Get the tag, date_published, author, section, title;
# 60 After all sections have been elapsed, repeat line 30; until total articles is 100 >
