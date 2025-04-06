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
    
    # 创建updater实例
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
    # and why things do not work as expected Meanwhile, update your config.ini as:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                        level=logging.INFO)
    
    # 注册命令处理程序
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

    # 注册消息处理程序
    global chatgpt
    chatgpt = HKBU_ChatGPT(config)
    chatgpt_handler = MessageHandler(Filters.text & (~Filters.command), 
                                     equipped_chatgpt)
    dispatcher.add_handler(chatgpt_handler)

    # 启动机器人
    updater.start_polling()
    updater.idle()

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "你好，我是一个专业的菜品推荐机器人，提供有以下的功能供你选择：\n"
        "1. 随机中式菜品推荐：使用 /popular 来随机获取一个推荐中式菜品。\n"
        "2. 菜品详情查询：使用 /detail 菜品名称 来获取指定菜品的详细信息。\n"
        "3. 饮食计划定制：使用 /plan 时长 热量（卡路里） 来生成多日饮食计划。\n"
        "4. 食材推荐：使用 /recommend 食材1 食材2...  来获取相应的菜品推荐。\n"
        "5. 收藏与历史记录：使用 /collect 菜品名称 来收藏菜品，/history 来查看收藏的菜品列表。\n"
        "6. 健康分析：使用 /nutrition 菜品名称 来获取菜品的营养成分分析。\n"
        "7. 删除收藏菜品：使用 /delete 菜品名称 来删除收藏的菜品。\n"
        "你也可以直接通过问答来获得答案。"
    )
    update.message.reply_text(help_text)

def clean_reply_message(message):
    """清理回复消息，去除 #、* 和 - 符号"""
    return message.replace('#', '').replace('*', '').replace('-', '')

def recipe_generation(update: Update, context: CallbackContext) -> None:
    """生成菜品"""
    try:
        keywords = " ".join(context.args)
        question = f"生成包含 {keywords} 的菜品列表"
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /recipe 食材 口味')

# 修改热门菜品推荐函数
def popular_recipes(update: Update, context: CallbackContext) -> None:
    """获取一个中式菜品"""
    question = "给我随机生成一个推荐的中式菜品，要求只返回菜品名称且每次询问你都要返回一个新的菜品（不能与之前的重复）。"
    reply_message = chatgpt.submit(question)
    # 尝试更精准地提取菜品名称，假设菜品名称以数字编号或换行分隔
    import re
    # 匹配可能的编号格式，如 "1. 菜品名称" 或直接的菜品名称
    pattern = r'(?:\d+\.\s*)?([^\n]+)'
    recipes = re.findall(pattern, reply_message)
    if recipes:
        random_recipe = random.choice(recipes)
        prompt = f"输入 /detail {random_recipe} 来获取此菜品的做法。"
        update.message.reply_text(f"随机推荐的热门菜品是：{random_recipe}\n{prompt}")
    else:
        update.message.reply_text("未获取到热门菜品。")

def recipe_details(update: Update, context: CallbackContext) -> None:
    """查询菜品详情"""
    try:
        recipe_name = context.args[0]
        question = f"{recipe_name} 的详细制作步骤"
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /detail 菜品名称')

def diet_plan(update: Update, context: CallbackContext) -> None:
    """定制饮食计划"""
    try:
        duration = context.args[0]
        calories = context.args[1]
        question = f"制定 {duration} 的饮食计划，每天热量控制在 {calories} 卡以内"
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /plan 时长 热量')

def ingredient_recommendation(update: Update, context: CallbackContext) -> None:
    """食材推荐菜品"""
    try:
        ingredients = " ".join(context.args)
        question = f"使用 {ingredients} 可以制作哪些菜品"
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /recommend 食材1 食材2...')

def collect_recipe(update: Update, context: CallbackContext) -> None:
    """收藏菜品"""
    try:
        recipe_name = context.args[0]
        # 这里可以添加收藏逻辑，例如存储到 redis
        global redis1  # Access the global redis1 variable
        redis1.sadd(f"user_{update.message.from_user.id}_favorites", recipe_name)
        update.message.reply_text(f"已收藏菜品：{recipe_name}")
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /collect 菜品名称')

def view_history(update: Update, context: CallbackContext) -> None:
    """查看历史记录（收藏的菜品列表）"""
    favorites = redis1.smembers(f"user_{update.message.from_user.id}_favorites")
    if favorites:
        favorites_text = "\n".join(favorites)
        update.message.reply_text(f"收藏的菜品列表：\n{favorites_text}\n可输入 /detail 菜品名称 来获取其具体做法")
    else:
        update.message.reply_text("暂无收藏的菜品。")

def nutrition_analysis(update: Update, context: CallbackContext) -> None:
    """营养分析"""
    try:
        recipe_name = context.args[0]
        question = f"{recipe_name} 的营养成分分析"
        reply_message = chatgpt.submit(question)
        clean_message = clean_reply_message(reply_message)
        update.message.reply_text(clean_message)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /nutrition 菜品名称')

def equipped_chatgpt(update, context): 
    """直接问答处理"""
    help_text = (
        "你好，我是一个专业的菜品推荐机器人，提供有以下的功能供你选择：\n"
        "1. 随机中式菜品推荐：使用 /popular 来随机获取一个推荐中式菜品。\n"
        "2. 菜品详情查询：使用 /detail 菜品名称 来获取指定菜品的详细信息。\n"
        "3. 饮食计划定制：使用 /plan 时长 热量（卡路里） 来生成多日饮食计划。\n"
        "4. 食材推荐：使用 /recommend 食材1 食材2...  来获取相应的菜品推荐。\n"
        "5. 收藏与历史记录：使用 /collect 菜品名称 来收藏菜品，/history 来查看收藏的菜品列表。\n"
        "6. 健康分析：使用 /nutrition 菜品名称 来获取菜品的营养成分分析。\n"
        "7. 删除收藏菜品：使用 /delete 菜品名称 来删除收藏的菜品。\n"
        "输入 /help 查看详细功能用法，也可以依靠直接问答来获得答案。"
    )
    question = update.message.text
    reply_message = chatgpt.submit(question)
    clean_message = clean_reply_message(reply_message)
    update.message.reply_text(clean_message)
    update.message.reply_text(help_text)

def delete_recipe(update: Update, context: CallbackContext) -> None:
    """删除收藏的菜品"""
    try:
        recipe_name = context.args[0]
        # 从 redis 中删除
        redis1.srem(f"user_{update.message.from_user.id}_favorites", recipe_name)
        update.message.reply_text(f"已删除收藏的菜品：{recipe_name}")
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /delete 菜品名称')

if __name__ == '__main__':
    main()
