"""
股票分析軟體 - 命令列介面

使用方式：
    python main.py price AAPL --period 1y
    python main.py info TSLA
    python main.py indicators MSFT --period 1y --plot
    python main.py fundamental AAPL
    python main.py portfolio --add AAPL,10,150 --add TSLA,5,200
    python main.py screen AAPL,TSLA,MSFT --rsi-min 30 --rsi-max 50
    python main.py export AAPL --format csv
"""

import argparse
import sys
import json
from pathlib import Path

# 確保可以 import 到 stock_analyzer 套件
sys.path.insert(0, str(Path(__file__).parent))

from stock_analyzer import (
    fetch_stock_data,
    fetch_stock_info,
    fetch_multiple_stocks,
    analyze_all_indicators,
    generate_signals,
    fetch_fundamental_data,
    format_fundamental_summary,
    Portfolio,
    StockScreener,
    plot_stock_chart,
    plot_portfolio,
    export_to_csv,
    export_to_excel,
)


def cmd_price(args):
    """查詢股價"""
    df = fetch_stock_data(args.symbol, period=args.period, interval=args.interval, market=args.market)
    print(f"\n[股價] {args.symbol} 最近 {len(df)} 筆價格資料")
    print(df.tail(args.tail).to_string())

    if args.export:
        path = export_to_csv(df, filename=f"{args.symbol}_price.csv")
        print(f"\n[完成] 已匯出: {path}")


def cmd_info(args):
    """查詢股票資訊"""
    info = fetch_stock_info(args.symbol, market=args.market)
    print(f"\n[資訊] {args.symbol} 基本資訊")
    for key, value in info.items():
        print(f"  {key}: {value}")


def cmd_indicators(args):
    """技術指標分析"""
    df = fetch_stock_data(args.symbol, period=args.period, market=args.market)
    df = analyze_all_indicators(df)
    signals = generate_signals(df)

    print(f"\n[技術指標] {args.symbol} 技術指標分析")
    print(f"  日期: {signals['date']}")
    print(f"  收盤價: {signals['close']:.2f}")
    print(f"  RSI: {signals['rsi']:.2f}")
    print(f"  MACD: {signals['macd']:.4f}")
    print(f"  訊號: {', '.join(signals['signals']) if signals['signals'] else '無明顯訊號'}")

    print("\n最近資料:")
    cols = ["close", "ma_5", "ma_20", "ma_60", "rsi", "macd", "macd_signal", "bb_upper", "bb_lower"]
    print(df[cols].tail(args.tail).to_string())

    if args.plot or args.save:
        fig = plot_stock_chart(df, args.symbol)
        if args.save:
            fig.savefig(args.save, dpi=150, bbox_inches="tight")
            print(f"\n[完成] 圖表已儲存: {args.save}")
        else:
            plt = __import__("matplotlib.pyplot")
            plt.show()

    if args.export:
        path = export_to_csv(df, filename=f"{args.symbol}_indicators.csv")
        print(f"\n[完成] 已匯出: {path}")


def cmd_fundamental(args):
    """基本面分析"""
    data = fetch_fundamental_data(args.symbol, market=args.market)
    summary = format_fundamental_summary(data)

    print(f"\n[基本面] {args.symbol} 基本面資料")
    print(summary.to_string(index=False))

    if args.export:
        path = export_to_excel(
            {
                "Summary": summary,
                "Income": data.get("income_stmt", {}),
                "Balance": data.get("balance_sheet", {}),
                "CashFlow": data.get("cash_flow", {}),
            },
            filename=f"{args.symbol}_fundamental.xlsx",
        )
        print(f"\n[完成] 已匯出: {path}")


def cmd_portfolio(args):
    """投資組合分析"""
    portfolio = Portfolio(name=args.name)

    if args.add:
        for item in args.add:
            try:
                symbol, shares, cost = item.split(",")
                portfolio.add_position(symbol.strip(), float(shares), float(cost), market=args.market)
                print(f"[完成] 已添加 {symbol.strip()}: {shares} 股 @ {cost}")
            except Exception as e:
                print(f"[警告] 添加庫存失敗 '{item}': {e}")

    if args.json:
        print(json.dumps(portfolio.to_dict(), indent=2, default=str))
    else:
        summary = portfolio.get_summary()
        if summary.empty:
            print("[警告] 投資組合為空，請使用 --add 添加庫存")
        else:
            print(f"\n[投資組合] {portfolio.name} 摘要")
            print(summary.to_string(index=False))

    if args.plot or args.save:
        fig = plot_portfolio(portfolio, kind="both")
        if args.save:
            fig.savefig(args.save, dpi=150, bbox_inches="tight")
            print(f"\n[完成] 圖表已儲存: {args.save}")
        else:
            plt = __import__("matplotlib.pyplot")
            plt.show()


