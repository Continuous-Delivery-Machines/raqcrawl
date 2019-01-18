import os


def read_config_from_environment(stage: str = "PROD"):
    base = "RAQ_CRAWLER_" + stage + "_"
    conf = dict()
    for key in (k for k in os.environ if k.startswith(base)):
        print(key)
        name = key[len(base):].lower()
        conf[name] = os.environ[key]
    return conf


if __name__ == '__main__':
    config = read_config_from_environment('DEV')
    print(config)
