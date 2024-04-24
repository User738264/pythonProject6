import sqlite3

chat_ids_and_their_links = {}
u = sqlite3.connect('users.db')
cursor_u = u.cursor()
cursor_u.execute('''
CREATE TABLE IF NOT EXISTS System (
orderid INT PRIMARY KEY,
user TEXT NOT NULL,
link TEXT NOT NULL,
qwerty TEXT NOT NULL,
tokens INTEGER
)
''')
u.commit()
u.close()

con = sqlite3.connect('users.db')
cur = con.cursor()
result = cur.execute("""SELECT user, link, qwerty FROM System""").fetchall()
con.commit()
con.close()
for i in result:
    chat_ids_and_their_links[i[0]] = (i[1], i[2])

a = sqlite3.connect('admins.db')
cursor_a = a.cursor()
cursor_a.execute('''
CREATE TABLE IF NOT EXISTS Admins (
id TEXT,
qwerty TEXT
)
''')
a.commit()
a.close()
con = sqlite3.connect('admins.db')
cur = con.cursor()
result1 = cur.execute("""SELECT id, qwerty FROM Admins""").fetchall()
print(result1)
con.commit()
con.close()
admins_and_their_group = {}
for i in result1:
    admins_and_their_group[i[0]] = i[1]
print(admins_and_their_group)
con = sqlite3.connect('users.db')
cursor_a = con.cursor()
cursor_a.execute('''
CREATE TABLE IF NOT EXISTS Exercise (
user TEXT,
task TEXT,
prompt TEXT,
password TEXT, 
state TEXT
)
''')
con.commit()
con.close()


con = sqlite3.connect('users.db')
cursor_a = con.cursor()
cursor_a.execute('''
CREATE TABLE IF NOT EXISTS Context (
user TEXT,
msg TEXT,
role TEXT
)
''')
con.commit()
con.close()
