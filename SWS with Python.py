# -*- coding: utf-8 -*-
"""
Created on Sun Aug 16 22:43:44 2020

@author: DavidRodrigo
"""

# Scraping and Crawling
####################################################################################

import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
import ssl
import re
import os

with open('PAGELINK.txt', 'r') as mainlink:
    baselink = mainlink.read()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

website = r'%s'%(baselink)
html = urllib.request.urlopen(website, context=ctx).read()

soup = BeautifulSoup(html, 'html.parser')
catPage_tags = soup('a')

catPag_links = set()
for tag in catPage_tags:
    catPag_links.add(tag.get('href', None))

cat_links = list()
for link in set(catPag_links):
    if link is None:
        continue
    elif len(re.findall('https://listado.mercadolibre.com.pe/[a-z-/]*/$', link)) >= 1:
        cat_links.append(link)


with open('CATEGORIAS.txt', 'w') as txt_file:
    for link in cat_links:
        txt_file.write('{}\n'.format(link))

###############################################################################

# Crawling por categoria
txt_file = open('CATEGORIAS.txt', 'r').readlines()
txt_file = [line.rstrip() for line in txt_file]

for fst_link in txt_file:

    # Links internos
    website = r'{}'.format(fst_link)
    html = urllib.request.urlopen(website, context=ctx).read()
    soup = BeautifulSoup(html, 'html.parser')

    a_tags = soup('a')
    links = [tag.get('href', None) for tag in a_tags]

    next_links = list()
    for link in set(links):
        if link is None:
            continue
        elif len(re.findall('{}_Desde_(.*)'.format(fst_link), link)) >= 1:
            next_links.append(link)

    next_links.insert(0, website)

    # Links externos
    max_len = list()
    unique = list()
    count = int()

    while True:

        for next_link in next_links:
            if next_link in unique:
                continue
            else:
                unique.append(next_link)

                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                website = r'{}'.format(next_link)
                html = urllib.request.urlopen(website, context=ctx).read()

                soup = BeautifulSoup(html, 'html.parser')
                a_tags = soup('a')

                links = [tag.get('href', None) for tag in a_tags]

                new_links = list()

                for link in set(links):
                    if link is None:
                        continue
                    elif len(re.findall('{}_Desde_[0-9]*$'.format(fst_link), link)) >= 1:
                        new_links.append(link)

                next_links += list(set(new_links))
                next_links = list(set(next_links))
                
                max_len.append(len(next_links))
                max_len = list(set(max_len))
                print('Links recuperados: {}'.format(max(max_len)))

        count += 1
        if count == 100:
            break

# Scraping por categoria
    data = dict()
    key = int()

    for link in next_links:

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        website = r'%s'%(link)
        html = urllib.request.urlopen(website, context=ctx).read()
        soup = BeautifulSoup(html, 'html.parser')

        span_tags = soup.findAll('span', {'class': 'price-tag ui-search-price__part'})
        price_data = [(tag.find('span', {'class': 'price-tag-symbol'}).getText(), tag.find('span', {'class': 'price-tag-fraction'}).getText()) for tag in span_tags]
        
        for sym, price in price_data:
            key += 1
            data[key] = ((sym, price))

    file_title = re.findall('https://listado.mercadolibre.com.pe/(.*)', fst_link)[0].replace('/','')
    
    print('Datos recuperados.\nGenerando archivo {}.txt'.format(file_title))

    with open('output/{}.txt'.format(file_title), 'w') as new_file:
        for k, v in data.items():
            new_file.write('{},{},{}\n'.format(k, v[0], v[1]))

print('FIN')

