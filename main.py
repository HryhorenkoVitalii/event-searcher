import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from Keyboards.keybords import hello_keyboard, artist_name_keyboard, buy_ticket_keyboard, pagination_keybord
from Parsers.scraper import search_artist, concert_artist
from config import API_TOKEN

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

start_state, choice_artist_state, choice_concert_state, write_name_state, buy_ticket_state, pagination_state = range(6)
user_state = {}
user_pagination = {}


def get_state(message):
    return user_state[message.from_user.id]


def make_pages(concert_list: list) -> list:
    temp_list = []
    count = 0
    result = []
    if len(concert_list) > 4:
        for concert in concert_list:
            temp_list.append(concert)
            count += 1
            if count == 4:
                result.append(temp_list)
                count = 0
                temp_list = []
    else:
        result = [concert_list]
    return result


async def _pagination(message):
    concerts_pages = user_pagination[message.from_user.id]["Concert"]
    page = user_pagination[message.from_user.id]["Page"]
    max_page = len(concerts_pages)
    for concert in concerts_pages[page]:
        keyboard = buy_ticket_keyboard(concert)

        await bot.send_message(message.from_user.id,
                               "Дата:  {}\n"
                               "Где:  {}\n"
                               "Место проведения:  {}".format(concert["Date"],
                                                              concert["Concert_hall"],
                                                              concert["Place"]),
                               reply_markup=keyboard)
    if max_page > 1:
        await bot.send_message(message.from_user.id, "{}/{}".format(page + 1, max_page),
                               reply_markup=pagination_keybord())


async def get_concert(message, concert_list):
    if concert_list is None:
        await bot.send_message(message.from_user.id,
                               "Концертов не найдено")
    else:
        await bot.send_message(message.from_user.id,
                               "Найдено {} концертов\nБлижайшие концерты.".format(concert_list[0]))
        user_pagination[message.from_user.id] = {"Page": 0,
                                                 "Concert": make_pages(concert_list[1])}
        user_state[message.from_user.id] = pagination_state
        await _pagination(message)




@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    user_state[message.chat.id] = start_state
    await bot.send_message(message.from_user.id,
                           "Я помогу тебе найти ближайшие концерты по всему земному шару.Выбери тип поиска",
                           reply_markup=hello_keyboard())


@dp.callback_query_handler(lambda x: x.data == "name")
async def search_from_name(message):
    user_state[message.from_user.id] = write_name_state
    await bot.send_message(message.from_user.id, "Введите имя артиста")


@dp.message_handler(lambda message: get_state(message) == write_name_state)
async def name_result(message):
    await bot.send_message(message.from_user.id, "Обрабатываю запрос, подождите")
    artist_list = search_artist(message.text)
    if len(artist_list) == 1:
        user_state[message.from_user.id] = choice_concert_state
        concert_list = concert_artist(artist_list[0]["Artist_code"])
        await get_concert(message, concert_list)
    elif len(artist_list) == 0:
        user_state[message.from_user.id] = write_name_state
        await bot.send_message(message.from_user.id, "Повторите ввод, по вашему запросу ничего не найдено.")
    else:
        user_state[message.from_user.id] = choice_artist_state
        keyboard = artist_name_keyboard(artist_list)
        await bot.send_message(message.from_user.id, "Найдено несколько артистов.", reply_markup=keyboard)


@dp.callback_query_handler(lambda message: get_state(message) == choice_artist_state)
async def choice_name(message):
    user_state[message.from_user.id] = choice_concert_state
    concert_list = concert_artist(message.data)
    await get_concert(message, concert_list)


# ----------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda x: x.data == "location")
async def search_from_location(message):
    await bot.send_message(message.from_user.id, message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
