import os
import random
from envs.player import Player
from envs.battle import Battle
from envs.player_strategy import ManualStrategy
from envs.loader import load_card_pool, load_deck_by_id, load_enemy_group
from model.stat_recommendsys import generate_action_stats, recommend_action_ranking


if __name__ == "__main__":
    examine_experiment_json = "basic_vs_Slime_Duo.json" # change here the simulated battle 
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    examine_path = os.path.join(base_dir, "experiments", examine_experiment_json)
    
    action_stats = generate_action_stats(examine_path, only_wins=True, strict_hand_match=False)  # gather the complete stat form 

    deck_path = os.path.join(base_dir, "data", "deck.json")
    enemy_path = os.path.join(base_dir, "data", "enemy_group.json")

    card_pool = load_card_pool("card.json")
    deck, _ = load_deck_by_id(deck_path, "deck02", card_pool)    # must use the same deck as in the simulation
    enemies_template, _ = load_enemy_group(enemy_path, "group01")     # same, need to comfront the same enemy as in the sim
    enemies = [e for e in enemies_template]
    
    # start battle 
    player = Player(name="Hero", hp=50, energy=3, strategy=ManualStrategy())
    battle = Battle(player, enemies, deck, card_pool=card_pool, if_battle_log=True)

    turn = 0
    while True:
        turn += 1
        player.begin_turn()
        print(f"\n=== Turn {turn} ===")
        battle.draw_cards(5)
        hand = battle.hand

        print("Hand:")
        for idx, card in enumerate(hand):
            print(f"{idx}. {card.name} (ID: {card.id}, Cost: {card.cost})")

        ranking = recommend_action_ranking(hand, turn, action_stats)
        
        # get recommendations by the cards in hand
        filtered_ranking = []
        seen_ids = set()
        for card, targets in ranking:
            if card.id in [c.id for c in hand] and card.id not in seen_ids:
                filtered_ranking.append((card, targets))
                seen_ids.add(card.id)
            if len(filtered_ranking) == 3:
                break

        if not filtered_ranking:
            print("No recommendations found.")
            selected = input("Enter 'p' to pass: ")
            if selected == "p":
                continue
            else:
                continue  # Invalid input fallback
        else:
            print("Recommended Actions by the order of winning time:")
            for i, (card, targets) in enumerate(filtered_ranking):
                print(f"{i+1}. {card.name} → targets: {targets}")

        # choose a card to play, you can choose a recommendation result or 
        selected = input("Choose [1-10] for hand, or r1/r2/r3 for the recommendation results by order, or 'p' to skip: ").strip().lower()
        if selected == "p":
            break
        ## select a recommended result
        elif selected.startswith("r") and selected[1:].isdigit():
            ridx = int(selected[1:]) - 1
            if 0 <= ridx < len(filtered_ranking):
                card, target_ids = filtered_ranking[ridx]
                break
            else:
                print("Invalid recommendation index.")
        ## select a card and its target in the player's wish
        elif selected.isdigit():
            hand_idx = int(selected) - 1
            if 0 <= hand_idx < len(hand):
                card = hand[hand_idx]
                sel=card.target_selector
                alive_enemies = [e for e in battle.enemies if e.hp > 0]
                alive_ids = [e.id for e in alive_enemies]

                ### if selected a card which need to have a target, then show the enemy list for player to choose from
                if  sel == "all_enemies":
                    target_ids = alive_ids
                elif sel =="random_enemy":
                    target_ids = [random.choice(alive_ids)] if alive_ids else []
                elif sel =="lowest_hp":
                    target = [min(alive_enemies, key=lambda e: e.hp)] if alive_enemies else None
                    target_ids = [target.id] if target else []
                elif sel == "self":
                    target_ids = []
                else:
                    print("Enemies:")
                    for i, enemy in enumerate(battle.enemies):
                        if enemy.hp > 0:
                            print(f"{i+1}. {enemy.name} (HP: {enemy.hp}, ID: {enemy.id})")
                    target_input = input("Select target enemy [1-N]").strip()
                    try:
                        indices = [int(x.strip()) - 1 for x in target_input.split(",")]
                        target_ids = [battle.enemies[i].id for i in indices if i < len(battle.enemies) and battle.enemies[i].hp > 0]
                        if not target_ids:
                            print("No valid target selected.")
                            continue
                    except Exception as e:
                        print("Invalid target selection.")
                        continue
                break
            else:
                print("Invalid hand index.")
                continue
        else:
            print("Invalid input.")
            continue
    
        print(f"\n You selected: {card.name} → {', '.join(target_ids) if target_ids else 'no target'}")
        target_objs = [e for e in battle.enemies if e.id in target_ids] if target_ids else []
        battle.play_card(card, player, target_objs)

        if battle.check_victory():
            break
        battle.enemy_turn()
        if battle.check_victory():
            break
        battle.cleanup()

        print("\n[Battle End]")
        print(f"Player HP: {player.hp}")

