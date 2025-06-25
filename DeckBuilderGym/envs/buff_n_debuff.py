def get_buff_value(entity, name):
    return entity.buffs.get(name, {}).get("value", 0)

def get_debuff_value(entity, name):
    return entity.debuffs.get(name, {}).get("value", 0)

def has_buff(entity, name):
    return name in entity.buffs

def has_debuff(entity, name):
    return name in entity.debuffs

def apply_regen(entity, entry):
    entity.heal(entry["value"])

def tick_poison(entity, entry):
    damage = entry["value"]
    entity.hp -= damage
    entry["value"] -= 1
    return entry["value"] > 0

def tick_standard_duration(entry):
    if "duration" not in entry:
        return True
    
    entry["duration"] -= 1
    return entry["duration"] > 0