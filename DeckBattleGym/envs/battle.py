import os
import random


class VictoryCondition:
    def is_victory(self, player, enemies, turn):
        return all(e.hp <= 0 for e in enemies)

    def is_defeat(self, player, enemies, turn):
        return player.hp <= 0
    

class Battle:
    def __init__(self, player, enemies, deck,
                draw_per_turn:int=5, hand_limit:int=10,
                card_pool=None,
                victory_condition=None, 
                if_battle_log=False):
        self.player = player
        self.enemies = enemies
        self.deck = deck
        self.original_deck = deck
        self.draw_per_turn = draw_per_turn
        self.hand_limit = hand_limit
        self.card_pool = card_pool or {}
        self.card_id_map = {c["id"]: c for c in card_pool}
        self.victory_condition = victory_condition or VictoryCondition()
        self.if_battle_log= if_battle_log
        self.hand = []
        self.picked_card = []
        self.discard_pile = []
        self.exhaust_pile = []
        self.used_powers = []
        self.turn = 0
        self.log = []
        self.simulation_log={
            "turns":[]
        }
        self.running_log = None
        self.battle_count = self._get_battle_count()
    
    def _get_battle_count(self):
        counter = 1
        while os.path.exists(f"battle_log_{counter}.txt"):
            counter += 1
        return counter

    def log_state(self):
        enemy_states = [f"{enemy.name}(HP: {enemy.hp}, Block:{enemy.block}, Buffs: {enemy.buffs}, Debuffs: {enemy.debuffs})" for enemy in self.enemies]
        self.log.append(f"[Turn {self.turn} End] Player HP: {self.player.hp}, Block: {self.player.block}, Buffs: {self.player.buffs}, Debuffs: {self.player.debuffs}, Powers: {self.player.powers}")
        for e_state in enemy_states:
            self.log.append(f"Enemy: {e_state}")
    
    def battle_start(self):
        random.shuffle(self.deck)

    def draw_cards(self, num, hand_limit=10):
        drawn = 0
        drawn_cards = []
        if "NoDraw" in self.player.debuffs:
            if self.if_battle_log:
                self.log.append("Prevented from drawing cards this turn.")
            return
        else:
            for _ in range(num):
                if len(self.hand) >= hand_limit:
                    if self.if_battle_log:
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
                    self.player.after_draw_card(card, battle=self)
                else:
                    break

        if self.if_battle_log:
            self.log.append(f"[Turn {self.turn}] Drew cards: {', '.join(drawn_cards)}")
            card_names = [card.name for card in self.hand]
            self.log.append(f"[Turn {self.turn}] Hand cards: {', '.join(card_names)}")
        return drawn
    
    def play_card(self, card, user, targets=None):
        if not isinstance(targets, list):
            targets = [targets]
        if self.if_battle_log:
            if targets:
                target_names = ", ".join(t.name for t in targets)
                target_info = f"targeting {target_names}"
            else:
                target_info = "with no target"
            self.log.append(f"[Play] {user.name} plays {card.name} {target_info}.")
        else:
            target_ids = [getattr(t, "id", "unknown") for t in targets]   
            self.running_log["actions"].append({
                "card":card.id,
                "targets":target_ids
            })
        #print(f"DEBUG: battle play card target {[t.name for t in targets]}")
        self.picked_card.append(card)
        if card in self.hand:
            self.hand.remove(card)
        card.apply(user, targets, battle=self)
        if card.cost =="x":
            actual_cost=user.energy
        else:
            actual_cost=card.cost
        user.energy -= actual_cost

        if getattr(card, 'exhaust', False):
            self.exhaust_pile.append(card)
            user.trigger_on_exhaust(self)
        elif getattr(card, 'shuffle_back', False):
            index = random.randint(0, len(self.deck))
            self.deck.insert(index, card)
        elif card.card_type == "power":
            self.used_powers.append(card)
        else:
            self.discard_pile.append(card)

        #if card in self.hand:
        #    self.hand.remove(card)

    def player_turn(self):
        self.player.begin_turn(self)
        if self.if_battle_log:
            self.log.append(f"\n[Turn {self.turn}] Player's turn begins.")
            self.draw_cards(self.draw_per_turn)
        else:
            self.draw_cards(self.draw_per_turn)
            self.running_log = {
                "turn": self.turn,
                "hand": [card.id for card in self.hand],
                "actions":[]
                }
        self.player.play_cards(self.hand, self.enemies, self)
        self.player.end_turn(self)
        if self.if_battle_log:
            card_names = [card.name for card in self.hand]
            self.log.append(f"[EndTurn] Hand cards: {', '.join(card_names)}")
        if not self.if_battle_log:
            self.running_log["hp_left"]=self.player.hp
            self.simulation_log["turns"].append(self.running_log)
    
    def enemy_turn(self):
        if self.if_battle_log:
            self.log.append(f"[Turn {self.turn}] Enemies' turn begins.")
        for enemy in self.enemies:
            if enemy.hp > 0:
                if enemy.die_after_turn is not None and self.turn >= enemy.die_after_turn:
                    enemy.hp = 0
                    if self.if_battle_log:
                        self.log.append(f"[AutoDeath] {enemy.name} dies automatically after turn {self.turn}.")
                    continue
                enemy.begin_turn(self)
                enemy.perform_action(self)
                enemy.end_turn(self)
        
    def cleanup(self):
        cards_to_discard = []
        cards_to_exhaust = []

        for card in self.hand:
            if card.name == "Burn":
                self.player.take_damage(2)
                cards_to_discard.append(card)
            elif getattr(card, 'ethereal', False):
                cards_to_exhaust.append(card)
                self.player.trigger_on_exhaust(self)
            elif not getattr(card, 'retain', False):
                cards_to_discard.append(card)

        for card in cards_to_discard:
            self.hand.remove(card)
            self.discard_pile.append(card)

        for card in cards_to_exhaust:
            self.hand.remove(card)
            self.exhaust_pile.append(card)
    

    def cleanup_after_battle(self):
        self.deck = self.original_deck[:]
        self.hand = []
        self.discard_pile.clear()
        self.exhaust_pile.clear()
        self.used_powers.clear()

    def check_victory(self):
        if self.victory_condition.is_victory(self.player, self.enemies, self.turn):
            if self.if_battle_log:
                self.log.append("[Battle] You win!")
            else:
                self.simulation_log["win"]=True
            return True
        if self.victory_condition.is_defeat(self.player, self.enemies, self.turn):
            if self.if_battle_log:
                self.log.append("[Battle] You lose!")
            else:
                self.simulation_log["win"]=False
            return True
        return False

    def save_log_to_file(self):
        filename = f"battle_log_{self.battle_count}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for entry in self.log:
                f.write(entry + "\n")

    def run(self):
        self.battle_start()
        while True:
            self.turn += 1
            if self.if_battle_log:
                self.log.append(f"\n--- Turn {self.turn} ---")
            self.player_turn()
            if self.check_victory():
                break
            self.cleanup()
            self.enemy_turn()
            if self.check_victory():
                break
            if self.if_battle_log:
                self.log_state()
        self.simulation_log["final_hp"] = self.player.hp
        self.simulation_log["turns_taken"] = self.turn
        self.cleanup_after_battle()
        
        if "win" not in self.simulation_log:
            self.simulation_log["win"] = False

        if self.if_battle_log:
            for entry in self.log:
                print(entry)
            self.save_log_to_file()