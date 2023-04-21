import discord
from discord.ext import commands

import json
import os
import openai
import requests
import server_message_history
from server_message_history import ServerMessageHistory

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

description = "The best bot ever!"

bot = commands.Bot(
    command_prefix="!H",
    descrtiption=description,
    intents=intents,
    case_insensitive=True
)

global model
global message_histories
message_histories = {}


@bot.event
async def on_ready():
    print(f"{bot.user} powered on!")
    with open('gpt_key', 'r') as f:
        gpt_key = f.read()
    # openai.organization("org-MLRPYyDJ6C8XJ64r1DulvAI1")
    openai.api_key = gpt_key
    global model
    model = "gpt-3.5-turbo"


def call_openai_api_using_lib(model_call, messages, max_tokens=200, n=1, stop=None):
    response = openai.ChatCompletion.create(
        engine=model_call,
        messages=messages,
        max_tokens=max_tokens,
        n=n,
        stop=stop
    )

    print(response)
    return response.choices[0].to_dict()


def call_openai_api_using_requests(model_call, messages, max_tokens=200, n=1, stop=None):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai.api_key}'
    }

    data = {
        'model': model_call,
        'messages': messages,
        'max_tokens': max_tokens,
        'n': n,
        'stop': stop
    }

    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(data))
    print("Response status code:", response.status_code)
    print("Response content:", response.json())
    return response.json()['choices'][0]


@bot.command(name="M")
async def hey_mai(ctx: commands.Context):
    content = ctx.author.name + ": " + ctx.message.content[len(ctx.prefix) + len(ctx.invoked_with):].strip()

    server_id = str(ctx.guild.id)
    if server_id not in message_histories:
        message_histories[server_id] = ServerMessageHistory(server_id)

    server_history = message_histories[server_id]
    server_history.add_message({"role": "user", "content": content})

    messages = [{"role": "system", "content": "You are a member of a discord server and trying to fit in"}]
    messages.extend(server_history.message_history)

    response = call_openai_api_using_requests(model, messages)

    reply = response['message']['content']

    server_history.add_message({"role": "assistant", "content": reply})

    await ctx.channel.send(reply)


with open('discord_key', 'r') as f:
    discord_key = f.read()
bot.run(discord_key)
