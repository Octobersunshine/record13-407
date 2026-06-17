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

        collision_count = 0
        while short_code in self.url_map:
            if self.url_map[short_code] == long_url:
                return self.base_url + short_code
            collision_count += 1
            suffix_chars = "0123456789abcdefghijklmnopqrstuvwxyz"
            suffix = ""
            temp = collision_count
            while temp > 0:
                suffix = suffix_chars[temp % 36] + suffix
                temp = temp // 36
            if not suffix:
                suffix = suffix_chars[0]
            short_code = md5_hash[:6] + suffix

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

    print("=== 哈希碰撞测试 ===")
    test_url = "https://test-collision.example.com/page1"
    test_hash = hashlib.md5(test_url.encode()).hexdigest()
    test_prefix = test_hash[:6]
    print(f"测试URL: {test_url}")
    print(f"MD5前6位: {test_prefix}")

    existing_url = "https://already-exists.example.com/page"
    service.url_map[test_prefix] = existing_url
    print(f"预先注入碰撞: {test_prefix} -> {existing_url}")

    new_short = service.encode(test_url)
    print(f"碰撞后生成的短链接: {new_short}")
    new_code = new_short.replace(service.base_url, "")
    print(f"碰撞后短码: {new_code}")
    print(f"原URL还原: {service.decode(service.base_url + test_prefix)}")
    print(f"新URL还原: {service.decode(new_short)}")
    print(f"碰撞处理成功: {new_code != test_prefix and service.decode(new_short) == test_url}")

    print("\n=== 多次碰撞测试 ===")
    for i in range(5):
        suffix_chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        suffix = ""
        temp = i + 1
        while temp > 0:
            suffix = suffix_chars[temp % 36] + suffix
            temp = temp // 36
        if not suffix:
            suffix = suffix_chars[0]
        service.url_map[test_prefix + suffix] = f"https://mock{i}.example.com"
        print(f"预先注入碰撞: {test_prefix + suffix} -> https://mock{i}.example.com")

    multi_collision_url = "https://multi-collision.example.com/page2"
    multi_hash = hashlib.md5(multi_collision_url.encode()).hexdigest()
    multi_prefix = multi_hash[:6]

    service.url_map[multi_prefix] = "https://mock-multi-base.example.com"
    print(f"预先注入碰撞: {multi_prefix} -> https://mock-multi-base.example.com")

    for i in range(6):
        suffix_chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        suffix = ""
        temp = i
        while temp > 0:
            suffix = suffix_chars[temp % 36] + suffix
            temp = temp // 36
        if not suffix:
            suffix = suffix_chars[0]
        service.url_map[multi_prefix + suffix] = f"https://mock-multi{i}.example.com"
        print(f"预先注入碰撞: {multi_prefix + suffix} -> https://mock-multi{i}.example.com")

    multi_short = service.encode(multi_collision_url)
    multi_code = multi_short.replace(service.base_url, "")
    print(f"多次碰撞后短码: {multi_code}")
    print(f"短码长度: {len(multi_code)} (基础6位 + 后缀)")
    print(f"还原正确: {service.decode(multi_short) == multi_collision_url}")

    print("\n=== 重复URL测试 ===")
    same_short = service.encode(urls[0])
    print(f"重复URL生成短链: {same_short}")
    first_short = service.encode(urls[0])
    print(f"首次生成短链一致: {same_short == first_short}")

    print("\n当前存储映射:")
    for code, url in service.url_map.items():
        print(f"  {code} -> {url}")
