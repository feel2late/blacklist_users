vk_bad = ['vk.com', 'vk.com/', 'https://vk.com', 'https://vk.com/']


async def delete_bad_symbols(number):
    number = number
    bad_symbols = ['+', '(', ')', ' ', '-']
    for symbol in bad_symbols:
        number = number.replace(symbol, '')
    return number


async def correctness_check(message, with_name=0):
    if message.isdigit() or message.startswith('+') and message[1:].isdigit():
        if message.startswith('89') and len(message) == 11:
            phonenumber = '7' + message[1:]
            return phonenumber, 'phonenumber'
        elif message.startswith('+79') and len(message) == 12:
            phonenumber = message[1:]
            return phonenumber, 'phonenumber'
        elif message.startswith('79') and len(message) == 11:
            phonenumber = message
            return phonenumber, 'phonenumber'
        elif len(message) == 10:
            phonenumber = '7' + message
            return phonenumber, 'phonenumber'
        else:
            return None, '❌ Ошибка!\n\nНеверный формат телефона или его длина\n'
    elif 'vk.com' in message and len(message) < 50:
        if message in vk_bad:
            return None, 'Не указан id пользователя'
        elif message.startswith('https://vk.com/'):
            vk_link = message[8:]
            return vk_link, 'vk'
        elif message.startswith('vk.com/'):
            vk_link = message
            return vk_link, 'vk'
        else:
            return None, '❌ Ошибка!\n\nНеверный формат ссылки\n'
    elif message.startswith('@'):
        nickname = message
        if len(nickname) < 50:
            return nickname, 'nickname'
        else:
            return None, '❌ Ошибка!\n\nВы пытаетесь ввести слишком длинный nickname'
    elif with_name == 1:
        name = message
        if len(name) < 50:
            return name, 'name'
        else:
            return None, '❌ Ошибка!\n\nВы пытаетесь ввести слишком длинное имя'
    else:
        return None, '❌ Ошибка!\n\nНеверный формат вводимых данных.\nИспользуйте подсказку /formats'
