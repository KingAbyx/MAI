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
global histories_folder
histories_folder = "message_histories"
global message_histories
message_histories = {}
global token_limit
token_limit = 200
global message_limit
message_limit = 100


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
    return response.json()


@bot.command(name="setup")
async def setup(ctx: commands.Context, system, user, assistant):
    server_id = str(ctx.guild.id)
    if server_id not in message_histories:
        message_histories[server_id] = ServerMessageHistory(server_id, histories_folder, message_limit)

    server_history = message_histories[server_id]
    server_history.frame = [{"role": "system", "content": system},
                            {"role": "user", "content": user},
                            {"role": "assistant", "content": assistant}]
    server_history.save_frame_messages()

    await ctx.channel.send("Setup complete!")


@bot.command(name="edit")
async def edit(ctx: commands.Context, change, value):
    server_id = str(ctx.guild.id)
    if server_id not in message_histories:
        await ctx.channel.send("Setup wasn't completed!")
        return

    server_history = message_histories[server_id]
    match change:
        case "system":
            server_history.frame[0]["content"] = value
            await ctx.channel.send(f"System message was changed to: {value}")
        case "user":
            server_history.frame[1]["content"] = value
            await ctx.channel.send(f"User message was changed to: {value}")
        case "assistant":
            server_history.frame[2]["content"] = value
            await ctx.channel.send(f"Assistant message was changed to: {value}")
        case other:
            await ctx.channel.send("Syntax Error!")
            return
    server_history.save_frame_messages()
    server_history.save_message_history()
    message_histories.pop(server_id)
    load_server_from_storage(server_id)
    return


def load_server_from_storage(server_id):
    if server_id in message_histories:
        return True
    elif os.path.exists(os.path.join(histories_folder, f'{server_id}_history.json')) and os.path.exists(os.path.join(histories_folder, f'{server_id}_frame.json')):
        message_histories[server_id] = ServerMessageHistory(server_id, histories_folder, message_limit)
        return True
    else:
        return False


@bot.command(name="M")
async def hey_mai(ctx: commands.Context):
    content = ctx.author.name + ": " + ctx.message.content[len(ctx.prefix) + len(ctx.invoked_with):].strip()

    server_id = str(ctx.guild.id)
    if not load_server_from_storage(server_id):
        await ctx.channel.send("Setup not completed!")
        return

    server_history = message_histories[server_id]
    server_history.add_message({"role": "user", "content": content})

    messages = server_history.frame
    messages.extend(server_history.message_history)
    # more fucking framing
    messages.insert(len(messages) - 1, server_history.frame[2])

    response = call_openai_api_using_requests(model, messages)

    if not response.status_code == 200:
        error_data = response.json()
        error_code = error_data.get("error", {}).get("code", None)
        error_message = error_data.get("error", {}).get("message", None)
        await ctx.send(f"API call failed with error code: {error_code}, message: {error_message}")

    response = response['choices'][0]
    reply = response['message']['content']

    server_history.add_message({"role": "assistant", "content": reply})

    await ctx.channel.send(reply)


with open('discord_key', 'r') as f:
    discord_key = f.read()
bot.run(discord_key)
