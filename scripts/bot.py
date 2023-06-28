import asyncio
from typing import List

import aiohttp
import discord

from src.helper import (
    dmess_to_proxy_urls,
    gather_proxy_urls_to_dfiles,
    get_s_image_urls,
    get_vt_soup,
    preprocess_s_image_urls,
    split_into_sublist,
)

client = discord.Client()
TOKEN = ()


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    print(f"{message.content} from {message.author} at {message.created_at}")

    if message.content.startswith("$compact"):
        await message.channel.send("Please wait")
        image_messages: List[discord.Message] = []

        await message.channel.send("Compiling history")
        async for msg in message.channel.history():
            if msg.content.startswith("$content"):
                image_messages.append(msg)
        proxy_urls = dmess_to_proxy_urls(image_messages)

        await message.channel.send("Fetching and sending images")
        for sub_urls in split_into_sublist(proxy_urls, 9):
            async with aiohttp.ClientSession() as session:
                dfiles = await gather_proxy_urls_to_dfiles(session, sub_urls)

            await message.channel.send(files=dfiles)
            await asyncio.sleep(5)

    if message.content.startswith("$run"):
        print(message)
        print(message.content)
        await message.channel.send("Please wait")
        thread_number = message.content.split(" ")[1]
        await message.channel.send(f"Fetching {thread_number}")
        thread_soup = get_vt_soup(thread_number)
        await message.channel.send(f"Done fetching {thread_number}")
        s_image_urls = get_s_image_urls(thread_soup)
        await message.channel.send(f"Preparing to send {len(s_image_urls)} images")

        s_image_urls = preprocess_s_image_urls(s_image_urls)
        # await message.channel.send(s_image_urls[0])
        for image_url in s_image_urls:
            await message.channel.send(image_url)
            await asyncio.sleep(2)

    if message.content.startswith("$purge"):
        await message.channel.purge()


client.run(TOKEN)
