import discord
from discord.ext import commands

import json
import os
import openai
import requests
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
token_limit = 800


@bot.event
async def on_ready():
    print(f"{bot.user} powered on!")
    with open('gpt_key', 'r') as f:
        gpt_key = f.read()
    openai.api_key = gpt_key
    global model
    model = "gpt-3.5-turbo"


def call_openai_api_using_lib(model_call, messages, max_tokens=token_limit, n=1, stop=None):
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
        'stop': stop,
        'temperature': 0.9
    }

    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(data))
    print("Response status code:", response.status_code)
    print("Response content:", response.json())
    return response


@bot.command(name="setup")
async def setup(ctx: commands.Context, system, user, assistant):
    server_id = str(ctx.guild.id)
    if server_id not in message_histories:
        message_histories[server_id] = ServerMessageHistory(server_id, histories_folder)

    server_history = message_histories[server_id]
    server_history.frame = [{"role": "system", "content": system},
                            {"role": "user", "content": user},
                            {"role": "assistant", "content": assistant}]
    server_history.save_frame_messages()

    print("Setup complete!")
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
    print("Frame edited!")
    return


def load_server_from_storage(server_id):
    print("Server data loaded from Storage!")
    if server_id in message_histories:
        return True
    elif os.path.exists(os.path.join(histories_folder, f'{server_id}_history.json')) and os.path.exists(os.path.join(histories_folder, f'{server_id}_frame.json')):
        message_histories[server_id] = ServerMessageHistory(server_id, histories_folder)
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

    messages = server_history.frame + server_history.message_history + [server_history.frame[0]]

    response = call_openai_api_using_requests(model, messages)

    while response.status_code == 400:
        print("Trimming history by two, trying API call again")
        server_history.trim_message_history(False)
        server_history.trim_message_history(False)

        messages = server_history.frame + server_history.message_history + [server_history.frame[0]]

        response = call_openai_api_using_requests(model, messages)

    if not response.status_code == 200:
        error_data = response.json()
        error_code = error_data.get("error", {}).get("code", None)
        error_message = error_data.get("error", {}).get("message", None)
        print(f"API call failed with error code: {error_code}, message: {error_message}")
        await ctx.send(f"API call failed with error code: {error_code}, message: {error_message}")
        server_history.trim_message_history(True)
        return

    response = response.json()['choices'][0]
    reply = response['message']['content']

    server_history.add_message({"role": "assistant", "content": reply})

    await ctx.channel.send(reply)


@bot.command(name="remove")
async def remove_replied_message_pair(ctx: commands.Context):
    if ctx.message.reference is None or ctx.message.reference.resolved is None:
        await ctx.send("You must reply to a message to use this command.")
        return

    server_id = str(ctx.guild.id)
    if not load_server_from_storage(server_id):
        await ctx.channel.send("Setup not completed!")
        return

    server_history = message_histories[server_id]

    replied_message_content = ctx.message.reference.resolved.content
    message_index = next((i for i, message in enumerate(server_history.message_history) if
                          message['role'] == 'assistant' and message['content'] == replied_message_content), None)

    if message_index is None:
        await ctx.send("Could not find the replied-to message in the stored message history.")
        return

    try:
        server_history.remove_message_pair_by_index(message_index)
        await ctx.channel.send(
            f"Successfully removed message pair!")
    except ValueError as e:
        await ctx.channel.send(str(e))


@bot.command(name="clear_history")
async def clear_history(ctx: commands.Context):
    server_id = str(ctx.guild.id)
    if not load_server_from_storage(server_id):
        await ctx.channel.send("Setup not completed!")
        return

    server_history = message_histories[server_id]
    server_history.clear_message_history()
    await ctx.channel.send("Server history has been cleared.")


with open('discord_key', 'r') as f:
    discord_key = f.read()
bot.run(discord_key)
