from card import EffectCalculator

class Enemy:
    def __init__(self, id, name, hp, max_hp, buffs=None, debuffs=None, intent_sq=None, tags=None):
        self.id = id
        self.name = name or id
        self.hp = hp
        self.max_hp = max_hp
        self.buffs = buffs or {}
        self.debuffs = debuffs or {}
        self.intent_sq = intent_sq
        self.intent_index = 0
        self.tags = tags
        self.block = 0
        self.enemy_group = []
    
    def set_group(self, group):
        self.enemy_group = group
    
    def begin_turn(self):
        self.block = 0
        self.tick_buffs_and_debuffs()
    
    def end_turn(self):
        for name in list(self.buffs.keys()):
            if self.buffs[name].get("temporary"):
                del self.buffs[name]
        for name in list(self.debuffs.keys()):
            if self.debuffs[name].get("temporary"):
                del self.debuffs[name]
                
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

    def take_damage(self, amount):
        damage = max(0, amount - self.block)
        self.hp -= damage
        self.block = max(0, self.block - amount)
    
    def gain_block(self, amount):
        self.block += amount
    
    def apply_buff(self, name, value):
        self.buffs[name] = self.buffs.get(name, 0) + value

    def apply_debuff(self, name, duration):
        self.debuffs[name] = self.debuffs.get(name, 0) + duration
    
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

