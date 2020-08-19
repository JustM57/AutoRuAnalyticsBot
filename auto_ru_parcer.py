from selenium import webdriver
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import time
import datetime
import pickle
import stats


def open_auto_ru():
    driver = webdriver.Firefox(executable_path=r'./geckodriver')
    driver.implicitly_wait(5)
    href = 'https://auto.ru/catalog/cars/'
    driver.get(href)
    time.sleep(1)
    btn_class="search-form-v2-mmm"
    elem = driver.find_elements_by_class_name(btn_class)[0]
    time.sleep(0.5)
    elem.click()
    return driver


def list_marks():
    driver = open_auto_ru()
    car_type_class = 'link'
    elems = driver.find_elements_by_class_name(car_type_class)
    elems = [elem for elem in elems if 'link link_pseudo link_theme_auto' in elem.get_attribute("class")]    
    marks = set()
    for elem in elems:
        mark = eval(elem.get_attribute('data-bem'))['search-form-v2-item']['name']
        marks.add(mark)
    driver.close()
    return marks


def list_models(mark):
    driver = open_auto_ru()
    car_type_class = 'link'
    elems = driver.find_elements_by_class_name(car_type_class)
    elems = [elem for elem in elems if 'link link_pseudo link_theme_auto' in elem.get_attribute("class")]
    for elem in elems:
        if mark == eval(elem.get_attribute('data-bem'))['search-form-v2-item']['name']:
            break
    mark_href = elem.get_attribute('href')
    driver.get(mark_href)
    time.sleep(1)

    models = set()
    elems = driver.find_elements_by_class_name(car_type_class)
    elems = [elem for elem in elems if 'link link_pseudo link_theme_auto' in elem.get_attribute("class")]
    for elem in elems:
        model = eval(elem.get_attribute('data-bem'))['search-form-v2-item']['name']
        models.add(model)
    driver.close()
    return mark, models


def get_car_params(elem):
    soup = BeautifulSoup(elem.get_attribute('innerHTML'), 'html.parser')
    model_name = soup.find('a', class_="Link ListingItemTitle-module__link").get_text()
    link = soup.find("a", class_="Link ListingItemTitle-module__link")['href']
    tech_attrs = []
    for tech_attr in soup.find_all("div", class_="ListingItemTechSummaryDesktop__cell"):
        tech_attr = tech_attr.get_text().replace('\u2009', '').replace('\xa0', '')
        tech_attrs.append(tech_attr)
    price = soup.find("div", class_="ListingItemPrice-module__content").get_text().replace('\xa0', '')
    year = soup.find("div", class_="ListingItem-module__year").get_text()
    dist = soup.find("div", class_="ListingItem-module__kmAge").get_text().replace('\xa0', '')
    if 'Проверенный дилер' in str(soup):
        verified_dealer = True
    else:
        verified_dealer = False
    price_mark = soup.find("div", class_="OfferPriceBadge OfferPriceBadge_good")
    if price_mark:
        price_mark = price_mark.get_text()
    try:
        img = [x for x in str(soup).split() if ('320x240' in x) and ('avatars' in x)][0][12:-6]
    except:
        img = None
    car = {
        'model_name': model_name,
        'link': link,
        'engine': tech_attrs[0],
        'transmission': tech_attrs[1],
        'body': tech_attrs[2],
        'drive': tech_attrs[3],
        'colour': tech_attrs[4],
        'price': price,
        'year': year,
        'dist': dist,
        'verified_dealer': verified_dealer,
        'price_mark': price_mark,
        'img': img
    }
    return pd.Series(car)


