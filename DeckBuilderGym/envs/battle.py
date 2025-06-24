import os
import random
from typing import List     


class VictoryCondition:
    def is_victory(self, player, enemies, turn):
        return all(e.hp <= 0 for e in enemies)

    def is_defeat(self, player, enemies, turn):
        return player.hp <= 0
    

class Battle:
    def __init__(self, player, enemies, deck, draw_per_turn:int=5, hand_limit:int=10, victory_condition=None):
        self.player = player
        self.enemies = enemies
        self.deck = deck
        self.original_deck = deck
        self.hand_limit = hand_limit
        self.draw_per_turn = draw_per_turn
        self.hand = []
        self.discard_pile = []
        self.exhaust_pile = []
        self.used_powers = []
        self.turn = 0
        self.victory_condition = victory_condition or VictoryCondition()
        self.log = []
        self.battle_count = self._get_battle_count()
    
    def _get_battle_count(self):
        counter = 1
        while os.path.exists(f"battle_log_{counter}.txt"):
            counter += 1
        return counter

    def log_state(self):
        enemy_states = [f"{enemy.name}(HP: {enemy.hp}, Buffs: {enemy.buffs}, Debuffs: {enemy.debuffs})" for enemy in self.enemies]
        self.log.append(f"[Turn {self.turn} End] Player HP: {self.player.hp}, Buffs: {self.player.buffs}, Debuffs: {self.player.debuffs}")
        for e_state in enemy_states:
            self.log.append(f"Enemy: {e_state}")

    def draw_cards(self, num, hand_limit=10):
        drawn = 0
        drawn_cards = []
        for _ in range(num):
            if len(self.hand) >= hand_limit:
                self.log.append("[Draw] Hand limit reached. Cannot draw more cards.")
                break

            if not self.deck and self.discard_pile:
                self.deck = self.discard_pile[:]
                random.shuffle(self.deck)
                self.discard_pile.clear()
            
            if self.deck:
                card = self.deck.pop()
                self.hand.append(card)
                drawn_cards.append(card.name)
                drawn += 1
            else:
                break

        self.log.append(f"[Turn {self.turn}] Drew cards: {', '.join(drawn_cards)}")
        return drawn
    
    def play_card(self, card, user, target=None):
        target_info = f"targeting {target.name}" if target else "with no target"
        self.log.append(f"[Play] {user.name} plays {card.name} {target_info}.")
        card.apply(user, target, battle=self)
        user.energy -= card.cost

        if getattr(card, 'exhaust', False):
            self.exhaust_pile.append(card)
        elif getattr(card, 'shuffle_back', False):
            index = random.randint(0, len(self.deck))
            self.deck.insert(index, card)
        elif card.card_type == "power":
            self.used_powers.append(card)
        else:
            self.discard_pile.append(card)

        if card in self.hand:
            self.hand.remove(card)

    def player_turn(self):
        self.player.begin_turn()
        self.log.append(f"\n[Turn {self.turn}] Player's turn begins.")
        self.draw_cards(self.draw_per_turn)
        self.player.play_cards(self.hand, self.enemies, self)
    
    def enemy_turn(self):
        self.log.append(f"[Turn {self.turn}] Enemies' turn begins.")
        for enemy in self.enemies:
            if enemy.hp > 0:
                enemy.begin_turn()
                enemy.perform_action(self.player)
        
    def cleanup(self):
        for card in self.hand:
            if getattr(card, 'ethereal', False):
                self.exhaust_pile.append(card)
            elif not getattr(card, 'retain', False):
                self.discard_pile.append(card)
        self.hand.clear()
    
    def cleanup_after_battle(self):
        self.deck = self.original_deck[:]
        self.hand = []
        self.discard_pile.clear()
        self.exhaust_pile.clear()
        self.used_powers.clear()

    def check_victory(self):
        if self.victory_condition:
            return self.victory_condition.check(self.player, self.enemies)
        return all(enemy.hp <= 0 for enemy in self.enemies)

    def save_log_to_file(self):
        filename = f"battle_log_{self.battle_count}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for entry in self.log:
                f.write(entry + "\n")

    def run(self):
        while True:
            self.turn += 1
            self.log.append(f"\n--- Turn {self.turn} ---")
            self.player_turn()
            if self.check_victory():
                self.log.append("[Battle] You win!")
                break
            self.enemy_turn()
            if self.player.hp <= 0:
                self.log.append("[Battle] You lose!")
                break
            self.cleanup()
            self.log_state()
        
        self.cleanup_after_battle()

        for entry in self.log:
            print(entry)

        self.save_log_to_file()