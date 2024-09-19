from evolution_algorithm import EvolutionAlgorithm
import json

def load_config(path):
    with open(path, 'r') as file:
        data = json.load(file)
    
    return data


if __name__ == "__main__":
    settings = load_config("static\\config.json")
    evolution = EvolutionAlgorithm(settings)
    evolution.simulate()
    