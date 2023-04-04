import asyncio
import logging
import random

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import config
import db_requests
import secret_name_list
from check import correctness_check, delete_bad_symbols
from models import Clients, db
from wellcome_messages import *


storage = MemoryStorage()
bot = Bot(token=config.API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)


class Comments_input(StatesGroup):
    user_comment = State()


class Add_client_data(StatesGroup):
    add_data = State()


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message, state: FSMContext,
 text_only=None):
    secret_name = secret_name_list.adjective[random.randint(0, len(
        secret_name_list.adjective)-1)] + ' ' + secret_name_list.animal[random.randint(0, len(secret_name_list.animal)-1)]
    button_what_can = InlineKeyboardButton(
        text='Что умеет бот?', callback_data='welcome_what_can')
    button_how_use = InlineKeyboardButton(
        text='Как пользоваться?', callback_data='welcome_how_use')
    button_for_what = InlineKeyboardButton(
        text='Для чего он нужен?', callback_data='welcome_for_what')
    button_anonymity = InlineKeyboardButton(
        text='Анонимность', callback_data='welcome_anonymity')
    welcome_keyboard = InlineKeyboardMarkup(row_width=2)
    welcome_keyboard.add(button_what_can).insert(
        button_how_use).add(button_for_what).insert(button_anonymity)

    if text_only == 1:
        return f'Остались вопросы?\n\nЕсли нет - жду от тебя номер телефона, vk или @username\n\n', welcome_keyboard
    try:
        user = await db_requests.get_user(message.from_user.id)
        bot_message = await message.answer(f'С возвращением, {user.secret_name}!\n\nВоспользуйся подсказками ниже - '
                                           'если нужно вспомнить, как со мной работать', reply_markup=welcome_keyboard)
        async with state.proxy() as fsmdata:
            fsmdata['client'] = bot_message
    except:
        await db_requests.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username, secret_name)
        bot_message = await message.answer(f'{welcome1}{secret_name}{welcome2}\n\nПочему так - '
                                           'я объясню, если нажмешь "Анонимность"', reply_markup=welcome_keyboard)
        async with state.proxy() as fsmdata:
            fsmdata['client'] = bot_message


@dp.callback_query_handler(text_contains='welcome_')
async def send_description(callback: types.Message, state: FSMContext):
    callback_data = callback.data[8:]
    welcome_messages = {'what_can': what_can, 'how_use': how_use,
                        'for_what': for_what, 'anonymity': anonymity}
    come_back = InlineKeyboardButton(
        text='Назад', callback_data='back_to_welcome')
    welcome_keyboard = InlineKeyboardMarkup(row_width=2)
    welcome_keyboard.add(come_back)
    await callback.message.edit_text(welcome_messages[callback_data], reply_markup=welcome_keyboard)


@dp.callback_query_handler(text='back_to_welcome')
async def back_to_welcome(callback: types.Message, state: FSMContext):
    wellcome_message = await send_welcome(callback, state, text_only=1)
    await callback.message.edit_text(wellcome_message[0], reply_markup=wellcome_message[1])


@dp.message_handler(commands=['formats'])
async def formats(message: types.Message):
    await message.answer(formats_message)


