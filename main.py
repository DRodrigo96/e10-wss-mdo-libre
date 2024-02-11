# main.py
# ==================================================
# standard
import ssl, re
import urllib.request, urllib.parse, urllib.error
# requirements
from bs4 import BeautifulSoup
import typer
# --------------------------------------------------

app = typer.Typer()

@app.command()
def categories() -> None:
    '''
    Recuperar links con categorías de website de Mercado Libre.
    Exporta el resultado a un archivo de texto "./resources/CATEGORIES.txt".
    '''
    website = 'https://www.mercadolibre.com.pe/categorias/'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    html = urllib.request.urlopen(website, context=ctx).read()
    soup = BeautifulSoup(html, 'html.parser')
    a_tags = soup('a')
    
    href_items = set()
    _ = [href_items.add(tag.get('href', None)) for tag in a_tags]
    
    categories_href = []
    for link in set(href_items):
        if link is None:
            continue
        elif len(re.findall('https://listado.mercadolibre.com.pe/[a-z-/]*/$', link)) >= 1:
            categories_href.append(link)
    
    with open('./temp/CATEGORIES.txt', 'w') as txt_file:
        _ = [txt_file.write('{}\n'.format(l)) for l in categories_href]
    print('[INFO] Done')

@app.command()
def crawling() -> None:
    '''
    Realiza crawling por cada una de las categorías del comando anterior.
    Busca extraer todos los links de información de cada categoría.
    '''
    cat_file = open('./temp/CATEGORIES.txt', 'r').readlines()
    cat_link = [line.rstrip() for line in cat_file]
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    for i, website in enumerate(cat_link):
        # links internos: links de la primera página visitada
        html = urllib.request.urlopen(website, context=ctx).read()
        soup = BeautifulSoup(html, 'html.parser')
        
        a_tags = soup('a')
        links = [tag.get('href', None) for tag in a_tags]
        
        nextpage_links = []
        for l in set(links):
            if l is None:
                continue
            elif len(re.findall('{}_Desde_(.*)'.format(website), l)) >= 1:
                nextpage_links.append(l)
        nextpage_links.insert(0, website)
        
        # links externos: links presentes en links encontrados en link internos 
        max_len, unique, count = list(), list(), int()
        
        while True:
            for sub_website in nextpage_links:
                if sub_website in unique:
                    continue
                else:
                    unique.append(sub_website)
                    html = urllib.request.urlopen(sub_website, context=ctx).read()
                    soup = BeautifulSoup(html, 'html.parser')
                    a_tags = soup('a')
                    sub_links = [tag.get('href', None) for tag in a_tags]
                    
                    new_links = []
                    for sl in set(sub_links):
                        if sl is None:
                            continue
                        elif len(re.findall('{}_Desde_[0-9]*$'.format(website), sl)) >= 1:
                            new_links.append(sl)
                    
                    nextpage_links += list(set(new_links))
                    nextpage_links = list(set(nextpage_links))
                    
                    max_len.append(len(nextpage_links))
                    max_len = list(set(max_len))
                    print('[INFO] Links recuperados: {}'.format(max(max_len)))
            
            count += 1
            if count == 100:
                break
        
        with open(f'./temp/SCRAPING_LINKS_{i}.txt', 'w') as txt_file:
            _ = [txt_file.write('{}\n'.format(l)) for l in nextpage_links]

@app.command()
def scraping() -> None:
    '''
    Recupera la información desde los links encontrados en la etapa de crawling.
    '''
    cat_file = open('./temp/CATEGORIES.txt', 'r').readlines()
    cat_link = [line.rstrip() for line in cat_file]
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    data = dict()
    key = int()
    
    for i, website in enumerate(cat_link):
        txt_file = open(f'./temp/SCRAPING_LINKS_{i}.txt', 'r').readlines()
        nextpage_links = [line.rstrip() for line in txt_file]
        
        for subwebsite in nextpage_links:
            html = urllib.request.urlopen(subwebsite, context=ctx).read()
            soup = BeautifulSoup(html, 'html.parser')
            
            span_tags = soup.findAll('span', {'class': 'price-tag ui-search-price__part'})
            price_data = [(tag.find('span', {'class': 'price-tag-symbol'}).getText(), tag.find('span', {'class': 'price-tag-fraction'}).getText()) for tag in span_tags]
            
            for sym, price in price_data:
                key += 1
                data[key] = ((sym, price))
        
        file_title = re.findall('https://listado.mercadolibre.com.pe/(.*)', website)[0].replace('/','')
        
        print('[INFO] Datos recuperados.\nGenerando archivo {}.txt'.format(file_title))
        with open('./resources/{}.txt'.format(file_title), 'w') as file:
            _ = [file.write('{},{},{}\n'.format(k, v[0], v[1])) for k, v in data.items()]
        print('[INFO] Done')

if __name__ == '__main__':
    app()
