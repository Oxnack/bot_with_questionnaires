TOKEN = 'bot_token'

bot_name = "bot_name"

#https://t.me/your_bot?start=parameter 

reqestPass_hash = "ac09723b8aa6cbc0017cec20523855d87c2cd1ff85ac71e4f4daea0f3e89f266" #897jkgy2489hei

# db data: ------------------------------------->>>
host = 'host_addr'  
database = 'tg_bot_data'
table_name_users = "users"
table_name_messages = "messages"

user = 'name'
password = 'passw'

# rules: root(send, get_admin, get_manager), admin(send, get_manager), manager(send), user(not)

rules_rights = {
    "root": ["send", "get_admin", "get_manager"],
    "admin": ["send", "get_manager"],
    "manager": ["send"],
    "user": ["not rights"]
}






