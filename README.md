# Hugard (v1.0.0)

Hugard (Pronounced /ˈhjuːɡɑːrd/) is a Discord bot designed to facilitate secure and anonymous payments between submissives and their dominants. It integrates directly with Coinbase Commerce to process payments and provides various commands for payment management and statistics.


## Features

- Secure & Anonymous Payments: Processes payments through Coinbase Commerce without storing sensitive information.
- Easy Setup: Direct integration with Coinbase Commerce for smooth transactions.
- Global Reach: Supports payments from users worldwide.
- Notification System: Alerts you as soon as payments are received.
- Payment Metrics: View payment statistics for individual users or the entire server.

## Commands

- /ping: Check the bot's response time.

- /about: Display information about the bot.

- /metrics [user]: Show payment statistics for a specific user or the entire server.

- /history: View your own payment history.

- /pay \<amount>: Initiate a payment to the owner.

## Customization

The accent colour for embeds can be customized by changing the `THEME_COLOUR` variable in `main.py` to any RGB value.

## Prerequisites

- Python 3.12 or higher (Tested on 3.12.4)
- Discord account and server
- Coinbase Commerce API key

## Setup

1. Clone the repository:
    ```
    git clone https://github.com/TheManStudios/Hugard.git
    cd Hugard
    ```

2. Create a Python Virtual Enviornment, then activate it
    ```
    python -m venv .venv
    source .venv/bin/activate
    ```

3. Install project dependencies:
    ```
    pip install -r requirements.txt
    ```

4. Run the bot once and enter the requested details:
    ```
    python -OO main.py
    ```
    
    *(Or you can manually fill them out in your `secrets/.env` file)*

5. Run the bot:
    ```
    python -OO main.py
    ```

<br><br>Still need help? Join our [support server](https://discord.gg/syHvfy4BVm)!


## Contributing

Contributions to Hugard are welcome! If you have a bug fix or new feature you'd like to contribute, go ahead and open a pull request!


## License

This project is licensed under the BSD 3-Clause License. See [LICENSE](LICENSE) for details.


## Disclaimer

This bot is intended for use between consenting adults. Please use it responsibly and in accordance with Discord's Terms of Service and local laws.
