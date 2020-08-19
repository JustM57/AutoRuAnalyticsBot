import pandas as pd
import pickle


def engine_volume(engine):
    volume = [x for x in engine.split('/') if ('л' in x) & ('с' not in x)]
    try:
        volume = float(volume[0].split()[0])
        return volume
    except ValueError:
        return None


def engine_power(engine):
    power = [x for x in engine.split('/') if 'л.с.' in x]
    power = int(power[0].split('л')[0])
    return power


def engine_type(engine):
    engine_type = engine.split('/')[-1]
    return engine_type


def electro_power(engine):
    power = [x for x in engine.split('/') if 'кВт' in x]
    try:
        power = int(power[0].split('к')[0].strip())
        return power
    except IndexError:
        return None


def get_prediction(df):
    X = df[['transmission', 'body', 'drive', 'colour', 'year', 'dist', 'verified_dealer',
       'engine_volume', 'horse_power', 'engine_oil', 'electro_power', 'mark', 'model']]
    with open("ml/model.txt", "rb") as fp:   # Unpickling
        ml_model = pickle.load(fp)
    with open("ml/model_low.txt", "rb") as fp:   # Unpickling
        ml_model_low = pickle.load(fp)
    with open("ml/model_up.txt", "rb") as fp:   # Unpickling
        ml_model_up = pickle.load(fp)
    prediction = pd.Series(ml_model.predict(X)).rename('prediction')
    prediction.index = X.index
    prediction_low = pd.Series(ml_model_low.predict(X)).rename('prediction_low')
    prediction_low.index = X.index
    prediction_up = pd.Series(ml_model_up.predict(X)).rename('prediction_up')
    prediction_up.index = X.index
    df = pd.concat([df, prediction, prediction_low, prediction_up], axis=1)
    df['sale'] = df.price - df.prediction
    df['sale%'] = 100 * (df.price - df.prediction)/df.prediction
    df['sale_low'] = df.price - df.prediction
    df['sale_low%'] = 100 * (df.price - df.prediction)/df.prediction
    df = df.sort_values(by=['mark', 'model', 'sale'])
    return df


def get_new_stats(mark, model):
    daily_df = pd.read_csv('daily_models.csv')
    daily_df = daily_df[(daily_df.mark==mark) & (daily_df.model==model)]
    cars = []
    for idx, row in daily_df.iterrows():
        car = {
            'car': ' '.join([row['colour'], row['body'], row['model_name']]),
            'engine': ' '.join([str(row['drive'])+' привод,', 'мотор '+str(row['engine_volume'])+'л',
                                row['engine_oil'], 'мощностью '+str(row['horse_power'])+'л.c.']),
            'transmission': row['transmission'],
            'age': ' '.join(['год '+str(row['year']),'с пробегом '+str(row['dist'])]),
            'price': ' '.join(['цена '+str(row['price']), 'в сравнении с другими '+str(round(row['sale'])), 
                                        'или '+str(round(row['sale%']))+'%', 'в диапазоне '+
                                        str(round(row['prediction_low']))+' - '+str(round(row['prediction_up']))]),
            'link': 'ссылка на авто ру: {}'.format(row['link'][16:]),
            'img': str(row['img'])
        }
        cars.append(car)
    return cars