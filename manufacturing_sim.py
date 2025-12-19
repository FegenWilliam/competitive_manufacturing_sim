#!/usr/bin/env python3
"""
Competitive Phone Manufacturing Simulation
A game where up to 4 players compete to be the manufacturing leader of phones.
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


# Game constants
PART_TYPES = ['ram', 'soc', 'screen', 'battery', 'camera', 'casing']
OPTIONAL_PARTS = ['fingerprint']
ALL_PARTS = PART_TYPES + OPTIONAL_PARTS
MAX_TIER = 10
STARTING_MONEY = 100000
STARTING_TIER = 1

# R&D costs and time (tier: (cost, months))
RND_CONFIG = {
    2: (5000, 2),
    3: (10000, 3),
    4: (20000, 4),
    5: (40000, 5),
    6: (70000, 6),
    7: (110000, 7),
    8: (160000, 8),
    9: (220000, 9),
    10: (300000, 10),
}

# Part costs per tier (for ordering)
PART_COST_PER_TIER = {
    1: 10,
    2: 25,
    3: 50,
    4: 100,
    5: 200,
    6: 400,
    7: 700,
    8: 1200,
    9: 2000,
    10: 3500,
}


@dataclass
class RnDProject:
    """Represents an ongoing R&D project"""
    part_type: str
    target_tier: int
    months_remaining: int
    cost: int

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return RnDProject(**data)


@dataclass
class PhoneBlueprint:
    """Represents a phone design/blueprint"""
    name: str
    ram_tier: int
    soc_tier: int
    screen_tier: int
    battery_tier: int
    camera_tier: int
    casing_tier: int
    fingerprint_tier: int  # 0 means no fingerprint
    sell_price: int

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return PhoneBlueprint(**data)

    def get_production_cost(self):
        """Calculate the cost to manufacture one unit"""
        cost = 0
        cost += PART_COST_PER_TIER[self.ram_tier]
        cost += PART_COST_PER_TIER[self.soc_tier]
        cost += PART_COST_PER_TIER[self.screen_tier]
        cost += PART_COST_PER_TIER[self.battery_tier]
        cost += PART_COST_PER_TIER[self.camera_tier]
        cost += PART_COST_PER_TIER[self.casing_tier]
        if self.fingerprint_tier > 0:
            cost += PART_COST_PER_TIER[self.fingerprint_tier]
        return cost

    def display(self):
        """Display blueprint details"""
        print(f"\n  Blueprint: {self.name}")
        print(f"  RAM: T{self.ram_tier} | SoC: T{self.soc_tier} | Screen: T{self.screen_tier}")
        print(f"  Battery: T{self.battery_tier} | Camera: T{self.camera_tier} | Casing: T{self.casing_tier}")
        if self.fingerprint_tier > 0:
            print(f"  Fingerprint: T{self.fingerprint_tier}")
        else:
            print(f"  Fingerprint: None")
        print(f"  Production Cost: ${self.get_production_cost()} | Sell Price: ${self.sell_price}")
        print(f"  Profit per unit: ${self.sell_price - self.get_production_cost()}")


class Player:
    """Represents a player in the game"""

    def __init__(self, name: str):
        self.name = name
        self.money = STARTING_MONEY
        self.current_month = 1

        # Start with T1 unlocked for all parts
        self.unlocked_tiers: Dict[str, int] = {part: STARTING_TIER for part in ALL_PARTS}

        # Ongoing R&D projects
        self.ongoing_rnd: List[RnDProject] = []

        # Phone blueprints
        self.blueprints: List[PhoneBlueprint] = []

        # Inventory of parts (part_type -> {tier -> quantity})
        self.inventory: Dict[str, Dict[int, int]] = {part: {} for part in ALL_PARTS}

        # Manufactured phones ready to sell (blueprint_name -> quantity)
        self.manufactured_phones: Dict[str, int] = {}

    def to_dict(self):
        """Convert player to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'money': self.money,
            'current_month': self.current_month,
            'unlocked_tiers': self.unlocked_tiers,
            'ongoing_rnd': [proj.to_dict() for proj in self.ongoing_rnd],
            'blueprints': [bp.to_dict() for bp in self.blueprints],
            'inventory': self.inventory,
            'manufactured_phones': self.manufactured_phones,
        }

    @staticmethod
    def from_dict(data):
        """Create player from dictionary"""
        player = Player(data['name'])
        player.money = data['money']
        player.current_month = data['current_month']
        player.unlocked_tiers = data['unlocked_tiers']
        player.ongoing_rnd = [RnDProject.from_dict(proj) for proj in data['ongoing_rnd']]
        player.blueprints = [PhoneBlueprint.from_dict(bp) for bp in data['blueprints']]
        player.inventory = data['inventory']
        player.manufactured_phones = data['manufactured_phones']
        return player

    def display_status(self):
        """Display player's current status"""
        print(f"\n{'='*60}")
        print(f"Player: {self.name}")
        print(f"Month: {self.current_month} | Money: ${self.money:,}")
        print(f"{'='*60}")

    def display_unlocked_tiers(self):
        """Display unlocked tiers for all parts"""
        print("\n--- Unlocked Tiers ---")
        for part in PART_TYPES:
            print(f"  {part.capitalize()}: T{self.unlocked_tiers[part]}")
        for part in OPTIONAL_PARTS:
            print(f"  {part.capitalize()} (optional): T{self.unlocked_tiers[part]}")

    def display_ongoing_rnd(self):
        """Display ongoing R&D projects"""
        if not self.ongoing_rnd:
            print("\n--- No ongoing R&D projects ---")
            return

        print("\n--- Ongoing R&D Projects ---")
        for i, proj in enumerate(self.ongoing_rnd, 1):
            print(f"  {i}. {proj.part_type.capitalize()} T{proj.target_tier} - "
                  f"{proj.months_remaining} months remaining")

    def display_inventory(self):
        """Display parts inventory"""
        print("\n--- Parts Inventory ---")
        has_parts = False
        for part in ALL_PARTS:
            if self.inventory[part]:
                for tier, qty in sorted(self.inventory[part].items()):
                    if qty > 0:
                        print(f"  {part.capitalize()} T{tier}: {qty} units")
                        has_parts = True
        if not has_parts:
            print("  No parts in inventory")

    def display_blueprints(self):
        """Display all phone blueprints"""
        if not self.blueprints:
            print("\n--- No phone blueprints created ---")
            return

        print("\n--- Phone Blueprints ---")
        for i, bp in enumerate(self.blueprints, 1):
            print(f"\n{i}. ", end="")
            bp.display()

    def display_manufactured_phones(self):
        """Display manufactured phones inventory"""
        if not self.manufactured_phones:
            print("\n--- No manufactured phones ---")
            return

        print("\n--- Manufactured Phones ---")
        for name, qty in self.manufactured_phones.items():
            print(f"  {name}: {qty} units")

    def advance_month(self):
        """Advance to next month and update R&D projects"""
        self.current_month += 1
        completed_projects = []

        for proj in self.ongoing_rnd:
            proj.months_remaining -= 1
            if proj.months_remaining <= 0:
                completed_projects.append(proj)
                self.unlocked_tiers[proj.part_type] = proj.target_tier

        # Remove completed projects
        for proj in completed_projects:
            self.ongoing_rnd.remove(proj)

        if completed_projects:
            print(f"\n🎉 R&D Projects Completed:")
            for proj in completed_projects:
                print(f"  - {proj.part_type.capitalize()} T{proj.target_tier} unlocked!")

        print(f"\n✓ Advanced to Month {self.current_month}")

    def start_rnd(self, part_type: str, target_tier: int) -> bool:
        """Start a new R&D project"""
        # Validate
        if part_type not in ALL_PARTS:
            print(f"❌ Invalid part type: {part_type}")
            return False

        if target_tier < 2 or target_tier > MAX_TIER:
            print(f"❌ Invalid tier: {target_tier}")
            return False

        if target_tier <= self.unlocked_tiers[part_type]:
            print(f"❌ {part_type.capitalize()} T{target_tier} is already unlocked!")
            return False

        if target_tier > self.unlocked_tiers[part_type] + 1:
            print(f"❌ Must unlock tiers sequentially. Current: T{self.unlocked_tiers[part_type]}")
            return False

        # Check if already researching this
        for proj in self.ongoing_rnd:
            if proj.part_type == part_type and proj.target_tier == target_tier:
                print(f"❌ Already researching {part_type.capitalize()} T{target_tier}!")
                return False

        cost, months = RND_CONFIG[target_tier]

        if self.money < cost:
            print(f"❌ Insufficient funds. Need ${cost:,}, have ${self.money:,}")
            return False

        # Start the project
        self.money -= cost
        project = RnDProject(part_type, target_tier, months, cost)
        self.ongoing_rnd.append(project)

        print(f"\n✓ Started R&D for {part_type.capitalize()} T{target_tier}")
        print(f"  Cost: ${cost:,} | Duration: {months} months")
        print(f"  Remaining balance: ${self.money:,}")
        return True

    def create_blueprint(self, name: str, parts: Dict[str, int], sell_price: int) -> bool:
        """Create a new phone blueprint"""
        # Check if name already exists
        for bp in self.blueprints:
            if bp.name == name:
                print(f"❌ Blueprint '{name}' already exists!")
                return False

        # Validate all mandatory parts are specified
        for part in PART_TYPES:
            if part not in parts:
                print(f"❌ Missing mandatory part: {part}")
                return False

            tier = parts[part]
            if tier > self.unlocked_tiers[part]:
                print(f"❌ {part.capitalize()} T{tier} not yet unlocked (current: T{self.unlocked_tiers[part]})")
                return False

        # Validate optional parts
        fingerprint_tier = parts.get('fingerprint', 0)
        if fingerprint_tier > 0 and fingerprint_tier > self.unlocked_tiers['fingerprint']:
            print(f"❌ Fingerprint T{fingerprint_tier} not yet unlocked (current: T{self.unlocked_tiers['fingerprint']})")
            return False

        blueprint = PhoneBlueprint(
            name=name,
            ram_tier=parts['ram'],
            soc_tier=parts['soc'],
            screen_tier=parts['screen'],
            battery_tier=parts['battery'],
            camera_tier=parts['camera'],
            casing_tier=parts['casing'],
            fingerprint_tier=fingerprint_tier,
            sell_price=sell_price
        )

        self.blueprints.append(blueprint)
        print(f"\n✓ Created blueprint: {name}")
        blueprint.display()
        return True

    def order_parts(self, part_type: str, tier: int, quantity: int) -> bool:
        """Order parts for inventory"""
        if part_type not in ALL_PARTS:
            print(f"❌ Invalid part type: {part_type}")
            return False

        if tier > self.unlocked_tiers[part_type]:
            print(f"❌ {part_type.capitalize()} T{tier} not yet unlocked!")
            return False

        if tier < 1 or tier > MAX_TIER:
            print(f"❌ Invalid tier: {tier}")
            return False

        if quantity < 1:
            print(f"❌ Invalid quantity: {quantity}")
            return False

        cost = PART_COST_PER_TIER[tier] * quantity

        if self.money < cost:
            print(f"❌ Insufficient funds. Need ${cost:,}, have ${self.money:,}")
            return False

        self.money -= cost
        if tier not in self.inventory[part_type]:
            self.inventory[part_type][tier] = 0
        self.inventory[part_type][tier] += quantity

        print(f"\n✓ Ordered {quantity}x {part_type.capitalize()} T{tier} for ${cost:,}")
        print(f"  Remaining balance: ${self.money:,}")
        return True

    def manufacture_phone(self, blueprint_name: str, quantity: int) -> bool:
        """Manufacture phones based on a blueprint"""
        # Find blueprint
        blueprint = None
        for bp in self.blueprints:
            if bp.name == blueprint_name:
                blueprint = bp
                break

        if not blueprint:
            print(f"❌ Blueprint '{blueprint_name}' not found!")
            return False

        if quantity < 1:
            print(f"❌ Invalid quantity: {quantity}")
            return False

        # Check if we have enough parts
        parts_needed = {
            'ram': blueprint.ram_tier,
            'soc': blueprint.soc_tier,
            'screen': blueprint.screen_tier,
            'battery': blueprint.battery_tier,
            'camera': blueprint.camera_tier,
            'casing': blueprint.casing_tier,
        }

        if blueprint.fingerprint_tier > 0:
            parts_needed['fingerprint'] = blueprint.fingerprint_tier

        # Validate inventory
        for part, tier in parts_needed.items():
            available = self.inventory[part].get(tier, 0)
            if available < quantity:
                print(f"❌ Insufficient {part.capitalize()} T{tier}. Need {quantity}, have {available}")
                return False

        # Deduct parts from inventory
        for part, tier in parts_needed.items():
            self.inventory[part][tier] -= quantity

        # Add manufactured phones
        if blueprint_name not in self.manufactured_phones:
            self.manufactured_phones[blueprint_name] = 0
        self.manufactured_phones[blueprint_name] += quantity

        print(f"\n✓ Manufactured {quantity}x {blueprint_name}")
        print(f"  Total inventory: {self.manufactured_phones[blueprint_name]} units")
        return True


