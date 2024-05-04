# SQL-TelegramBot

Subscription manager Telegram Bot on Python with SQL database.

There a lot of subscriptions in our life that require constant tracking.
But we often forget about them and get unexpected expenses. This Bot allows
to add information about current subscriptions and get list of all 
subscriptions that you have.

The following functionality is implemented in this project:
There is the main.py file with the Telegram bot code and there is the 
database.py file with database queries. Interaction with database
implemented with SQL scripts.

Firstly you start the bot by pressing /start. You can check if you are
in database by pressing /in_users. 
Then you can add new subscription by pressing /new_sub and giving
information about it.
This info is stored in SQLite database ('users.db' by default)
and can be accessed at any time. By pressing /list_subs you get
list of all your subscriptions. Also, you can remove all records about
yourself by pressing /delete_user. At any moment you can /cancel
operation of adding new subscription.

There will be updates in this project connected with sending notifications
about future payments and better interaction with list of subscriptions.