def get_cars(mark, model, new=False):
    if (len(mark.split()) > 1) or (len(model.split()) > 1):
        driver = open_auto_ru()
        car_type_class = 'link'
        elems = driver.find_elements_by_class_name(car_type_class)
        elems = [elem for elem in elems if 'link link_pseudo link_theme_auto' in elem.get_attribute("class")]
        for elem in elems:
            if mark == eval(elem.get_attribute('data-bem'))['search-form-v2-item']['name']:
                break
        mark_href = elem.get_attribute('href')
        driver.get(mark_href)
        time.sleep(1)
        
        #find the right model
        elems = driver.find_elements_by_class_name(car_type_class)
        elems = [elem for elem in elems if 'link link_pseudo link_theme_auto' in elem.get_attribute("class")]
        for elem in elems:
            if model == eval(elem.get_attribute('data-bem'))['search-form-v2-item']['name']:
                break
        model_href = elem.get_attribute('href')

        ###iterate over pages
        page_number = 1
        cars = pd.DataFrame()
        while True:
            len1 = cars.shape[1]
            if new:
                href_new = 'https://auto.ru/moskva/cars/' + '/'.join(model_href.split('/')[-3:-1])+\
                    '/used' + '?top_days=1&page={}&output_type=list'.format(page_number)
            else:
                href_new = 'https://auto.ru/moskva/cars/' + '/'.join(model_href.split('/')[-3:-1])+\
                    '/used' + '?page={}&output_type=list'.format(page_number)
            driver.get(href_new)
            time.sleep(3)
            car_class = 'ListingItem-module__description'
            car_elems = driver.find_elements_by_class_name(car_class)

            for car_elem in car_elems:
                try:
                    this_car = get_car_params(car_elem)
                    cars = pd.concat([cars, this_car], axis=1)
                except Exception as e:
                    pass
            cars = cars.T
            cars = cars.drop_duplicates()
            cars = cars.T
            if cars.shape[1] == len1:
                break
            page_number += 1

    else:
        driver = webdriver.Firefox(executable_path=r'./geckodriver')
        driver.implicitly_wait(5)

        ###iterate over pages
        page_number = 1
        cars = pd.DataFrame()
        while True:
            len1 = cars.shape[1]
            if new:
                # href_new = 'https://auto.ru/moskva/cars/' + '/'.join(model_href.split('/')[-3:-1])+\
                #     '/used' + '?top_days=1&page={}&output_type=list'.format(page_number)
                href_new = 'https://auto.ru/moskva/cars/' + '/'.join([mark, model])+\
                    '/used' + '?top_days=1&page={}&output_type=list'.format(page_number)
            else:
                # href_new = 'https://auto.ru/moskva/cars/' + '/'.join(model_href.split('/')[-3:-1])+\
                #     '/used' + '?page={}&output_type=list'.format(page_number)
                href_new = 'https://auto.ru/moskva/cars/' + '/'.join([mark, model])+\
                    '/used' + '?page={}&output_type=list'.format(page_number)
            driver.get(href_new)
            time.sleep(3)
            car_class = 'ListingItem-module__main'
            car_elems = driver.find_elements_by_class_name(car_class)
            print(len(car_elems))

            for idx, car_elem in enumerate(car_elems):
                try:
                    this_car = get_car_params(car_elem)
                    cars = pd.concat([cars, this_car], axis=1)
                except Exception as e:
                    print(e, idx)
                    pass
            cars = cars.T
            cars = cars.drop_duplicates()
            cars = cars.T
            if cars.shape[1] == len1:
                break
            page_number += 1
        
    ###preprocess dataframe
    cars = cars.T
    print(cars.columns)
    cars.price = cars.price.map(lambda x: int(x[:-1]))
    cars['engine_volume'] = cars.engine.map(stats.engine_volume)
    cars['horse_power'] = cars.engine.map(stats.engine_power)
    cars['engine_oil'] = cars.engine.map(stats.engine_type)
    cars['electro_power'] = cars.engine.map(stats.electro_power)
    cars['mark'] = mark
    cars['model'] = model
    cars.dist = cars.dist.map(lambda x: int(x[:-2]))
    driver.close()
    return cars


def update_new():
    with open("daily_models.txt", "rb") as fp:   # Unpickling
        daily_models = pickle.load(fp)
    all_cars = pd.DataFrame()
    for car_name in tqdm(daily_models):
        cars = get_cars(car_name[0], car_name[1], new=True)
        all_cars = pd.concat([all_cars, cars], axis=0)
    all_cars = stats.get_prediction(all_cars)
    all_cars.to_csv('daily_models.csv', index=False)


def main():
    interesting_models = [
        ('Renault', 'Logan'),
        ('Kia', 'Rio'),
        ('Volkswagen', 'Polo'),
        ('Hyundai', 'Solaris'),
        ('Toyota', 'Corolla'),
        ('Skoda', 'Rapid'),
        ('Ford', 'Focus'),
        ('LADA (ВАЗ)', 'Vesta'),
        ('LADA (ВАЗ)', 'Granta'),
        ('LADA (ВАЗ)', 'Kalina')
                        ]
    all_cars = pd.DataFrame()
    for car_name in tqdm(interesting_models):
        cars = get_cars(car_name[0], car_name[1])
        all_cars = pd.concat([all_cars, cars], axis=0)
        date = datetime.datetime.now()
        all_cars.to_csv('data/cars_{}_{}_{}.csv'.format(date.year, date.month, date.day), index=False)


if __name__ == "__main__":
    main()