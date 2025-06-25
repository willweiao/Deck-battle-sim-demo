from card import EffectCalculator
from player_strategy import SimpleStrategy
from buff_n_debuff import apply_regen, tick_poison, tick_standard_duration

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
            if duration is not None:
                self.buffs[name]["duration"] += duration
        else:
            self.buffs[name] = {"value": value}
            if duration is not None:
                self.buffs[name]["duration"] = duration

    def apply_debuff(self, name, duration, value=None):
        if name in self.debuffs:
            self.debuffs[name]["duration"] += duration
            if value is not None:
                self.debuffs[name]["value"] += value
        else:
            self.debuffs[name] = {"duration": duration}
            if value is not None:
                self.debuffs[name]["value"] = value

    def gain_energy(self, amount):
        self.energy+=amount
    
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
    
    def tick_buffs_and_debuffs(self):
        # Buffs
        for name in list(self.buffs.keys()):
            entry = self.buffs[name]

            if name == "Regen":
                self.heal(entry["value"])

            if not tick_standard_duration(entry):
                del self.buffs[name]

        # Debuffs
        for name in list(self.debuffs.keys()):
            entry = self.debuffs[name]

            if name == "Poison":
                damage = entry["value"]
                self.hp -= damage
                entry["value"] -= 1
                if entry["value"] <= 0:
                    del self.debuffs[name]
            elif not tick_standard_duration(entry):
                del self.debuffs[name]


    def play_cards(self, hand, enemies, battle):
        while True:
            card = self.strategy.select_card(hand, self, enemies, battle)
            if card is None:
                break

            targets = self.strategy.select_target(card, self, enemies, battle)
            if not targets:
                break
            
            #print(f"DEBUG: play_cards target: {[t.name for t in targets]}")
            battle.play_card(card, self, targets)

