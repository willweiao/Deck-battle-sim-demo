import random

class SimpleStrategy:
    def select_card(self, hand, player, enemies, battle):
        # 依次打出所有可用卡
        for card in hand:
            if card.cost <= player.energy:
                return card
        return None  # 没牌可打

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