class Game:
    """Main game controller"""

    def __init__(self):
        self.players: List[Player] = []
        self.current_player_index = 0

    def to_dict(self):
        """Convert game state to dictionary"""
        return {
            'players': [p.to_dict() for p in self.players],
            'current_player_index': self.current_player_index,
        }

    @staticmethod
    def from_dict(data):
        """Load game from dictionary"""
        game = Game()
        game.players = [Player.from_dict(p) for p in data['players']]
        game.current_player_index = data['current_player_index']
        return game

    def save_game(self, filename: str = "savegame.json"):
        """Save game to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            print(f"\n✓ Game saved to {filename}")
            return True
        except Exception as e:
            print(f"\n❌ Error saving game: {e}")
            return False

    @staticmethod
    def load_game(filename: str = "savegame.json"):
        """Load game from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            game = Game.from_dict(data)
            print(f"\n✓ Game loaded from {filename}")
            return game
        except FileNotFoundError:
            print(f"\n❌ Save file not found: {filename}")
            return None
        except Exception as e:
            print(f"\n❌ Error loading game: {e}")
            return None

    def setup_players(self):
        """Set up players for a new game"""
        while True:
            try:
                num_players = int(input("\nHow many players? (1-4): "))
                if 1 <= num_players <= 4:
                    break
                print("Please enter a number between 1 and 4")
            except ValueError:
                print("Please enter a valid number")

        for i in range(num_players):
            name = input(f"Enter name for Player {i+1}: ").strip()
            if not name:
                name = f"Player {i+1}"
            self.players.append(Player(name))

        print(f"\n✓ Game setup complete with {num_players} player(s)")

    def get_current_player(self) -> Player:
        """Get the currently active player"""
        return self.players[self.current_player_index]

    def next_player(self):
        """Move to next player"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def menu_rnd(self, player: Player):
        """R&D menu"""
        while True:
            print("\n" + "="*60)
            print("R&D MENU")
            print("="*60)
            player.display_unlocked_tiers()
            player.display_ongoing_rnd()

            print(f"\nCurrent balance: ${player.money:,}")
            print("\nAvailable actions:")
            print("1. Start new R&D project")
            print("2. View R&D costs")
            print("3. Back to main menu")

            choice = input("\nChoice: ").strip()

            if choice == '1':
                print("\nSelect part type:")
                for i, part in enumerate(ALL_PARTS, 1):
                    current_tier = player.unlocked_tiers[part]
                    next_tier = current_tier + 1
                    if next_tier <= MAX_TIER:
                        cost, months = RND_CONFIG.get(next_tier, (0, 0))
                        print(f"{i}. {part.capitalize()} (Current: T{current_tier}, "
                              f"Next: T{next_tier}, Cost: ${cost:,}, Time: {months} months)")
                    else:
                        print(f"{i}. {part.capitalize()} (Current: T{current_tier}, MAX TIER REACHED)")

                try:
                    part_choice = int(input("\nSelect part (number): ")) - 1
                    if 0 <= part_choice < len(ALL_PARTS):
                        part_type = ALL_PARTS[part_choice]
                        target_tier = player.unlocked_tiers[part_type] + 1

                        if target_tier <= MAX_TIER:
                            player.start_rnd(part_type, target_tier)
                        else:
                            print("❌ Already at maximum tier!")
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Invalid input")

            elif choice == '2':
                print("\n--- R&D Costs & Time ---")
                for tier, (cost, months) in sorted(RND_CONFIG.items()):
                    print(f"  T{tier}: ${cost:,} - {months} months")

            elif choice == '3':
                break

    def menu_create_phone(self, player: Player):
        """Create phone blueprint menu"""
        print("\n" + "="*60)
        print("CREATE PHONE BLUEPRINT")
        print("="*60)
        player.display_unlocked_tiers()

        name = input("\nEnter blueprint name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            return

        parts = {}

        print("\nEnter tier for each part:")
        for part in PART_TYPES:
            while True:
                try:
                    tier = int(input(f"  {part.capitalize()} (T1-T{player.unlocked_tiers[part]}): "))
                    if 1 <= tier <= player.unlocked_tiers[part]:
                        parts[part] = tier
                        break
                    else:
                        print(f"    Invalid. Must be between 1 and {player.unlocked_tiers[part]}")
                except ValueError:
                    print("    Invalid input")

        # Optional fingerprint
        use_fingerprint = input("\nInclude fingerprint sensor? (y/n): ").strip().lower()
        if use_fingerprint == 'y':
            while True:
                try:
                    tier = int(input(f"  Fingerprint tier (T1-T{player.unlocked_tiers['fingerprint']}): "))
                    if 1 <= tier <= player.unlocked_tiers['fingerprint']:
                        parts['fingerprint'] = tier
                        break
                    else:
                        print(f"    Invalid. Must be between 1 and {player.unlocked_tiers['fingerprint']}")
                except ValueError:
                    print("    Invalid input")

        # Calculate suggested price
        suggested_cost = 0
        for part in PART_TYPES:
            suggested_cost += PART_COST_PER_TIER[parts[part]]
        if 'fingerprint' in parts:
            suggested_cost += PART_COST_PER_TIER[parts['fingerprint']]

        print(f"\nProduction cost per unit: ${suggested_cost}")
        print(f"Suggested sell price (1.5x cost): ${int(suggested_cost * 1.5)}")

        while True:
            try:
                sell_price = int(input("Enter sell price: $"))
                if sell_price > 0:
                    break
                else:
                    print("Price must be positive")
            except ValueError:
                print("Invalid input")

        player.create_blueprint(name, parts, sell_price)

    def menu_order_parts(self, player: Player):
        """Order parts menu"""
        while True:
            print("\n" + "="*60)
            print("ORDER PARTS")
            print("="*60)
            player.display_unlocked_tiers()
            player.display_inventory()
            print(f"\nCurrent balance: ${player.money:,}")

            print("\nSelect part type:")
            for i, part in enumerate(ALL_PARTS, 1):
                print(f"{i}. {part.capitalize()}")
            print(f"{len(ALL_PARTS)+1}. Back to main menu")

            try:
                choice = int(input("\nChoice: "))
                if choice == len(ALL_PARTS) + 1:
                    break

                if 1 <= choice <= len(ALL_PARTS):
                    part_type = ALL_PARTS[choice - 1]
                    max_tier = player.unlocked_tiers[part_type]

                    print(f"\nSelect tier (1-{max_tier}):")
                    for t in range(1, max_tier + 1):
                        print(f"  T{t}: ${PART_COST_PER_TIER[t]} per unit")

                    tier = int(input("Tier: "))
                    if tier < 1 or tier > max_tier:
                        print("❌ Invalid tier")
                        continue

                    quantity = int(input("Quantity: "))
                    if quantity < 1:
                        print("❌ Invalid quantity")
                        continue

                    total_cost = PART_COST_PER_TIER[tier] * quantity
                    print(f"\nTotal cost: ${total_cost:,}")
                    confirm = input("Confirm order? (y/n): ").strip().lower()

                    if confirm == 'y':
                        player.order_parts(part_type, tier, quantity)
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")

    def menu_manufacturing(self, player: Player):
        """Manufacturing menu"""
        while True:
            print("\n" + "="*60)
            print("MANUFACTURING")
            print("="*60)
            player.display_blueprints()
            player.display_inventory()
            player.display_manufactured_phones()

            if not player.blueprints:
                print("\n❌ No blueprints available. Create a blueprint first!")
                input("\nPress Enter to continue...")
                break

            print("\nActions:")
            print("1. Manufacture phones")
            print("2. Back to main menu")

            choice = input("\nChoice: ").strip()

            if choice == '1':
                print("\nSelect blueprint:")
                for i, bp in enumerate(player.blueprints, 1):
                    print(f"{i}. {bp.name} (Cost: ${bp.get_production_cost()}/unit)")

                try:
                    bp_choice = int(input("\nBlueprint number: ")) - 1
                    if 0 <= bp_choice < len(player.blueprints):
                        blueprint = player.blueprints[bp_choice]
                        quantity = int(input("Quantity to manufacture: "))

                        if quantity > 0:
                            player.manufacture_phone(blueprint.name, quantity)
                        else:
                            print("❌ Invalid quantity")
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Invalid input")

            elif choice == '2':
                break

    def main_menu(self):
        """Main game menu"""
        player = self.get_current_player()

        while True:
            player.display_status()

            print("\n--- MAIN MENU ---")
            print("1. Advance Month")
            print("2. Create Phone Blueprint")
            print("3. Order Parts")
            print("4. Manufacturing")
            print("5. R&D")
            print("6. View Status")
            print("7. Save Game")
            print("8. Next Player" if len(self.players) > 1 else "8. (Single Player)")
            print("9. Quit")

            choice = input("\nChoice: ").strip()

            if choice == '1':
                player.advance_month()
                input("\nPress Enter to continue...")

            elif choice == '2':
                self.menu_create_phone(player)

            elif choice == '3':
                self.menu_order_parts(player)

            elif choice == '4':
                self.menu_manufacturing(player)

            elif choice == '5':
                self.menu_rnd(player)

            elif choice == '6':
                player.display_status()
                player.display_unlocked_tiers()
                player.display_ongoing_rnd()
                player.display_inventory()
                player.display_blueprints()
                player.display_manufactured_phones()
                input("\nPress Enter to continue...")

            elif choice == '7':
                filename = input("Enter filename (default: savegame.json): ").strip()
                if not filename:
                    filename = "savegame.json"
                self.save_game(filename)
                input("\nPress Enter to continue...")

            elif choice == '8':
                if len(self.players) > 1:
                    self.next_player()
                    print(f"\n>>> Switching to {self.get_current_player().name} <<<")
                    input("Press Enter to continue...")
                    return  # Return to show next player's menu
                else:
                    print("Single player mode - no other players")
                    input("\nPress Enter to continue...")

            elif choice == '9':
                confirm = input("\nQuit game? (y/n): ").strip().lower()
                if confirm == 'y':
                    return 'quit'

    def run(self):
        """Main game loop"""
        print("\n" + "="*60)
        print("COMPETITIVE PHONE MANUFACTURING SIMULATOR")
        print("="*60)

        print("\n1. New Game")
        print("2. Load Game")

        choice = input("\nChoice: ").strip()

        if choice == '2':
            filename = input("Enter filename (default: savegame.json): ").strip()
            if not filename:
                filename = "savegame.json"

            loaded_game = Game.load_game(filename)
            if loaded_game:
                self.players = loaded_game.players
                self.current_player_index = loaded_game.current_player_index
            else:
                print("Starting new game instead...")
                self.setup_players()
        else:
            self.setup_players()

        # Main game loop
        while True:
            result = self.main_menu()
            if result == 'quit':
                print("\nThanks for playing!")
                break


if __name__ == "__main__":
    game = Game()
    game.run()
