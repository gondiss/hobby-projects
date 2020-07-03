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


url_apts = 'https://www.apartments.com/apartments-condos/cupertino-ca/2-to-3-bedrooms-2-bathrooms-under-4000/washer-dryer-dishwasher'

headers = {'User-Agent': 'Mozilla/5.0'}

url_list = set()


def fetchDetails(url):
    details = requests.get(url, timeout=20, headers=headers)
    soup = BeautifulSoup(details.text, 'html.parser')
    res = '\n'
    rents = []
    addr = soup.find('script', {"type": "application/ld+json"})
    d = json.loads(addr.get_text())
    res = res + d["about"]["name"] + " , " + \
        d["mainEntity"][0]["address"]["streetAddress"] + "\n\n"

    item0 = soup.find('tr', {"data-beds": "2", "data-baths": "1.5"})
    if item0 is not None:
        rent = item0.find('td', {"class": "rent"})
        sqft = item0.find('td', {"class": "sqft"})
        rents.append(
            "2Br/1.5Bt , " +
            rent.get_text().strip() +
            ' -> ' +
            sqft.get_text().strip())

    item1 = soup.find('tr', {"data-beds": "2", "data-baths": "2"})
    if item1 is not None:
        rent = item1.find('td', {"class": "rent"})
        sqft = item1.find('td', {"class": "sqft"})
        rents.append(
            "2Br/2Bt , " +
            rent.get_text().strip() +
            ' -> ' +
            sqft.get_text().strip())

    item2 = soup.find('tr', {"data-beds": "3", "data-baths": "2"})
    if item2 is not None:
        rent = item2.find('td', {"class": "rent"})
        sqft = item2.find('td', {"class": "sqft"})
        rents.append(
            "3Br/2Bt , " +
            rent.get_text().strip() +
            ' -> ' +
            sqft.get_text().strip())

    item3 = soup.find('tr', {"data-beds": "3", "data-baths": "2.5"})
    if item3 is not None:
        rent = item3.find('td', {"class": "rent"})
        sqft = item3.find('td', {"class": "sqft"})
        rents.append(
            "3Br/2.5Bt , " +
            rent.get_text().strip() +
            ' -> ' +
            sqft.get_text().strip())

    res = res + ' | '.join(rents)
    res = res + "\n\n"
    res = res + "Schools: \n"
    for schoolcard in soup.findAll('div', {"class": "schoolCard"}):
        schoolType = schoolcard.find('p', {"class": "schoolType"})
        if "Public Elementary School" in schoolType.get_text():
            res = res + schoolcard.find('p',
                                        {"class": "schoolName"}).get_text()
            res = res + "\n"
    res = res + "---------------------------------------------"
    return res


def fetchApts(base_url):
    res_ls = list()
    try:
        response = requests.get(base_url, timeout=20, headers=headers)
    except BaseException:
        print "Unexpected error:", sys.exc_info()[0]

    soup = BeautifulSoup(response.text, 'html.parser')
    #print soup.get_text()
    for item in soup.findAll('script', {"type": "application/ld+json"}):
        d = json.loads(item.get_text())
        #print json.dumps(d, indent=2, sort_keys=True)
        for apt in d['about']:
            res = ''
            if 'Cupertino' in apt["Address"]["addressLocality"] and apt['url'] not in url_list:
                print apt['url']
                url_list.add(apt['url'])
                res = fetchDetails(apt['url'])
            if res != '':
                res_ls.append(res)

    return '\n'.join(res_ls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="rental script")
    parser.add_argument(
        "--email",
        '-e',
        type=str,
        help="file containing email details. smtp login, smtp passwd and email id(to send script output to) on separate lines",
    )
    opt = parser.parse_args()
    try:
        res = '\n'
        res += 'Cupertino rents \n'
        res += '________________________________________\n'
        start = time()
        res += fetchApts(url_apts)
        end = time()
        print res
        print "fetchRents took - %2.2f" % (end - start)
        if opt.email is not None:
            with open(opt.email, "r") as cred:
                l = next(cred)
                p = next(cred)
                email = next(cred)
                send_message(
                    l.strip(),
                    p.strip(),
                    email.strip(),
                    'Cupertino Rentals \n' +
                    res.encode("utf8"))
    except BaseException:
        print "something went wrong : ", sys.exc_info()[0]

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
