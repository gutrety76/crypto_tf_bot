import datetime
import os
import threading
import time
from dotenv import load_dotenv
import requests
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
import logging
from fetchingdata import add_signal,get_all_users, block_user, check_user_status, delete_exact_signal, get_all_requested_users, get_all_unblocked_users, get_new_signals, get_or_create_user, request_signal, reset_signal_request, search_all_signals, unblock_user
from telebot.apihelper import ApiTelegramException
import telebot
from telebot import types

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

courses = dict()
user_states = {}
user_photos = {}
bot_token = os.getenv("TG_TOKEN")
bot = telebot.TeleBot(bot_token)

def handle_photo(message):
   
    
    text_of_message,date_of_start,date_of_end = message.text.split("+")
    date_of_st = date_of_start.split(":")
    date_of_en = date_of_end.split(":")
    dt = datetime.datetime(int(date_of_st[0]), int(date_of_st[1]), int(date_of_st[2]), int(date_of_st[3]), int(date_of_st[4]))
    de = datetime.datetime(int(date_of_en[0]), int(date_of_en[1]), int(date_of_en[2]), int(date_of_en[3]), int(date_of_en[4]))
    
    try:

        add_signal(text_of_message, dt, de)
        bot.send_message(chat_id=message.chat.id, text="Сигнал создан")
    except e:
        print(e)
def create_keyboard_with_courses():
    markup = types.InlineKeyboardMarkup()
    
    markup.add(types.InlineKeyboardButton(text="📈Получить вход", callback_data="getsignal"))
    markup.add(types.InlineKeyboardButton(text="💬Тех. Поддержка", callback_data="support"))
    #markup.add(types.InlineKeyboardButton(text="👨‍💻FAQ", callback_data="faq"))
    return markup



@bot.message_handler(func=lambda message: True)
def echo_message(message):
    user_id = message.chat.id
    print(user_states)
    print(message.text)
    if message.text.lower() == "/start":
        start(message)
        if user_id not in user_states:
            user_states[user_id] = "NORMAL"
        
    else:
        if message.chat.id == -1001511072724:
            
            if message.text == "/createsignal":
                user_states[message.chat.id] = "WAITING_FOR_PHOTO"
                bot.send_message(chat_id=message.chat.id, text="Отправь одним сообщением в формате: текст+year:month:day:hour:minute+year:month:day:hour:minute" )
            elif message.text == "/closesignal":
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(text="Сигнал был удачный", callback_data="goodsignal"))
                markup.add(types.InlineKeyboardButton(text="Сигнал был неудачный", callback_data="badsignal"))
                for key, value in user_photos.items():
                    user_photos[key] = []
                bot.send_message(chat_id=message.chat.id, text="Выберите опцию", reply_markup=markup)
            elif message.text == "/createnotification":
                bot.send_message(chat_id=message.chat.id, text="След сообщение будет текстом уведомления для всех" )
                user_states[message.chat.id] = "WAITING_FOR_NOTIFICATION"
            elif user_states[message.chat.id] == "WAITING_FOR_NOTIFICATION":
                user_states[message.chat.id] = "NORMAL"

                res = get_all_users()
                for i in res:
                    try:
                        bot.send_message(chat_id=i[0], text=message.text)
                    except ApiTelegramException as e:
                        if e.error_code == 403:
                            print(f"Skipped user {i[0]} due to deactivation or blocking.")
                        else:
                            raise  # Re-raise the exception if it's not the one we're trying to handle
                user_states[message.chat.id] = "NORMAL"
            elif message.text == "/deletesignal":
                res = search_all_signals()
                
                markup = types.InlineKeyboardMarkup()
                
                for i in res:
                    
                    markup.add(types.InlineKeyboardButton(text=i[2], callback_data=f"delete-{i[0]}"))
                bot.send_message(chat_id=user_id, reply_markup=markup, text="Выбери сигнал для удаления")
            elif message.text == "/unblockuser":
                bot.send_message(chat_id=user_id, text= "Напиши id челика")
                user_states[user_id] = "WAITING_FOR_ID_FOR_UNBAN"
            elif user_states[user_id] == "WAITING_FOR_ID_FOR_UNBAN":
                user_states[int(message.text)] = "NORMAL"
                reset_signal_request(int(message.text))
                unblock_user(int(message.text))
                user_photos[int(message.text)] = []
                bot.send_message(chat_id=int(message.text), text="Вы разблокированы! Теперь вы можете пользоваться ботом")
                bot.send_message(chat_id=user_id, text="Пользователь разблокирован!")

            elif message.text == "/ad":
                
                markup = types.InlineKeyboardMarkup()
                url_button = types.InlineKeyboardButton(text="ПЕРЕЙТИ В БОТА ✅", url="https://t.me/MarketViewTradingBot")
                markup.add(url_button)

                text = """▫️ Добро пожаловать в MarketViewBot.

▪️ Ежедневные *Premium Intraday Входы* за концепцией Smart Money.

Как это работает? 

- заходите в указанную позицию на своем аккаунте Binance (или другой крипто биржи)
- прикрепляете скриншот открытой позиции в бота.
- после закрытия позиции отправляете квитанцию о закрытом ордере.
- скидываете *50% прибыли* в *USDT через сеть TRC20*.
- отправляете квитанцию платежа: скриншот или фото."""
    
                photo_url = 'https://i.ibb.co/N12qvc0/ad.jpg' # replace with the URL or file_id of your photo
    
                bot.send_photo(chat_id=message.chat.id,parse_mode="Markdown",photo=photo_url, caption=text, reply_markup=markup)
            elif user_states.get(message.chat.id) == "WAITING_FOR_PHOTO":
                
                handle_photo(message)

        
