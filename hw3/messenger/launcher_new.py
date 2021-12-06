import subprocess

NICKNAMES = ['Admin', 'Alice', 'Bob', 'Eve']  # Список пользователей

# Объявляем и сразу вносим экземпляр сервера
PROCESS = [subprocess.Popen('python server_new.py', creationflags=subprocess.CREATE_NEW_CONSOLE)]

for i in NICKNAMES:  # добавляем процессы согласно списка пользователей
    PROCESS.append(subprocess.Popen(f'python client_new.py -n {i}', creationflags=subprocess.CREATE_NEW_CONSOLE))

inp = input('Введите что нибудь для окончания работы чата -')  # просто ждём ввод, после которого всё закончится
while PROCESS:  # Закрываем все дочерние процессы
    VICTIM = PROCESS.pop()
    VICTIM.kill()
