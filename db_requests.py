from sqlalchemy import and_, or_
from models import Clients, Comments, Users, Votes_down, Votes_up, db


async def client_in_db(id):
    data = db.query(Clients).filter(or_(Clients.phonenumber ==
                                        id, Clients.username == id, Clients.vk_link == id)).first()
    return data


async def add_user(telegram_id, user_name, telegram_username, secret_name):
    user = Users(user_telegram_id=telegram_id, user_name=user_name,
                 telegram_username=telegram_username, secret_name=secret_name)
    db.add(user)
    try:
        db.commit()
    except:
        pass


async def get_user_id(telegram_id):
    id = db.query(Users).filter(Users.user_telegram_id == telegram_id).first()
    return id.id


async def get_user(telegram_id):
    user = db.query(Users).filter(Users.user_telegram_id == telegram_id).first()
    return user


async def get_commentator_id(telegram_id):
    data = db.query(Users).filter(
        Users.user_telegram_id == telegram_id).first()
    return data.id


async def get_commentator_secret_name(telegram_id):
    data = db.query(Users).filter(
        Users.user_telegram_id == telegram_id).first()
    return data.secret_name


async def add_comment(text, commentator_id, commented_id, commentator_secret_name):
    comment = Comments(text=text, commentator_id=commentator_id,
                       commented_id=commented_id, commentator_secret_name=commentator_secret_name)
    commentator = db.query(Users).filter(Users.id == commentator_id).first()
    commentator.comments += 1
    db.add_all([comment, commentator])
    db.commit()


async def get_comments(commented_id):
    comments = db.query(Comments).filter(
        Comments.commented_id == commented_id).all()
    comments_list = []
    for row in comments:
        comments_list.append([row.commentator_secret_name, row.text])
    return comments_list


async def get_amount_comments(commented_id):
    comments = db.query(Comments).filter(
        Comments.commented_id == commented_id).count()
    return comments


async def get_ids_who_voted_up(client_id):
    data = db.query(Votes_up).filter(Votes_up.evaluating_id == client_id).all()
    ids = []
    for user in data:
        ids.append(user.assessed_id)
    return ids


async def get_ids_who_voted_down(client_id):
    data = db.query(Votes_down).filter(
        Votes_down.evaluating_id == client_id).all()
    ids = []
    for user in data:
        ids.append(user.assessed_id)
    return ids


async def vote_up(user_id, client_id):
    client = db.query(Clients).filter(Clients.id == client_id).first()
    user = db.query(Users).filter(Users.id == user_id).first()
    who_voted_up = Votes_up(assessed_id=user_id, evaluating_id=client_id)
    ids_who_voted_up = await get_ids_who_voted_up(client_id)
    ids_who_voted_down = await get_ids_who_voted_down(client_id)
    obj_voted_down = db.query(Votes_down).filter(and_(
        Votes_down.assessed_id == user_id, Votes_down.evaluating_id == client_id)).first()
    if user_id not in ids_who_voted_up:
        client.good_ratings += 1
        if user_id in ids_who_voted_down:
            client.bad_ratings -= 1
        user.ratings += 1
        if obj_voted_down:
            db.delete(obj_voted_down)
        db.add_all([client, user, who_voted_up])
        db.commit()
        return 'Спасибо за оценку!'
    else:
        return 'Вы уже оценили данного клиента!'


async def vote_down(user_id, client_id):
    client = db.query(Clients).filter(Clients.id == client_id).first()
    user = db.query(Users).filter(Users.id == user_id).first()
    who_voted_down = Votes_down(assessed_id=user_id, evaluating_id=client_id)
    ids_who_voted_up = await get_ids_who_voted_up(client_id)
    ids_who_voted_down = await get_ids_who_voted_down(client_id)
    obj_voted_up = db.query(Votes_up).filter(and_(
        Votes_up.assessed_id == user_id, Votes_up.evaluating_id == client_id)).first()

    if user_id not in ids_who_voted_down:
        client.bad_ratings += 1
        if user_id in ids_who_voted_up:
            client.good_ratings -= 1
        user.ratings += 1
        if obj_voted_up:
            db.delete(obj_voted_up)
        db.add_all([client, user, who_voted_down])
        db.commit()
        return 'Спасибо за оценку!'
    else:
        return 'Вы уже оценили данного клиента!'


async def add_client_details(client_id, data_type, data):
    client = db.query(Clients).filter(Clients.id == client_id).first()
    if data_type == 'phonenumber':

        client.phonenumber = data
    if data_type == 'name':
        client.name = data
    if data_type == 'vk_link':
        client.vk_link = data
    if data_type == 'username':
        client.username = data
    db.add(client)
    db.commit()
