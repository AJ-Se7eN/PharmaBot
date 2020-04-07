import telebot
import config                       #импортирую файл с конфигурациями бота(токен, база данных)
import mysql.connector              #импортирую конектор для связи с сервером
from telebot import types           #клавиатура
bot = telebot.TeleBot(config.TOKEN) #токен бота

db = config.DB                      #база данных
cursor = db.cursor()

apteka_dict = {}                   

class Apteka:
    def __init__(self, name):
        self.name = name
        self.adress = None
        self.region = None
        self.selection = None
        self.search_name = None
        self.constant = None

#keyboard and sticker
@bot.message_handler(commands=['start'])
def welcome(message):
    msg = bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAI3eV56Cj5ob-7NfqeTZ4HBdwvTZXhbAAJlAgADOKAKtGgxreR2qoYYBA')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('👩🏻‍⚕️ Продавец-фармацевт', '🧴 Покупатель')
    bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот созданный чтобы помочь, Вам!".format(message.from_user, bot.get_me()),
    parse_mode='html', reply_markup=markup)

#bot answer 
@bot.message_handler(content_types=['text'])
def pharmac_or_buyer(message):
    if message.text == '🧴 Покупатель' or message.text== '🚪 Назад':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('👩🏻‍⚕️ Аптеки в Районах Бишкека', '🧴 Поиск Маски по названию и адресу','🚪 Выйти')
        msg = bot.send_message(message.chat.id, "Выберите пожалуйста:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_search_pharm) #119 строка
    elif message.text == '👩🏻‍⚕️ Продавец-фармацевт':
        msg = bot.reply_to(message, "Название вашей аптеки?",reply_markup = types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_apteka_name)

#процесс инициализации имени и принятия адресса
def process_apteka_name(message):
    try:
        user_id = message.chat.id
        apteka_dict[user_id] = Apteka(message.text)

        msg = bot.reply_to(message, "Адрес вашей Аптеки?")
        bot.register_next_step_handler(msg, process_apteka_adress)
    except Exception as e:
        bot.reply_to(message, 'oooops')

#процесс инициализации адресса и вывод меню регионов
def process_apteka_adress(message):
    try:
        user_id = message.chat.id
        apteka = apteka_dict[user_id]
        apteka.adress = message.text

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True,resize_keyboard=True)
        markup.add('Ленинский', 'Свердловский','Первомайский', 'Октябрьский')
        msg = bot.reply_to(message, 'Район вашей аптеки?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_apteka_region)
    except Exception as e:
        bot.reply_to(message, 'oooops')

#процесс инициализации региона и вывод запроса позьзователя
def process_apteka_region(message):
    try:
        user_id = message.chat.id
        apteka = apteka_dict[user_id]
        apteka.region = message.text
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True,resize_keyboard=True)
        markup.add('Да', 'Нет',)
        msg = bot.send_message(message.chat.id, f'Название вашей аптеки: {apteka.name} \n Адрес вашей аптеки: \
        {apteka.adress} \n Ваш район: {apteka.region} \nАптека успешно создана!', reply_markup=markup)
        bot.send_message(message.chat.id,'У вас имеются маски?')
        bot.register_next_step_handler(msg, yes_no_mask)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def yes_no_mask(message):
    if message.text == 'Нет':               #если ответ пользователя 'нет', то constanta принимает False 
        Apteka.constant = False             #чтобы не спрашивать у пользователя кол-во масок
        bot.send_message(message.chat.id,'Спасибо! Данные сохранены!')
        process_register_pharm(message)

    elif message.text == 'Да':              #если ответ пользователя 'да', то constanta принимает True
        Apteka.constant = True              #чтобы не спрашивать у пользователя кол-во масок
        msg = bot.send_message(message.chat.id,'Введите количество:')
        bot.register_next_step_handler(msg,process_register_pharm)

