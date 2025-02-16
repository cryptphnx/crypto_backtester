# dashboard.py (snippet)
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
        # Run backtest using default parameters
        initial_value, final_value, trade_log, cerebro = run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            start_str='1 month ago UTC',
            strategy_params=DEFAULT_PARAMS
        )
        # [rest of your backtest processing code...]
        return metrics_components, fig

    elif button_id == "run-optimization":
        # Import run_optimization here instead of at the top of the file.
        from ga_optimization import run_optimization
        best_value, best_params = run_optimization(symbol=symbol, timeframe=timeframe)
        metrics_components = [
            html.P(f"Best Portfolio Value from Optimization: {best_value:.2f}"),
            html.Hr(),
            html.H3("Best Strategy Parameters:"),
            html.Pre(json.dumps(best_params, indent=2))
        ]
        return metrics_components, go.Figure()
