<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Registration Bot</title>
</head>
<body>
    <h1>User Registration Bot</h1>
    <p>This bot is designed for user registration in a database and assigning roles according to a hierarchy. For better code organization and readability, functions (excluding routers) are separated into <code>defs.py</code>. Configuration settings can be adjusted in <code>config.py</code> for easy setup.</p>

    <h2>Prerequisites</h2>
    <p>Ensure you have Python 3 installed on your Ubuntu/Debian system. You will also need to install the necessary dependencies listed in <code>requirements.txt</code>.</p>

    <h2>Setting Up a Virtual Environment</h2>
    <p>To set up a virtual environment, use the following commands:</p>
    <h3>For standard shell:</h3>
    <pre><code>source venv/bin/activate</code></pre>
    <h3>For Fish shell:</h3>
    <pre><code>source venv/bin/activate.fish</code></pre>

    <h2>Running the Bot</h2>
    <p>Once your virtual environment is activated, you can start the bot with the following command:</p>
    <pre><code>python3 tgBot.py</code></pre>

    <h2>Configuration</h2>
    <p>Before running the bot, make sure to configure your settings in <code>config.py</code>. This file contains essential parameters that the bot requires for proper operation.</p>

    <h2>Contributing</h2>
    <p>If you would like to contribute to this project, please feel free to submit a pull request or open an issue. Your contributions are welcome!</p>

    <h2>License</h2>
    <p>This project is licensed under the MIT License. See the LICENSE file for more details.</p>
</body>
</html>
