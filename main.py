import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
import time
import asyncio

TELEGRAM_TOKEN = '7297136903:AAEvGYzJjhs5yfqqSfss0xx8jPWFfbT2RxY'  # Ваш TELEGRAM_TOKEN
CHAT_ID = '704160356'  # Ваш CHAT_ID

tender_numbers = []

def get_remaining_time(tender_number):
    url = f'https://eprocurement.gov.tj/ru/announce/index/{tender_number}?tab=lots#'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    time_div = soup.find('div', id='asNeeded', class_='is-countdown')
    if time_div:
        time_text = time_div.text.strip()
        days, hours, minutes, seconds = parse_time(time_text)
        return days, hours, minutes, seconds
    return None

def parse_time(time_text):
    time_parts = time_text.split(',')
    days = int(time_parts[0].split()[0])
    hours = int(time_parts[1].split()[0])
    minutes = int(time_parts[2].split()[0])
    seconds = int(time_parts[3].split()[0])
    return days, hours, minutes, seconds

async def send_message(context: ContextTypes.DEFAULT_TYPE, tender_number):
    message = f'Tender {tender_number} has 3 days remaining!'
    await context.bot.send_message(chat_id=CHAT_ID, text=message)

async def check_tender(context: ContextTypes.DEFAULT_TYPE):
    tender_number = context.job.data
    remaining_time = get_remaining_time(tender_number)
    if remaining_time:
        days, hours, minutes, seconds = remaining_time
        if days == 3:
            await send_message(context, tender_number)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Send me the tender number to track.")

async def add_tender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tender_number = int(context.args[0])
        if tender_number not in tender_numbers:
            tender_numbers.append(tender_number)
            await schedule_tender_check(tender_number, context)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Tender {tender_number} added for tracking.')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Tender {tender_number} is already being tracked.')
    except (IndexError, ValueError):
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Usage: /add <tender_number>')

async def schedule_tender_check(tender_number, context: ContextTypes.DEFAULT_TYPE):
    job_queue = context.job_queue
    job_queue.run_repeating(check_tender, interval=3600, first=0, data=tender_number)

async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('add', add_tender))

    # Initialize the application
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == '__main__':
    asyncio.run(main())