def cmd_screen(args):
    """選股篩選"""
    symbols = [s.strip() for s in args.symbols.split(",")]
    screener = StockScreener()

    if args.rsi_min is not None or args.rsi_max is not None:
        screener.add_condition("rsi", min_val=args.rsi_min, max_val=args.rsi_max)

    if args.above_ma:
        screener.add_condition("close", operator=">", field=f"ma_{args.above_ma}")

    if args.below_ma:
        screener.add_condition("close", operator="<", field=f"ma_{args.below_ma}")

    print(f"\n[篩選] 開始篩選 {len(symbols)} 檔股票...")
    results = screener.screen(symbols, period=args.period, market=args.market)

    if results.empty:
        print("沒有符合條件的股票。")
    else:
        print(f"\n[完成] 找到 {len(results)} 檔符合條件的股票:")
        print(results.to_string(index=False))

    if args.export and not results.empty:
        path = export_to_csv(results, filename="screen_results.csv")
        print(f"\n[完成] 已匯出: {path}")


def cmd_export(args):
    """匯出股票資料"""
    symbols = [s.strip() for s in args.symbols.split(",")]
    data = fetch_multiple_stocks(symbols, period=args.period, market=args.market)

    if args.format == "csv":
        for symbol, df in data.items():
            if not df.empty:
                path = export_to_csv(df, filename=f"{symbol}.csv")
                print(f"[完成] {symbol} 已匯出: {path}")
    elif args.format == "excel":
        sheets = {symbol: df for symbol, df in data.items() if not df.empty}
        if sheets:
            path = export_to_excel(sheets, filename="multi_stocks.xlsx")
            print(f"[完成] 已匯出: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="股票分析軟體 - 支援股價查詢、技術指標、基本面、投資組合、選股篩選",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python main.py price AAPL --period 6mo
  python main.py indicators TSLA --plot
  python main.py fundamental 2330 --market tw
  python main.py portfolio --add AAPL,10,150 --add TSLA,5,200 --plot
  python main.py screen AAPL,MSFT,GOOGL --rsi-min 30 --rsi-max 50
  python main.py export AAPL,TSLA --format excel
        """,
    )
    parser.add_argument("--market", default="auto", choices=["auto", "us", "tw", "hk"],
                        help="市場別（預設自動判斷）")

    subparsers = parser.add_subparsers(dest="command", help="可用指令")

    # price
    p_price = subparsers.add_parser("price", help="查詢股價")
    p_price.add_argument("symbol", help="股票代碼")
    p_price.add_argument("--period", default="1y", help="時間區間（預設 1y）")
    p_price.add_argument("--interval", default="1d", help="資料頻率（預設 1d）")
    p_price.add_argument("--tail", type=int, default=10, help="顯示最近幾筆")
    p_price.add_argument("--export", action="store_true", help="匯出 CSV")
    p_price.set_defaults(func=cmd_price)

    # info
    p_info = subparsers.add_parser("info", help="查詢股票基本資訊")
    p_info.add_argument("symbol", help="股票代碼")
    p_info.set_defaults(func=cmd_info)

    # indicators
    p_ind = subparsers.add_parser("indicators", help="技術指標分析")
    p_ind.add_argument("symbol", help="股票代碼")
    p_ind.add_argument("--period", default="1y", help="時間區間")
    p_ind.add_argument("--tail", type=int, default=5, help="顯示最近幾筆")
    p_ind.add_argument("--plot", action="store_true", help="繪製圖表")
    p_ind.add_argument("--save", help="儲存圖表路徑")
    p_ind.add_argument("--export", action="store_true", help="匯出 CSV")
    p_ind.set_defaults(func=cmd_indicators)

    # fundamental
    p_fund = subparsers.add_parser("fundamental", help="基本面分析")
    p_fund.add_argument("symbol", help="股票代碼")
    p_fund.add_argument("--export", action="store_true", help="匯出 Excel")
    p_fund.set_defaults(func=cmd_fundamental)

    # portfolio
    p_port = subparsers.add_parser("portfolio", help="投資組合分析")
    p_port.add_argument("--name", default="我的投資組合", help="投資組合名稱")
    p_port.add_argument("--add", action="append", help="添加庫存，格式: 代碼,股數,成本")
    p_port.add_argument("--plot", action="store_true", help="繪製圖表")
    p_port.add_argument("--save", help="儲存圖表路徑")
    p_port.add_argument("--json", action="store_true", help="以 JSON 輸出")
    p_port.set_defaults(func=cmd_portfolio)

    # screen
    p_screen = subparsers.add_parser("screen", help="選股篩選")
    p_screen.add_argument("symbols", help="股票代碼列表，以逗號分隔")
    p_screen.add_argument("--period", default="1y", help="時間區間")
    p_screen.add_argument("--rsi-min", type=float, help="RSI 最小值")
    p_screen.add_argument("--rsi-max", type=float, help="RSI 最大值")
    p_screen.add_argument("--above-ma", type=int, help="股價在多少日均線之上")
    p_screen.add_argument("--below-ma", type=int, help="股價在多少日均線之下")
    p_screen.add_argument("--export", action="store_true", help="匯出 CSV")
    p_screen.set_defaults(func=cmd_screen)

    # export
    p_export = subparsers.add_parser("export", help="批量匯出股票資料")
    p_export.add_argument("symbols", help="股票代碼列表，以逗號分隔")
    p_export.add_argument("--period", default="1y", help="時間區間")
    p_export.add_argument("--format", default="csv", choices=["csv", "excel"], help="匯出格式")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
