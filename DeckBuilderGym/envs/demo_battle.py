import os
import random
from player import Player
from card import Card
from enemy import Enemy
from battle import Battle
from loader import load_card_pool,build_starting_deck, load_enemy_by_id, load_deck_by_id, load_enemy_group


if __name__ == "__main__":
    card_pool = load_card_pool()
    #deck = build_starting_deck(card_pool)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    deck_json_path = os.path.join(base_dir, "data", "deck.json")
    enemygroup_json_path = os.path.join(base_dir, "data", "enemy_group.json")
    deck, _= load_deck_by_id(deck_json_path, "deck05", card_pool)   # debug deck
    player=Player(name="Hero", hp=50, energy=3)
    enemies, _ = load_enemy_group(enemygroup_json_path, "group00")
    battle = Battle(player, enemies, deck, card_pool=card_pool, if_battle_log=True)
    battle.run()