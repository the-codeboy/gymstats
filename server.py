from datetime import date
from datetime import datetime, date
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import pandas as pd
import os
from scipy.interpolate import UnivariateSpline

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

def fit_polynomial(data):
    # Fit a polynomial to the minute averages
    x = np.arange(len(data))
    coefficients = np.polyfit(x, data, 17)
    poly_function = np.poly1d(coefficients)
    approximated_values = poly_function(x).clip(0, 200)  # Clip values to be between 0 and 200
    return approximated_values

def fit_spline(data):
    # Fit a spline to the minute averages
    x = np.arange(len(data))
    spline = UnivariateSpline(x, data, k=5)  # k is the degree of the spline
    approximated_values = spline(x).clip(0, 200)  # Clip values to be between 0 and 200
    approximated_values[data == 0] = 0 # Set values to 0 where the original data was 0
    return approximated_values


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
        
        # get amount of days between start and end date
        days = (enddate - startdate).days + 1
        
        df_resampled = df_resampled.resample('min' if days < 3 else '10min' if days < 5 else '30min').mean().ffill()  # Resample to minute averages and forward fill missing values
        
        approximate_poly = fit_polynomial(df_resampled['people'])
        approximate_spline = fit_spline(df_resampled['people'])

        return {'labels': df_resampled.index.strftime('%Y-%m-%d %H:%M:%S').tolist(), 'values': df_resampled['people'].tolist(), 'approximated_values': approximate_poly.tolist(), 'approximated_spline': approximate_spline.tolist()}

if __name__ == '__main__':
    #app.run(debug=True)
    from waitress import serve# uncomment in production
    serve(app, host="0.0.0.0", port=8080)