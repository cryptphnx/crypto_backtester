# dashboard.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import pandas as pd
import json
from backtesting import run_backtest
from ga_optimization import run_optimization
from data import get_historical_data

# 1. Create the Dash app and expose the underlying Flask server.
app = dash.Dash(__name__)
server = app.server

# 2. Define default strategy parameters used for backtesting.
DEFAULT_PARAMS = {
    "longTermFastLen": 50,
    "longTermSlowLen": 200,
    "shortTermFastLen": 10,
    "shortTermSlowLen": 20,
    "fixedStopLossPct": 0.01,
    "fixedTakeProfitPct": 0.02,
    "fixedTrailingPct": 0.01,
    "useAdxFilter": False,
    "adxPeriod": 14,
    "adxThreshold": 20.0,
    "useVolumeFilter": False,
    "volumeMALen": 20,
    "useRSIFilter": False,
    "rsiPeriod": 14,
    "rsiLongThreshold": 50.0,
    "rsiShortThreshold": 50.0,
    "useAtrFilter": False,
    "atrFilterThreshold": 0.01,
    "enableHigherTFFilter": False,
    "enableSessionFilter": False,
}

# 3. Define the layout of the dashboard.
app.layout = html.Div(
    style={'backgroundColor': 'black', 'color': 'yellow', 'padding': '20px'},
    children=[
        html.H1("Crypto Backtesting Dashboard"),
        html.Div([
            html.Label("Symbol:"),
            dcc.Input(id='symbol', type='text', value='BTCUSDT')
        ]),
        html.Div([
            html.Label("Timeframe:"),
            dcc.Dropdown(
                id='timeframe',
                options=[
                    {'label': '1 Minute', 'value': '1m'},
                    {'label': '5 Minutes', 'value': '5m'},
                    {'label': '15 Minutes', 'value': '15m'},
                    {'label': '1 Hour', 'value': '1h'},
                    {'label': '1 Day', 'value': '1d'},
                    {'label': '1 Week', 'value': '1w'},
                ],
                value='5m'
            )
        ]),
        # Future: Additional strategy parameter inputs can be added here.
        html.Div([
            html.Button("Run Backtest", id="run-backtest", n_clicks=0, style={'marginRight': '10px'}),
            html.Button("Run Optimization", id="run-optimization", n_clicks=0)
        ]),
        html.Br(),
        # Wrap outputs in a Loading component to show progress during processing.
        dcc.Loading(
            id="loading-indicator",
            type="default",
            children=[
                html.Div(id="output-metrics"),
                dcc.Graph(id='price-chart')
            ]
        )
    ]
)

# 4. Define the callbacks.
@app.callback(
    Output("output-metrics", "children"),
    Outp
