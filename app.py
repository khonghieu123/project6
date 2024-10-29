import os
from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', 'aaaaa')

# Cấu hình kết nối MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '07082004'
app.config['MYSQL_DB'] = 'family_expense_tracker'

mysql = MySQL(app)

@app.route("/home")
def home():
    return render_template("homepage.html")

@app.route("/")
def add():
    return render_template("home.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM register WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            msg = 'Tài khoản đã tồn tại!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Địa chỉ email không hợp lệ!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Tên người dùng chỉ chứa chữ cái và số!'
        else:
            cursor.execute('INSERT INTO register (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
            mysql.connection.commit()
            msg = 'Bạn đã đăng ký thành công!'
            return redirect('/signin')

    return render_template('signup.html', msg=msg)

@app.route("/signin")
def signin():
    return render_template("login.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    global userid
    msg = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM register WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            userid = account[0]
            session['username'] = account[1]
            return redirect('/home')
        else:
            msg = 'Tên người dùng hoặc mật khẩu không đúng!'
    return render_template('login.html', msg=msg)

@app.route("/add")
def adding():
    return render_template('add.html')

@app.route('/addexpense', methods=['GET', 'POST'])
def addexpense():
    if 'loggedin' not in session:
        return redirect('/signin')

    if request.method == 'POST':
        date = request.form['date']
        expensename = request.form['expensename']
        amount = request.form['amount']
        paymode = request.form['paymode']
        category = request.form['category']

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO expenses (userid, date, expensename, amount, paymode, category) VALUES (%s, %s, %s, %s, %s, %s)',
                       (session['id'], date, expensename, amount, paymode, category))
        mysql.connection.commit()
        return redirect("/display")

@app.route("/display")
def display():
    if 'loggedin' not in session:
        return redirect('/signin')

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE userid = %s ORDER BY date DESC', (session['id'],))
    expense = cursor.fetchall()

    return render_template('display.html', expense=expense)

@app.route('/delete/<string:id>', methods=['POST', 'GET'])
def delete(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = %s', (id,))
    mysql.connection.commit()
    return redirect("/display")

@app.route('/edit/<id>', methods=['POST', 'GET'])
def edit(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE id = %s', (id,))
    row = cursor.fetchone()
    return render_template('edit.html', expenses=row)

@app.route('/update/<id>', methods=['POST'])
def update(id):
    if request.method == 'POST':
        date = request.form['date']
        expensename = request.form['expensename']
        amount = request.form['amount']
        paymode = request.form['paymode']
        category = request.form['category']

        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE expenses SET date = %s, expensename = %s, amount = %s, paymode = %s, category = %s WHERE id = %s",
            (date, expensename, amount, paymode, category, id))
        mysql.connection.commit()
        return redirect("/display")

@app.route("/limit")
def limit():
    return redirect('/limitn')

@app.route("/limitnum", methods=['POST'])
def limitnum():
    if request.method == "POST":
        number = request.form['number']
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO limits VALUES (NULL, %s, %s)', (session['id'], number))
        mysql.connection.commit()
        return redirect('/limitn')

@app.route("/limitn")
def limitn():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT limitss FROM limits ORDER BY id DESC LIMIT 1')
    x = cursor.fetchone()
    s = x[0] if x else 0  # Kiểm tra xem có giá trị hay không

    return render_template("limit.html", y=s)

@app.route("/today")
def today():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT TIME(date), amount FROM expenses WHERE userid = %s AND DATE(date) = DATE(NOW())', (session['id'],))
    texpense = cursor.fetchall()

    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND DATE(date) = DATE(NOW()) ORDER BY date DESC', (session['id'],))
    expense = cursor.fetchall()

    total = 0
    t_food = t_entertainment = t_business = t_rent = t_EMI = t_other = 0

    for x in expense:
        total += x[4]
        if x[6] == "food":
            t_food += x[4]
        elif x[6] == "entertainment":
            t_entertainment += x[4]
        elif x[6] == "business":
            t_business += x[4]
        elif x[6] == "rent":
            t_rent += x[4]
        elif x[6] == "EMI":
            t_EMI += x[4]
        else:
            t_other += x[4]

    return render_template("today.html", t=t_food, e=t_entertainment, b=t_business, r=t_rent, em=t_EMI, o=t_other, total=total, time=texpense)

if __name__ == '__main__':
    app.run(debug=True)
