# dashboard.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import pandas as pd
import json
from backtesting import run_backtest
from ga_optimization import run_optimization
from data import get_historical_data

app = dash.Dash(__name__)
server = app.server

# Default strategy parameters used for backtesting
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

app.layout = html.Div(style={'backgroundColor': 'black', 'color': 'yellow', 'padding': '20px'}, children=[
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
    # Wrap outputs in a loading component to show progress.
    dcc.Loading(
        id="loading-indicator",
        type="default",
        children=[
            html.Div(id="output-metrics"),
            dcc.Graph(id='price-chart')
        ]
    )
])

@app.callback(
    Output("output-metrics", "children"),
    Output("price-chart", "figure"),
    Input("run-backtest", "n_clicks"),
    Input("run-optimization", "n_clicks"),
    State("symbol", "value"),
    State("timeframe", "value")
)
def update_dashboard(n_backtest, n_optimization, symbol, timeframe):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", go.Figure()
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "run-backtest":
        initial_value, final_value, trade_log, cerebro = run_backtest(
            symbol=symbol, timeframe=timeframe, start_str='1 month ago UTC',
            strategy_params=DEFAULT_PARAMS
        )
        net_profit = final_value - initial_value
        num_trades = len(trade_log)
        
        metrics_components = [
            html.P(f"Initial Portfolio Value: {initial_value:.2f}"),
            html.P(f"Final Portfolio Value: {final_value:.2f}"),
            html.P(f"Net Profit: {net_profit:.2f}"),
            html.P(f"Number of Trades: {num_trades}"),
            html.Hr(),
            html.H3("Strategy Parameters Used:"),
            html.Pre(json.dumps(DEFAULT_PARAMS, indent=2))
        ]
        
        if trade_log:
            table = dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in trade_log[0].keys()],
                data=trade_log,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'backgroundColor': 'black', 'color': 'yellow'},
                page_size=10
            )
            metrics_components.append(html.Hr())
            metrics_components.append(html.H3("Trade Log:"))
            metrics_components.append(table)
        
        df = get_historical_data(symbol=symbol, interval=timeframe, start_str='1 month ago UTC')
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                                             open=df['open'],
                                             high=df['high'],
                                             low=df['low'],
                                             close=df['close'])])
        fig.update_layout(template='plotly_dark', title=f"{symbol} Price Chart ({timeframe})")
        return metrics_components, fig

    elif button_id == "run-optimization":
        best_value, best_params = run_optimization(symbol=symbol, timeframe=timeframe)
        metrics_components = [
            html.P(f"Best Portfolio Value from Optimization: {best_value:.2f}"),
            html.Hr(),
            html.H3("Best Strategy Parameters:"),
            html.Pre(json.dumps(best_params, indent=2))
        ]
        return metrics_components, go.Figure()

if __name__ == "__main__":
    app.run_server(debug=True)
