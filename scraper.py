import requests
from re import sub, findall
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import List

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

        splitted_post_urls = [
            post_urls[x : x + 5] for x in range(0, len(post_urls), 5)
        ]

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


if __name__ == "__main__":
    soup = get_vt_soup(48446494)
    image_urls = get_s_image_urls(soup)
    # image_urls = [image_url[1] for image_url in image_urls]
    # print(preprocess_image_urls(image_urls))
    print(image_urls)
    print([len(list_) for list_ in image_urls])
    print([preprocess_image_urls(image_urls)])
