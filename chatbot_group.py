from telegram import Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, 
                          CallbackContext)
import configparser
import logging
import redis
import random

from ChatGpt_HKBU import HKBU_ChatGPT

global redis1

def main():
    # Load your token and create an Updater for your Bot
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Create an Updater instance
    updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), 
                      use_context=True)
    
    dispatcher = updater.dispatcher
    
    global redis1  # Declare redis1 as a global variable
    redis1 = redis.Redis(host=(config['REDIS']['HOST']), 
                         password=(config['REDIS']['PASSWORD']), 
                         port=(config['REDIS']['REDISPORT']),
                         decode_responses=(config['REDIS']['DECODE_RESPONSE']),
                         username=(config['REDIS']['USER_NAME']))
   
    # You can set this logging module, so you will know when 
    # and why things do not work as expected. Meanwhile, update your config.ini as:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                        level=logging.INFO)
    
    # Register command handlers
    dispatcher.add_handler(CommandHandler("popular", popular_recipes))
    dispatcher.add_handler(CommandHandler("recipe", recipe_generation))
    dispatcher.add_handler(CommandHandler("detail", recipe_details))
    dispatcher.add_handler(CommandHandler("plan", diet_plan))
    dispatcher.add_handler(CommandHandler("recommend", ingredient_recommendation))
    dispatcher.add_handler(CommandHandler("collect", collect_recipe))
    dispatcher.add_handler(CommandHandler("history", view_history))
    dispatcher.add_handler(CommandHandler("nutrition", nutrition_analysis))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("delete", delete_recipe)) 

    # Register message handler
    global chatgpt
    chatgpt = HKBU_ChatGPT(config)
    chatgpt_handler = MessageHandler(Filters.text & (~Filters.command), 
                                     equipped_chatgpt)
    dispatcher.add_handler(chatgpt_handler)

    # Start the bot
    updater.start_polling()
    updater.idle()

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "Hello, I'm a professional recipe recommendation bot. Here are the functions I offer:\n"
        "1. Random popular recipe recommendation: Use /popular to get a randomly recommended popular recipe.\n"
        "2. Recipe details query: Use /detail <recipe_name> to get detailed information about a specific recipe.\n"
        "3. Diet plan customization: Use /plan <duration> <calories> to generate a multi - day diet plan.\n"
        "4. Ingredient - based recipe recommendation: Use /recommend <ingredient1> <ingredient2>... to get recipe recommendations based on the given ingredients.\n"
        "5. Recipe collection and history: Use /collect <recipe_name> to collect a recipe, and /history to view the list of collected recipes.\n"
        "6. Nutrition analysis: Use /nutrition <recipe_name> to get the nutritional analysis of a recipe.\n"
        "7. Delete a collected recipe: Use /delete <recipe_name> to delete a collected recipe.\n"
        "You can also get answers by directly asking questions."
    )
    update.message.reply_text(help_text)

def clean_reply_message(message):
    """Clean the reply message by removing #, * and - symbols"""
    return message.replace('#', '').replace('*', '').replace('-', '')

def recipe_generation(update: Update, context: CallbackContext) -> None:
    """Generate recipes"""
    try:
        keywords = " ".join(context.args)
        question = f"Generate a list of recipes containing {keywords}"
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /recipe <ingredients> <taste>')

def popular_recipes(update: Update, context: CallbackContext) -> None:
    """Get a random popular recipe"""
    question = "Randomly generate a recommended Chinese home cooked dish for me, requiring only the dish name to be returned and a new dish to be returned every time you are asked (cannot be repeated with the previous one)"
    reply_message = chatgpt.submit(question)
    # Try to extract the recipe name more accurately, assuming the recipe name is separated by numbers or line breaks
    import re
    # Match possible numbering formats, such as "1. Recipe Name" or just the recipe name
    pattern = r'(?:\d+\.\s*)?([^\n]+)'
    recipes = re.findall(pattern, reply_message)
    if recipes:
        random_recipe = random.choice(recipes)
        prompt = f"Enter /detail {random_recipe} to get the cooking method of this recipe."
        update.message.reply_text(f"The randomly recommended popular recipe is: {random_recipe}\n{prompt}")
    else:
        update.message.reply_text("No popular recipes were obtained.")

