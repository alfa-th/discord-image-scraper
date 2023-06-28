import asyncio
import io
from re import findall
from typing import List, Optional

import aiohttp
import discord
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from PIL import Image

pattern = r"(https://(files|litter).catbox.moe/(\w{6}).(png|jpg))"


def get_s_image_urls(soup: BeautifulSoup):
    splitted_image_urls = []

    for post_tag in soup.select(".replyContainer"):
        assert isinstance(post_tag, Tag)
        # img_tag = post_tag.select_one(".fileThumb")

        # if isinstance(img_tag, Tag):
        #     image_urls.append(
        #         sub("//", "https://", img_tag.get("href"))
        #     )

        text = post_tag.get_text()
        matches = findall(pattern, text)

        post_urls = []
        for match in matches:
            post_urls.append(match[0])

        splitted_post_urls = [post_urls[x : x + 5] for x in range(0, len(post_urls), 5)]

        splitted_image_urls += splitted_post_urls

    return splitted_image_urls


def get_vt_soup(thread_number):
    url = f"https://boards.4channel.org/vt/thread/{thread_number}"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    return soup


def preprocess_s_image_urls(s_image_urls: List[List[str]]):
    for i in range(len(s_image_urls)):
        s_image_urls[i] = ["$content"] + s_image_urls[i]
        s_image_urls[i] = " \n".join(s_image_urls[i])

    return s_image_urls


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
        print(f"Given image has the size of {get_size_in_mb(img.getbuffer()):2f} MB")
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


if __name__ == "__main__":
    soup = get_vt_soup(48446494)
    image_urls = get_s_image_urls(soup)
    # image_urls = [image_url[1] for image_url in image_urls]
    # print(preprocess_image_urls(image_urls))
    print(image_urls)
    print([len(list_) for list_ in image_urls])
    print([preprocess_s_image_urls(image_urls)])
