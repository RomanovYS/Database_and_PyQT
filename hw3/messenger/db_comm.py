from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from common.variables import DATABASE_PATH

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(25))
    info = Column(String(50))

    def __init__(self, name, info):
        self.name = name
        self.info = info


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
    engine = create_engine(DATABASE_PATH, pool_recycle=3600, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    def reg_user(self, name, info=''):
        __user = User(name, info)
        __q_user = []  # query user
        __create_time = ''
        __no_user = False  # флаг отсутствия пользователя в БД

        metadata = MetaData()
        users_table = Table('users', metadata,
                            Column('id', Integer, primary_key=True, unique=True, autoincrement=True),
                            Column('name', String(25), unique=True, nullable=False),
                            Column('info', String(50)),
                            )
        hist_table = Table('history', metadata,
                           Column('id', Integer, primary_key=True, unique=True, autoincrement=True),
                           Column('user_id', Integer, ForeignKey("users.id")),
                           Column('in_time', String(26)),
                           Column('create', String(26)),
                           )

        try:
            __q_user = self.session.query(User).filter_by(name=__user.name).first()  # делаем пробный запрос к БД
        except sqlalchemy.exc.OperationalError:  # если БД вдруг не существует
            metadata.create_all(self.engine)  # Выполним запрос CREATE TABLE для создания таблиц
            print('Создана новая БД')
            __no_user = True  # будем добавлять
        else:  # при наличии БД
            if not __q_user:  # если пользователь с таким именем не найден
                __no_user = True  # будет добавлен
            else:
                print('Пользователь уже зарегистрирован в БД')
        finally:
            if __no_user:  # если обнаружилось что, пользователя нет - добавляем
                self.session.add(__user)  # помещаем в базу нового пользователя
                __create_time = datetime.now()  # отмечаем дату создания пользователя
                self.session.commit()  # сохраняем изменения в БД
                print('Пользователь добавлен в БД')
                __q_user = self.session.query(User).filter_by(
                    name=__user.name).first()  # и получаем финальные данные по пользователю
            print('ID пользователя', __q_user.id)
            hist_time = History(__q_user.id, datetime.now(), __create_time)
            self.session.add(hist_time)  # пишем в БД время входа
            self.session.commit()  # сохраняем изменения в БД

# для отладки
# u = DataBase()
# u.reg_user('111','New user')
