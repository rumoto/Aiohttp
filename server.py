from __future__ import annotations
from aiohttp import web
import pydantic
import typing
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.exc import IntegrityError
import json


router = web.RouteTableDef()
app = web.Application()

PG_DSN = 'postgresql+asyncpg://postgres:postgres@127.0.0.1:5431/aiohttp'
engine = create_async_engine(PG_DSN, echo=True)
Base = declarative_base()


class HTTPError(web.HTTPException):

    def __init__(
            self,
            *,
            headers  = None,
            reason = None,
            body = None,
            message = None
    ):
        json_response = json.dumps({'error': message})
        super().__init__(headers=headers, reason=reason, body=body, text=json_response, content_type='application/json')


class BadRequest(HTTPError):
    status_code = 400


class NotFound(HTTPError):
    status_code = 400

class Advertisement(Base):

    __tablename__ = 'advertisements'

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    owner = Column(String, nullable=False)


async def get_advertisement(advertisement_id: int, session) -> Advertisement:
    advertisement = await session.get(Advertisement, advertisement_id)
    if not advertisement:
        raise NotFound(message='advertisement not found')
    return advertisement



class AdvertisementView(web.View):

    async def get(self):
        advertisement_id = int(self.request.match_info['advertisement_id'])
        async with app.async_session_maker() as session:
            advertisement = await get_advertisement(advertisement_id, session)
            return web.json_response({'title': advertisement.title,
                            'created_at': int(advertisement.created_at.timestamp())})


    async def post(self):

        advertisement_data = await self.request.json()
        new_advertisement = Advertisement(**advertisement_data)
        async with app.async_session_maker() as session:
            try:
                session.add(new_advertisement)
                await session.commit()
                return web.json_response({'id': new_advertisement.id})
            except IntegrityError as er:
                raise BadRequest(message='user already exists')


    async def patch(self):
        advertisement_id = int(self.request.match_info['advertisement_id'])
        advertisement_data = await self.request.json()
        async with app.async_session_maker() as session:
            advertisement = await get_advertisement(advertisement_id, session)
            for column, value in advertisement_data.items():
                setattr(advertisement, column, value)
            session.add(advertisement)
            await session.commit()
            return web.json_response({'status': 'success'})


    async def delete(self):
        advertisement_id = int(self.request.match_info['advertisement_id'])
        async with app.async_session_maker() as session:
            advertisement = await get_advertisement(advertisement_id, session)
            await session.delete(advertisement)
            await session.commit()
            return web.json_response({'status': 'advertisement deleted'})


async def init_orm(app: web.Application):
    print('Приложение стартовало')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async_session_maker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession )
        app.async_session_maker = async_session_maker
        yield
    print('Приложение закрылось')


app.cleanup_ctx.append(init_orm)
app.add_routes([web.get('/advertisements/{advertisement_id:\d+}', AdvertisementView)])
app.add_routes([web.patch('/advertisements/{advertisement_id:\d+}', AdvertisementView)])
app.add_routes([web.delete('/advertisements/{advertisement_id:\d+}', AdvertisementView)])
app.add_routes([web.post('/advertisements/', AdvertisementView)])
web.run_app(app)