@bot.message_handler(content_types=['photo'])
def handle_message_with_photo(message):
    user_id = message.chat.id
    
    if user_states.get(user_id) == "WAITING_FOR_FIRST_SCREEN":
        markup = types.InlineKeyboardMarkup()
        
        markup.add(types.InlineKeyboardButton(text="Подтвердить", callback_data=f"fscreen-accept-{user_id}"))
        markup.add(types.InlineKeyboardButton(text="Отклонить", callback_data=f"fscreen-decline-{user_id}"))
        markup.add(types.InlineKeyboardButton(text="Заблокировать", callback_data=f"fscreen-userblock-{user_id}"))
        bot.send_photo(chat_id=-1001511072724, photo=message.photo[-1].file_id, reply_markup=markup, caption=f"{user_id}")
        bot.send_message(chat_id = user_id, text = "Скриншот отправлен! Находится в обработке⏳")
    if user_states.get(user_id) == "WAITING_FOR_SECOND_SCREEN":
        if user_id not in user_photos:
            user_photos[user_id] = [] 
        if len(user_photos[user_id]) == 1:
            user_photos[user_id].append(message.photo[-1].file_id)
        elif len(user_photos[user_id]) == 0:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text="✅ Оплата совершена", callback_data=f"oplatasovershena-{user_id}"))
            bot.send_message(chat_id = user_id,reply_markup=markup, parse_mode="MARKDOWN",text = "Оплата производится стейблкойном (USDT) по адресу кошелька.\n" +
                             "Сумма: **50% от прибыли**\n" +
                             "Сеть: **Tron (TRC20)**\n" +
                             "Адрес: `TBputbak1tfsJ3CThQjtReEu23aydRbYcG`\n\n" +
                             "*Вы платите физическому лицу. Деньги поступят на счёт получателя.*")
            user_photos[user_id].append(message.photo[-1].file_id)
        
        if len(user_photos[user_id]) >= 2:
            markup = types.InlineKeyboardMarkup()
            markup.add()
            markup.add(types.InlineKeyboardButton(text="Подтвердить", callback_data=f"sscreen-accept-{user_id}"))
            markup.add(types.InlineKeyboardButton(text="Отклонить", callback_data=f"sscreen-decline-{user_id}"))
            markup.add(types.InlineKeyboardButton(text="Заблокировать", callback_data=f"sscreen-userblock-{user_id}"))
            bot.send_photo(chat_id=-1001511072724, photo=user_photos[user_id][0])
            bot.send_photo(chat_id=-1001511072724, photo=user_photos[user_id][1], reply_markup=markup, caption=user_id)
            bot.send_message(chat_id = user_id, text = "Скриншоты отправлены ✅! Ожидайте их обработки")
            