def recipe_details(update: Update, context: CallbackContext) -> None:
    """Query recipe details"""
    try:
        recipe_name = context.args[0]
        question = f"Detailed cooking steps for {recipe_name}"
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /detail <recipe_name>')

def diet_plan(update: Update, context: CallbackContext) -> None:
    """Customize a diet plan"""
    try:
        duration = context.args[0]
        calories = context.args[1]
        question = f"Develop a {duration} diet plan with a daily calorie limit of {calories} calories."
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /plan <duration> <calories>')

def ingredient_recommendation(update: Update, context: CallbackContext) -> None:
    """Recommend recipes based on ingredients"""
    try:
        ingredients = " ".join(context.args)
        question = f"What recipes can be made using {ingredients}"
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /recommend <ingredient1> <ingredient2>...')

def collect_recipe(update: Update, context: CallbackContext) -> None:
    """Collect a recipe"""
    try:
        recipe_name = context.args[0]
        # Here you can add collection logic, such as storing in redis
        global redis1  # Access the global redis1 variable
        redis1.sadd(f"user_{update.message.from_user.id}_favorites", recipe_name)
        update.message.reply_text(f"The recipe {recipe_name} has been collected.")
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /collect <recipe_name>')

def view_history(update: Update, context: CallbackContext) -> None:
    """View the history (list of collected recipes)"""
    favorites = redis1.smembers(f"user_{update.message.from_user.id}_favorites")
    if favorites:
        favorites_text = "\n".join(favorites)
        update.message.reply_text(f"List of collected recipes:\n{favorites_text}\nEnter /detail <recipe_name> to get its specific cooking method.")
    else:
        update.message.reply_text("No recipes have been collected yet.")

def nutrition_analysis(update: Update, context: CallbackContext) -> None:
    """Nutrition analysis"""
    try:
        recipe_name = context.args[0]
        question = f"Nutritional analysis of {recipe_name}"
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /nutrition <recipe_name>')

def equipped_chatgpt(update, context): 
    """Direct Q&A processing"""
    help_text = (
        "Hello, I'm a professional recipe recommendation bot. Here are the functions I offer:\n"
        "1. Random popular recipe recommendation: Use /popular to get a randomly recommended popular recipe.\n"
        "2. Recipe details query: Use /detail <recipe_name> to get detailed information about a specific recipe.\n"
        "3. Diet plan customization: Use /plan <duration> <calories> to generate a multi - day diet plan.\n"
        "4. Ingredient - based recipe recommendation: Use /recommend <ingredient1> <ingredient2>... to get recipe recommendations based on the given ingredients.\n"
        "5. Recipe collection and history: Use /collect <recipe_name> to collect a recipe, and /history to view the list of collected recipes.\n"
        "6. Nutrition analysis: Use /nutrition <recipe_name> to get the nutritional analysis of a recipe.\n"
        "7. Delete a collected recipe: Use /delete <recipe_name> to delete a collected recipe.\n"
        "Enter /help to view detailed function usage, or you can directly ask questions to get answers."
    )
    question = update.message.text
    reply_message = chatgpt.submit(question)
    clean_message = clean_reply_message(reply_message)
    update.message.reply_text(clean_message)
    update.message.reply_text(help_text)

def delete_recipe(update: Update, context: CallbackContext) -> None:
    """Delete a collected recipe"""
    try:
        recipe_name = context.args[0]
        # Delete from redis
        redis1.srem(f"user_{update.message.from_user.id}_favorites", recipe_name)
        update.message.reply_text(f"The collected recipe {recipe_name} has been deleted.")
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /delete <recipe_name>')

if __name__ == '__main__':
    main()
