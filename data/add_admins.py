import sqlite3
p = input()
a = sqlite3.connect('admins.db')
cursor_a = a.cursor()
t = cursor_a.execute('''SELECT * from Admins''').fetchall()
print(t)
cursor_a.execute('''INSERT INTO Admins (id, qwerty) VALUES (?, ?)''', (p, '-'))

a.commit()
a.close()
