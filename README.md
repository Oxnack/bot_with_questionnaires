# User Registration Bot

This bot is designed for user registration and role assignment within a database. It assigns roles based on a predefined hierarchy.

The code is structured to separate functions for clarity and maintainability. Non-router functions are placed in `defs.py` for easier understanding. The bot's configuration is stored in `config.py`.

## Project Structure

- **defs.py**: Contains the base functions (not routers).
- **config.py**: Configuration file for setting up the bot parameters.
- **tgBot.py**: Main script for running the bot.

## Installation and Setup
  clone repository:
  ```
  git clone https://github.com/Oxnack/bot_with_questionnaires.git
  ```
### Setting Up the Virtual Environment

1. To create and activate the virtual environment, use the following command for the bash shell:
    ```bash
    source venv/bin/activate
    ```
    If you are using the fish shell, use this command instead:

    ```bash
    source venv/bin/activate.fish
    ```

2. Running the Bot
    To run the bot, simply execute the following command:

    ```bash
    python3 tgBot.py
    ```

    Install the required dependencies (if you have a requirements.txt file, use the following command):

    ```bash
    pip install -r requirements.txt
    ```
    Configuration
    Open and modify config.py to set up your bot, including bot token, database settings, and other parameters.
    Deployment on Ubuntu/Debian
    To deploy and run the bot on Ubuntu/Debian systems, ensure you have Python 3.x and the required dependencies installed. Use the following commands:

    ```bash
    sudo apt update
    sudo apt install python3 python3-pip python3-venv
    ```
    After setting up the virtual environment, follow the instructions above to activate it and run the bot.
