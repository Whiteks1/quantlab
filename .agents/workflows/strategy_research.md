\# strategy\_research



Run a small strategy research sweep and save outputs.



\## Commands (Windows)

```bash

.\\.venv\\Scripts\\python.exe -m pip install -e .

.\\.venv\\Scripts\\python.exe main.py --ticker ETH-USD --start 2023-01-01 --end 2024-01-01 --paper --initial\_cash 700 --slippage\_mode fixed --slippage\_bps 8 --fee 0.002 --save\_price\_plot

.\\.venv\\Scripts\\python.exe main.py --ticker ETH-USD --start 2023-01-01 --end 2024-01-01 --paper --initial\_cash 700 --slippage\_mode atr --k\_atr 0.05 --fee 0.002 --save\_price\_plot

