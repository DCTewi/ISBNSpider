#coding=utf-8

import re
import time
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

timestamp = time.strftime("%Y %b%d %H-%M-%S", time.localtime(time.time()))

def debugLog(msg : str):
    now = time.strftime("%Y %b%d %H:%M:%S", time.localtime(time.time()))
    with open("debug-{}.log".format(timestamp), mode="a", encoding="utf8") as f:
        f.write(now + msg + "\n")
    # print(now + msg)

class Book():
    def __init__(self, name, publisher):
        self.name = name
        self.publisher = publisher
        self.isbn = ""
        self.isZiying = True
        self.found = True

def checkPublisher(a : str, b : str):
    a = a.replace('２１', '二十一')
    b = b.replace('２１', '二十一')
    a = a.split('出版')
    b = b.split('出版')
    return a[0] == b[0]

def readBookNames():
    with open("booknames.txt", encoding="utf8") as f:
        res = f.readlines()
    with open("publisher.txt", encoding="utf8") as f:
        pub = f.readlines()
    return res, pub

def tryFindBook(name : str, publisher : str, isddsale : bool):

    debugLog('[ INFO] Searching {} with ddsale:{}'.format(name, isddsale))

    searchurl = 'http://search.dangdang.com/?key={}&ddsale={}'.format(urllib.parse.quote(name), '1' if isddsale else '0')
    searchpage = urllib.request.urlopen(searchurl).read()
    searchpage = searchpage.decode('GB18030', 'ignore')

    if len(re.findall('<div class=\"no_result\">', searchpage)) != 0:
        debugLog('[ WARN] Not found with ddsale:{}'.format(isddsale))
        return "-", False
    
    products = re.findall('http://product.dangdang.com/[0-9]+.html', searchpage)

    for product in products:
        try:
            time.sleep(0.5)
            debugLog('[ INFO] GET {}'.format(product))

            page = urllib.request.urlopen(product).read()
            soup = BeautifulSoup(page, 'lxml')

            pbr = soup.select('#product_info > div.messbox_info > span:nth-child(2) > a')[0].string

            if checkPublisher(pbr, publisher):
                debugLog('[TRACE] Same publisher {} and {}'.format(pbr, publisher))
                
                isbn = soup.select('#detail_describe > ul > li:nth-child(5)')[0].string
                isbn = re.findall('(?<=ISBN：)[0-9]+', isbn)

                if len(isbn) > 0:
                    debugLog('[ INFO] Fill ISBN of {} by {}'.format(name, isbn[0]))
                    return isbn[0], True
        except Exception as e:
            debugLog('[ WARN] Excepted exception {} when searching {}'.format(e, name))
            pass

    return "-", False

def initCSV():
    with open("temp-{}.csv".format(timestamp), mode="w", encoding="utf8") as f:
        f.write("Name, ISBN, Type\n")

def saveBook(book : Book):
    with open("temp-{}.csv".format(timestamp), mode="a", encoding="utf8") as f:
        f.write("{},{},{}\n".format(book.name, book.isbn, '没有找到' if not book.found else '当当自营' if book.isZiying else '全部商品'))

def saveBookAll(books):
    with open("result.csv", mode="w", encoding="utf8") as f:
        for book in books:
            f.write("{},{},{}\n".format(book.name, book.isbn, '没有找到' if not book.found else '当当自营' if book.isZiying else '全部商品'))

def main():
    names, publishers = readBookNames()
    books = []

    debugLog('[ INFO] Spider begin')

    initCSV()
    for i in range(749, 2500):
        name = names[i].strip(' \n')
        publisher = publishers[i].strip(' \n')
        book = Book(name, publisher)

        book.isbn, foundInDDSale = tryFindBook(name, publisher, True)

        if not foundInDDSale:
            book.isbn, foundInAll = tryFindBook(name, publisher, False)
            book.isZiying = False
            if not foundInAll:
                tempname = re.sub("\\(.*?\\)", "", book.name)
                book.isbn, foundFinal = tryFindBook(tempname, publisher, False)
                if not foundFinal:
                    debugLog('[ERROR] Totally not found: {}'.format(name))
                    book.found = False
        
        books.append(book)

        saveBook(book)

    saveBookAll(books)

    debugLog('Spider end')

if __name__ == "__main__":
    main()
