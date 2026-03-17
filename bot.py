import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
TOGETHER_API_KEY = os.environ["TOGETHER_API_KEY"]
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]

def search_web(query):
    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True
        }
    )
    data = response.json()
    results = []
    for r in data.get("results", []):
        results.append(f"- {r['title']}: {r['content'][:300]}\n  Источник: {r['url']}")
    return "\n\n".join(results)

async def handle_message(update, context):
    user_query = update.message.text
    await update.message.reply_text("Ищу информацию...")

    search_results = search_web(user_query)

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "messages": [
            {
                "role": "system",
                "content": "Ты аналитик FMCG рынка. Отвечай на русском языке. Давай конкретные факты. Используй только предоставленные данные поиска."
            },
            {
                "role": "user",
                "content": f"Вопрос: {user_query}\n\nДанные из поиска:\n{search_results}"
            }
        ]
    }

    try:
        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",
