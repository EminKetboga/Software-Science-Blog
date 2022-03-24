from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f( *args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("login"))

    return decorated_function

def login_gerek(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f( *args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("login"))

    return decorated_function


class RegisterForm(Form):
    name = StringField("İsim Soyİsim:",validators=[validators.Length(min = 3,max = 20)])
    username = StringField("Kullanıcı Adı:",validators=[validators.Length(min = 5,max = 25)])
    email = StringField("Email Adresi:",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Giriniz...")])
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message = "Lütfen Parola Bölümünü Doldurunuz..."),
        validators.EqualTo(fieldname = "confirm",message = "Parolanız Uyuşmuyor...")

    ])
    confirm = PasswordField("Parola Tekrar:")
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")



app = Flask(__name__)
app.secret_key = "Ybblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route('/') 
def index():

    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/articles/<string:id>")
def detail(id):
    return "Articles:" + id


#Register İşlemi
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert into kayit(name,email,username,password) Values (%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()

        flash("Başarı İle Kaydoldunuz...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)
#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()

        return render_template("article.html",article = article)

    else:
        return render_template("article.html")
#Profil İşlemi

@app.route("/profile/<string:id>",methods=["GET","POST"])
@login_required
def profile(id):
    
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        sorgu="Select *From users where id=%s and username=%s"
        result=cursor.execute(sorgu,(id,session["username"]))
 
        if result==0:
           flash("Böyle bir kullanıcı yok veya yetkiniz yok..","danger")
           return redirect(url_for("index"))
 
        else:
            user=cursor.fetchone()
            form = RegisterForm(request.form)
            form.username.data = user["username"]
            form.email.data = user["email"]
            form.password.data = sha256_crypt.encrypt(user["password"])
            #form.password.data = sha256_crypt.decrypt(user["password"])
            return render_template("profile.html",form=form)
 
 
    else:
        #post request icin durum kontrolu
        form=RegisterForm(request.form)
        newusername=form.username.data
        newemail=form.email.data
        newpassword=sha256_crypt.encrypt(form.password.data)
 
 
        sorgu2=" Update users Set username=%s,email=%s,password=%s where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newusername,newemail,newpassword,id))
        mysql.connection.commit()
 
        flash("Profil Basarı ile Güncellendi","success")
 
        if newusername == session["username"]:
            return redirect(url_for("profile"))
        else:
            logout()
            return redirect(url_for("login"))
        
#Login İşlemi        
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From kayit where username = %s"
        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarı ile Giriş Yaptınız...","success")
                session["logged_in"] = True
                session["username"] = username


                return redirect(url_for("index"))

            else:
                flash("Parolanızı yanlış Girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle Bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form = form)

# Logout İşlemi
@app.route("/logout")
def logout():
    session.clear()
    
    return redirect(url_for("index")),flash("Başarı İle Çıkış Yapıldı...","success")
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)


    if result > 0:
        articles = cursor.fetchall()

        return render_template("articles.html",articles = articles)

    else:
        return render_template("articles.html")

#DashBoard İşlemi
@app.route("/dashboard")
@login_required
def dashboard():

    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")
# Mkaale Silme
@app.route("/delete/<string:id>")
@login_gerek
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle Bir Makale Yok Veya Yetkiniz Yok!","danger")
        return redirect(url_for("index"))


#Makale Güncelleme
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":

        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where id = %s and author = %s"

        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle Bir Makale Yok Veya Buna Yetkiniz Yok!","danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
    else:
        # Post Request

        form = ArticleForm(request.form)

        newTitle = form.title.data

        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Makaleniz Başarı ile Güncellendi!","success")
        return redirect(url_for("dashboard"))


# Makale Ekleme
@app.route("/addarticles",methods = ["GET","POST"]) 
@login_gerek
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Makale Başarı İle Eklendi","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticles.html",form = form)


class ArticleForm(Form):
    title = StringField("Makale Başlığı:",validators=[validators.Length(min=5,max = 100)])
    content = TextAreaField("Makale İçeriği:",validators=[validators.Length(min=5)])

#Arama Url
@app.route("/search",methods = ["POST","GET"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where title like '%" + keyword + "%'"

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aradığınız Kelimeye Uygun Makale Bulunamadı...","waring")
            return redirect(url_for("articles"))

        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)

if __name__ == "__main__":
    app.run(debug=True)  

