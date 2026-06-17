import hashlib
import time


class ShortURLService:
    def __init__(self, default_ttl: int = None):
        self.url_map = {}
        self.base_url = "http://short.cn/"
        self.default_ttl = default_ttl

    def _is_expired(self, entry: dict) -> bool:
        if entry["expire_at"] is None:
            return False
        return time.time() > entry["expire_at"]

    def _cleanup_expired(self):
        expired_codes = [
            code for code, entry in self.url_map.items()
            if self._is_expired(entry)
        ]
        for code in expired_codes:
            del self.url_map[code]
        return len(expired_codes)

    def encode(self, long_url: str, ttl: int = None) -> str:
        self._cleanup_expired()

        effective_ttl = ttl if ttl is not None else self.default_ttl
        expire_at = time.time() + effective_ttl if effective_ttl else None

        for short_code, entry in self.url_map.items():
            if not self._is_expired(entry) and entry["url"] == long_url:
                return self.base_url + short_code

        md5_hash = hashlib.md5(long_url.encode()).hexdigest()
        short_code = md5_hash[:6]

        collision_count = 0
        while short_code in self.url_map:
            entry = self.url_map[short_code]
            if not self._is_expired(entry) and entry["url"] == long_url:
                return self.base_url + short_code
            if self._is_expired(entry):
                break
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

        self.url_map[short_code] = {
            "url": long_url,
            "expire_at": expire_at,
            "created_at": time.time()
        }
        return self.base_url + short_code

    def decode(self, short_url: str) -> str:
        self._cleanup_expired()
        short_code = short_url.replace(self.base_url, "")
        entry = self.url_map.get(short_code)
        if entry is None:
            return "Not Found"
        if self._is_expired(entry):
            del self.url_map[short_code]
            return "Not Found (Expired)"
        return entry["url"]

    def get_expire_info(self, short_url: str) -> dict:
        short_code = short_url.replace(self.base_url, "")
        entry = self.url_map.get(short_code)
        if entry is None:
            return {"error": "Not Found"}
        if self._is_expired(entry):
            return {"error": "Expired"}
        return {
            "url": entry["url"],
            "created_at": entry["created_at"],
            "expire_at": entry["expire_at"],
            "ttl_remaining": int(entry["expire_at"] - time.time()) if entry["expire_at"] else None
        }


if __name__ == "__main__":
    service = ShortURLService()
    now = time.time()

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
    service.url_map[test_prefix] = {"url": existing_url, "expire_at": None, "created_at": now}
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
        service.url_map[test_prefix + suffix] = {"url": f"https://mock{i}.example.com", "expire_at": None, "created_at": now}
        print(f"预先注入碰撞: {test_prefix + suffix} -> https://mock{i}.example.com")

    multi_collision_url = "https://multi-collision.example.com/page2"
    multi_hash = hashlib.md5(multi_collision_url.encode()).hexdigest()
    multi_prefix = multi_hash[:6]

    service.url_map[multi_prefix] = {"url": "https://mock-multi-base.example.com", "expire_at": None, "created_at": now}
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
        service.url_map[multi_prefix + suffix] = {"url": f"https://mock-multi{i}.example.com", "expire_at": None, "created_at": now}
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

    print("\n=== TTL 过期功能测试 ===")
    ttl_service = ShortURLService()

    ttl_url_1 = "https://expire-test-1.example.com"
    ttl_url_2 = "https://expire-test-2.example.com"
    ttl_url_3 = "https://expire-test-3.example.com"

    short_1 = ttl_service.encode(ttl_url_1, ttl=2)
    short_2 = ttl_service.encode(ttl_url_2, ttl=3600)
    short_3 = ttl_service.encode(ttl_url_3)

    print(f"短链1 (2秒过期): {short_1}")
    print(f"短链2 (1小时过期): {short_2}")
    print(f"短链3 (永不过期): {short_3}")

    print("\n立即查询:")
    print(f"  短链1: {ttl_service.decode(short_1)}")
    info = ttl_service.get_expire_info(short_1)
    print(f"  过期信息: 剩余TTL={info['ttl_remaining']}秒")
    print(f"  短链2: {ttl_service.decode(short_2)}")
    print(f"  短链3: {ttl_service.decode(short_3)}")

    print("\n等待1秒...")
    time.sleep(1)
    print(f"  短链1: {ttl_service.decode(short_1)}")
    info = ttl_service.get_expire_info(short_1)
    print(f"  过期信息: 剩余TTL={info['ttl_remaining']}秒")

    print("\n等待2秒 (短链1应该过期)...")
    time.sleep(2)
    print(f"  短链1: {ttl_service.decode(short_1)}")
    print(f"  短链2: {ttl_service.decode(short_2)}")
    print(f"  短链3: {ttl_service.decode(short_3)}")
    info = ttl_service.get_expire_info(short_1)
    print(f"  短链1过期信息: {info}")

    print("\n=== 过期条目复用测试 ===")
    expired_short = ttl_service.encode(ttl_url_1, ttl=1)
    print(f"生成新短链: {expired_short}")
    time.sleep(1.5)
    print(f"过期后查询: {ttl_service.decode(expired_short)}")
    reused_short = ttl_service.encode(ttl_url_1, ttl=100)
    print(f"重新编码相同URL: {reused_short}")
    print(f"短码复用: {expired_short == reused_short}")

    print("\n=== 默认TTL测试 ===")
    default_ttl_service = ShortURLService(default_ttl=5)
    default_url = "https://default-ttl.example.com"
    default_short = default_ttl_service.encode(default_url)
    info = default_ttl_service.get_expire_info(default_short)
    print(f"默认TTL=5秒, 实际剩余: {info['ttl_remaining']}秒")
    print(f"查询正常: {default_ttl_service.decode(default_short) == default_url}")

    print("\n=== 主动清理测试 ===")
    cleanup_service = ShortURLService()
    for i in range(3):
        url = f"https://cleanup-test-{i}.example.com"
        cleanup_service.encode(url, ttl=1)
    print(f"清理前条目数: {len(cleanup_service.url_map)}")
    time.sleep(1.5)
    cleaned = cleanup_service._cleanup_expired()
    print(f"清理过期条目数: {cleaned}")
    print(f"清理后条目数: {len(cleanup_service.url_map)}")

    print("\n当前存储映射:")
    for code, entry in service.url_map.items():
        expire_str = "永不过期" if entry["expire_at"] is None else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["expire_at"]))
        print(f"  {code} -> {entry['url']} (过期: {expire_str})")
