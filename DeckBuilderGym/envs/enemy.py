from card import Card,EffectCalculator
from loader import load_enemy_by_id, resolve_target_selector
from buff_n_debuff import apply_regen, tick_poison, tick_standard_duration

class Enemy:
    def __init__(self, id, name, hp, max_hp,
                 block=0,
                 buffs=None, 
                 debuffs=None, 
                 intent_sq=None, 
                 tags=None,
                 die_after_turn=None):
        self.id = id
        self.name = name or id
        self.hp = hp
        self.max_hp = max_hp or hp
        self.block = block or 0
        self.prev_hp = hp
        self.buffs = buffs or {}
        self.debuffs = debuffs or {}
        self.intent_sq = intent_sq
        self.intent_index = 0
        self.tags = tags
        self.die_after_turn=die_after_turn
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
        
        intents = self.intent_sq[self.intent_index % len(self.intent_sq)]
        self.intent_index += 1
        boss = next((e for e in self.enemy_group if "Boss" in e.tags), None)
        
        for intent in intents: 
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


class EnemyIntent:
    def execute(self, user, battle):
        raise NotImplementedError
    

class AttackIntent(EnemyIntent):
    def __init__(self, amount):
        self.amount = amount

    def execute(self, user, battle):
        damage = EffectCalculator.modified_damage(self.amount, attacker=user, defender=battle.player)
        battle.player.take_damage(damage)

class BlockIntent(EnemyIntent):
    def __init__(self, amount, target_selector):
        self.amount = amount
        self.target_selector = target_selector

    def execute(self, user, battle):
        targets = resolve_target_selector(user, self.target_selector, battle)
        for target in targets:
            block = EffectCalculator.modified_block(self.amount, user=target)
            self.target.gain_block(block)

class BuffIntent(EnemyIntent):
    def __init__(self, name, target_selector, value, duration=None):
        self.name = name
        self.target_selector = target_selector
        self.value = value
        self.duration = duration

    def execute(self, user, battle):
        targets = resolve_target_selector(user, self.target_selector, battle)
        for target in targets:
            target.apply_buff(self.name, self.value, self.duration)

class DebuffIntent(EnemyIntent):
    def __init__(self, name, duration, value=None):
        self.name = name
        self.duration = duration
        self.value = value
    
    def execute(self, user, battle):
        battle.player.apply_buff(self.name, self.value, self.duration)

class HealIntent(EnemyIntent):
    def __init__(self, amount, target_selector):
        self.amount = amount
        self.target_selector = target_selector

    def execute(self, user, battle):
        targets = resolve_target_selector(user, self.target_selector, battle)
        for target in targets:
            target.heal(self.amount)

class InsertCardIntent(EnemyIntent):
    def __init__(self, card_id, amount=1):
        self.card_id = card_id
        self.amount = amount

    def execute(self, user, battle):
        for _ in range(self.amount):
            card_template = battle.card_id_map[self.card_id]
            card = Card(**card_template)
            battle.player.discard_pile.append(card)
        if battle.if_battle_log:
            battle.log.append(f"[Intent] {user.name} inserts {self.amount}x '{card.name}' into player's discard pile.")

class SpawnIntent(EnemyIntent):
    def __init__(self, threshold, summon_enemy_id, amount=2):
        self.threshold = threshold
        self.summon_enemy_id = summon_enemy_id
        self.amount = amount

    def execute(self, user, battle):
        if user.hp <= self.threshold:
            for _ in range(self.amount):
                mid_slime = load_enemy_by_id(self.summon_enemy_id)
                mid_slime.hp = user.hp
                battle.enemies.append(mid_slime)
            user.hp = 0
            if battle.if_battle_log:
                battle.log.append(f"[Intent] {user.name} splits into {self.amount} {self.summon_enemy_id}s!")