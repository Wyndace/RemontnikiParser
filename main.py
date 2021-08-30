from bs4 import BeautifulSoup
import time
import asyncio
import aiohttp
from os.path import exists
from os import makedirs
import json

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
}

url = 'https://www.remontnik.ru'


async def get_workers_data(session, works_dict):
    users = {}
    print('Getting the workers')
    for worker in works_dict:
        async with session.get(f'{url}{works_dict[worker]}', headers=headers) as responce:
            soup = BeautifulSoup(await responce.text(), 'lxml')
            try:
                block_users = soup.find_all('div', class_='service-master')
                for block_user in block_users:
                    link = BeautifulSoup(str(BeautifulSoup(str(block_user), 'lxml').find(name='div', class_='name')),
                                         'lxml').find(name='a')['href']
                    id = BeautifulSoup(str(BeautifulSoup(str(block_user), 'lxml').find(name='div', class_='name')),
                                       'lxml').find(name='a')['href'].split('/')[1:-1][-1]
                    info_arr = []
                    user_new_data = {}
                    try:
                        async with session.get(f'{url}{link}', headers=headers) as raw_user_data:
                            user_data = await raw_user_data.text()
                            with open('index.html', 'w') as file:
                                file.write(user_data)
                            try:
                                name = BeautifulSoup(user_data, 'lxml').find(name='div',
                                                                             class_='contractor-block__name').text.strip()
                            except Exception as ex:
                                name = "Имя не найдено"
                                print(ex)
                            try:
                                town = BeautifulSoup(str(BeautifulSoup(user_data, 'lxml').find(name='div',
                                                                                               class_='contractor-block__location')),
                                                     'lxml').find(name='b').text.strip()
                            except Exception as ex:
                                town = "Город не найден"
                                print(ex)
                            try:
                                region = BeautifulSoup(str(BeautifulSoup(user_data, 'lxml').find(name='div',
                                                                                                 class_='contractor-block__location')),
                                                       'lxml').find(name='span', class_='text-muted').text.strip()
                            except Exception as ex:
                                region = "Регион не найден"
                                print(ex)
                            try:
                                info_array = BeautifulSoup(user_data, 'lxml').find_all(name='div',
                                                                                       class_='contractor' +
                                                                                              '-block__pricelist-row')
                                for info in info_array:
                                    info_dict = {}
                                    info_name = BeautifulSoup(str(info), 'lxml').find(name='div',
                                                                                      class_="contractor-block__service").text.strip()
                                    info_price = BeautifulSoup(str(info), 'lxml').find(name='div',
                                                                                       class_="contractor-block__price").text.strip()
                                    info_dict[info_name] = info_price
                                    info_arr.append(info_dict)
                            except Exception as ex:
                                info_arr = "Специальности не найден"
                                print(ex)
                        user_new_data['Регион'] = region
                        user_new_data['Город'] = town
                        user_new_data['Специальности'] = info_arr
                        users[name] = user_new_data
                    except Exception as ex:
                        print(f'Не удалось получить {id}', raw_user_data.url, ex, sep='\n')
            except Exception as ex:
                print(ex)
    with open('./user.json', 'w') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


async def get_works_data(session, block_dict):
    print('Getting a links to workers')
    for block_link in block_dict:
        async with session.get(f'{url}{block_dict[block_link]}', headers=headers) as responce:
            tasks = []
            try:
                links = {}
                just_links = BeautifulSoup(str(
                    BeautifulSoup(await responce.text(), 'lxml').find_all(name='div', class_='category-services-list')[
                        0]), 'lxml').find(name='a')
                high_links = BeautifulSoup(
                    str(BeautifulSoup(await responce.text(), 'lxml').find_all(name='div', class_='high-priority')[0]),
                    'lxml').find(name='a')
                links[BeautifulSoup(str(just_links), 'lxml').find(name='span').text] = just_links['href']
                links[BeautifulSoup(str(high_links), 'lxml').find(name='span', class_='heading').text] = high_links[
                    'href']
                task = asyncio.create_task(get_workers_data(session, links))
                tasks.append(task)
            except Exception as ex:
                print("!!!!!!!!!!!!!!!!!!!")
                print(responce.url)
                print("!!!!!!!!!!!!!!!!!!!")
        await asyncio.gather(*tasks)


async def get_moscow_works_data(session, block_dict):
    pass


async def get_region_data(session, region_dict, region="Тюменская"):
    for current_region in region_dict:
        print('Getting a blocks')
        if region in current_region:
            async with session.get(f'{url}/{region_dict[current_region]}', headers=headers) as responce:
                tasks = []
                all_blocks = BeautifulSoup(await responce.text(), 'lxml').find_all(name='category-children')
                for block_tag in all_blocks:
                    blocks = BeautifulSoup(str(block_tag), 'lxml').find_all(name='li')[0:-1]
                    for block in blocks:
                        block_link = {BeautifulSoup(str(block), 'lxml').find(name='a').text.strip():
                                          BeautifulSoup(str(block), 'lxml').find(name='a')['href']}
                        task = asyncio.create_task(get_works_data(session, block_link))
                        tasks.append(task)
            await asyncio.gather(*tasks)


async def get_gather_data(current_region='Тюменская'):
    print('Getting a links to regions')
    async with aiohttp.ClientSession() as session:
        tasks = []
        response = await session.get(url=f'{url}/catalog/', headers=headers)
        all_regs = BeautifulSoup(str(BeautifulSoup(await response.text(), 'lxml').find_all(class_='columned-list')[1]),
                                 'lxml').find_all(name='a')
        for region in all_regs:
            reg = {region.text: region['href']}
            task = asyncio.create_task(get_region_data(session, reg, current_region))
            tasks.append(task)
        await asyncio.gather(*tasks)


def main():
    cur_time = time.time()
    asyncio.run(get_gather_data())
    print(f'Занятое время: {time.time() - cur_time}')


if __name__ == "__main__":
    main()
