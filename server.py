from datetime import date
from datetime import datetime, date
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import pandas as pd
import os

from requests import get

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'people_at_the_gym.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
db = SQLAlchemy(app)


def get_first_date():
    return Gym.query.order_by(Gym.timestamp).first().timestamp.date()
    
def get_last_date():
    return Gym.query.order_by(Gym.timestamp.desc()).first().timestamp.date()

class Gym(db.Model):
    timestamp = db.Column(db.DateTime, primary_key=True, index=True)
    people = db.Column(db.Integer)
    @app.route('/')
    def home():
        return render_template('index.html', first_date=get_first_date(), last_date=get_last_date())

    @app.route('/daily')
    def get_data():
        startdate_str = request.args.get('startdate')
        startdate = datetime.strptime(startdate_str, '%Y-%m-%d').date() if startdate_str else date.today()
        enddate_str = request.args.get('enddate')
        enddate = datetime.strptime(enddate_str, '%Y-%m-%d').date() if enddate_str else date.today()
        data = Gym.query.filter(db.func.date(Gym.timestamp).between(startdate, enddate)).order_by(Gym.timestamp).all()
        df = pd.DataFrame([(row.timestamp, row.people) for row in data], columns=['timestamp', 'people'])
        df.set_index('timestamp', inplace=True)
        
        # Resample to 1-second intervals and forward fill missing values
        df_resampled = df.resample('s').ffill()
        
        df_resampled = df_resampled.resample('min').mean().ffill()  # Resample to minute averages and forward fill missing values

        # Fit a polynomial to the minute averages
        x = np.arange(len(df_resampled))
        coefficients = np.polyfit(x, df_resampled['people'], 17)
        poly_function = np.poly1d(coefficients)
        approximated_values = poly_function(x).clip(0, 200)  # Clip values to be between 0 and 200

        return {'labels': df_resampled.index.strftime('%Y-%m-%d %H:%M:%S').tolist(), 'values': df_resampled['people'].tolist(), 'approximated_values': approximated_values.tolist()}

if __name__ == '__main__':
    #app.run(debug=True)
    from waitress import serve# uncomment in production
    serve(app, host="0.0.0.0", port=8080)