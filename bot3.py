import os
import requests
from telegram.ext import ApplicationBuilder, MessageHandler, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
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
        },
        timeout=30
    )
    data = response.json()
    results = []
    for r in data.get("results", []):
        results.append("- " + r["title"] + ": " + r["content"][:300] + "\n  Источник: " + r["url"])
    return "\n\n".join(results)

async def handle_message(update, context):
    user_query = update.message.text
    await update.message.reply_text("Ищу информацию...")

    search_results = search_web(user_query)

    headers = {
        "Authorization": "Bearer " + OPENROUTER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct",
        "messages": [
            {
                "role": "system",
                "content": "Ты аналитик FMCG рынка. Отвечай на русском языке. Давай конкретные факты. Используй только предоставленные данные поиска."
            },
            {
                "role": "user",
                "content": "Вопрос: " + user_query + "\n\nДанные из поиска:\n" + search_results
            }
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        raw = response.json()
        if "choices" in raw:
            answer = raw["choices"][0]["message"]["content"]
        else:
            answer = "Ответ API: " + str(raw)[:1000]
    except Exception as e:
        answer = "Ошибка: " + str(e)

    await update.message.reply_text(answer)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
