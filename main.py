import db, bot, dotenv

if __name__ == "__main__":
    dotenv.load_dotenv()
    db.create()
    bot.run()
