import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import datetime
import pdb
import pickle



file_name = open('iv_chart', 'rb')
df = pickle.load(file_name) 






df['datetime'] = pd.to_datetime(df['datetime'])

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='candlestick-chart'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # Update every second
        n_intervals=0
    )
])

@app.callback(
    Output('candlestick-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_chart(n):
    global df

    file_name = open('iv_chart', 'rb')
    df = pickle.load(file_name) 

    df['datetime'] = pd.to_datetime(df['datetime'])


    fig = go.Figure(data=[go.Candlestick(
        x=df['datetime'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    )])

    fig.update_layout(title='Candlestick Chart', xaxis_title='Datetime', yaxis_title='Price',autosize=True,height=1080, width=1920)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)


