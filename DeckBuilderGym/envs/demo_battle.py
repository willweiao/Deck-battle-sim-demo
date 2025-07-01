import random
from player import Player
from card import Card
from enemy import Enemy
from battle import Battle
from loader import load_card_pool,build_starting_deck, load_enemy_by_id


if __name__ == "__main__":
    card_pool = load_card_pool()
    deck = build_starting_deck(card_pool)
    player=Player(name="Hero", hp=50, energy=3)
    e1 = load_enemy_by_id("1")
    e2 = load_enemy_by_id("2")
    enemies=[e1, e2]
    battle = Battle(player, enemies, deck, card_pool=card_pool, if_battle_log=True)
    battle.run()