def start(message):
    user_id = message.chat.id
    text =  """▫️ Добро пожаловать в MarketViewBot.

▪️ Ежедневные *Premium Intraday Входы* за концепцией Smart Money.

Как это работает? 

- заходите в указанную позицию на своем аккаунте Binance (или другой крипто биржи)
- прикрепляете скриншот открытой позиции в бота.
- после закрытия позиции отправляете квитанцию о закрытом ордере.
- скидываете *50% прибыли* в *USDT через сеть TRC20*.
- отправляете квитанцию платежа: скриншот или фото."""
    user = get_or_create_user(user_id)
    markup = create_keyboard_with_courses()
    bot.send_message(chat_id=message.chat.id, parse_mode="markdown", text=text, reply_markup=markup)
   

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    prefix = call.data.split("-")
    user_id = call.message.chat.id
    if len(prefix) > 2:
        prefix[2] = int(prefix[2])

    if prefix[0] == "support":
        bot.send_message(chat_id=user_id, text=f"Напишите ваш вопрос напрямую менеджеру MarketView:\n@MarketView_Manager. Не забудьте отправить менеджеру ваш id: {user_id}")
    if prefix[0] == "delete":
        res = delete_exact_signal(prefix[1])
        print(res)
        bot.send_message(chat_id=user_id, text="Сигнал удален")
    if prefix[0] == "getsignal":
        check = check_user_status(user_id)
        if check:
            if user_states[user_id] == "WAITING_FOR_FIRST_SCREEN":
                bot.send_message(chat_id=user_id, text="Вы не отправили скрин захода в позицию")
            elif user_states[user_id] == "WAITING_FOR_SECOND_SCREEN":
                bot.send_message(chat_id=user_id, text="Вы не отправили скриншоты полученной прибыли и отправленных денег")
            else:
                request_signal(user_id)
                bot.send_message(chat_id=user_id, text="✅ Бот принял ваш запрос на получение позиции! Как только команда Market View найдет хорошую ситуацию на текущем рынке - Бот скинет вам вход в позицию сообщением в котором будет:\n"
                + "\n- график.\n- текстовое описание.\n- вход, take profit, stop loss.")
        else:
            bot.send_message(chat_id = user_id, text = "Вы заблокированы! Чтобы подать апеляцию напишите в тех. поддержку.")
    ###### Closing of signal 
    elif prefix[0] == "oplatasovershena":
        bot.send_message(chat_id=int(prefix[1]), text="💸 Оплатили?\n\n👌🏻 Тогда отправьте сюда картинкой(макс. 1 картинка) квитанцию платежа: скриншот или фото.\n\n‼️ На квитанции должны быть четко видны: дата, время и сумма платежа.")
    elif prefix[0] == "goodsignal":
        for key, value in user_states.items():
            if value == 'WAITING_FOR_RESPOND_FROM_ADMINS':
                bot.send_message(chat_id=key,parse_mode="MARKDOWN", text="✅ **Take Profit** по торговой паре был успешно отработан.\n\n" + 
                                 "🟢 Отправьте скриншот закрытого ордера.(макс. 1 картинка)\n\n" +
                                 "‼️ На квитанции должны быть четко видны: **дата, время и реализованная прибыль.**")
                user_states[key] = "WAITING_FOR_SECOND_SCREEN"
                user_photos[key] = []
    elif prefix[0] == "badsignal":
        for key, value in user_states.items():
            if value == 'WAITING_FOR_RESPOND_FROM_ADMINS':
                markup = types.InlineKeyboardMarkup()
    
                markup.add(types.InlineKeyboardButton(text="📈Получить вход", callback_data="getsignal"))
                markup.add(types.InlineKeyboardButton(text="💬Тех. Поддержка", callback_data="support"))
                bot.send_message(chat_id=key, reply_markup=markup, text="Сработал stop loss⛔️. Со следующей успешной сделки вы не будете отправлять % прибыли нашей команде 👌")
                user_states[key] = "NORMAL"
                user_photos[key] = []
    #######Handling of 1 screen
    elif prefix[0] == "fscreen" and prefix[1] == "accept":
        bot.send_message(chat_id=prefix[2], parse_mode="MARKDOWN",  text="Ваш скриншот захода в позицию был одобрен. Ожидаем отработку текущей позиции ✅")
        bot.send_message(chat_id=1001511072724, text="Одобрено")
        user_states[int(prefix[2])] = "WAITING_FOR_RESPOND_FROM_ADMINS"
        user_photos[key] = []
    elif prefix[0] == "fscreen" and prefix[1] == "decline":
        bot.send_message(chat_id=prefix[2], text="Ваш скриншот захода в позицию не был одобрен.")
        bot.send_message(chat_id=1001511072724, text="Отклонено")
        user_photos[key] = []
    elif prefix[0] == "fscreen" and prefix[1] == "userblock":
        bot.send_message(chat_id=prefix[2], text = "Вы заблокированы. Чтобы подать апеляцию напишите в тех. поддержку.")
        block_user(prefix[2])
        
    elif prefix[0] == "sscreen" and prefix[1] == "accept":
        markup = create_keyboard_with_courses()
        bot.send_message(chat_id=prefix[2], reply_markup=markup, parse_mode="MARKDOWN",  text="Ваши скриншоты подтверждения оплаты были одобрены. Теперь вы можете получить еще один сигнал.")
        bot.send_message(chat_id=1001511072724, text="Принято")
        user_states[prefix[2]] = "NORMAL"
        user_photos[key] = []
    elif prefix[0] == "sscreen" and prefix[1] == "decline":
        bot.send_message(chat_id=prefix[2], text="Ваши скриншоты подтверждения оплаты не были одобрены. Сделайте более качественный скриншот или обратитесь в тех. поддержку!")
        bot.send_message(chat_id=1001511072724, text="Отклонено")
        user_photos[key] = []
    elif prefix[0] == "sscreen" and prefix[1] == "userblock":
        bot.send_message(chat_id=prefix[2], text = "Вы заблокированы. Чтобы подать апеляцию напишите в тех. поддержку.")
        block_user(prefix[2])



