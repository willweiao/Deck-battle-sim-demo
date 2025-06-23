import random


class Card:
    def __init__(self, id, name, cost, effects, card_type, ethereal=False, exhaust=False, innate=False, retain=False, shuffle_back=False):
        self.id = id
        self.name = name 
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
    def __init__(self, target_selector=None):
        self.target_selector = target_selector or DefaultTargetSelector()

    def apply(self, user, target, battle=None):
        raise NotImplementedError


class AttackEffect(CardEffect):
    def __init__(self, amount, target_selector=None):
        super().__init__(target_selector)
        self.amount = amount

    def apply(self, user, enemies, battle=None):
        targets = self.target_selector.select(user, enemies)
        for target in targets:
            damage = EffectCalculator.modified_damage(self.amount, attacker=user, defender=target)
            target.take_damage(damage)


class BlockEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target, battle=None):
        block =  EffectCalculator.modified_block(self.amount, user)
        user.gain_block(block)


class BuffEffect(CardEffect):
    def __init__(self, name, value, target_self=True):
        self.name = name
        self.value = value
        self.target_self = target_self
    
    def apply(self, user, target, battle=None):
        if self.target_self:
            user.apply_buff(self.name, self.value)
        else:
            target.apply_buff(self.name, self.value)


class DebuffEffect(CardEffect):
    def __init__(self, name, duration, target_user=False):
        self.name = name
        self.duration = duration
        self.target_user = target_user

    def apply(self, user, target, battle=None):
        if self.target_user:
            user.apply_debuff(self.name, self.duration)
        else:
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


class TargetSelector:
    def select(self, user, enemies):
        raise NotImplementedError


class SingleRandomEnemy(TargetSelector):
    def select(self, user, enemies):
        alive = [e for e in enemies if e.hp > 0]
        return [random.choice(alive)] if alive else []


class AllEnemies(TargetSelector):
    def select(self, user, enemies):
        return [e for e in enemies if e.hp > 0]


class LowestHPEnemy(TargetSelector):
    def select(self, user, enemies):
        alive = [e for e in enemies if e.hp > 0]
        return [min(alive, key=lambda e: e.hp)] if alive else []


class DefaultTargetSelector(TargetSelector):
    def select(self, user, enemies):
        raise Exception(
            "[TargetSelector Error] This card effect requires a target selector, but none was provided.\n"
            "You must explicitly assign a TargetSelector (e.g., SingleEnemySelector, AllEnemiesSelector) when creating the effect."
        )
    

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
            damage = int(damage * 1.25)

        return max(0, damage)
    
    @staticmethod
    def modified_block(base_block, user):
        block = base_block

        if "Frail" in user.debuffs:
            block = int(block * 0.75)

        if "Dexterity" in user.buffs:
            block += user.buffs["Dexterity"]

        return max(0, block)
