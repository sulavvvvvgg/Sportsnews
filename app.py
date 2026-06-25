from flask import Flask, render_template, request, redirect, url_for
from models import db, Article

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def home():
    articles = Article.query.all()
    return render_template('index.html', articles=articles)

@app.route('/create', methods=['GET', 'POST'])
def create_article():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        author = request.form['author']

        new_article = Article(title=title, content=content, category=category, author=author)
        db.session.add(new_article)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('create_article.html')

@app.route('/edit/<int:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    article = Article.query.get(article_id)

    if request.method == 'POST':
        article.title = request.form['title']
        article.content = request.form['content']
        article.category = request.form['category']
        article.author = request.form['author']

        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit_article.html', article=article)

@app.route('/delete/<int:article_id>')
def delete_article(article_id):
    article = Article.query.get(article_id)
    db.session.delete(article)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
