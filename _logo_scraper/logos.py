# made using https://github.com/goldsmith/Wikipedia
import urllib.request
import urllib3
import json
import threading
from requests_html import HTMLSession
import os


def main():
    open("logo_scraper/notfound.txt", 'w').close()
    brandNames = [line.strip() for line in open('logo_scraper/brands.txt')]
    for brand in brandNames:
        thr = threading.Thread(target=getCompanyLogo, args=[brand])
        thr.start()


def getCompanyLogo(companyName):
    try:
        logoURL = None
        if logoURL is None:
			# using google as a fallback
            print(companyName + " logo")
            logoURL = wiki_image(companyName)
            if logoURL is None:
                addToNotFoundList(companyName)
                return
        if not os.path.exists(f'./brands/{companyName}.png'):
            urllib.request.urlretrieve(f'https:{logoURL}',
                                f"./brands/{companyName}" + getExtension(logoURL))
        print(logoURL)
    except:
        addToNotFoundList(companyName)
    return


def wiki_image(x):

    opener = urllib.request.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    print(x)

    session = HTMLSession()
    response = session.get(f'https://en.wikipedia.org/wiki/{x}')
    selector = response.html.xpath("//img[contains(@src,'logo') or contains(@src,'Logo')]/@src")
    first = selector[0]
    print(first)
    return first


def getExtension(url):
    for i in range(len(url)-1, -1, -1):
        if url[i] == '.':
            return url[i:]


def addToNotFoundList(companyName):
    f = open("logo_scraper/notfound.txt", 'a')
    f.write(companyName+"\n")
    f.close()


if __name__ == "__main__":
    main()
