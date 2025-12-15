from flask import Flask, request, redirect, url_for, render_template, session
import psycopg2

app = Flask(__name__)
app.secret_key = "supersecret"


# ---------------------------------------
# DB CONNECTION
# ---------------------------------------
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="hungerfree",
        user="postgres",
        password="root@123",
        port="3306"
    )


# ---------------------------------------
# REGISTER
# ---------------------------------------
@app.route('/submit_register', methods=['POST'])
def submit_register():
    name = request.form.get('Name')
    email = request.form.get('Email')
    password = request.form.get('Password')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id",
            (name, email, password)
        )
        new_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        session['user_id'] = new_id
        session['username'] = name

        return redirect(url_for('homepage'))

    except Exception as e:
        return f"<h1>Error</h1><p>{e}</p>"


# ---------------------------------------
# HOMEPAGE
# ---------------------------------------
@app.route('/homepage')
def homepage():
    if 'username' not in session:
        return redirect('/')
    return render_template('homepage.html', name=session['username'])


# ---------------------------------------
# LOGIN
# ---------------------------------------
@app.route('/submit_login', methods=['POST'])
def submit_login():
    email = request.form.get('Email')
    password = request.form.get('Password')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, name FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('homepage'))
        else:
            return "<h1>Invalid Email or Password</h1>"

    except Exception as e:
        return f"<h1>Error</h1><p>{e}</p>"


# ---------------------------------------
# DONATE FOOD
# ---------------------------------------
@app.route('/donate_food', methods=['GET', 'POST'])
def donate_food():
    if 'username' not in session:
        return redirect('/')

    message = None

    if request.method == 'POST':
        donor_name = request.form.get('donor_name')
        donor_phone = request.form.get('donor_phone')
        address = request.form.get('address')
        food_type = request.form.get('FoodType')
        quantity = request.form.get('quantity')
        notes = request.form.get('notes')
        user_name = session.get('username')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO donations 
                (donor_name, donor_phone, address, food_type, quantity, notes, user_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (donor_name, donor_phone, address, food_type, quantity, notes, user_name))

            conn.commit()
            cur.close()
            conn.close()

            message = "Donation reported successfully!"

        except Exception as e:
            return f"<h1>Error Saving Donation</h1><p>{e}</p>"

    return render_template('donate.html', message=message)


# ---------------------------------------
# MY DONATIONS
# ---------------------------------------
@app.route('/my_donations')
def my_donations():
    if 'username' not in session:
        return redirect('/')

    user = session['username']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT donor_name, donor_phone, address, food_type, quantity, notes
        FROM donations
        WHERE user_name = %s
        ORDER BY id DESC
    """, (user,))

    donations = cur.fetchall()
    conn.close()

    return render_template('my_donations.html', donations=donations)


# ---------------------------------------
# DONATION STATUS PAGE
# ---------------------------------------
@app.route('/donations_status')
def donations_status():
    if 'username' not in session:
        return redirect('/')
    return render_template('donation_status.html')


# ---------------------------------------
# FIND NGOS
# ---------------------------------------
@app.route('/find_ngos')
def find_ngos():
    if 'username' not in session:
        return redirect('/')
    return render_template('find_ngos.html')


# ---------------------------------------
# PROFILE PAGE
# ---------------------------------------
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, email, password, COALESCE(about,'')
        FROM users 
        WHERE id=%s
    """, (session['user_id'],))

    data = cur.fetchone()
    conn.close()

    return render_template(
        'profile.html',
        name=data[0],
        email=data[1],
        password=data[2],
        about=data[3]
    )


# ---------------------------------------
# UPDATE PROFILE
# ---------------------------------------
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect('/')

    name = request.form.get("name")
    email = request.form.get("email")
    about = request.form.get("about")
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")

    conn = get_db_connection()
    cur = conn.cursor()

    # Update basic details
    cur.execute("""
        UPDATE users 
        SET name=%s, email=%s, about=%s 
        WHERE id=%s
    """, (name, email, about, session["user_id"]))

    # Update password ONLY if user wants to change
    if current_password and new_password:
        cur.execute(
            "SELECT password FROM users WHERE id=%s",
            (session["user_id"],)
        )
        stored_password = cur.fetchone()[0]

        if stored_password == current_password:
            cur.execute(
                "UPDATE users SET password=%s WHERE id=%s",
                (new_password, session["user_id"])
            )
        else:
            conn.close()
            return "<h3>Current password is incorrect</h3>"

    conn.commit()
    cur.close()
    conn.close()

    session['username'] = name
    return redirect("/profile")


# ---------------------------------------
# CONTACT PAGE
# ---------------------------------------
@app.route('/contact')
def contact():
    if 'username' not in session:
        return redirect('/')
    return render_template('contact.html')


# ---------------------------------------
# LOGOUT
# ---------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('login.html')


# ---------------------------------------
# RUN
# ---------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
