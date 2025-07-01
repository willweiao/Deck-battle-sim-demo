import random

class SimpleStrategy:
    def select_card(self, hand, player, enemies, battle):
        for card in hand:
            if not getattr(card, "playable", True):
                continue

            if card.cost == "x":
                return card
            elif isinstance(card.cost, (int, float)) and card.cost <= player.energy:
                return card
        return None

    def select_target(self, card, player, enemies, battle):
        sel = card.target_selector
        alive = [e for e in enemies if e.hp > 0]

        if sel == "all_enemies":
            return alive
        elif sel == "random_enemy":
            return [random.choice(alive)] if alive else []
        elif sel == "lowest_hp":
            return [min(alive, key=lambda e: e.hp)] if alive else []
        elif sel == "single_enemy":
            target = next((e for e in alive), None)
            return [target] if target else []
        elif sel == "self":
            return [player]
        else:
            raise ValueError(f"Unknown target_selector: {sel}")
        
class RandomStrategy:
    def select_card(self, hand, player, enemies, battle):
        can_play = [card for card in hand if card.cost <= player.energy and getattr(card, "playable", True)]
        return random.choice(can_play) if can_play else None

    def select_target(self, card, player, enemies, battle):
        sel = card.target_selector
        alive = [e for e in enemies if e.hp > 0]

        if sel == "all_enemies":
            return alive
        elif sel == "random_enemy":
            return [random.choice(alive)] if alive else []
        elif sel == "lowest_hp":
            return [min(alive, key=lambda e: e.hp)] if alive else []
        elif sel == "single_enemy":
            return [random.choice(alive)] if alive else []
        elif sel == "self":
            return [player]
        else:
            return []
        

class ManualStrategy:
    def select_card(self, hand, player, enemies, battle):
        return None 

    def select_target(self, card, player, enemies, battle):
        return []