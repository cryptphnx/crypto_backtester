# main.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import pandas as pd
import json

# Our local modules (assuming they are separate files, or we unify them).
from backtesting import run_backtest
from ga_optimization import run_optimization, PARAM_BOUNDARIES
from data import get_historical_data
from strategy import PineStrategy

app = dash.Dash(__name__)
server = app.server

# Default Strategy Params
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

app.layout = html.Div(
    style={'backgroundColor': '#222', 'color': '#FFC107', 'padding': '20px', 'fontFamily': 'Arial'},
    children=[
        html.H1("All-in-One Backtesting Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),
        # Control Panel
        html.Div([
            html.Label("Symbol:", style={'marginRight': '10px'}),
            dcc.Input(id='symbol', type='text', value='BTCUSDT', style={'width': '120px', 'marginRight': '30px'}),
            
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
                style={'width': '150px', 'display': 'inline-block', 'marginRight': '30px'}
            ),
            html.Button("Run Backtest", id="run-backtest", n_clicks=0, style={'padding': '10px 20px', 'fontSize': '16px', 'marginRight': '10px'}),
            html.Button("Run Optimization", id="run-optimization", n_clicks=0, style={'padding': '10px 20px', 'fontSize': '16px'}),
        ], style={'textAlign': 'center', 'marginBottom': '40px'}),

        # Chart
        dcc.Loading(
            id="loading-chart",
            type="default",
            children=[dcc.Graph(id='price-chart')]
        ),
        html.Hr(style={'borderColor': '#FFC107'}),
        # Metrics & Parameter Display
        html.Div(id="output-metrics", style={'marginBottom': '30px'}),
        html.Hr(style={'borderColor': '#FFC107'}),
        # Trades Section
        html.Div(id="trade-log-div"),
        html.Br(),
        html.Div([
            html.Button("Download Trade Log CSV", id="download-btn", n_clicks=0,
                        style={'padding': '10px 20px', 'fontSize': '16px'}),
            dcc.Download(id="download-trade-log")
        ], style={'textAlign': 'center', 'marginTop': '20px'}),

        # Hidden Storage
        dcc.Store(id='trade-log-store')
    ]
)

@app.callback(
    [Output("output-metrics", "children"),
     Output("price-chart", "figure"),
     Output("trade-log-div", "children"),
     Output("trade-log-store", "data")],
    [Input("run-backtest", "n_clicks"),
     Input("run-optimization", "n_clicks")],
    [State("symbol", "value"),
     State("timeframe", "value")]
)
def run_actions(n_backtest, n_opt, symbol, timeframe):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", go.Figure(), "", []
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    metrics_html = ""
    fig = go.Figure()
    trades_html = ""
    trades_store = []

    if button_id == "run-backtest":
        # Actually run the backtest
        init_val, final_val, trade_log, cerebro = run_backtest(
            symbol=symbol, timeframe=timeframe, start_str='1 month ago UTC',
            strategy_params=DEFAULT_PARAMS
        )
        net_profit = final_val - init_val
        # Build metrics
        metrics_list = [
            html.P(f"Symbol: {symbol}"),
            html.P(f"Timeframe: {timeframe}"),
            html.P(f"Initial Value: {init_val:.2f}"),
            html.P(f"Final Value: {final_val:.2f}"),
            html.P(f"Net Profit: {net_profit:.2f}"),
            html.P(f"Number of Trades: {len(trade_log)}"),
            html.H3("Parameters Used:"),
            html.Pre(json.dumps(DEFAULT_PARAMS, indent=2))
        ]
        metrics_html = html.Div(metrics_list, style={'border': '1px solid #FFC107', 'padding': '10px'})

        # Build chart
        df = get_historical_data(symbol=symbol, interval=timeframe, start_str='1 month ago UTC')
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])
        fig.update_layout(template='plotly_dark', title=f"{symbol} Price Chart ({timeframe})")

        # Add trade markers to the chart if we have trades
        if trade_log and len(trade_log) > 0:
            # Convert trade times to actual x-values in the df
            # We'll do a simple approach: for each trade, add a scatter marker for entry & exit
            entries_x = []
            entries_y = []
            exits_x = []
            exits_y = []
            for t in trade_log:
                # If we want to match them with df index, we can do approximate matching
                # or we can just place them by date. We'll do a direct approach
                ent_date = t["Entry Date"]
                exit_date = t["Exit Date"]
                # We won't do an exact match of index. We'll do a fallback approach: just place them if they exist in df
                try:
                    ent_ts = pd.to_datetime(ent_date)
                    exit_ts = pd.to_datetime(exit_date)
                    if ent_ts in df.index:
                        entries_x.append(ent_ts)
                        # approximate price
                        # We might guess the open price
                        entries_y.append(df.loc[ent_ts, 'close'])
                    if exit_ts in df.index:
                        exits_x.append(exit_ts)
                        exits_y.append(df.loc[exit_ts, 'close'])
                except:
                    pass
            
            fig.add_trace(go.Scatter(
                x=entries_x,
                y=entries_y,
                mode='markers',
                marker=dict(symbol='triangle-up', color='green', size=12),
                name='Entries'
            ))
            fig.add_trace(go.Scatter(
                x=exits_x,
                y=exits_y,
                mode='markers',
                marker=dict(symbol='triangle-down', color='red', size=12),
                name='Exits'
            ))

        # Build trades log table if trades exist
        if trade_log and len(trade_log) > 0:
            table = dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in trade_log[0].keys()],
                data=trade_log,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'backgroundColor': '#222', 'color': '#FFC107'},
                page_size=10
            )
            trades_html = html.Div([
                html.H3("Trade Log:"),
                table
            ], style={'border': '1px solid #FFC107', 'padding': '10px'})
            trades_store = trade_log
        else:
            trades_html = html.Div([
                html.P("No trades executed or no trade log generated.")
            ], style={'border': '1px solid #FFC107', 'padding': '10px'})
            trades_store = []

    elif button_id == "run-optimization":
        best_val, best_params = run_optimization(symbol=symbol, timeframe=timeframe)
        metrics_html = html.Div([
            html.P("Optimization Results:"),
            html.P(f"Best Value: {best_val:.2f}"),
            html.Pre(json.dumps(best_params, indent=2))
        ], style={'border': '1px solid #FFC107', 'padding': '10px'})
        fig = go.Figure()
        trades_html = html.Div([
            html.P("No trade log for optimization runs.")
        ], style={'border': '1px solid #FFC107', 'padding': '10px'})
        trades_store = []

    return metrics_html, fig, trades_html, trades_store

# Download CSV
@app.callback(
    Output("download-trade-log", "data"),
    Input("download-btn", "n_clicks"),
    State("trade-log-store", "data"),
    prevent_initial_call=True
)
def download_log_as_csv(n_clicks, trade_data):
    if not trade_data or len(trade_data) == 0:
        return None
    df = pd.DataFrame(trade_data)
    return dcc.send_data_frame(df.to_csv, "trade_log.csv", index=False)

if __name__ == "__main__":
    app.run_server(debug=True)
