import inspect
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from common.variables import DATABASE_PATH, SERVER_NAME

Base = declarative_base()


class Messages(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    sender = Column(String(25), nullable=False)
    recipient = Column(String(25), nullable=False)
    message = Column(String)
    time = Column(String(26))
    deleted = Column(Integer)

    def __init__(self, sender, recipient, message, time, deleted):
        self.sender = sender
        self.recipient = recipient
        self.message = message
        self.time = time
        self.deleted = deleted


class Contacts(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(25), nullable=False)

    def __init__(self, name):
        self.name = name


class Dealings(Base):
    __tablename__ = 'dealings'
    id = Column(Integer, primary_key=True, unique=True)
    who = Column(Integer, ForeignKey("users.id"))
    whom = Column(Integer, ForeignKey("users.id"))

    def __init__(self, who, whom):
        self.who = who
        self.whom = whom

    def __repr__(self):
        return "%i, %i" % (self.who, self.whom)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(25))
    info = Column(String(50))

    def __init__(self, name, info):
        self.name = name
        self.info = info

    def __repr__(self):
        return "%i, %s" % (self.id, self.name)


class History(Base):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    in_time = Column(String(26))
    create = Column(String(26))

    def __init__(self, user_id, in_time, create):
        self.user_id = user_id
        self.in_time = in_time
        self.create = create


class DataBase:

    def __init__(self, user_name):
        self.user_name = user_name
        self.__q_user = []  # query user
        n = DATABASE_PATH.rfind('.')  # находим в пути к БД позицию последней точки-разделителя
        self.path = ''.join(
            [DATABASE_PATH[:n], '_', self.user_name, DATABASE_PATH[n:]])  # получаем путь вставив в него имя
        self.engine = create_engine(self.path, pool_recycle=3600, echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.metadata = MetaData()
        if inspect.stack()[1].function == 'Server':  # если обращение к БД от сервера - формируем его таблицы
            # if False:  # - для проверки
            users_table = Table('users', self.metadata,
                                Column('id', Integer, primary_key=True, unique=True, autoincrement=True),
                                Column('name', String(25), unique=True, nullable=False),
                                Column('info', String(50)),
                                )
            hist_table = Table('history', self.metadata,
                               Column('id', Integer, primary_key=True, unique=True, autoincrement=True),
                               Column('user_id', Integer, ForeignKey("users.id")),
                               Column('in_time', String(26)),
                               Column('create', String(26)),
                               )
            deal_table = Table('dealings', self.metadata,
                               Column('id', Integer, primary_key=True, unique=True, autoincrement=True),
                               Column('who', Integer, ForeignKey("users.id")),
                               Column('whom', Integer, ForeignKey("users.id")),
                               )
            try:
                self.__q_user = self.session.query(User).first()  # делаем пробный запрос к БД
            except sqlalchemy.exc.OperationalError:  # если БД вдруг не существует
                self.metadata.create_all(self.engine)  # Выполним запрос CREATE TABLE для создания таблиц
                print('Создана новая БД:', self.path)
        else:  # если от Client - формируем клиентские таблицы
            messages_table = Table('messages', self.metadata,
                                   Column('id', Integer, primary_key=True, unique=True, autoincrement=True),
                                   Column('sender', String(25), nullable=False),
                                   Column('recipient', String(25), nullable=False),
                                   Column('message', String),
                                   Column('time', String(26)),
                                   Column('deleted', Integer),  # для отметки, что сообщение "удалено"
                                   )
            my_contacts = Table('contacts', self.metadata,
                                Column('id', Integer, primary_key=True, unique=True, autoincrement=True),
                                Column('name', String(25), nullable=False),
                                )
            try:
                self.__q_user = self.session.query(Messages).first()  # делаем пробный запрос к БД
            except sqlalchemy.exc.OperationalError:  # если БД вдруг не существует
                self.metadata.create_all(self.engine)  # Выполним запрос CREATE TABLE для создания таблиц
                print('Создана новая БД:', self.path)

    def save_mess(self, sender, recipient, message):  # сохранение сообщений в БД
        self.session.add(Messages(sender, recipient, message, datetime.now(), False))  # при сохранении: deleted - False
        self.session.commit()

    def save_friend(self,name):
        self.session.add(Contacts(name))  # при сохранении: deleted - False
        self.session.commit()

    def reg_user(self, name, info=''):
        __user = User(name, info)
        __create_time = ''

        self.__q_user = self.session.query(User).filter_by(name=__user.name).first()  # запрос к БД
        if not self.__q_user:  # если пользователь с таким именем не найден
            self.session.add(__user)  # помещаем в базу нового пользователя
            self.__q_user = self.session.query(User).filter_by(name=__user.name).first()
            print(f'Пользователь {__user.name} добавлен в БД. ID пользователя:', self.__q_user.id)
            __create_time = datetime.now()
        else:
            print(f'Пользователь {__user.name} уже зарегистрирован в БД.')
        self.session.add(History(self.__q_user.id, datetime.now(), __create_time))
        self.session.commit()  # сохраняем изменения в БД

    def get_users(self):
        return self.session.query(User).all()

    def get_my_list(self, who_id):
        return self.session.query(Dealings).filter_by(who=who_id).all()

    def get_user(self, who_id):  # Получаем Имя пользователя по его ID
        try:
            return self.session.query(User).filter_by(id=who_id).one().name
        except sqlalchemy.exc.NoResultFound:
            return 'Unknown'

    def find_user(self, who):  # Получаем ID пользователя по его имени
        try:
            q_find = self.session.query(User).filter_by(name=who).one().id
        except Exception:  # в случае ошибки, присваиваем ID=0 (sqlalchemy.exc.NoResultFound , IndexError)
            return 0
        else:  # или возвращаем ID пользователя
            return q_find

    def del_user(self, who_id, whom_id):
        result = self.session.query(Dealings).filter_by(who=who_id, whom=whom_id).delete(synchronize_session=False)
        self.session.commit()  # сохраняем изменения в БД
        return result

    def add_user(self, who, whom):
        # Делаем запрос к БД на предмет существования подобного соотношения
        __q_deal = self.session.query(Dealings).filter_by(who=who, whom=whom).all()
        if not bool(__q_deal):  # если возвращённый запросом список пуст
            users_deal = Dealings(who, whom)  # создаём объект записи
            self.session.add(users_deal)  # кидаем его в БД
            self.session.commit()  # сохраняем изменения
            return True
        else:  # если соотношение найдено в БД ....
            return False

# для отладки
# u = DataBase(SERVER_NAME)
# u.reg_user('111','New user')
# for _ in u.get_users():
#     print(_.name)
#
# u = DataBase('!server')
# print(u.find_user('Admin'))
# u.del_user(3,2)

# print(u.get_my_list(4))
# print(u.get_user(4))


# u = DataBase('Test')
# u.save_mess('Bob','Eve','Hello Eve')
