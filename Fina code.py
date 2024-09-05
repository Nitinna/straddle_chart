import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import pickle

# Load data
def load_data():
    with open('iv_chart', 'rb') as file:
        df = pickle.load(file)
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

df = load_data()

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
    df = load_data()

    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=df['datetime'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    )])

    # Add latest price annotation
    latest = df.iloc[-1]
    fig.add_trace(go.Scatter(
        x=[latest['datetime']],
        y=[latest['close']],
        mode='markers+text',
        marker=dict(color='black', size=1),
        text=[f'{latest["close"]:.2f}'],
        textposition='top right',
        name='PRICE'
    ))

    fig.update_layout(
        title='STRADDLE_CHART',
        xaxis_title='Datetime',
        yaxis_title='Price',
        autosize=True,
        height=1080,
        width=1920
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
