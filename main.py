from select import select
from sqlalchemy import func
import random
import sqlalchemy
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import json

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

user = 'postgres'  #имя пользователя
password = ''  #пароль пользователя
host = ''  #адрес хоста
port = 5432  #номер порта
name_db = ''  #название базы данных

DSN = f'postgresql://{user}:{password}@{host}:{port}/{name_db}'

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.Integer, unique = True, nullable=False)

class Dictionary(Base):
    __tablename__ = "dictionary"

    id = sq.Column(sq.Integer, primary_key=True)
    target_word = sq.Column(sq.String(length=40), nullable=False, unique = True)
    translate = sq.Column(sq.String(length=40),  nullable=False)


class VisibleOrNot(Base):
    __tablename__ = "visible_or_not"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.name"), nullable= True)
    is_visible =  sq.Column(sq.Boolean, default=True)
    dictionary_id = sq.Column(sq.Integer, sq.ForeignKey("dictionary.id"), nullable= True)

    user = relationship(User, backref = 'visible_or_not')
    dictionary = relationship(Dictionary, backref = 'visible_or_not')



def create_tables(engine):
    #  Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

engine = sqlalchemy.create_engine(DSN)
create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()
# заполнили бд
w1 = Dictionary(target_word = 'Peace', translate = 'Мир')
w2 = Dictionary(target_word = 'Hello',translate = 'Привет')
w3 = Dictionary(target_word = 'Hell',translate = 'Ад')
w4 = Dictionary(target_word ='Green',translate = 'Зелёный')
w5 = Dictionary(target_word='Blue',translate = 'Синий')
w6 = Dictionary(target_word='White',translate = 'Белый')
w7 = Dictionary(target_word='Car',translate = 'Машина')
w8 = Dictionary(target_word='She',translate = 'Она')
w9 = Dictionary(target_word='He',translate = 'Он')
w10 = Dictionary(target_word='It',translate = 'Оно')
#  session.add_all([w1, w2, w3, w4, w5 ,w6 ,w7, w8, w9, w10])
#  session.add(w1)
#  session.commit()

def add_user(username):
    new_user = User(name = username)
    session.add(new_user)
    session.commit()

def add_visible(user_id, is_visible, word_id):
    new_visible = VisibleOrNot(user_id = user_id, is_visible = is_visible, dictionary_id = word_id)
    session.add(new_visible)
    session.commit()

def add_word(target_word, translate):
    w = Dictionary(target_word= target_word,translate = translate)
    session.add(w)
    session.commit()

def update_not_visible(user_id, word_id):
    # Получаем объект из базы данных
    user = session.query(VisibleOrNot).filter(
        VisibleOrNot.user_id == user_id,
        VisibleOrNot.dictionary_id == word_id
    ).first()  # используем first() для получения первого результата или None

    # Проверяем, найден ли объект
    if user:
        user.is_visible = False  # Изменяем значение is_visible
        session.commit()  # Сохраняем изменения в базе данных
    else:
        print("Пользователь или слово не найдены.")  # Обработка случая, когда объект не найден

def update_visible(user_id, word_id):
    # Получаем объект из базы данных
    user = session.query(VisibleOrNot).filter(
        VisibleOrNot.user_id == user_id,
        VisibleOrNot.dictionary_id == word_id
    ).first()  # используем first() для получения первого результата или None

    # Проверяем, найден ли объект
    if user:
        user.is_visible = True  # Изменяем значение is_visible
        session.commit()  # Сохраняем изменения в базе данных
    else:
        print("Пользователь или слово не найдены.")  # Обработка случая, когда объект не найден


