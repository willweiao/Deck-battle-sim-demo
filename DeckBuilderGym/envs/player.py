from card import EffectCalculator
from player_strategy import SimpleStrategy
from buff_n_debuff import apply_regen, apply_strength_gain, tick_poison, tick_standard_duration

class Player:
    def __init__(self, name, hp, energy, 
                 max_hp=None, 
                 max_energy=3, 
                 buffs=None, 
                 debuffs=None, 
                 powers=None, 
                 strategy=None):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp or hp
        self.energy = energy
        self.max_energy = max_energy
        self.buffs = buffs or {}
        self.debuffs = debuffs or {}
        self.powers = powers or {}
        self.status_flags = {}
        self.strategy = strategy or SimpleStrategy()
        self.block = 0
    
    def begin_turn(self, battle=None):
        if not self.has_power("Barricade"):
            self.block = 0
        self.energy = self.max_energy
        self.tick_buffs_and_debuffs()
        self.trigger_begin_turn_powers(battle=battle)

    def trigger_begin_turn_powers(self, battle):
        if "Brutality" in self.powers:
            value = self.powers["Brutality"]
            self.take_damage(value, source="self")
            battle.draw_cards(value)

    def end_turn(self):
        for name in list(self.buffs.keys()):
            if self.buffs[name].get("temporary"):
                del self.buffs[name]
        for name in list(self.debuffs.keys()):
            if self.debuffs[name].get("temporary"):
                del self.debuffs[name]
        for name in list(self.status_flags.keys()):
            if self.status_flags[name].get("temporary"):
                del self.status_flags[name]

    def take_damage(self, amount, source="enemy"):
        damage = max(0, amount - self.block)
        self.hp -= damage
        self.block = max(0, self.block - amount)

        if source == "self" and "Rupture" in self.powers:
            strength_gain = self.powers["Rupture"]

            if "Strength" not in self.buffs:
                self.buffs["Strength"] = {"value": 0}

            self.buffs["Strength"]["value"] += strength_gain

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
    
    def has_power(self, name):
        return name in self.powers
    
    def trigger_on_exhaust(self, battle=None):
        if "GainBlockOnExhaust" in self.powers:
            block_per_exhaust = self.powers["GainBlockOnExhaust"]
            self.block += block_per_exhaust
        if "DrawOnExhaust" in self.powers:
            draw_per_exhaust = self.powers["DrawOnExhaust"]
            battle.draw_cards(draw_per_exhaust)

    def tick_buffs_and_debuffs(self):
        # Buffs
        for name in list(self.buffs.keys()):
            entry = self.buffs[name]

            if name == "Regen":
                apply_regen(self,entry)
            elif name == "StrengthGain":
                apply_strength_gain(self, entry)

            if not tick_standard_duration(entry):
                del self.buffs[name]

        # Debuffs
        for name in list(self.debuffs.keys()):
            entry = self.debuffs[name]

            if name == "Poison":
                tick_poison(self, entry)
            
            if not tick_standard_duration(entry):
                del self.debuffs[name]

    def after_draw_card(self, card, battle=None):
        if "Evolve" in self.powers:
            trigger_types = {"status", "curse"}
            if card.card_type in trigger_types:
                amount = self.powers["Evolve"]
                if battle:
                    battle.draw_cards(amount)
        if "FireBreath" in self.powers:
            trigger_types = {"status", "curse"}
            if card.card_type in trigger_types:
                amount = self.powers["FireBreath"]
                if battle:
                    for enemy in battle.enemies:
                        if enemy.hp > 0:
                            enemy.take_damage(amount)

    def play_cards(self, hand, enemies, battle):
        while True:
            card = self.strategy.select_card(hand, self, enemies, battle)
            if card is None:
                break
            if not getattr(card, "playable", True):
                if battle.if_battle_log:
                    battle.log.append(f"[Skip] {card.name} is not playable.")
                continue

            targets = self.strategy.select_target(card, self, enemies, battle)
            if not targets:
                break
            
            #print(f"DEBUG: play_cards target: {[t.name for t in targets]}")
            battle.play_card(card, self, targets)

