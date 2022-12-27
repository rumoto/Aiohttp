import asyncio
import aiohttp
from asyncio import run


async def main():

    async with aiohttp.ClientSession() as session:
        response = await session.post('http://127.0.0.1:8080/advertisements/', json={'title': 'title_1',
                                                                                     'description': 'description_1',
                                                                                     'owner': 'owner_1'})
        print(await response.json())
        response = await session.get('http://127.0.0.1:8080/advertisements/1')
        print(await response.json())
        response = await session.patch('http://127.0.0.1:8080/advertisements/1', json={'title': 'new_title'})
        print(await response.json())
        response = await session.get('http://127.0.0.1:8080/advertisements/1')
        print(await response.json())
        response = await session.delete('http://127.0.0.1:8080/advertisements/1')
        print(await response.json())
        response = await session.get('http://127.0.0.1:8080/advertisements/1')
        print(await response.json())

run(main())