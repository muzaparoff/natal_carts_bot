# Natal Charts Telegram Bot

A Telegram bot that generates natal charts and astrological predictions based on user birth data. This bot allows users to input their birth date, time, and location to receive personalized astrological insights.

## Features

- Generate personalized astrological predictions
- Calculate planetary positions using Swiss Ephemeris
- Support for multiple prediction types:
  - General character analysis
  - Daily horoscope
  - Compatibility insights
  - Financial perspectives
- Automatic timezone detection based on birth location
- User-friendly conversation flow

## Requirements

- Python 3.9+
- python-telegram-bot
- geopy
- timezonefinder
- pyswisseph
- zoneinfo (included in Python 3.9+)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/natal_carts_bot.git
cd natal_carts_bot
```
2. Install the required dependencies:
```bash
pip install -r requirements.txt
 ```

3. Set up your Telegram bot token:
```bash
export TELEGRAM_TOKEN="your_telegram_bot_token"
 ```

## Usage
1. Start the bot:
```bash
python bot.py
 ```

2. In Telegram, start a conversation with your bot and use one of the following commands:
   
   - /goroskop
   - /натальная_карта
   - Or simply type "натальная карта" or "гороскоп"
3. Follow the conversation prompts:
   
   - Enter your birth date (DD.MM.YYYY)
   - Enter your birth time (HH:MM)
   - Enter your birth place (city, country)
   - Choose the type of prediction you want
## Docker Deployment
This project can be deployed using Docker:

1. Build the Docker image:
```bash
docker build -t natal-carts-bot .
 ```

2. Run the container:
```bash
docker run -d --restart unless-stopped --name natal-carts-bot \
  -e TELEGRAM_TOKEN="your_telegram_bot_token" \
  natal-carts-bot
 ```
```

## CI/CD
This project uses GitHub Actions for continuous integration and deployment. When code is pushed to the main branch, it automatically:

- Builds a Docker image
- Pushes it to Docker Hub
- Deploys it to the production server
## License
MIT License

## Acknowledgements
- Swiss Ephemeris for planetary calculations
- python-telegram-bot for the Telegram API integration

This README provides a comprehensive overview of your project, including installation instructions, usage guidelines, and deployment options. Feel free to adjust any details to better match your specific project setup.