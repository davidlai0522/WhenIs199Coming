#!/usr/bin/env python3
import os
import argparse
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from colorama import Fore
from app_func import *

LTA_API_KEY = os.environ.get("LTA_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

async def error_handler(update, context):
    # Log the error
    print(f"An error occurred: {context.error}")

    if update is not None and update.message:
        await update.message.reply_text("An unexpected error occurred. Please try again later.")

def main(args):
    print(Fore.GREEN + "Welcome to WhenIs199Coming bus app!" + Fore.RESET)

    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Create App Object
    bus_app = App(
        lta_api_key=LTA_API_KEY,
        bus_stop_code=args.bus_stop_code,
        bus_service_no=args.bus_service_no,
        groq_api_key=GROQ_API_KEY,
    )

    # Add command handlers
    application.add_handler(CommandHandler("start", bus_app.start))
    application.add_handler(CommandHandler("bus", bus_app.bus_arrival_async))
    application.add_handler(CommandHandler("bus_stop", bus_app.bus_stop_async))
    application.add_handler(CommandHandler("bus_route", bus_app.send_bus_stop_image_async))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bus_app.handle_text)
    )
    application.add_error_handler(error_handler)

    # Run the bot
    try:
        application.run_polling(timeout=None)
    except Exception as e:
        print(e)

    print(Fore.YELLOW + "Bye. Hope to see you soon." + Fore.RESET)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bus_stop_code",
        default="27011",
        help="Set the desired bus stop code to be tracked.",
    )  # Default bus stop code is at NTU Hall 11 bus stop
    parser.add_argument(
        "--bus_service_no",
        default="199",
        help="Bus service to be tracked.",
    )  # Default bus service is 199

    main(args=parser.parse_args())
