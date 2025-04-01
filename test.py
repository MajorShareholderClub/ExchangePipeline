from common.setting.properties import get_symbol_collect_url

if __name__ == "__main__":
    urls = get_symbol_collect_url("upbit", "korea", "socket")
    print(urls)
