# region imports
import random
import traceback
import sys
import os

# endregion

random.seed('ТРОМБОЛОН КОЛЮ В ОЧКО')
# region Настройка логирования

# endregion

# region Инициализация переменных

difficulty = 15  # Количество символов на 1 символ
library = [
    'а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х',
    'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w',
    'x', 'y', 'z',
    'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х',
    'Ц', 'Ч', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
    'X', 'Y', 'Z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    '!', '"', '#', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\',
    ']', '^', '_', '`', '{', '|', '}', '~', ' '
]

key = ''
mkr = 0
message_crypted = ''
chunks = []
uncipher_chunks = []
mu = 0

# endregion

# region очистка файлов

def clear_file(filename):
    """Очистка содержимого файла."""
    try:
        with open(filename, 'w') as file:
            file.write('')
        print(f"Файл {filename} очищен.")
    except Exception as error:
        print(f"Ошибка при очистке файла {filename}: {error}")

# Проверяем, существует ли директория 'data'
if not os.path.exists('data'):
    os.makedirs('data')
    print("Создана директория 'data'.")

# Очищаем содержимое файлов в директории 'data'

# endregion

# region чтение файлов mkr (mode key reader) 0 - key_all 1 - key_for_cipher 2 - key_for_uncipher

def key_reader(mkr):
    """Чтение ключей из файла в зависимости от значения переменной mkr."""
    try:
        if mkr == 0:
            filename = 'data/key_all'
        elif mkr == 1:
            filename = 'data/key_for_cipher'
        elif mkr == 2:
            filename = 'data/key_for_uncipher'
        else:
            raise ValueError("Неправильное значение переменной mkr.")

        with open(filename, 'r', encoding='utf-8') as f:
            key = f.read()
            if mkr == 0:
                key = key[::-1]

        chunks = [key[i:i + difficulty] for i in range(0, len(key), difficulty)]
        print(f"Ключ успешно прочитан из файла {filename}.")
        return chunks

    except Exception as error:
        print(f"Ошибка при чтении ключа: {error}")
        return []

# endregion

# region генерация случайного числа

def random_key():
    """Генерация случайного ключа."""
    try:
        rand = ""
        while len(rand) < difficulty:
            population = "abcdeghijklmnopqrstuvwxyz0123456789"
            rand += "".join(random.sample(population, len(population)))
        rand = rand[:difficulty]
        print("Случайный ключ успешно сгенерирован.")
        return rand

    except Exception as error:
        print(f"Ошибка при генерации случайного ключа: {error}")
        return ""

# endregion

# region генерация "пули"

def RR_algorithm(do_decode_list):
    """Генерация пули с использованием алгоритма RR."""
    try:
        local_chunks = key_reader(mkr)

        while True:
            try:
                rand = ""
                while len(rand) < difficulty:
                    population = "abcdeghijklmnopqrstuvwxyz0123456789"
                    rand += "".join(random.sample(population, len(population)))
                rand = rand[:difficulty]

                if rand not in local_chunks:
                    index = library.index(random.choice(do_decode_list))
                    index_str = str(index).zfill(3)
                    bullet = index_str + rand + "".join(random.sample(population, 17))
                    local_chunks[index] = rand

                    with open("data/key_for_cipher", "w", encoding="utf-8") as f:
                        f.write(''.join(local_chunks))

                    print(f"Пуля сгенерирована и записана: {bullet}")
                    return bullet

            except Exception as error:
                print(f"Ошибка в RR_algorithm: {error}")
                return ""

    except Exception as error:
        print(f"Ошибка при генерации пули RR: {error}")
        return ""

# endregion

# region генерация фейковой пули

def FRR_algorithm():
    """Генерация фейковой пули с использованием алгоритма FRR."""
    try:
        bullet = ''
        while len(bullet) < difficulty:
            population = "abcdeghijklmnopqrstuvwxyz0123456789"
            bullet += str("".join(random.sample(population, len(population))))
            if isinstance(bullet[:3], str):
                break

        print(f"Фейковая пуля успешно сгенерирована: {bullet}")
        return bullet

    except Exception as error:
        print(f"Ошибка при генерации фейковой пули FRR: {error}")
        return ""

# endregion

# region инициация ключа

