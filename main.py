import os.path


# проверить правильность введенных данных
def get_filename():
    while True:
        filename = input("Введите имя файла, содержащего дамп памяти(.txt): ")
        if not os.path.isfile(filename):
            print("Извините, не удается найти указанный вами файл.")
            continue
        else:
            break
    return filename


def get_vaddr():
    while True:
        try:
            vaddr = hex(int((input("Пожалуйста, введите виртуальный адрес:")), 16))
        except ValueError:  #если строка или другая недопустимая форма
            print("Виртуальный адрес недействителен.")
            continue  # продолжайте попытки до тех пор, пока не будет введен правильный ввод
        except TypeError:
            print("Виртуальный адрес недействителен.")
            continue
        else:
            # успешно проанализирован пользовательский ввод
            break
    return vaddr


# класс для хранения информации о страницах
class MemoryDump():

    def __init__(self):
        self.frames = []
        self.pdbr = None
        self.boffset = None
        self.vaddrs = dict()

    def find_paddr(self, vaddr=0x40dd):
        vaddr = (bin(int(vaddr, 16))[2:]).zfill(15)
        print("Преобразованный виртуальный адрес в двоичный: ", vaddr, "\n")

        bpage, bframe, boffset = (vaddr[i:i + 5] for i in range(0, len(vaddr), 5))
        page, frame, offset = (int(i, 2) for i in (bpage, bframe, boffset))

        print("Страница", bpage, "в двоичном и", page, "в десятичном виде")
        print("Фрейм", bframe, "в двоичном и", frame, "в десятичном виде")
        print("Смещение", boffset, "в двоичном и", offset, "в десятичном виде\n")
        print("Проверка кадра PDBR", self.pdbr, "[" + str(page) + "]")

        # найти |ДЕЙСТВИТЕЛЬНО|PFN6 ... PFN0|
        value1 = self.frames[self.pdbr][page]
        # преобразовать его в двоичный и проверить первый бит, если он действителен
        first = bin(int(value1, 16))[2:]
        if first[0] == '0':
            return None, None
        # если он действителен, мы используем оставшиеся 7 бит, чтобы найти следующий кадр
        first = int(first[1:], 2)
        print("Проверка фрейма", first, "[" + str(frame) + "]")

        # найти |ДЕЙСТВИТЕЛЬНО|PT6 ... PT0|
        value2 = self.frames[first][frame]
        second = bin(int(value2, 16))[2:]
        # проверить, действительность
        if second[0] == '0':
            return None, None

        # создать физический адрес: 7 бит PFN + 5 бит смещения
        paddr = hex(int((second[1:] + boffset), 2))

        second = int(second[1:], 2)
        print("Проверка фрейма", second, "[" + str(offset) + "] чтобы найти значение, на которое он указывает.\n")

        # последний шаг: найти значение, на которое он указывает
        value = self.frames[second][offset]

        return paddr, value


def create_dump(filename):
    # открыть файл и прочитать содержимое
    file = open(filename, 'r')
    memdump = MemoryDump()

    for line in file:
        line = line.strip()
        # сохранить фрейм

        startsw = (line[:line.find(":")].lower()).split(' ')[0]
        data = (line[line.find(':') + 1:].strip()).split(' ')

        if startsw == "frame":
            # если он начинается с кадра, сохраните кадр
            memdump.frames.append(data)
        elif startsw == "pdbr":
            # если pdbr, сохранить значение для дальнейшего использования
            memdump.pdbr = int(data[0])

    file.close()

    # проверка ошибок
    if not memdump.frames:
        print("Что-то пошло не так с поиском кадров.")
        raise ValueError
    if not memdump.pdbr:
        print("Пожалуйста, поместите PDBR в файл.")
        raise ValueError

    memdump.boffset = len(memdump.frames[0])

    if not memdump.boffset or memdump.boffset < 0:
        print("Неверное смещение байта.")
        raise ValueError

    return memdump


if __name__ == "__main__":
    filename = get_filename()
    memdump = create_dump(filename)

    print("Смещение байта: ", memdump.boffset)
    print("Местонахождение PDBR: ", memdump.pdbr)
    print("Количество кадров: ", len(memdump.frames))

    while True:
        vaddr = get_vaddr()
        # получить физический адрес и значение, на которое он указывает, если существует, иначе вычислить его
        memdump.vaddrs[vaddr] = memdump.vaddrs.get(vaddr, memdump.find_paddr(vaddr))
        paddr, value = memdump.vaddrs[vaddr]

        print(memdump.vaddrs)

        if not paddr and not value:
            print("Виртуальный адрес недействителен!\n")
        else:
            print("Физический адрес", hex(int(paddr, 16)), "и значение, на которое он указывает, равно",
                  hex(int(value, 16)), "\n")