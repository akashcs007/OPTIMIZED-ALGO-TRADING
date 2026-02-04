# OPTIMIZED-ALGO-TRADING


# 📈 EMA Trend-Following Trading Strategy (Backtrader)

This project implements a **trend-following tactical buy-and-hold trading strategy** using
**EMA(50/200) crossover** with **ATR-based risk management**, backtested on SPY market data
using **Backtrader** and **Yahoo Finance**.

The goal is to stay invested during strong market uptrends while exiting during trend reversals,
thereby maximizing returns and minimizing drawdowns.

---

## 🚀 Strategy Overview

**Core Idea:**  
Markets trend upward over the long term. Instead of frequent trading, this strategy:
- Enters only during confirmed uptrends
- Exits during trend reversals
- Uses wide ATR-based stops to avoid noise
- Minimizes overtrading

---

## 🧠 Trading Logic

### Entry Rule
- EMA(50) crosses **above** EMA(200) (Golden Cross)

### Exit Rules
- EMA(50) crosses **below** EMA(200) (Trend reversal)
- ATR-based stop loss is hit

### Risk Management
- 95% capital allocation per trade
- ATR(14) × 8 wide stop-loss
- Low trade frequency to reduce transaction costs