#инициализация кол-ва масок и отправка данных пользователя в сервер
def process_register_pharm(message):
    try:
        if Apteka.constant:
            user_id = message.chat.id
            selection = message.text
        elif Apteka.constant == False:
            user_id = message.chat.id
            selection = 0
        apteka = apteka_dict[user_id]
        apteka.selection = selection

        sql = "INSERT INTO pharmacy (user_id, name, adress, region, mask) VALUES (%s, %s, %s, %s, %s)"
        val = (message.chat.id, apteka.name, apteka.adress, apteka.region, apteka.selection)
        cursor.execute(sql, val)
        db.commit()

        #кнопка вначало
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True,resize_keyboard=True)
        markup.add('/start')
        msg = bot.send_message(message.chat.id, 'Можете нажать на кнопку и начнется чудо😄', reply_markup=markup)
        bot.register_next_step_handler(msg, welcome)
    except:
        bot.reply_to(message, 'oooops')

#кнопки для выбора режимa поиска
def process_search_pharm(message):
    if message.text == '👩🏻‍⚕️ Аптеки в Районах Бишкека':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('Ленинский', 'Свердловский','Первомайский', 'Октябрьский','🚪 Назад')
        send = bot.send_message(message.chat.id, "Выберите пожалуйста:", reply_markup=markup)
        bot.register_next_step_handler(send, process_search_region)#175 строка

    elif message.text == '🧴 Поиск Маски по названию и адресу':
        msg = bot.send_message(message.chat.id, 'Введите пожалуйста название аптеки:',reply_markup = types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg,process_search_names)
    
    elif message.text == '🚪 Выйти':
        exit_(message)

#запрос серверу для поиска имени по базе данных
def process_search_names(message):
    sql = "SELECT * FROM pharmacy WHERE name LIKE %s"
    val = ('%'+ message.text +'%', )
    cursor.execute(sql,val)
    search_name = cursor.fetchall()
    Apteka.search_name = search_name #записываю в переменную для дальнейшего сравнения 156 строка

    msg = bot.send_message(message.chat.id, 'Введите пожалуйста адрес аптеки:')
    bot.register_next_step_handler(msg,process_search_adress)

#запрос к серверу и окончательный вывод ответа
def process_search_adress(message):
    try:
        x = 0       # переменная для посчета аптек удовлетворяющих данным параметрам
        sql = "SELECT * FROM pharmacy WHERE adress LIKE %s"
        val = ('%'+ message.text +'%', )
        cursor.execute(sql,val)
        search_address = cursor.fetchall()
        #Пускаем result по циклу в котором хранятся все данные(название аптеки, район, адрес и т.д) 
        #То есть данные каждой отдельной аптеки, которые удовлетворяют искомой аптеке по адресу
        #Если данные аптеки так же удовлетворяют искомой аптеке по имени, то выводим result
        for result in search_address:
            if result in Apteka.search_name:
                #обращаюсь индексу таблицы (result- отдельная аптека) 
                #в таблице под индексом 0 хранится имена, под индексом 2 адреса и т.д
                bot.send_message(message.chat.id,f"Название: {result[0]} \n \
                Адрес: {result[2]} \nНаличие масок: {str(result[4])}")

                x+=1 #добавляем к переменной так как такой адрес имеется
        #если не имеется аптек по данному адресу и с таким именем в бд то отправляем смс
        if x == 0:
            bot.send_message(message.chat.id, "Аптека с такими данными не зарегистрированна!")
        #кнопка назад
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('🚪 Назад')
        send = bot.send_message(message.chat.id, "Желаете вернуться назад?", reply_markup=markup)
        bot.register_next_step_handler(send, pharmac_or_buyer)
    except:
        bot.reply_to(message, 'oooops')

def process_search_region(message):
    if message.text == "🚪 Назад":
        farmac_or_buyer(message)

    else:
        try: #вывод аптек по данным районам
            sql = "SELECT * FROM pharmacy WHERE region LIKE %s"
            val = (message.text,)
            cursor.execute(sql,val)
            regions = cursor.fetchall()
            for region_ in regions:
                bot.send_message(message.chat.id,f"Название: {region_[0]} \
                \nАдрес: {region_[2]} \nНаличие масок: {str(region_[4])}")

        except:
            bot.reply_to(message, 'oooops')

def exit_(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('/start')  
    msg = bot.send_message(message.chat.id, 'Можете нажать на кнопку и начнется чудо😄', reply_markup=markup)
    bot.register_next_step_handler(msg, welcome)

#цикл запроса бота к собственному серверу чтобы получать письма
bot.polling(none_stop=True)