# dashboard.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import pandas as pd
import json
from backtesting import run_backtest
from ga_optimization import run_optimization
from data import get_historical_data

# Create the Dash app and expose the underlying Flask server.
app = dash.Dash(__name__)
server = app.server

# Default strategy parameters used for backtesting.
DEFAULT_PARAMS = {
    "longTermFastLen": 50,
    "longTermSlowLen": 200,
    "shortTermFastLen": 10,
    "shortTermSlowLen": 20,
    "fixedStopLossPct": 1,
    "fixedTakeProfitPct": 2,
    "fixedTrailingPct": 1.5,
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

# Define the layout.
app.layout = html.Div(
    style={'backgroundColor': 'black', 'color': 'yellow', 'padding': '20px'},
    children=[
        html.H1("Crypto Backtesting Dashboard"),
        # Control Panel
        html.Div([
            html.Label("Symbol:"),
            dcc.Input(id='symbol', type='text', value='BTCUSDT', style={'marginRight': '20px'}),
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
                value='5m',
                style={'width': '150px', 'display': 'inline-block'}
            ),
            html.Button("Run Backtest", id="run-backtest", n_clicks=0, style={'marginLeft': '20px', 'marginRight': '10px'}),
            html.Button("Run Optimization", id="run-optimization", n_clicks=0)
        ], style={'marginBottom': '20px'}),
        # Chart Section (on top)
        dcc.Loading(
            id="loading-chart",
            type="default",
            children=[
                dcc.Graph(id='price-chart')
            ]
        ),
        html.Hr(style={'borderColor': 'yellow'}),
        # Metrics & Trades Log Section (at the bottom)
        dcc.Loading(
            id="loading-metrics",
            type="default",
            children=[
                html.Div(id="output-metrics")
            ]
        )
    ]
)

@app.callback(
    [Output("output-metrics", "children"),
     Output("price-chart", "figure")],
    [Input("run-backtest", "n_clicks"),
     Input("run-optimization", "n_clicks")],
    [State("symbol", "value"),
     State("timeframe", "value")]
)
def update_dashboard(n_backtest, n_optimization, symbol, timeframe):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", go.Figure()
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Initialize placeholders
    metrics_output = ""
    fig = go.Figure()

    if button_id == "run-backtest":
        initial_value, final_value, trade_log, cerebro = run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            start_str='1 month ago UTC',
            strategy_params=DEFAULT_PARAMS
        )
        net_profit = final_value - initial_value
        num_trades = len(trade_log)
        
        # Build metrics section.
        metrics_components = [
            html.P(f"Initial Portfolio Value: {initial_value:.2f}"),
            html.P(f"Final Portfolio Value: {final_value:.2f}"),
            html.P(f"Net Profit: {net_profit:.2f}"),
            html.P(f"Number of Trades: {num_trades}"),
            html.H3("Strategy Parameters Used:"),
            html.Pre(json.dumps(DEFAULT_PARAMS, indent=2))
        ]
        
        # Build trades log section.
        if trade_log:
            trades_table = dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in trade_log[0].keys()],
                data=trade_log,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'backgroundColor': 'black', 'color': 'yellow'},
                page_size=10
            )
            trades_section = [
                html.H3("Trade Log:"),
                trades_table
            ]
        else:
            trades_section = [html.P("No trades were executed during this backtest.")]
        
        # Combine metrics and trades log.
        metrics_output = html.Div(metrics_components + trades_section, style={'marginTop': '20px'})
        
        # Build the chart.
        df = get_historical_data(symbol=symbol, interval=timeframe, start_str='1 month ago UTC')
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])
        fig.update_layout(template='plotly_dark', title=f"{symbol} Price Chart ({timeframe})")

    elif button_id == "run-optimization":
        best_value, best_params = run_optimization(symbol=symbol, timeframe=timeframe)
        metrics_output = html.Div([
            html.P(f"Best Portfolio Value from Optimization: {best_value:.2f}"),
            html.H3("Best Strategy Parameters:"),
            html.Pre(json.dumps(best_params, indent=2))
        ], style={'marginTop': '20px'})
        # Optionally, you could display a chart here if desired.
        fig = go.Figure()

    return metrics_output, fig

if __name__ == "__main__":
    app.run_server(debug=True)
