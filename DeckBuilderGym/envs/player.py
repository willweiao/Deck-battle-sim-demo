from card import EffectCalculator
from player_strategy import SimpleStrategy

class Player:
    def __init__(self, name, hp, energy, max_hp=None, max_energy=3, buffs=None, debuffs=None, strategy=None):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp or hp
        self.energy = energy
        self.max_energy = max_energy
        self.buffs = buffs or {}
        self.debuffs = debuffs or {}
        self.strategy = strategy or SimpleStrategy()
        self.block = 0
    
    def begin_turn(self):
        self.block = 0
        self.energy = self.max_energy
        self.tick_buffs_and_debuffs()
    
    def end_turn(self):
        for name in list(self.buffs.keys()):
            if self.buffs[name].get("temporary"):
                del self.buffs[name]
        for name in list(self.debuffs.keys()):
            if self.debuffs[name].get("temporary"):
                del self.debuffs[name]

    def take_damage(self, amount):
        damage = max(0, amount - self.block)
        self.hp -= damage
        self.block = max(0, self.block - amount)
    
    def gain_block(self, amount):
        self.block += amount
    
    def apply_buff(self, name, value, duration=None):
        if name in self.buffs:
            self.buffs[name]["value"] += value
            if duration:
                self.buffs[name]["duration"] = duration
        else:
            self.buffs[name] = {"value": value}
            if duration:
                self.buffs[name]["duration"] = duration

    def apply_debuff(self, name, value, duration=None):
        if name in self.debuffs:
            self.debuffs[name]["value"] += value
            if duration:
                self.debuffs[name]["duration"] = duration
        else:
            self.debuffs[name] = {"value": value}
            if duration:
                self.debuffs[name]["duration"] = duration
    
    def gain_energy(self, amount):
        self.energy+=amount
    
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
    
    def tick_buffs_and_debuffs(self):
        for name in list(self.buffs.keys()):
            entry = self.buffs[name]

            if name == "Regen":
                self.heal(entry["value"])

            if "duration" in entry:
                entry["duration"] -= 1
                if entry["duration"] <= 0:
                    del self.buffs[name]

        for name in list(self.debuffs.keys()):
            entry = self.debuffs[name]
            if name == "Poison":
                damage = entry["value"]
                self.hp -= damage
                entry["value"] -= 1
                if entry["value"] <= 0:
                    del self.debuffs[name]
            else:
                entry["duration"] -= 1
                if entry["duration"] <= 0:
                    del self.debuffs[name]

    def play_cards(self, hand, enemies, battle):
        while True:
            card = self.strategy.select_card(hand, self, enemies, battle)
            if card is None:
                break

            target = self.strategy.select_target(card, self, enemies, battle)
            if target is None:
                break

            battle.play_card(card, self, target)

"""
# 可能需要修改以下的逻辑，我在battle类中定义了打牌以及回合中的逻辑，但是我想把选牌以及选取目标领出来做一个新的可维护的类，用组合优化的方式写一些可选的策略
class PlayStrategy:
    def decide_and_play(self, player, hand, enemies, battle):
        raise NotImplementedError


class ManualStrategy(PlayStrategy):
    def __init__(self, n=3):
        self.n = n
 
    def decide_and_play(self, player, hand, enemies, battle):
        cards_played = 0

        for card in hand[:]:
            if cards_played >= self.n:
                break
        
        if player.energy >= card.cost:
            target = None
            if enemies:
                target = enemies[0]

            card.apply(player, target)
            player.energy -= card.cost
            cards_played += 1
"""