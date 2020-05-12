import mysql.connector


TOKEN = 'You bot token'  #bot token  @BotFather
DB = mysql.connector.connect(
  host="You hostname",
  user="username",
  passwd="password",
  database="name database"
)

mycursor = DB.cursor()