@dp.message_handler(content_types='text')
async def get_client(message: types.Message, state: FSMContext, first=1, from_vote=None, text_only=None):
    if first == 1:
        await state.finish()
    cleared_data_for_check = await delete_bad_symbols(message.text)
    data = await correctness_check(cleared_data_for_check)
    if not data[0]:
        await message.reply(data[1])
        return
    client = await db_requests.client_in_db(data[0])

    if not client:
        if data[1] == 'phonenumber':
            client = Clients(phonenumber=data[0])
        elif data[1] == 'vk':
            client = Clients(vk_link=data[0])
        elif data[1] == 'nickname':
            client = Clients(username=data[0])
        db.add(client)
        db.commit()

    client = await db_requests.client_in_db(data[0])
    button_up = InlineKeyboardButton(
        text=f'👍 ({client.good_ratings})', callback_data='vote_up')
    button_down = InlineKeyboardButton(
        text=f'👎 ({client.bad_ratings})', callback_data='vote_down')
    button_comments = InlineKeyboardButton(text=f'💬 ({await db_requests.get_amount_comments(client.id)})', callback_data=f'view_comments')
    button_add_client_details = InlineKeyboardButton(
        text=f'➕', callback_data='add_client_details')
    ratings_keyboard = InlineKeyboardMarkup(row_width=2)
    ratings_keyboard.add(button_up).insert(button_down).add(button_comments)

    async with state.proxy() as fsmdata:
        fsmdata['client'] = client
        fsmdata['message'] = message
        try:
            fsmdata['user_id'] = await db_requests.get_user_id(message.from_user.id)
        except:
            await message.answer('Пожалуйста, нажми ещё раз /start')
            return

    message_to_user = f'Карточка клиента\n\n'
    if client.phonenumber:
        message_to_user += f'📞 Номер: {client.phonenumber}\n'
    if client.name:
        message_to_user += f'🗣 Имя: {client.name}\n'
    if client.vk_link:
        message_to_user += f'🌐 VK: https://{client.vk_link}\n'
    if client.username:
        message_to_user += f'📨 Telegram username:{" " if client.username.startswith("@") else " @"}{client.username}\n'
    if not client.phonenumber or not client.name or not client.vk_link or not client.username:
        message_to_user += f'\nВы можете добавить данные о клиенте нажав ➕'
        ratings_keyboard = InlineKeyboardMarkup(row_width=2)
        ratings_keyboard.add(button_up).insert(button_down).add(
            button_comments).insert(button_add_client_details)
    if from_vote:
        await from_vote.edit_reply_markup(reply_markup=ratings_keyboard)
    elif text_only == 1:
        return message_to_user, ratings_keyboard
    else:
        bot_message = await bot.send_message(message.from_user.id, message_to_user, reply_markup=ratings_keyboard)
        await state.update_data(bot_message=bot_message)


@dp.callback_query_handler(text_contains='view_comments')
async def view_comments(callback: types.CallbackQuery, state: FSMContext, page=0, main=1):
    fsmdata = await state.get_data()
    try:
        client = fsmdata['client']
    except:
        await callback.answer('Пожалуста, пришлите мне номер телефона ещё раз', show_alert=True)
        return
    comments = await db_requests.get_comments(client.id)
    await state.update_data(len_comments=len(comments))
    agree = InlineKeyboardButton(
        text='💬 Написать отзыв', callback_data=f'add_comment')
    disagree = InlineKeyboardButton(
        text='Вернуться к профилю', callback_data='come_back_to_profile')
    page_number = InlineKeyboardButton(
        text=f'{page+1}/{len(comments)}', callback_data=f'number_page_{len(comments)}')
    next_page = InlineKeyboardButton(
        text='>>', callback_data=f'next_page_{page}')
    previous_page = InlineKeyboardButton(
        text='<<', callback_data=f'previous_page_{page}')
    ratings_keyboard = InlineKeyboardMarkup(row_width=3)
    if len(comments) > 0:
        ratings_keyboard.add(previous_page).insert(
            page_number).insert(next_page).add(disagree).insert(agree)
    else:
        ratings_keyboard.add(disagree).insert(agree)

    if main == 1:
        if await db_requests.get_amount_comments(client.id) == 0:
            await callback.message.edit_text(f'Пока у клиента нет отзывов. Вы можете добавить свой', reply_markup=ratings_keyboard)
        else:
            await callback.message.edit_text(f'{comments[page][0]} оставил отзыв:\n\n{comments[page][1]}', reply_markup=ratings_keyboard)
    else:
        return f'{comments[page][0]} оставил отзыв:\n\n{comments[page][1]}', ratings_keyboard