def key_initiation():
    """Инициация ключа."""
    global key, chunks
    clear_file('data/key_all')
    try:
        population = "abcdeghijklmnopqrstuvwxyz0123456789"
        while len(key) < len(library) * difficulty:
            key += "".join(random.sample(population, len(population)))
        if len(key) > len(library) * difficulty:
            key = key[:len(library) * difficulty]
        chunks = [key[i:i + difficulty] for i in range(0, len(key), difficulty)]
        chunks = find_duplicates(chunks)

        with open('data/key_all', 'w') as f:
            f.write(key[::-1])

        with open('data/key_for_cipher', 'w') as f:
            f.write(key)

        chunks = key_reader(mkr=0)
        print("Ключ успешно инициализирован и записан в файлы.")

    except Exception as error:
        tb = traceback.extract_tb(sys.exc_info()[2])
        lineno = tb[0][1]
        print(f"Ошибка в строке {lineno} в key_initiation: {error}")

# endregion

# region поиск дупликатов

def find_duplicates(lst):
    """Поиск и удаление дубликатов из списка."""
    try:
        unique_lst = list(dict.fromkeys(lst))
        while len(unique_lst) < len(lst):
            unique_lst.append(random_key())
        print("Дубликаты успешно обработаны.")
        return unique_lst

    except Exception as error:
        print(f"Ошибка при поиске дубликатов в find_duplicates: {error}")
        return lst

# endregion

# region шифрование

def cipher(message_docrypted, message_crypted=""):
    """Шифрование сообщения."""
    global chunks
    global mkr
    message_crypted = ""

    try:
        message_do_crypted = message_docrypted
        do_decode_list = list(message_do_crypted)

        if mkr == 1:
            bullet = RR_algorithm(do_decode_list)
        elif mkr == 0:
            bullet = FRR_algorithm()
            mkr = 1

        for uncipher_symbol in do_decode_list:
            try:
                index = library.index(uncipher_symbol)
                cipher_symbol = chunks[index]
                message_crypted += cipher_symbol
            except ValueError:
                with open('data/bugs', 'a') as f:
                    f.write(f"{uncipher_symbol}\n")
                print(f"Неизвестный символ '{uncipher_symbol}' записан в файл 'data/bugs'.")

        message_crypted += bullet

        chunks = key_reader(mkr=1)
        print("Сообщение успешно зашифровано и записано в файл 'data/message'.")
        return message_crypted

    except Exception as error:
        tb = traceback.extract_tb(sys.exc_info()[2])
        lineno = tb[0][1]
        print(f"Ошибка в строке {lineno} в cipher: {error}")

# endregion

# region Расшифровка
def uncipher(msg, mu):
    """Расшифровка сообщения."""
    message_codding_list = []

    try:

        message_codding_list.append(msg)

        for message_codding in message_codding_list:
            uncipher_chunks = key_reader(mkr=2)
            chunks_for_replace = uncipher_chunks.copy()

            bullet = message_codding[-(difficulty + 20):]
            index = bullet[:3]
            replace_element = bullet[3:3 + difficulty]
            message_codding = message_codding[:-(difficulty + 20)]

            message_for_uncipher = [message_codding[i:i + difficulty] for i in range(0, len(message_codding), difficulty)]
            message_uncipher = ""

            if index.isdigit():
                chunks_for_replace[int(index)] = replace_element
                uncipher_chunks = key_reader(mkr=2)
                chunks_for_replace = uncipher_chunks
            else:
                uncipher_chunks = key_reader(mkr=0)
                chunks_for_replace = uncipher_chunks

            for cell in message_for_uncipher:
                index_cell = uncipher_chunks.index(cell)
                element = library[index_cell]
                message_uncipher += element

            with open("data/key_for_uncipher", "w", encoding="utf-8") as f:
                f.write(''.join(chunks_for_replace))

            print(f"Сообщение успешно расшифровано и записано в файл 'data/message_uncrypted'.")
            return message_uncipher

    except Exception as error:
        print(f"Ошибка при расшифровке сообщения: {error}")

    print('Работа завершена')

# endregion

# Инициализация ключа
key_initiation()

if __name__ == '__main__':
    while True:
        msg=input('Введите сообщение: ')
        crypto_msg=cipher(msg)
        print(crypto_msg)
        uncrypto_msg=uncipher(crypto_msg, mu=1)
        print(uncrypto_msg)