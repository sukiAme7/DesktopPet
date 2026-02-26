import yaml

class Config:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(self, key, Config(value))
            else:
                setattr(self, key, value)

def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        config_dict=yaml.safe_load(f)
    return Config(config_dict)

