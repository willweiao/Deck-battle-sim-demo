import random
from buff_n_debuff import get_buff_value, get_debuff_value, has_buff, has_debuff


class Card:
    def __init__(self, id, name, tag, cost, effects, card_type, target_selector=None, ethereal=False, exhaust=False, innate=False, retain=False, shuffle_back=False):
        self.id = id
        self.name = name
        self.tag = tag
        self.cost = cost
        self.effects = effects
        self.card_type = card_type
        self.target_selector = target_selector
        self.ethereal = ethereal
        self.exhaust = exhaust
        self.innate = innate
        self.retain = retain
        self.shuffle_back = shuffle_back

    def apply(self, user, targets, battle=None):
        if not targets:
            raise ValueError(f"[CardError] Card '{self.name}' expected at least one target but got: {targets}.")
        
        for effect in self.effects:
            for target in targets:
                effect.apply(user, target, battle=battle)

class CardEffect:
    def apply(self, user, target, battle=None):
        raise NotImplementedError


class AttackEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target, battle=None):
        damage = EffectCalculator.modified_damage(self.amount, attacker=user, defender=target)
        target.take_damage(damage)

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

        damage += get_buff_value(attacker, "Strength")

        if has_debuff(attacker, "Weak"):
            damage = int(damage * 0.75)

        if has_buff(defender, "Intangible"):
            damage = min(damage, 1)

        if has_debuff(defender, "Vulnerable"):
            damage = int(damage * 1.5)

        return max(0, damage)

    @staticmethod
    def modified_block(base_block, user):
        block = base_block

        if has_debuff(user, "Frail"):
            block = int(block * 0.75)

        block += get_buff_value(user, "Dexterity")

        return max(0, block)
