import random

class SimpleStrategy:
    def select_card(self, hand, player, enemies, battle):
        # 依次打出所有可用卡
        for card in hand:
            if card.cost <= player.energy:
                return card
        return None  # 没牌可打

    def select_target(self, card, player, enemies, battle):
        sel = card.effects[0].target_selector
        if sel == "all_enemies":
            return [e for e in enemies if e.hp > 0]
        elif sel == "random_enemy":
            return random.choice([e for e in enemies if e.hp > 0])
        elif sel == "lowest_hp":
            return min([e for e in enemies if e.hp > 0], key=lambda e: e.hp)
        else:  # 默认：第一个存活敌人
            return next((e for e in enemies if e.hp > 0), None)