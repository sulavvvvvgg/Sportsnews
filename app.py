from flask import Flask, render_template, request, redirect, url_for
from models import db, Article
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Article, User, Comment, Category
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Article, User, Comment
import requests
from dotenv import load_dotenv
import os

load_dotenv()
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sportsuser:sulavgg2005@localhost/sportsnews'
app.config['SECRET_KEY'] = 'change-this-later'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            error = "Username and password are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif User.query.filter_by(username=username).first():
            error = "Username already taken. Please choose another."
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            error = "Please enter both username and password."
        else:
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                error = "Invalid username or password."

    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
def home():
    category = request.args.get('category')
    if category:
        articles = Article.query.filter_by(category=category).all()
    else:
        articles = Article.query.all()
    all_categories = Category.query.all()
    return render_template('index.html', articles=articles, selected_category=category, categories=all_categories)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_article():
    if not current_user.is_admin:
        return "Access denied. Admins only."

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        author = request.form['author']

        new_article = Article(title=title, content=content, category=category.lower(), author=author)
        db.session.add(new_article)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('create_article.html')

@app.route('/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get(article_id)
    if not current_user.is_admin:
        return "Access denied. Admins only."

    if request.method == 'POST':
        article.title = request.form['title']
        article.content = request.form['content']
        article.category = request.form['category']
        article.author = request.form['author']

        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit_article.html', article=article)

@app.route('/delete/<int:article_id>')
@login_required
def delete_article(article_id):
    article = Article.query.get(article_id)
    db.session.delete(article)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/fetch-news/<sport>')
@login_required
def fetch_news(sport):
    if not current_user.is_admin:
        return "Access denied. Admins only."

    url = "https://newsapi.org/v2/everything"
    params = {
        'q': sport,
        'sortBy': 'publishedAt',
        'language': 'en',
        'pageSize': 5,
        'apiKey': NEWS_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data['status'] == 'ok':
        for item in data['articles']:
            title = item['title']
            content = item['description'] or "No description available."
            author = item['source']['name']
            image_url = item.get('urlToImage', None)

            existing = Article.query.filter_by(title=title).first()
            if not existing:
                new_article = Article(title=title, content=content, category=sport, author=author, image_url=image_url)
                db.session.add(new_article)

        db.session.commit()
        return redirect(url_for('home'))

    return "Failed to fetch news"

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    article = Article.query.get(article_id)
    comments = Comment.query.filter_by(article_id=article_id).all()
    return render_template('article_detail.html', article=article, comments=comments)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    error = None
    success = None
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']

        if not new_username:
            error = "Username cannot be empty."
        elif new_username != current_user.username and User.query.filter_by(username=new_username).first():
            error = "Username already taken."
        else:
            current_user.username = new_username
            if new_password:
                current_user.password = generate_password_hash(new_password)
            db.session.commit()
            success = "Profile updated successfully."

    return render_template('profile.html', error=error, success=success)


@app.route('/delete-account')
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    logout_user()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/article/<int:article_id>/comment', methods=['POST'])
@login_required
def add_comment(article_id):
    content = request.form['content']
    if not content:
        return redirect(url_for('article_detail', article_id=article_id))

    new_comment = Comment(
        content=content,
        user_id=current_user.id,
        article_id=article_id,
        username=current_user.username
    )
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('article_detail', article_id=article_id))


@app.route('/comment/edit/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment.user_id != current_user.id and not current_user.is_admin:
        return "Access denied."

    if request.method == 'POST':
        comment.content = request.form['content']
        db.session.commit()
        return redirect(url_for('article_detail', article_id=comment.article_id))

    return render_template('edit_comment.html', comment=comment)


@app.route('/comment/delete/<int:comment_id>')
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment.user_id != current_user.id and not current_user.is_admin:
        return "Access denied."

    article_id = comment.article_id
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('article_detail', article_id=article_id))


@app.route('/categories')
def categories():
    all_categories = Category.query.all()
    return render_template('categories.html', categories=all_categories)


@app.route('/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if not current_user.is_admin:
        return "Access denied. Admins only."

    error = None
    if request.method == 'POST':
        name = request.form['name'].lower()
        if not name:
            error = "Category name cannot be empty."
        elif Category.query.filter_by(name=name).first():
            error = "Category already exists."
        else:
            new_category = Category(name=name)
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('categories'))

    return render_template('add_category.html', error=error)


@app.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    if not current_user.is_admin:
        return "Access denied. Admins only."

    category = Category.query.get(category_id)
    if request.method == 'POST':
        category.name = request.form['name'].lower()
        db.session.commit()
        return redirect(url_for('categories'))

    return render_template('edit_category.html', category=category)


@app.route('/category/delete/<int:category_id>')
@login_required
def delete_category(category_id):
    if not current_user.is_admin:
        return "Access denied. Admins only."

    category = Category.query.get(category_id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('categories'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

