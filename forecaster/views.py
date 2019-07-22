import requests
import json
import pandas as pd
import numpy as np
import datetime
from django.shortcuts import render
from django.core.cache import cache
from .forms import UserForm
from statsmodels.tsa.arima_model import ARIMA as ai


# Create your views here.


def home(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        validCheck = form.is_valid()
        if form.cleaned_data['base_Currency'] == form.cleaned_data['target_Currency']:
            validCheck = False

        if validCheck:

            post = dict()
            post['base_Currency'] = form.cleaned_data['base_Currency']
            post['target_Currency'] = form.cleaned_data['target_Currency']
            post['amount'] = form.cleaned_data['amount']
            post['startDate'] = form.cleaned_data['startDate']
            if form.cleaned_data['max_waiting_time'] > 6:
                post['max_waiting_time'] = 6
            elif form.cleaned_data['max_waiting_time'] < 1:
                post['max_waiting_time'] = 1
            else:
                post['max_waiting_time'] = form.cleaned_data['max_waiting_time']

                
            result_json = predictor(post)
            print(result_json)

            return render(request, 'currency/result.html', {'result': json.loads(result_json)})
    else:
        form = UserForm()

    return render(request, 'currency/home.html', {'form': form})


def about(request):
    return render(request, 'currency/about.html')


def inr_convert(value):
    key = list(value.keys())
    return value[key[0]]


def predictor(post):

    # dec
    t2month = datetime.timedelta(days=60)
    t1day = datetime.timedelta(days=1)
    token = hit_api()

    # getting the data from cache
    data_cache = cache.get('data')

    # setting up variables
    sym = token[int(post['target_Currency'])]
    base = token[int(post['base_Currency'])]
    max_waiting_time = post['max_waiting_time']
    amount = post['amount']

    # checking if the cache is empty or not
    if data_cache is None:
        start = post['startDate'] - t2month
        end = post['startDate'] - t1day

        df = magic(start, end, sym, base)
        last_value = df.iloc[-1, :-1].values[1]

        cache.set('data', df, 60)
        # print(train_model(df['rates'].values, max_waiting_time, last_value))
        # return train_model(df['rates'].values, max_waiting_time, last_value)


    else:
        data_cache = cache.get('data')
        start = data_cache.iloc[-1, :-1].values[0]
        end = post['startDate'] - t1day

        if datetime.datetime.strptime(str(start), "%Y-%m-%d").date() != datetime.date.today():
            df = magic(start, end, sym, base)
            print('T1')
            print(df)
            print('T2')
            last_value = df.iloc[-1, :-1].values[1]
            diff = df.shape[0]

            data_cache = pd.DataFrame(data_cache)
            print('S1')
            print(data_cache)
            print('S2')
            data_cache = data_cache.iloc[diff:]
            frames = [data_cache, df]
            df = pd.concat(frames)
            print('SV1')
            print(data_cache)
            print('SV2')
            cache.set('data', df, 60)
            # print(train_model(df['rates'].values, max_waiting_time, last_value))
            # return train_model(df['rates'].values, max_waiting_time, last_value)

        else:
            data_cache = cache.get('data')
            df = pd.DataFrame(data_cache)
            last_value = df.iloc[-1, :-1].values[1]
            # print(train_model(df['rates'].values, max_waiting_time, last_value))
            # return train_model(df['rates'].values, max_waiting_time, last_value)
        
    return train_model(df['rates'].values, max_waiting_time, last_value, amount)



# Function that calls ARIMA model to fit and forecast the data
def start_arima_forecasting(actual, p, d, q):
    model = ai(actual, order=(p, d, q))
    model_fit = model.fit(disp=0)
    return model_fit


def hit_api():
    start = datetime.date.today()
    tdelta = datetime.timedelta(days=1)
    end = start+tdelta

    if start.weekday() == 5 or start.weekday() ==6:
        tdel = datetime.timedelta(days=2)
        start -= tdel
        end = start + tdelta
    base = 'USD'

    data = requests.get(f"https://api.exchangeratesapi.io/history?start_at={start}&"
                        f"end_at={end}&base={base}")

    data = json.loads(data.text)
    curr = list(data['rates'][str(start)].keys())
    curr.append(base)
    return dict(enumerate(curr))


def findFriday():

    startdate = datetime.date.today()
    days = [startdate+datetime.timedelta(days=i) for i in range(7)]

    for val in days:
        if val.weekday() == 4:
            return days.index(val), days


def updateResult(index, result, days, time, last_value, amount):

    print(result)
    if index == len(result)+1:
        result.insert(0, last_value)
        result.insert(1, last_value)

    elif index == len(result):
        result.insert(0, result[index-1])
        result.insert(index+1, result[-1])

    else:
        result.insert(index+1, result[index])
        result.insert(index+2, result[index])

    resultdict = list()
    for i in range(time):
        print(str(days[i]))
        print(result[i])
        temp = dict()
        temp['date'] = str(days[i])
        temp['predicted_value'] = str(result[i])
        temp['amount'] = amount
        temp['final_amount'] = result[i] * amount
        resultdict.append(temp)


    return resultdict


def magic(start, end, sym, base):
    data = requests.get(f"https://api.exchangeratesapi.io/history?start_at={start}&"
                        f"end_at={end}&symbols={sym}&base={base}")
    data = json.loads(data.text)

    df = pd.DataFrame(data).reset_index()
    print('------------MAGIC------------------')
    print(df)
    print('------------MAGIC------------------')
    df['rates'] = df['rates'].apply(inr_convert)

    return df

def train_model(actualdata, max_waiting_time, last_value, amount):
    model_fit = start_arima_forecasting(actualdata, 3, 1, 0)
    predicted_result = model_fit.forecast(5)[0]
    predicted_result = np.array(predicted_result).tolist()

    friday, days = findFriday()

    resultDict = updateResult(friday, predicted_result, days, max_waiting_time, last_value, amount)
    result_json = json.dumps(resultDict)
    
    print(result_json)
    return result_json