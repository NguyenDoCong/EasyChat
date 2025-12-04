from requests_html import HTMLSession
import pprint
from bs4 import BeautifulSoup

session = HTMLSession()
r = session.get('https://rangdong.com.vn/category/den-ban-hoc-bao-ve-mat-chong-can')

# pprint.pprint(r.html.links)

first_element = r.html.find('base', first=True)
html = r.html.xpath('/html', first=True, clean=True)
# print(first_element.attrs.get('href'))
print(r.html.text)

# soup = BeautifulSoup(html.text, 'html.parser')

# print(soup.get_text())

