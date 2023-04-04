from sqlalchemy import BigInteger, Column, Integer, String, create_engine, or_
from sqlalchemy.orm import DeclarativeBase, Session

engine = create_engine("postgresql://postgres:psqluser@localhost/blacklist")


class Base(DeclarativeBase):
    pass


with Session(autoflush=False, bind=engine) as db:
    pass


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_telegram_id = Column(BigInteger, unique=True)
    user_name = Column(String, unique=True)
    telegram_username = Column(String, unique=True)
    ratings = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    secret_name = Column(String)


class Clients(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    phonenumber = Column(String)
    username = Column(String)
    vk_link = Column(String)
    name = Column(String)
    good_ratings = Column(Integer, default=0)
    bad_ratings = Column(Integer, default=0)
    comments = Column(Integer, default=0)


class Comments(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    commentator_id = Column(Integer)
    commented_id = Column(Integer)
    text = Column(String(500))
    commentator_secret_name = Column(String)


class Votes_up(Base):
    __tablename__ = 'votes_up'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    assessed_id = Column(Integer)
    evaluating_id = Column(Integer)


class Votes_down(Base):
    __tablename__ = 'votes_down'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    assessed_id = Column(Integer)
    evaluating_id = Column(Integer)


Base.metadata.create_all(bind=engine)
