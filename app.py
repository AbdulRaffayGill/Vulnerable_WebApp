from flask import *
import sqlite3, os

a = Flask(__name__)
a.secret_key = "dev123"

up = "uploads"
os.makedirs(up, exist_ok=True)


def db():
    c = sqlite3.connect("lab.db")
    x = c.cursor()

    x.execute("create table if not exists users(id integer primary key autoincrement,username text,password text,role text,pic text)")
    x.execute("create table if not exists docs(id integer primary key autoincrement,title text,body text)")

    if not x.execute("select * from users").fetchall():
        x.execute("insert into users(username,password,role,pic) values('admin','admin123','superadmin','1.png')")
        x.execute("insert into users(username,password,role,pic) values('carlos','qwerty','analyst','2.png')")
        x.execute("insert into users(username,password,role,pic) values('wiener','peter123','intern','3.png')")

    if not x.execute("select * from docs").fetchall():
        x.execute("insert into docs(title,body) values('Payroll Report','salary records and banking')")
        x.execute("insert into docs(title,body) values('VPN Secrets','private vpn passwords')")
        x.execute("insert into docs(title,body) values('Incident Report','company breach details')")

    c.commit()
    c.close()


db()


@a.route('/')
def i():
    return render_template("index.html")


@a.route('/login', methods=["GET", "POST"])
def l():
    error = False
    if request.method == "POST":
        u = request.form['u']
        p = request.form['p']

        c = sqlite3.connect("lab.db")
        x = c.cursor()

        q = f"select * from users where username='{u}' and password='{p}'"
        r = x.execute(q).fetchone()

        c.close()

        if r:
            session['u'] = r[1]
            return redirect("/academy")
        else:
            error = True

    return render_template("login.html", error=error)


@a.route('/logout')
def logout():
    session.clear()
    return redirect("/login")


@a.route('/academy')
def d():
    if 'u' not in session:
        return redirect("/login")
    return render_template("dashboard.html")


@a.route('/profile')
def p():
    if 'u' not in session:
        return redirect("/login")
    i = request.args.get("id")

    c = sqlite3.connect("lab.db")
    x = c.cursor()

    u = x.execute(f"select * from users where id={i}").fetchone()

    c.close()

    return render_template("profile.html", u=u)


@a.route('/search')
def s():
    if 'u' not in session:
        return redirect("/login")
    q = request.args.get("q", "")

    c = sqlite3.connect("lab.db")
    x = c.cursor()

    sql = f"select id,title,body from docs where title like '%{q}%'"

    try:
        r = x.execute(sql).fetchall()
    except Exception as e:
        r = [("x", str(e), "")]

    c.close()

    return render_template("search.html", r=r, q=q)


@a.route('/traversal')
def traversal():
    if 'u' not in session:
        return redirect("/login")
    f = request.args.get("f", "")
    content = None
    if f:
        try:
            path = os.path.join("static", f)
            with open(path, "r", errors="replace") as fh:
                content = fh.read()
        except Exception as e:
            content = f"Error: {e}"
    return render_template("traversal.html", f=f, content=content)


@a.route('/upload', methods=["GET", "POST"])
def u():
    if 'u' not in session:
        return redirect("/login")
    f = None

    if request.method == "POST":
        z = request.files['f']
        z.save(os.path.join(up, z.filename))
        f = z.filename

    return render_template("upload.html", f=f)


@a.route('/uploads/<x>')
def uu(x):
    return send_file(os.path.join(up, x))


@a.route('/execute', methods=["GET", "POST"])
def execute():
    if 'u' not in session:
        return redirect("/login")
    files = os.listdir(up)
    output = None
    fname = None
    err = None
    if request.method == "POST":
        fname = request.form.get("fname", "")
        path = os.path.join(up, fname)
        try:
            import subprocess
            result = subprocess.run(
                ["python3", path],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout
            err = result.stderr
        except subprocess.TimeoutExpired:
            err = "Execution timed out after 5 seconds."
        except Exception as e:
            err = str(e)
    return render_template("execute.html", files=files, output=output, fname=fname, err=err)


@a.route('/img')
def img():
    f = request.args.get("f")
    return send_file(os.path.join("static", f))



if __name__ == '__main__':
    a.run(host='0.0.0.0', debug=True)
