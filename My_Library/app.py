# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_here_change_this'  # 请更换为更安全的密钥
app.config['UPLOAD_FOLDER'] = 'books'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 数据库路径
DATABASE = 'database.db'


# 初始化数据库
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                cover_url TEXT,
                file_path TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_favorites (
                user_id INTEGER,
                book_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (book_id) REFERENCES books (id),
                PRIMARY KEY (user_id, book_id)
            );
        ''')
        conn.commit()


# 检查文件扩展名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# 获取数据库连接（带行工厂）
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # 可以用列名访问
    return conn


# 首页 - 显示书籍 + 搜索
@app.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    conn = get_db()
    cursor = conn.cursor()

    if search_query:
        query = '''
            SELECT * FROM books 
            WHERE title LIKE ? OR author LIKE ?
            ORDER BY title
        '''
        cursor.execute(query, (f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute("SELECT * FROM books ORDER BY title")

    books = cursor.fetchall()
    conn.close()

    # 获取当前用户收藏的书籍ID (如果已登录)
    favorite_ids = []
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT book_id FROM user_favorites WHERE user_id = ?', (session['user_id'],))
        favorite_ids = [row['book_id'] for row in cursor.fetchall()]
        conn.close()

    return render_template('index.html', books=books, favorite_ids=favorite_ids, search_query=search_query)


# 注册

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            flash('用户名和密码不能为空')
            return redirect(url_for('register'))

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('用户名已存在')
        finally:
            conn.close()

    return render_template('register.html')


# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user['password'] == password:  # 实际应使用哈希（如 werkzeug.security）
            session['user_id'] = user['id']
            session['username'] = username
            flash('登录成功')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误')

    return render_template('login.html')


# 登出
@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录')
    return redirect(url_for('index'))


# 收藏/取消收藏
@app.route('/toggle_favorite/<int:book_id>')
def toggle_favorite(book_id):
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    # 检查是否已收藏
    cursor.execute("SELECT 1 FROM user_favorites WHERE user_id = ? AND book_id = ?", (user_id, book_id))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("DELETE FROM user_favorites WHERE user_id = ? AND book_id = ?", (user_id, book_id))
        flash('已取消收藏')
    else:
        cursor.execute("INSERT INTO user_favorites (user_id, book_id) VALUES (?, ?)", (user_id, book_id))
        flash('已添加收藏')

    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('index'))


# 我的收藏
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.* FROM books b
        JOIN user_favorites f ON b.id = f.book_id
        WHERE f.user_id = ?
        ORDER BY b.title
    ''', (user_id,))
    favorite_books = cursor.fetchall()
    conn.close()

    return render_template('profile.html', books=favorite_books)


# 管理员页面
@app.route('/admin')
def admin():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))

    if session['username'] != 'admin':
        flash('权限不足')
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY title")
    books = cursor.fetchall()
    conn.close()

    return render_template('admin.html', books=books)


# 添加书籍
@app.route('/admin/add', methods=['POST'])
def add_book():
    if session.get('username') != 'admin':
        return redirect(url_for('index'))

    title = request.form['title'].strip()
    author = request.form['author'].strip()
    cover_url = request.form['cover_url'].strip() or None  # 可为空

    if 'file' not in request.files:
        flash('未选择文件')
        return redirect(url_for('admin'))

    file = request.files['file']
    if file.filename == '':
        flash('未选择文件')
        return redirect(url_for('admin'))

    if file and allowed_file(file.filename):
        # 使用安全的文件名，避免冲突
        filename = secure_filename(f"{title}_{author}.{file.filename.rsplit('.', 1)[1].lower()}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # 保存文件
        file.save(file_path)

        # 写入数据库
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO books (title, author, cover_url, file_path)
                VALUES (?, ?, ?, ?)
            ''', (title, author, cover_url, file_path))
            conn.commit()
            flash('书籍添加成功')
        except Exception as e:
            flash(f'数据库写入失败: {str(e)}')
            if os.path.exists(file_path):
                os.remove(file_path)  # 删除已上传的文件
        finally:
            conn.close()
    else:
        flash('仅支持 .txt 文件')

    return redirect(url_for('admin'))


# 删除书籍
@app.route('/admin/delete/<int:book_id>')
def delete_book(book_id):
    if session.get('username') != 'admin':
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT file_path FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if book:
        file_path = book['file_path']
        # 删除本地文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                flash(f'文件删除失败: {str(e)}')

        # 删除数据库记录
        cursor.execute("DELETE FROM user_favorites WHERE book_id = ?", (book_id,))
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        flash('书籍删除成功')
    else:
        flash('书籍不存在')

    conn.close()
    return redirect(url_for('admin'))


# 修改书籍
@app.route('/admin/edit/<int:book_id>', methods=['POST'])
def edit_book(book_id):
    if session.get('username') != 'admin':
        return redirect(url_for('index'))

    title = request.form['title'].strip()
    author = request.form['author'].strip()
    cover_url = request.form['cover_url'].strip() or None

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE books SET title = ?, author = ?, cover_url = ?
            WHERE id = ?
        ''', (title, author, cover_url, book_id))
        conn.commit()
        flash('书籍信息已更新')
    except Exception as e:
        flash(f'更新失败: {str(e)}')
    finally:
        conn.close()

    return redirect(url_for('admin'))


# 阅读书籍
@app.route('/read/<int:book_id>')
def read_book(book_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        flash('书籍不存在')
        return redirect(url_for('index'))

    book = {
        'id': row['id'],
        'title': row['title'],
        'author': row['author'],
        'cover_url': row['cover_url'],
        'file_path': row['file_path']
    }

    # ✅ 关键修复：检查 file_path 是否为本地路径
    if book['file_path'].startswith('http://') or book['file_path'].startswith('https://'):
        content = "❌ 错误：书籍内容路径不能是网络链接。请检查是否误将封面图链接填入文件路径。"
    else:
        try:
            with open(book['file_path'], 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            content = "❌ 错误：书籍文件未找到，请检查文件是否被删除或路径错误。"
        except PermissionError:
            content = "❌ 错误：无权限读取该文件。"
        except Exception as e:
            content = f"❌ 读取失败：{str(e)}"

    return render_template('read.html', book=book, content=content)


# 初始化数据库并运行
if __name__ == '__main__':
    init_db()

    # 创建默认管理员账号
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'admin123')")
            conn.commit()
            print("✅ 默认管理员账号 'admin' / 'admin123' 已创建")
        except sqlite3.IntegrityError:
            print("ℹ️  管理员账号已存在，跳过创建")

    print("🚀 服务器启动中... 访问 http://127.0.0.1:5000")
    app.run(debug=True)