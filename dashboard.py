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
    style={'backgroundColor': '#222', 'color': '#FFC107', 'padding': '20px', 'fontFamily': 'Arial'},
    children=[
        html.H1("Crypto Backtesting Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),
        # Control Panel Section
        html.Div([
            html.Div([
                html.Label("Symbol:", style={'marginRight': '10px'}),
                dcc.Input(id='symbol', type='text', value='BTCUSDT', style={'width': '120px'})
            ], style={'display': 'inline-block', 'marginRight': '30px'}),
            html.Div([
                html.Label("Timeframe:", style={'marginRight': '10px'}),
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
                    style={'width': '150px'}
                )
            ], style={'display': 'inline-block', 'marginRight': '30px'}),
            html.Div([
                html.Button("Run Backtest", id="run-backtest", n_clicks=0, style={'marginRight': '10px'}),
                html.Button("Run Optimization", id="run-optimization", n_clicks=0)
            ], style={'display': 'inline-block'})
        ], style={'textAlign': 'center', 'marginBottom': '40px'}),
        # Chart Section (on Top)
        dcc.Loading(
            id="loading-chart",
            type="default",
            children=[dcc.Graph(id='price-chart')]
        ),
        html.Hr(style={'borderColor': '#FFC107', 'marginTop': '40px'}),
        # Metrics & Trade Log Section (at the Bottom)
        dcc.Loading(
            id="loading-metrics",
            type="default",
            children=[html.Div(id="output-metrics")]
        ),
        # Hidden Store to keep trade log data for CSV download.
        dcc.Store(id='trade-log-store'),
        # Download Button Section
        html.Div([
            html.Button("Download Trade Log CSV", id="download-btn", n_clicks=0, style={'padding': '10px 20px', 'fontSize': '16px'}),
            dcc.Download(id="download-trade-log")
        ], style={'textAlign': 'center', 'marginTop': '30px'})
    ]
)

# Main callback: update metrics, chart, and store trade log data.
@app.callback(
    [Output("output-metrics", "children"),
     Output("price-chart", "figure"),
     Output("trade-log-store", "data")],
    [Input("run-backtest", "n_clicks"),
     Input("run-optimization", "n_clicks")],
    [State("symbol", "value"),
     State("timeframe", "value")]
)
def update_dashboard(n_backtest, n_optimization, symbol, timeframe):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", go.Figure(), None
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    metrics_output = ""
    fig = go.Figure()
    trade_log_data = None

    if button_id == "run-backtest":
        initial_value, final_value, trade_log, cerebro = run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            start_str='1 month ago UTC',
            strategy_params=DEFAULT_PARAMS
        )
        net_profit = final_value - initial_value
        num_trades = len(trade_log)
        
        metrics_components = [
            html.P(f"Initial Portfolio Value: {initial_value:.2f}"),
            html.P(f"Final Portfolio Value: {final_value:.2f}"),
            html.P(f"Net Profit: {net_profit:.2f}"),
            html.P(f"Number of Trades: {num_trades}"),
            html.H3("Strategy Parameters Used:"),
            html.Pre(json.dumps(DEFAULT_PARAMS, indent=2))
        ]
        
        if trade_log:
            trades_table = dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in trade_log[0].keys()],
                data=trade_log,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'backgroundColor': '#222', 'color': '#FFC107'},
                page_size=10
            )
            trades_section = [html.H3("Trade Log:"), trades_table]
            metrics_components += trades_section
            trade_log_data = trade_log
        else:
            metrics_components.append(html.P("No trades were executed during this backtest."))
        
        metrics_output = html.Div(metrics_components, style={'marginTop': '20px', 'padding': '10px', 'border': '1px solid #FFC107'})
        
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
        ], style={'marginTop': '20px', 'padding': '10px', 'border': '1px solid #FFC107'})
        fig = go.Figure()
    
    return metrics_output, fig, trade_log_data

# Callback for downloading the trade log as CSV.
@app.callback(
    Output("download-trade-log", "data"),
    Input("download-btn", "n_clicks"),
    State("trade-log-store", "data"),
    prevent_initial_call=True
)
def download_trade_log(n_clicks, trade_log_data):
    if not trade_log_data:
        return None
    df = pd.DataFrame(trade_log_data)
    return dcc.send_data_frame(df.to_csv, "trade_log.csv", index=False)

if __name__ == "__main__":
    app.run_server(debug=True)
