########################################################################################
#In the name of Allah
# This bot is made for serving those who want to read Quran
# May Allah accept your prayers
# Don't forget us in your prayers
########################################################################################


############### DATABASES ##################
from sqlalchemy import Column, Integer, Boolean, DateTime, String, ForeignKey, create_engine
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship, contains_eager
from sqlalchemy.ext.declarative import declarative_base
import datetime
engine = create_engine('sqlite:///temp.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    fullname = Column(String(100))
    username = Column(String(50))
    telegram_id = Column(String(50), nullable=False, unique=True)
    chat_id = Column(String(50), nullable=False, unique=True)
    in_group_index = Column(Integer, nullable=True, unique=False) #1-based
    
    group_id = Column(Integer, ForeignKey('groups.id'))
    group = relationship("Group", back_populates='all_users')
    
    def __repr__(self):
        return "<User(fullname='%s', username='%s', telegram_id='%s', chat_id='%s')>" %(self.fullname, self.username, self.telegram_id, self.chat_id)

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    is_full = Column(Boolean, nullable=False, default=False)
    has_started = Column(Boolean, nullable=False, default=False)
    last_update = Column(DateTime, onupdate=datetime.datetime.now)
    start_date = Column(DateTime, nullable=True, server_default=func.now())
    all_users = relationship("User", order_by=User.id, back_populates='group')

    def __repr__(self):
        return "<Group(is_full='%s', has_started='%s', start_date='%s')>" %(self.is_full, self.has_started, self.start_date)

Base.metadata.create_all(engine)

##### DB functions #######
def getAllUsers():
    print("getAllUser")
    users = session.query(User).join(User.group).options(contains_eager(User.group)).all()
    return users

def addUser(fullname, username, telegram_id, chat_id):
    max_user = 355
    users = getAllUsers()
    # users = session.query(User).join(User.group).options(contains_eager(User.group)).all()
    
    for user in users:
        if not user.group.is_full:
            print("getAllUser")
            empty_group = None
        if user.telegram_id == telegram_id:
            raise Exception('You are already signed in')
    new_user = User(fullname=fullname, username=username, telegram_id=telegram_id, chat_id=chat_id)

    group = None
    # TODO
    # query the last group fromm the database -> group = session.query(Group).last()
    # if it's full/empty(no group) create a new group
    if group is None or group.is_full:
        print("Group None")
        group = Group()
        session.add(group)
    new_user.in_group_index = len(group.all_users)+1 #1-based
    group.all_users.append(new_user)
    if len(group.all_users) > max_user:
        group.is_full=True
    #    groupFullNotif(group)
    session.commit() 


######################################################################################
#######################################################################################
############### BOT CODES ###################
import passlib
from passlib.hash import pbkdf2_sha256 as auth
# from passlib.hash import pbkdf2_sha26 as auth
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import logging
import configparser

logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
#########################################################################################
############# Functions ################
def doStart(group_id=0):
    #TODO finish this function
    users = getAllUsers()
    for user in users:
        bot.sendMessage(chat_id=user.chat_id, text="lotfan shoroo konid")
        # TODO send the document and the row

    ##### 1- query the group - session.query(Group).filter(Group.id=group_id)
        ##2-  users = group.all_users
        
def groupFullNotif(Group):
    #TODO
    pass

########################################################################################
############# COMMAND HANDLERS ##############
def signup(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    user = update.message.from_user
    try:
        addUser(fullname=user.first_name+' '+user.last_name, username=user.username, telegram_id=user.id, chat_id=update.message.chat_id)
        bot.sendMessage(chat_id=update.message.chat_id, text="Salaam, Mamnoon az sabte nam. سلام")
        bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_DOCUMENT) 
        bot.sendDocument(chat_id=update.message.chat_id, document=open('temp.txt','rb'), caption=user.first_name+'az radife ?? shoru konid')
        print("User added")
    except Exception as e:
        bot.sendMessage(chat_id=update.message.chat_id, text=str(e))
        print ("User adding failed:", str(e) )

def signout(bot, update):
    #TODO
    bot.sendMessage(chat_id=update.message.chat_id, text="Salaam, Mamnoon az sabte nam. Khodahafez")

def getall(bot, update, password_entered):
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    global hashed_passowrd
    password_entered = update.message.text
    if auth.verify(password_entered, hashed_password):
        users = getAllUsers()
        string = ""
        for user in users:
            string+=str(user)+' '+str(user.group)+'\n'
        print( '#'*50)
        print (string)
        print ('#'*50)
        bot.sendMessage(chat_id=update.message.chat_id, text=string)

def start(bot, update, password_entered):
    try:
        user_id = update.message.from_user.id
        password_entered = update.message.text
        # password_entered, group_id = update.message.text.split()
        global hashed_password
        if auth.verify(password_entered, hashed_password):
            group_id = 0
            doStart(group_id)
        else:
            bot.sendMessage(chat_id=update.message.chat_id, text="Wrong password!")

    except:
        bot.sendMessage(chat_id=update.message.chat_id, text="Something went wrong!")

def schedule(bot, update):
    telegram_user = update.message.from_user
    db_user = session.query(User).filter(User.telegram_id == telegram_user.id)
    # TODO: check if the user is in database, if not register him
    # if so -> two options: 1- register the user 2- send a message that he should register first

    if db_user.group.has_started != True:
        bot.sendMessage(chat_id=update.message.chat_id, text="goroohe shoma hanuz shoroo nashode ast.")
    else:    
        in_group_index = db_user.in_group_index
        
        bot.sendMessage(chat_id=update.message.chat_id, text="Lotfan kami sabr konid.")
        bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_DOCUMENT) 
        bot.sendDocument(chat_id=update.message.chat_id, document=open('temp.txt','rb'), caption=user.first_name+'az radife {} shoru konid'.format(in_group_index))
        # days = current_date - db_user.group.start_date
        # shomare_radife_emruz = in_group_index+days
        # send message 

def emruz(bot, update):
    pass

def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Wrong message.")
    

############# MESSAGE HANDLERS ###############
def echo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=update.message.text)

############# ERROR LOGGNING ################
def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def main():
    m = open('bot.ini', 'r')
    for l in m:
        print( l)

    config = configparser.ConfigParser()
    config.read('bot.ini')
    token = config['KEYS']['token']
    global hashed_password
    hashed_password = config['KEYS']['hashed_password']
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('signup', signup))
    dispatcher.add_handler(CommandHandler('signout', signout))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('getall', getall))
    dispatcher.add_handler(CommandHandler('schedule', schedule))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))
    dispatcher.add_error_handler(error)

    updater.start_polling()
    
    updater.idle()

if __name__ == '__main__':
    main()