@bot.message_handler(commands=['help'])
def help_command(message):
    """Displays info on how to use the bot."""
    bot.send_message(chat_id=message.chat.id, text="Напиши /start чтобы начать использовать бот.")





def send_signal_to_all_unblocked_users():
    last_check_time = datetime.datetime.now()
    
    while True:
        time.sleep(1) 
       
        new_signals = get_new_signals(last_check_time) 
        last_check_time = datetime.datetime.now()
        for signal in new_signals: 
            
            all_unblocked_users = get_all_requested_users()  
            for user in all_unblocked_users:
                try:
                    
                    dt = signal["start_date"].strftime('%Y_%m_%d-%H:%M')
                    de = signal["end_date"].strftime('%Y_%m_%d-%H:%M')
                    markup = create_keyboard_with_courses()
                    

                    bot.send_message(chat_id=user['id'], text=signal["text"] + "\n" + dt + ' - ' + de + "(UTC+3)" , reply_markup=markup)
                    bot.send_message(chat_id=user['id'],parse_mode="MARKDOWN", text = "📊 Прикрепите скриншот вашей открытой позиции.\n" + 

"‼️ На фото должны быть четко видны: **объем, торговая пара и текущий P&L.**\n"+"🚫 За спам вы можете быть заблокированы!")
                    user_states[user['id']] = "WAITING_FOR_FIRST_SCREEN"
                    reset_signal_request(user['id'])
                    #block_user(user['id'])
                    

                except telebot.apihelper.ApiException:
                    print("Error 108")
                    #mark_user_as_blocked(user)  

if __name__ == "__main__":
    while True:
        try:
            threading.Thread(target=send_signal_to_all_unblocked_users).start()
            bot.infinity_polling()
            
        except Exception as e:
            print(f"An exception occurred: {e}. Sleeping for a while before retrying...")
            time.sleep(10)
