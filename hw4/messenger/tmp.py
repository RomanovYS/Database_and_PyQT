from messenger.common.variables import DATABASE_PATH


class MyClass:

    def __init__(self, user_name):
        self.user_name = user_name

        n = DATABASE_PATH.rfind('.')
        print(''.join([DATABASE_PATH[:n],'_',self.user_name,DATABASE_PATH[n:]]))


a = MyClass('Vasya')
