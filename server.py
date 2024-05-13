from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'people_at_the_gym.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
db = SQLAlchemy(app)


class Gym(db.Model):
    timestamp = db.Column(db.DateTime, primary_key=True)
    people = db.Column(db.Integer)
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/data')
    def get_data():
        data = Gym.query.all()
        labels = [row.timestamp.strftime('%Y-%m-%d %H:%M') for row in data]
        values = [row.people for row in data]
        return {'labels': labels, 'values': values}

if __name__ == '__main__':
    app.run()