@dp.callback_query_handler(text_contains='vote_up')
async def vote_up(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    try:
        client_id = fsmdata['client'].id
    except:
        await callback.answer('Пожалуста, пришлите мне номер телефона ещё раз', show_alert=True)
        return
    user_id = fsmdata['user_id']
    message = fsmdata['message']
    bot_message = fsmdata['bot_message']
    response = await db_requests.vote_up(user_id, client_id)
    if response == 'Спасибо за оценку!':
        await callback.answer(response)
        await get_client(message, state, first=0, from_vote=bot_message)
    elif response == 'Вы уже оценили данного клиента!':
        await callback.answer(response, show_alert=True)


@dp.callback_query_handler(text_contains='vote_down')
async def vote_down(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    try:
        client_id = fsmdata['client'].id
    except:
        await callback.answer('Пожалуста, пришлите мне номер телефона ещё раз', show_alert=True)
        return
    user_id = fsmdata['user_id']
    message = fsmdata['message']
    bot_message = fsmdata['bot_message']
    response = await db_requests.vote_down(user_id, client_id)
    if response == 'Спасибо за оценку!':
        await callback.answer(response)
        await get_client(message, state, first=0, from_vote=bot_message)
    elif response == 'Вы уже оценили данного клиента!':
        await callback.answer(response, show_alert=True)


@dp.callback_query_handler(text_contains='next_page')
async def next_page(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    page = int(callback.data[10:]) + 1
    if page == fsmdata['len_comments']:
        await callback.answer('Это последний отзыв', show_alert=True)
    else:
        data = await view_comments(callback, state, page, main=0)
        await callback.message.edit_text(data[0], reply_markup=data[1])


@dp.callback_query_handler(text_contains='previous_page')
async def next_page(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data[14:]) - 1
    if page < 0:
        await callback.answer('Это первый отзыв', show_alert=True)
    else:
        data = await view_comments(callback, state, page, main=0)
        await callback.message.edit_text(data[0], reply_markup=data[1])


@dp.callback_query_handler(text_contains='number_page_')
async def next_page(callback: types.CallbackQuery, state: FSMContext):
    pages = int(callback.data[12:])
    await callback.answer(f'Всего {pages} страниц(ы)', show_alert=True)


@dp.callback_query_handler(text='come_back_to_profile')
async def come_back_to_profile(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    message = fsmdata['message']
    get_text = await get_client(message, state, first=0, text_only=1)
    await callback.message.edit_text(get_text[0], reply_markup=get_text[1])


@dp.callback_query_handler(text_contains='add_comment')
async def add_comment(callback: types.CallbackQuery, state: FSMContext):
    await Comments_input.user_comment.set()
    cancel = InlineKeyboardButton(
        text='Вернуться к профилю', callback_data='come_back_to_profile_from_state')
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(cancel)
    msg_bot_input_review = await callback.message.edit_text(f'Напишите отзыв о клиенте одним сообщением.', reply_markup=keyboard)
    await state.update_data(msg_bot_input_review=msg_bot_input_review)


@dp.callback_query_handler(text='come_back_to_profile_from_state', state='*')
async def come_back_to_profile(callback: types.CallbackQuery, state: FSMContext):
    fsmdata = await state.get_data()
    message = fsmdata['message']
    msg_bot_input_review = fsmdata['msg_bot_input_review']
    get_text = await get_client(message, state, first=0, text_only=1)
    await msg_bot_input_review.edit_text(get_text[0], reply_markup=get_text[1])
    await state.reset_state(with_data=False)


@dp.message_handler(state=Comments_input.user_comment)
async def comment_added(message: types.Message, state: FSMContext):
    text = message.text
    fsmdata = await state.get_data()
    commentator_id = await db_requests.get_commentator_id(message.from_user.id)
    commentator_secret_name = await db_requests.get_commentator_secret_name(message.from_user.id)
    commented_id = fsmdata['client'].id
    message = fsmdata['message']
    counter = 3
    await db_requests.add_comment(text, commentator_id, commented_id, commentator_secret_name)
    msg = await message.answer(f'Отзыв успешно сохранён.\nВозвращаемся в профиль клиента... ({counter})')
    while counter != 0:
        await msg.edit_text(f'Отзыв успешно сохранён.\nВозвращаемся в профиль клиента через ({counter})')
        counter -= 1
        await asyncio.sleep(1)
    await msg.delete()
    await state.reset_state(with_data=False)
    await get_client(message, state, first=0)


@dp.callback_query_handler(text='add_client_details')
async def add_client_details(callback: types.CallbackQuery, state: FSMContext):
    # await Add_client_data.add_data.set()
    fsmdata = await state.get_data()
    client = fsmdata['client']
    add_phonenumber = InlineKeyboardButton(
        text='📞 Номер телефона', callback_data='add_client_phonenumber')
    add_name = InlineKeyboardButton(
        text='🗣 Имя', callback_data='add_client_name')
    add_vk_link = InlineKeyboardButton(
        text='🌐 Страницу VK', callback_data='add_client_vk_link')
    add_username = InlineKeyboardButton(
        text='📨 Telegram username', callback_data='add_client_username')
    back_to_profile = InlineKeyboardButton(
        text='Вернуться к профилю', callback_data='come_back_to_profile')
    client_details_keyboard = InlineKeyboardMarkup(row_width=3)
    if not client.phonenumber:
        client_details_keyboard.add(add_phonenumber)
    if not client.name:
        client_details_keyboard.add(add_name)
    if not client.vk_link:
        client_details_keyboard.add(add_vk_link)
    if not client.username:
        client_details_keyboard.add(add_username)
    client_details_keyboard.add(back_to_profile)
    await callback.message.edit_text('Какие данные вы хотите добавить?', reply_markup=client_details_keyboard)


@dp.callback_query_handler(text_contains='add_client_')
async def add_client_details(callback: types.CallbackQuery, state: FSMContext):
    await Add_client_data.add_data.set()
    data_type = callback.data[11:]
    await state.update_data(data_type=data_type)
    cancel = InlineKeyboardButton(
        text='Вернуться к профилю', callback_data='come_back_to_profile_from_state')
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(cancel)
    if data_type == 'phonenumber':
        data_type_for_message = 'номер телефона, который'
    elif data_type == 'name':
        data_type_for_message = 'имя, которое'
    elif data_type == 'vk_link':
        data_type_for_message = 'ссылку на VK, которую'
    elif data_type == 'username':
        data_type_for_message = 'ник в телеграм (telegram username), который'
    msg_bot_input_review = await callback.message.edit_text(f'Пришлите {data_type_for_message} вы хотите добавить.', reply_markup=keyboard)
    await state.update_data(msg_bot_input_review=msg_bot_input_review)


@dp.message_handler(state=Add_client_data.add_data)
async def comment_added(message: types.Message, state: FSMContext):
    data = message.text
    input_message = message
    fsmdata = await state.get_data()
    client_id = fsmdata['client'].id
    message = fsmdata['message']
    data_type = fsmdata['data_type']
    msg_bot_input_review = fsmdata['msg_bot_input_review']
    counter = 3
    cleared_data_for_check = await delete_bad_symbols(data)
    data = await correctness_check(cleared_data_for_check, with_name=1)
    if not data[0]:
        cancel = InlineKeyboardButton(
            text='Вернуться к профилю', callback_data='come_back_to_profile_from_state')
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(cancel)
        await input_message.delete()
        await msg_bot_input_review.delete()
        await message.answer(data[1] + ', попробуйте ещё раз', reply_markup=keyboard)
        await state.reset_state(with_data=False)
        await Add_client_data.add_data.set()
        return
    await db_requests.add_client_details(client_id, data_type, data[0])
    msg = await message.answer(f'Данные добавлены в карточку клиента.\nВозвращаемся в профиль клиента через')
    while counter != 0:
        await msg.edit_text(f'Данные добавлены в карточку клиента.\nВозвращаемся в профиль клиента через ({counter})')
        counter -= 1
        await asyncio.sleep(1)
    await msg.delete()
    await input_message.delete()
    await msg_bot_input_review.delete()
    await state.reset_state(with_data=False)
    await get_client(message, state, first=0)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
