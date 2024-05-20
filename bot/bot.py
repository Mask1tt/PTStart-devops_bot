import logging
from pathlib import Path
import re
from dotenv import load_dotenv
import os
import paramiko
import psycopg2
from psycopg2 import Error


from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, ContextTypes

TOKEN = os.getenv('TOKEN')
updater = Updater(TOKEN, use_context=True)
j= updater.job_queue

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска адресов электронной почты: ')

    return 'find_email'

def verifypasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для его проверки: ')

    return 'verify_password'

def aptlistCommand(update: Update, context):
    update.message.reply_text('Введите название пакета(или напишите "all",что бы посмотреть все пакеты): ')

    return 'get_apt_list'




def findPhoneNumbers (update: Update, context: CallbackContext):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r'(?:\+7|8|7)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}') # формат 8 (000) 000-00-00

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END # Завершаем выполнение функции
    
    phones = ""
    for phone in phoneNumberList:
        phones += phone + "\n"

        
    update.message.reply_text(phones) 
    context.user_data['foundPhoneNumbers'] = phoneNumberList
    update.message.reply_text('Хотите ли вы записать эти данные в базу данных?(Да(y)/Нет(n))')
    return 'add_phone' # Завершаем работу обработчика диалога

def addphone(update: Update, context: CallbackContext):
    user_input = update.message.text
    if user_input == 'Да' or user_input == 'y':
        addph = context.user_data['foundPhoneNumbers']
        connection = None
        try:
            connection = psycopg2.connect(user=os.getenv('USER_DB'),
                                        password=os.getenv('PASSWORD_DB'),
                                        host=os.getenv('HOST_DB'),
                                        port=os.getenv('PORT_DB'),
                                        database=os.getenv('DATABASE_DB'))

            cursor= connection.cursor()

            for phone in addph:
                cursor.execute("INSERT INTO phones (phone) VALUES (%s)", (phone, ))
            connection.commit()
            update.message.reply_text('Запись успешно выполнена!')
        except (Exception, Error) as error:
            update.message.reply_text("Ошибка при записи")
            logging.error('Ошибка: %s', error)
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто.")
        return ConversationHandler.END
    elif user_input == 'Нет' or user_input == 'n':
        update.message.reply_text('Данные не записаны.')
        return ConversationHandler.END

def findEmail (update: Update, context: CallbackContext):
    user_input = update.message.text 

    EmailRegex = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}') # формат example@example.example

    EmailList = EmailRegex.findall(user_input) 

    if not EmailList: 
        update.message.reply_text('Адреса электронных почт не найдены!')
        return ConversationHandler.END # Завершаем выполнение функции
    
    emails = ""
    for email in EmailList:
        emails += email + "\n"
        
    update.message.reply_text(emails) 
    context.user_data['foundEmail'] = EmailList
    update.message.reply_text('Хотите ли вы записать эти данные в базу данных?(Да(y)/Нет(n))')
    return 'add_email'

def addemail(update: Update, context: CallbackContext):
    user_input = update.message.text
    if user_input == 'Да' or user_input == 'y':
        addem = context.user_data['foundEmail']
        update.message.reply_text(addem)
        connection = None
        try:
            connection = psycopg2.connect(user=os.getenv('USER_DB'),
                                        password=os.getenv('PASSWORD_DB'),
                                        host=os.getenv('HOST_DB'),
                                        port=os.getenv('PORT_DB'),
                                        database=os.getenv('DATABASE_DB'))

            cursor= connection.cursor()
            for email in addem:
                cursor.execute("INSERT INTO emails (email) VALUES (%s)", (email, ))
            connection.commit()
            update.message.reply_text('Запись успешно выполнена!')
        except (Exception, Error) as error:
            update.message.reply_text("Ошибка при записи")
            logging.error('Ошибка: %s', error)
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто.")
        return ConversationHandler.END
    elif user_input == 'Нет' or user_input == 'n':
        update.message.reply_text('Данные не записаны.')
        return ConversationHandler.END

