import random


class Card:
    def __init__(self, id, name, tag, cost, effects, card_type, ethereal=False, exhaust=False, innate=False, retain=False, shuffle_back=False):
        self.id = id
        self.name = name
        self.tag = tag
        self.cost = cost
        self.effects = effects
        self.card_type = card_type
        self.ethereal = ethereal
        self.exhaust = exhaust
        self.innate = innate
        self.retain = retain
        self.shuffle_back = shuffle_back

    def apply(self, user, target, battle=None):
        for effect in self.effects:
            effect.apply(user, target, battle=battle)


class CardEffect:
    def __init__(self, target_selector: str = "single_enemy"):
        self.target_selector = target_selector  # 只是一个描述用的字段

    def apply(self, user, target, battle=None):
        raise NotImplementedError


class AttackEffect(CardEffect):
    def __init__(self, amount, target_selector=None):
        self.target_selector = target_selector
        self.amount = amount

    def apply(self, user, enemies, battle=None):
        if not isinstance(targets, list):
            targets = [targets]
        for target in targets:
            dmg = EffectCalculator.modified_damage(self.amount, user, target)
            target.take_damage(dmg)

class BlockEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target, battle=None):
        block =  EffectCalculator.modified_block(self.amount, user)
        user.gain_block(block)


class BuffEffect(CardEffect):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def apply(self, user, target, battle=None):
        target.apply_buff(self.name, self.value)


class DebuffEffect(CardEffect):
    def __init__(self, name, duration):
        self.name = name
        self.duration = duration

    def apply(self, user, target, battle=None):
        target.apply_debuff(self.name, self.duration)


class DrawEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target=None, battle=None):
        if battle is None:
            raise ValueError("DrawEffect requires access to the battle context.")
        battle.draw_cards(self.amount)


class EnergyEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target, battle=None):
        user.energy += self.amount


class EffectCalculator:
    
    @staticmethod
    def modified_damage(base_damage, attacker, defender):
        damage = base_damage

        if "Strength" in attacker.buffs:
            damage += attacker.buffs["Strength"]

        if "Weak" in attacker.debuffs:
            damage = int(damage * 0.75)

        if "Intangible" in defender.buffs:
            damage = min(damage, 1)
        
        if "Vulnerable" in defender.buffs:
            damage = int(damage * 1.5)

        return max(0, damage)
    
    @staticmethod
    def modified_block(base_block, user):
        block = base_block

        if "Frail" in user.debuffs:
            block = int(block * 0.75)

        if "Dexterity" in user.buffs:
            block += user.buffs["Dexterity"]

        return max(0, block)
