import hashlib


class ShortURLService:
    def __init__(self):
        self.url_map = {}
        self.base_url = "http://short.cn/"

    def encode(self, long_url: str) -> str:
        if long_url in self.url_map.values():
            for short_code, stored_url in self.url_map.items():
                if stored_url == long_url:
                    return self.base_url + short_code

        md5_hash = hashlib.md5(long_url.encode()).hexdigest()
        short_code = md5_hash[:6]

        if short_code in self.url_map:
            suffix = 1
            while True:
                new_code = short_code + str(suffix)
                if new_code not in self.url_map:
                    short_code = new_code
                    break
                suffix += 1

        self.url_map[short_code] = long_url
        return self.base_url + short_code

    def decode(self, short_url: str) -> str:
        short_code = short_url.replace(self.base_url, "")
        return self.url_map.get(short_code, "Not Found")


if __name__ == "__main__":
    service = ShortURLService()

    urls = [
        "https://www.example.com/very/long/path/to/page/1",
        "https://www.python.org/doc/python-tutorial",
        "https://github.com/user/repo/blob/main/src/main.py",
    ]

    for url in urls:
        short = service.encode(url)
        print(f"长链接: {url}")
        print(f"短链接: {short}")
        recovered = service.decode(short)
        print(f"还原后: {recovered}\n")

    print("当前存储映射:")
    for code, url in service.url_map.items():
        print(f"  {code} -> {url}")