def verifypassword (update: Update, context):
    user_input = update.message.text 

    passwordRegex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$') 

    password = passwordRegex.findall(user_input) 

    if not password: 
        update.message.reply_text('Пароль простой')
        return ConversationHandler.END
    else:
        update.message.reply_text('Пароль сложный')
        return ConversationHandler.END
        
def getrelease (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uname -r')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def getumane (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uname -a')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END 

def getuptime (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uptime -p')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END 

def getdf (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('df -h')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END  

def getfree (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('free -h')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END 

def getmpstat (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('mpstat')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END 

def getw (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('w')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END 

def getauths (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('last -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END     

def getcritical (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('journalctl -p 0 -n 5')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END 

def getps (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ps -A u | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END 

def getss (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ss | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def getaptlist (update: Update, context):
    user_input = update.message.text

    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    if user_input == 'all':
        stdin, stdout, stderr = client.exec_command('apt list --installed | head -n 10')
        data = stdout.read() + stderr.read()
        client.close()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        update.message.reply_text(data)
        return ConversationHandler.END 
    else:
        stdin, stdout, stderr = client.exec_command('apt list '+user_input+' --installed | head -n 10')
        data = stdout.read() + stderr.read()
        client.close()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        update.message.reply_text(data)
        return ConversationHandler.END 
    
def getservices (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('systemctl | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def getrepllogs (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('docker logs db --tail 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(data)

def getemails (update: Update, context):
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv('USER_DB'),
                                    password=os.getenv('PASSWORD_DB'),
                                    host=os.getenv('HOST_DB'),
                                    port=os.getenv('PORT_DB'),
                                    database=os.getenv('DATABASE_DB'))

        cursor= connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()
        update.message.reply_text(data)
        logging.info("Команда успешно выполнена!")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто.")
    return ConversationHandler.END

def getphonenumbers (update: Update, context):
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv('USER_DB'),
                                    password=os.getenv('PASSWORD_DB'),
                                    host=os.getenv('HOST_DB'),
                                    port=os.getenv('PORT_DB'),
                                    database=os.getenv('DATABASE_DB'))

        cursor= connection.cursor()
        cursor.execute("SELECT * FROM phones;")
        data = cursor.fetchall()
        update.message.reply_text(data)
        logging.info("Команда успешно выполнена!")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто.")
    return ConversationHandler.END


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'add_phone' : [MessageHandler(Filters.text & ~Filters.command, addphone)]
        },
        fallbacks=[]
    )

    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'add_email': [MessageHandler(Filters.text & ~Filters.command, addemail)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifypasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifypassword)],
        },
        fallbacks=[]
    )

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', aptlistCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, getaptlist)],
        },
        fallbacks=[]
    )

	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerGetAptList)
    dp.add_handler(CommandHandler("get_release", getrelease))
    dp.add_handler(CommandHandler("get_uname", getumane))
    dp.add_handler(CommandHandler("get_uptime", getuptime))
    dp.add_handler(CommandHandler("get_df", getdf))
    dp.add_handler(CommandHandler("get_free", getfree))
    dp.add_handler(CommandHandler("get_mpstat", getmpstat))
    dp.add_handler(CommandHandler("get_w", getw))
    dp.add_handler(CommandHandler("get_auths", getauths))
    dp.add_handler(CommandHandler("get_critical", getcritical))
    dp.add_handler(CommandHandler("get_ps", getps))
    dp.add_handler(CommandHandler("get_ss", getss))
    dp.add_handler(CommandHandler("get_services", getservices))
    dp.add_handler(CommandHandler("get_repl_logs", getrepllogs))
    dp.add_handler(CommandHandler("get_emails", getemails))
    dp.add_handler(CommandHandler("get_phone_numbers", getphonenumbers))


	# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
