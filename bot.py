import discord
import asyncio
import io
import sys
import aiohttp
from PIL import Image
from scraper import get_s_image_urls, get_vt_soup, preprocess_s_image_urls
from typing import List, Optional

TOKEN = ()

client = discord.Client()


def convert_to_compressed_jpg(ori_bytesio, quality=75):
    orig_img = Image.open(ori_bytesio)
    new_bytesio = io.BytesIO()

    orig_img.convert("RGB").save(
        fp=new_bytesio, format="JPEG", quality=quality, optimize=True
    )

    ori_bytesio.seek(0)
    new_bytesio.seek(0)

    return new_bytesio


def get_size_in_mb(buffer: memoryview):
    size_in_bytes = buffer.nbytes

    return size_in_bytes / (1024 * 1024)


async def fetch_as_dfile(
    session: aiohttp.ClientSession, url: str
) -> Optional[discord.File]:
    async with session.get(url) as resp:
        img = io.BytesIO(await resp.read())
        print(
            "Given image has the size of"
            f" {get_size_in_mb(img.getbuffer()):2f} MB"
        )
        try:
            proc_img = convert_to_compressed_jpg(img, 95)
            print(
                "Compressed image has the size of"
                f" {get_size_in_mb(proc_img.getbuffer()):2f} MB"
            )
            return discord.File(proc_img, url)
        except Exception as e:
            print(e)
            print(url)

            return None


async def proxy_urls_to_dfiles(
    session: aiohttp.ClientSession, urls: List[str]
) -> List[discord.File]:
    results = []

    for i in range(len(urls)):
        print(f"Fetching {i}-th URL")
        results.append(await fetch_as_dfile(session, urls[i]))

    return results


async def gather_proxy_urls_to_dfiles(
    session: aiohttp.ClientSession, urls: List[str]
) -> List[discord.File]:
    tasks = []
    for url in urls:
        task = asyncio.create_task(fetch_as_dfile(session, url))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    results = [x for x in results if x is not None]
    return results


def dmess_to_proxy_urls(
    messages: List[discord.Message],
) -> List[str]:
    proxy_urls = []
    for msg in messages:
        for embed in msg.embeds:
            proxy_urls.append(embed.thumbnail.proxy_url)

    return proxy_urls


def split_into_sublist(list_: List, n=9):
    return [list_[x : x + n] for x in range(0, len(list_), n)]


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
        await message.channel.send(
            f"Preparing to send {len(s_image_urls)} images"
        )

        s_image_urls = preprocess_s_image_urls(s_image_urls)
        # await message.channel.send(s_image_urls[0])
        for image_url in s_image_urls:
            await message.channel.send(image_url)
            await asyncio.sleep(2)

    if message.content.startswith("$purge"):
        await message.channel.purge()


client.run(TOKEN)