print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = ''   #  токен телеграм-бота
bot = TeleBot(token_bot, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []

def show_hint(*lines):
    return '\n'.join(lines)

def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"

class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


def get_user_step(cid):
    old_user = session.query(VisibleOrNot.user_id).filter(VisibleOrNot.user_id == cid)
    old1_user = session.query(User.name).filter(User.name == cid)
    if old1_user.first():
        return True
    else:
        add_user(cid)  # добавили пользователя
    if old_user.first():
        return True
    else:
        add_visible(cid, True, 1)
        add_visible(cid, True, 2)
        add_visible(cid, True, 3)
        add_visible(cid, True, 4)
        add_visible(cid, True, 5)
        add_visible(cid, True, 6)
        add_visible(cid, True, 7)
        add_visible(cid, True, 8)
        add_visible(cid, True, 9)
        add_visible(cid, True, 10)



@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    cid = message.chat.id
    if cid not in known_users:
        get_user_step(cid)
        known_users.append(cid)
        userStep[cid] = 0
        bot.send_message(cid, "Hello, stranger, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)


    global buttons
    buttons = []
    # target&translate words

    count = int(session.query(func.count('*')).select_from(Dictionary).scalar())
    min_value = 1
    max_value = int(count)

    tw1 = session.query(Dictionary.target_word).join(VisibleOrNot,
Dictionary.id == VisibleOrNot.dictionary_id).filter(VisibleOrNot.user_id == cid).filter(VisibleOrNot.is_visible == True).order_by(func.random()).first()
    for i in tw1:
        target_word = i

    tw2 = session.query(Dictionary.translate).filter(Dictionary.target_word == target_word)
    for y in tw2:
        translate = y.translate

    tw3 = session.query(Dictionary.id).filter(Dictionary.target_word == target_word)
    for k in tw3:
        id_for_target = k.id

    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    # others
    while True:
        num1 = random.randint(min_value, max_value)
        if num1 != id_for_target:
            break

    while True:
        num2 = random.randint(min_value, max_value)
        if num2 != id_for_target and num2 != num1:
            break

    while True:
        num3 = random.randint(min_value, max_value)
        if num3 != id_for_target and num3 != num1 and num3 != num2:
            break

    others1 = session.query(Dictionary.target_word).filter(Dictionary.id == num1)
    others2 = session.query(Dictionary.target_word).filter(Dictionary.id == num2)
    others3 = session.query(Dictionary.target_word).filter(Dictionary.id == num3)

    others = []

    for o1 in others1:
        others.append(o1.target_word)
    for o2 in others2:
        others.append(o2.target_word)
    for o3 in others3:
        others.append(o3.target_word)

    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)

    if next_btn not in buttons:
        buttons.append(next_btn)
    if add_word_btn not in buttons:
        buttons.append(add_word_btn)
    if delete_word_btn not in buttons:
        buttons.append(delete_word_btn)

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    cid = message.chat.id
    bot.retrieve_data(message.from_user.id, message.chat.id)
    bot.send_message(cid, "Введите слово, которое хотите удалить из вашего словаря:")
    @bot.message_handler(content_types=['text'])
    def process_word(message):
        word_to_delete = message.text.strip().capitalize()
        q = session.query(Dictionary.id).filter(Dictionary.translate == word_to_delete)
        if q.first():
            update_not_visible(cid, q)
            bot.send_message(cid, "Указанное слово удаленно из вашего словаря.")
            session.commit()  # фиксируем изменения
        else:
            bot.send_message(cid, "Указанное слово отсутствует в вашем словаре. Попробуйте снова.")

    bot.register_next_step_handler(message, process_word)
    return


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def adding_word(message):
    cid = message.chat.id
    bot.send_message(cid, "Введите слово (на английском языке), которое хотите добавить в словарь:")

    # Убедимся, что состояние устанавливается правильно
    bot.set_state(message.from_user.id, 'waiting_for_word')

    @bot.message_handler(content_types=['text'], state='waiting_for_word')
    def process_word(message):
        word_to_add = message.text.strip().capitalize()
        q = session.query(Dictionary.id).filter(Dictionary.target_word == word_to_add)
        vis = session.query(VisibleOrNot.is_visible).filter(VisibleOrNot.user_id == cid, VisibleOrNot.dictionary_id == q)

        if q.first():
            if any(i.is_visible for i in vis):
                bot.send_message(cid, "Указанное слово уже присутствует в вашем словаре.")
            else:
                update_visible(cid, q)
                bot.send_message(cid, "Указанное слово добавлено в ваш словарь.")
        else:
            bot.send_message(cid, "Введите слово (на русском языке), которое хотите добавить в словарь:")
            bot.set_state(message.from_user.id, 'waiting_for_translation')

        # Убедитесь, что здесь вызывается только process_word2
        bot.register_next_step_handler(message, lambda msg: process_word2(msg, word_to_add))

    @bot.message_handler(content_types=['text'], state='waiting_for_translation')
    def process_word2(message, word_to_add):
        if bot.get_state(message.from_user.id) == 'waiting_for_translation':
            translate_word = message.text.strip().capitalize()
            add_word(word_to_add, translate_word)
            q2 = session.query(Dictionary.id).filter(Dictionary.target_word == word_to_add)
            add_visible(cid, True, q2)
            bot.send_message(cid, "Указанное слово добавлено в ваш словарь.")
            bot.set_state(message.from_user.id, None)  # Сброс состояния

    bot.register_next_step_handler(message, process_word)
    return

@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data.get('target_word')  # Используем get для безопасного извлечения данных

        if not target_word:
            bot.send_message(message.chat.id, "Ошибка: Неизвестное слово.")
            return

        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!", f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")

    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)





