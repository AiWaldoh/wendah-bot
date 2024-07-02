# Wendah Simple

This project contains a simple Discord bot named Wendah that interacts with users in a Discord channel using a chat API.

## Features

- Extracts and processes messages from users in a Discord server
- Interacts with the Cohere chat API to generate responses in a conversational manner
- Provides a simple interface for launching a Discord bot and handling messages

## Installation

1. Clone the repository
2. Install Poetry (if not already installed): `curl -sSL https://install.python-poetry.org | python3`
3. Install project dependencies: `poetry install`
4. Set up your environment variables in a `.env` file following the provided template in the `.env.example` file
5. Sign in to discord with headless browser set to false the first time you run the bot (to bypass captcha). This will create a session file in the `secret` folder.

## Usage

1. Activate the virtual environment created by Poetry: `poetry shell`
2. Start the API server: `poetry run python src/api.py`
3. Start the Discord bot: `poetry run python src/main.py`
4. The bot will log in to Discord, listen for new messages, and respond using the Cohere chat API

## Configurations

Ensure to configure the following variables in your `.env` file:

- DISCORD_EMAIL: Your Discord email
- DISCORD_PASSWORD: Your Discord password
- DISCORD_CHANNEL_URL: The Discord channel URL to listen and respond to
- COOKIE_FILE_NAME: Name of the cookie file
- BOT_NAME: Mention name for the bot in Discord
- API_URL: URL for any external APIs used
- COHERE_API_KEY: API key for the Cohere chat API

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.