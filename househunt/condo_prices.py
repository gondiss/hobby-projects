import argparse
from bs4 import BeautifulSoup
import json
import requests
import smtplib
import sys
from time import time


def send_message(login, passwd, to, body):
    print "sending email to : ", to
    smtp = smtplib.SMTP("smtp.mailgun.org", 587)
    smtp.login(login, passwd)
    smtp.sendmail("pi@example.com", to, body)


city_list = [
    'Sunnyvale,CA',
    'Mountain_View,CA',
    'Cupertino,CA',
    'Palo_Alto,CA',
    'Santa_Clara,CA',
    'Belmont,CA',
    'Burlingame,CA',
    'Los_Altos,CA']

url_trulia = 'https://www.trulia.com/'
url_p1 = 'https://www.trulia.com/for_sale/'
url_p2 = '/2p_beds/1p_baths/0-1000000_price/APARTMENT,CONDO,COOP,TOWNHOUSE_type/'

headers = {'User-Agent': 'Mozilla/5.0'}

url_list = set()


def areSchoolsAboveX(schools):
    elementary = False
    middle = False
    high = False

    for sch in schools:
        if 'ELEMENTARY' in sch['categories'] and sch['providerRating']['rating'] >= 7:
            elementary = True
        if 'MIDDLE' in sch['categories'] and sch['providerRating']['rating'] >= 7:
            middle = True
        if 'HIGH' in sch['categories'] and sch['providerRating']['rating'] >= 7:
            high = True
    return elementary and middle and high


def fetchDetails(url):
    details = requests.get(url, timeout=20, headers=headers)
    soup = BeautifulSoup(details.text, 'html.parser')
    res = ''
    for item in soup.findAll(
            'script', {"id": "__NEXT_DATA__", "type": "application/json"}):
        d = json.loads(item.get_text())

        if not areSchoolsAboveX(
                d['props']['homeDetails']['assignedSchools']['schools']):
            return res

        res += "\n"
        res += ("%s | %s/%s | %s | %s " % (d['props']['homeDetails']['location']['jsonLdSchemaFullLocation'],
                                           d['props']['homeDetails']['bedrooms']['formattedValue'],
                                           d['props']['homeDetails']['bathrooms']['formattedValue'],
                                           d['props']['homeDetails']['floorSpace']['formattedDimension'],
                                           d['props']['homeDetails']['price']['formattedPrice']))

        res += "\nSchools:\n"
        for sch in d['props']['homeDetails']['assignedSchools']['schools']:
            res += ("%s | %s | %s | %s" % (sch['name'],
                                           sch['districtName'],
                                           sch['gradesRange'],
                                           sch['providerRating']['rating']))
            res += "\n"

    return res


def fetchHomes(base_url):
    res_ls = list()
    try:
        response = requests.get(base_url, timeout=20, headers=headers)
    except BaseException:
        print "Unexpected error:", sys.exc_info()[0]

    soup = BeautifulSoup(response.text, 'html.parser')

    for item in soup.findAll(
            'script', {"id": "__NEXT_DATA__", "type": "application/json"}):
        d = json.loads(item.get_text())
        for home in d['props']['searchData']['homes']:
            res = ''
            if 'url' in home.keys() and home['url'] not in url_list:
                url_list.add(home['url'])
                res = fetchDetails(url_trulia + home['url'])
            if res != '':
                res_ls.append(res)

    return '\n'.join(res_ls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="condos script")
    parser.add_argument(
        "--email",
        '-e',
        type=str,
        help="file containing email details. smtp login, smtp passwd and email id(to send script output to) on separate lines",
    )
    opt = parser.parse_args()
    try:
        res_list = list()
        for city in city_list:
            res = '\n'
            res += 'Homes in ' + city + ' : \n'
            res += '________________________________________\n'
            start = time()
            res += fetchHomes(url_p1 + city + url_p2)
            end = time()
            print res
            res_list.append(res)
            print "fetchHomes took - %2.2f" % (end - start)
        if opt.email is not None:
            with open(opt.email, "r") as cred:
                l = next(cred)
                p = next(cred)
                email = next(cred)
                send_message(
                    l.strip(),
                    p.strip(),
                    email.strip(),
                    'Bay Area Condos for Sale \n' +
                    '\n'.join(res_list).encode("utf8"))
    except BaseException:
        print "something went wrong : ", sys.exc_info()[0]

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
