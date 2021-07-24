import markdown2
import uuid
import os
import redis
import json
from flask import Flask, render_template, request
from flask_mdeditor import MDEditor
from datetime import datetime


def takeDate(elem):
    return elem['creation_date']


# Functions section
# Function for creating an ID
def article_id():
    id = uuid.uuid4()
    return str(id)[:6]


# Convert dict to string and the other way
# For dict to string, way == in
# For string to dict, way == out
def dict_to_string(dictio, way):
    if way == "in":
        return json.dumps(dictio)
    elif way == "out":
        return json.loads(dictio)


# Function to convert Markdown to HTML
def convert_to_html(markdown):
    html = markdown2.markdown(markdown)
    return html


# Function to write HTML into a file
def create_html_version(article_id, html):
    open(f'templates/articles/{article_id}.html', 'x')
    file_html = open(f'templates/articles/{article_id}.html', 'w')
    file_html.write(html)
    file_html.close()


# Function to delete HTML file
def delete_html_file(article_id):
    if os.path.exists(f'templates/articles/{article_id}.html'):
        os.remove(f'templates/articles/{article_id}.html')
    else:
        print('The file does not exist')


# Function to generate article path
def create_art_include_path(article_id):
    art_include_path = f'articles/{article_id}.html'
    return art_include_path


# Insert the article into Redis
def insert_article(article_id, title, author, emoji, private):
    r = redis.Redis()
    article = {
            "id": article_id,
            "author": author,
            "title": title,
            "emoji": emoji,
            "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "private": private,
    }
    r.set(article_id, dict_to_string(article, "in"))
    return "OK"


# Get all articles
# With details or only IDs
def get_all_articles(details):
    r = redis.Redis()
    if details:
        articles = []
        for key in r.keys():
            articles.append(dict_to_string(r.get(key), "out"))
        articles.sort(key=takeDate, reverse=True)
        return articles
    elif not details:
        articles = []
        for key in r.keys():
            articles.append(key)
        return articles


# Get one article by his ID
def get_one_article(article_id):
    r = redis.Redis()
    article = dict_to_string(r.get(article_id), "out")
    return article


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)


# Home
@app.route('/')
def index():
    articles = get_all_articles(True)
    return render_template('index.html', articles=articles)


# Backend dashboard
@app.route('/backend', methods=['POST', 'GET'])
def backend():
    articles = get_all_articles(True)
    return render_template('backend/index.html', articles=articles)


# Backend for new article
@app.route('/backend/new', methods=['POST', 'GET'])
def saving():
    if request.method == 'POST':
        markdown = request.form.get('mdeditor')
        title = request.form.get('title')
        emoji = request.form.get('emoji')
        if not emoji:
            emoji = "em-desktop_computer"
        private = request.form.get('priv')
        author = request.form.get('author')
        id = article_id()
        html_data = convert_to_html(markdown)
        create_html_version(id, html_data)
        insert_article(
            id,
            title,
            author,
            emoji,
            private
        )
        return f"Article créé : <a href='/article/{id}'>Lien</a>"
    else:
        return render_template('backend/new_article.html')


# Delete article
@app.route('/backend/delete/<article_id>')
def delete_article(article_id):
    r = redis.Redis()
    r.delete(article_id)
    delete_html_file(article_id)
    return "Article supprimé<br> <a href='/backend'>Retour au backend</a>"


@app.route('/article/<article_id>')
def article(article_id):
    article = get_one_article(article_id)
    art_title = article['title']
    art_include_path = create_art_include_path(article_id)
    art_author = article['author']
    art_creation_date = article['creation_date']
    return render_template('article.html', art_include_path=art_include_path,
                           art_title=art_title, art_author=art_author, art_creation_date=art_creation_date)


app.config['MDEDITOR_FILE_UPLOADER'] = os.path.join(basedir, 'uploads')
app.config['MDEDITOR_LANGUAGE'] = 'en'
mdeditor = MDEditor(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0')