from card import EffectCalculator
from buff_n_debuff import apply_regen, tick_poison, tick_standard_duration

class Enemy:
    def __init__(self, id, name, hp, max_hp, 
                 buffs=None, 
                 debuffs=None, 
                 intent_sq=None, 
                 tags=None,
                 die_after_turn=None):
        self.id = id
        self.name = name or id
        self.hp = hp
        self.max_hp = max_hp
        self.buffs = buffs or {}
        self.debuffs = debuffs or {}
        self.intent_sq = intent_sq
        self.intent_index = 0
        self.tags = tags
        self.die_after_turn=die_after_turn
        self.block = 0
        self.enemy_group = []
    
    def set_group(self, group):
        self.enemy_group = group
    
    def begin_turn(self):
        self.block = 0
        self.tick_buffs_and_debuffs()
    
    def end_turn(self,battle=None):
        if "LoseStrength" in self.debuffs:
            amount = self.debuffs["LoseStrength"].get("value", 0)
            if "Strength" in self.buffs:
                self.buffs["Strength"]["value"] = self.buffs["Strength"]["value"] - amount
                if battle is not None and battle.if_battle_log:
                    battle.log.append(f"[EndTurn] {self.name} loses {amount} Strength.")
            del self.debuffs["LoseStrength"]
                
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

    def take_damage(self, amount):
        damage = max(0, amount - self.block)
        self.hp -= damage
        self.block = max(0, self.block - amount)
    
    def gain_block(self, amount):
        self.block += amount
    
    def apply_buff(self, name, value, duration=None):
        if name not in self.buffs:
            self.buffs[name] = {"value": 0}

        self.buffs[name]["value"] += value

        if duration is not None:
            if "duration" in self.buffs[name]:
                self.buffs[name]["duration"] += duration
            else:
                self.buffs[name]["duration"] = duration

    def apply_debuff(self, name, duration, value=None):
        if name not in self.debuffs:
            self.debuffs[name] = {"duration": 0}

        self.debuffs[name]["duration"] += duration

        if value is not None:
            if "value" in self.debuffs[name]:
                self.debuffs[name]["value"] += value
            else:
                self.debuffs[name]["value"] = value

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def perform_action(self, player):
        if not self.intent_sq:
            return
        
        intent = self.intent_sq[self.intent_index % len(self.intent_sq)]
        self.intent_index += 1
        boss = next((e for e in self.enemy_group if "Boss" in e.tags), None)
        intent_type = intent.get("type")
        intent_name = intent.get("name", "")
        intent_value = intent.get("value", 0)
        intent_duration = intent.get("duration", 1)
        
        if intent_type=="attack":
            damage = EffectCalculator.modified_damage(intent_value, attacker=self, defender=player)
            player.take_damage(damage)
        elif intent_type=="block":
            block = EffectCalculator.modified_block(intent_value, user=self)
            self.gain_block(block)
        elif intent_type=="buff":
            self.apply_buff(intent_name, intent_value)
        elif intent_type=="debuff":
            player.apply_debuff(intent_name, intent_duration)
        elif intent_type=="heal":
            self.heal(intent_value)
        elif intent_type=="block_boss" and boss:
            block = EffectCalculator.modified_block(intent_value, user=boss)
            boss.gain_block(block)
        elif intent_type=="buff_boss" and boss:
            boss.apply_buff(intent_name, intent_value)
        elif intent_type=="heal_boss" and boss:
            boss.heal(intent_value)

