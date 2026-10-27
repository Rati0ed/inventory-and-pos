


| [`inventory-pos/`](inventory-pos) | Desktop inventory & point-of-sale app (Tkinter + JSON + Matplotlib) |


## Inventory & POS app

A small shop management app with a login screen, stock list with live search, shopping cart with running total, sales that update stock and record profit, a sales history window with a profit pie chart, and a settings window to add, edit and delete products. Data is saved in `stock.json` and `sales_history.json`.

```bash
cd inventory-pos
pip install matplotlib
python main.py
```

Demo login: `admin` / `admin` (set in `main.py`; hardcoded credentials are for demo only).

Profit per item = selling price − cost price − (sale tax % × selling price).



## Requirements

Python 3.8+. Tkinter comes with Python on Windows/macOS; on Linux install `python3-tk`.
