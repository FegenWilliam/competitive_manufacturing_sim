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
CORE_PARTS = ['ram', 'soc', 'screen', 'battery', 'camera', 'casing', 'storage']
OPTIONAL_PARTS = ['fingerprint']
ALL_PARTS = CORE_PARTS + OPTIONAL_PARTS
MAX_TIER = 10
STARTING_MONEY = 100000
MANUFACTURING_LIMIT_PER_MONTH = 1000

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
    storage_tier: int
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
        cost += PART_COST_PER_TIER[self.storage_tier]
        if self.fingerprint_tier > 0:
            cost += PART_COST_PER_TIER[self.fingerprint_tier]
        return cost

    def display(self):
        """Display blueprint details"""
        print(f"\n  Blueprint: {self.name}")
        print(f"  RAM: T{self.ram_tier} | SoC: T{self.soc_tier} | Screen: T{self.screen_tier} | Storage: T{self.storage_tier}")
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

        # Start with T1-T5 unlocked for core parts, T1-T5 for optional parts
        self.unlocked_tiers: Dict[str, int] = {}
        for part in CORE_PARTS:
            self.unlocked_tiers[part] = 5
        for part in OPTIONAL_PARTS:
            self.unlocked_tiers[part] = 5

        # Ongoing R&D projects
        self.ongoing_rnd: List[RnDProject] = []

        # Phone blueprints
        self.blueprints: List[PhoneBlueprint] = []

        # Manufactured phones ready to sell (blueprint_name -> quantity)
        self.manufactured_phones: Dict[str, int] = {}

        # Manufacturing queue (blueprint_name, quantity, months_remaining)
        self.manufacturing_queue: List[tuple] = []

        # Track manufacturing units used this month
        self.manufacturing_used_this_month: int = 0

    def to_dict(self):
        """Convert player to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'money': self.money,
            'current_month': self.current_month,
            'unlocked_tiers': self.unlocked_tiers,
            'ongoing_rnd': [proj.to_dict() for proj in self.ongoing_rnd],
            'blueprints': [bp.to_dict() for bp in self.blueprints],
            'manufactured_phones': self.manufactured_phones,
            'manufacturing_queue': self.manufacturing_queue,
            'manufacturing_used_this_month': self.manufacturing_used_this_month,
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
        player.manufactured_phones = data['manufactured_phones']
        player.manufacturing_queue = data.get('manufacturing_queue', [])
        player.manufacturing_used_this_month = data.get('manufacturing_used_this_month', 0)
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
        print("Core parts:")
        for part in CORE_PARTS:
            print(f"  {part.capitalize()}: T{self.unlocked_tiers[part]}")
        print("Optional parts:")
        for part in OPTIONAL_PARTS:
            tier = self.unlocked_tiers[part]
            if tier == 0:
                print(f"  {part.capitalize()}: Not unlocked (need R&D)")
            else:
                print(f"  {part.capitalize()}: T{tier}")

    def display_ongoing_rnd(self):
        """Display ongoing R&D projects"""
        if not self.ongoing_rnd:
            print("\n--- No ongoing R&D projects ---")
            return

        print("\n--- Ongoing R&D Projects ---")
        for i, proj in enumerate(self.ongoing_rnd, 1):
            print(f"  {i}. {proj.part_type.capitalize()} T{proj.target_tier} - "
                  f"{proj.months_remaining} months remaining")

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

    def display_manufacturing_queue(self):
        """Display manufacturing queue"""
        if not self.manufacturing_queue:
            print("\n--- No phones in manufacturing ---")
            return

        print("\n--- Manufacturing Queue ---")
        for i, (blueprint_name, quantity, months_remaining) in enumerate(self.manufacturing_queue, 1):
            if months_remaining == 1:
                print(f"  {i}. {blueprint_name}: {quantity} units (completes next month)")
            else:
                print(f"  {i}. {blueprint_name}: {quantity} units ({months_remaining} months remaining)")

        remaining_capacity = MANUFACTURING_LIMIT_PER_MONTH - self.manufacturing_used_this_month
        print(f"\nManufacturing capacity remaining this month: {remaining_capacity}/{MANUFACTURING_LIMIT_PER_MONTH}")

    def advance_month(self):
        """Advance to next month and update R&D projects and manufacturing"""
        self.current_month += 1

        # Reset manufacturing limit for new month
        self.manufacturing_used_this_month = 0

        # Update R&D projects
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

        # Update manufacturing queue
        completed_manufacturing = []
        for i, (blueprint_name, quantity, months_remaining) in enumerate(self.manufacturing_queue):
            months_remaining -= 1
            if months_remaining <= 0:
                completed_manufacturing.append((blueprint_name, quantity))
                if blueprint_name not in self.manufactured_phones:
                    self.manufactured_phones[blueprint_name] = 0
                self.manufactured_phones[blueprint_name] += quantity
            else:
                self.manufacturing_queue[i] = (blueprint_name, quantity, months_remaining)

        # Remove completed manufacturing
        self.manufacturing_queue = [(name, qty, months) for (name, qty, months) in self.manufacturing_queue if months > 0]

        if completed_manufacturing:
            print(f"\n📦 Manufacturing Completed:")
            for name, qty in completed_manufacturing:
                print(f"  - {qty}x {name} ready to sell!")

        print(f"\n✓ Advanced to Month {self.current_month}")

    def start_rnd(self, part_type: str, target_tier: int, min_tier: int = 1, max_tier: int = MAX_TIER) -> bool:
        """Start a new R&D project"""
        # Validate
        if part_type not in ALL_PARTS:
            print(f"❌ Invalid part type: {part_type}")
            return False

        current_tier = self.unlocked_tiers[part_type]

        # Check if target tier is within available range
        if target_tier < min_tier or target_tier > max_tier:
            print(f"❌ Tier {target_tier} is not available. Available range: T{min_tier}-T{max_tier}")
            return False

        if target_tier < 2 or target_tier > MAX_TIER:
            print(f"❌ Invalid tier: {target_tier}")
            return False

        if target_tier <= current_tier:
            print(f"❌ {part_type.capitalize()} T{target_tier} is already unlocked!")
            return False

        if target_tier > current_tier + 1:
            print(f"❌ Must unlock tiers sequentially. Current: T{current_tier}")
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

    def create_blueprint(self, name: str, parts: Dict[str, int], sell_price: int,
                        min_tier: int = 1, max_tier: int = MAX_TIER) -> bool:
        """Create a new phone blueprint"""
        # Check if name already exists
        for bp in self.blueprints:
            if bp.name == name:
                print(f"❌ Blueprint '{name}' already exists!")
                return False

        # Validate all mandatory parts are specified
        for part in CORE_PARTS:
            if part not in parts:
                print(f"❌ Missing mandatory part: {part}")
                return False

            tier = parts[part]

            # Check if tier is within available range
            if tier < min_tier or tier > max_tier:
                print(f"❌ {part.capitalize()} T{tier} is not available. Available range: T{min_tier}-T{max_tier}")
                return False

            if tier > self.unlocked_tiers[part]:
                print(f"❌ {part.capitalize()} T{tier} not yet unlocked (current: T{self.unlocked_tiers[part]})")
                return False

        # Validate optional parts
        fingerprint_tier = parts.get('fingerprint', 0)
        if fingerprint_tier > 0:
            # Check if tier is within available range
            if fingerprint_tier < min_tier or fingerprint_tier > max_tier:
                print(f"❌ Fingerprint T{fingerprint_tier} is not available. Available range: T{min_tier}-T{max_tier}")
                return False

            if fingerprint_tier > self.unlocked_tiers['fingerprint']:
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
            storage_tier=parts['storage'],
            fingerprint_tier=fingerprint_tier,
            sell_price=sell_price
        )

        self.blueprints.append(blueprint)
        print(f"\n✓ Created blueprint: {name}")
        blueprint.display()
        return True

    def manufacture_phone(self, blueprint_name: str, quantity: int) -> bool:
        """Start manufacturing phones based on a blueprint"""
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

        # Check manufacturing capacity
        remaining_capacity = MANUFACTURING_LIMIT_PER_MONTH - self.manufacturing_used_this_month
        if quantity > remaining_capacity:
            print(f"❌ Insufficient manufacturing capacity. Can only manufacture {remaining_capacity} more units this month.")
            print(f"   (Monthly limit: {MANUFACTURING_LIMIT_PER_MONTH}, already used: {self.manufacturing_used_this_month})")
            return False

        # Calculate total cost (parts are bought instantly)
        cost_per_unit = blueprint.get_production_cost()
        total_cost = cost_per_unit * quantity

        if self.money < total_cost:
            print(f"❌ Insufficient funds. Need ${total_cost:,}, have ${self.money:,}")
            return False

        # Deduct money and add to manufacturing queue
        self.money -= total_cost
        self.manufacturing_used_this_month += quantity
        self.manufacturing_queue.append((blueprint_name, quantity, 1))  # Takes 1 month

        print(f"\n✓ Started manufacturing {quantity}x {blueprint_name}")
        print(f"  Parts cost: ${total_cost:,}")
        print(f"  Will complete in 1 month (Month {self.current_month + 1})")
        print(f"  Remaining balance: ${self.money:,}")
        print(f"  Manufacturing capacity used: {self.manufacturing_used_this_month}/{MANUFACTURING_LIMIT_PER_MONTH}")
        return True


class Game:
    """Main game controller"""

    def __init__(self):
        self.players: List[Player] = []
        self.current_player_index = 0
        self.global_month = 1  # Global game month
        self.global_tech_level = 1  # Determines which 5 tiers are available (1 = tiers 1-5, 2 = tiers 2-6, etc.)
        self.months_until_tech_advance = 36  # Tech advances every 3 years (36 months)

    def to_dict(self):
        """Convert game state to dictionary"""
        return {
            'players': [p.to_dict() for p in self.players],
            'current_player_index': self.current_player_index,
            'global_month': self.global_month,
            'global_tech_level': self.global_tech_level,
            'months_until_tech_advance': self.months_until_tech_advance,
        }

    @staticmethod
    def from_dict(data):
        """Load game from dictionary"""
        game = Game()
        game.players = [Player.from_dict(p) for p in data['players']]
        game.current_player_index = data['current_player_index']
        game.global_month = data.get('global_month', 1)
        game.global_tech_level = data.get('global_tech_level', 1)
        game.months_until_tech_advance = data.get('months_until_tech_advance', 36)
        return game

    def get_available_tier_range(self):
        """Get the current available tier range (min_tier, max_tier)"""
        min_tier = self.global_tech_level
        max_tier = self.global_tech_level + 4
        return min_tier, max_tier

    def advance_global_tech(self):
        """Advance the global tech level (called every 36 months)"""
        old_min, old_max = self.get_available_tier_range()
        self.global_tech_level += 1
        new_min, new_max = self.get_available_tier_range()

        print(f"\n{'='*60}")
        print(f"🚀 GLOBAL TECH ADVANCEMENT!")
        print(f"{'='*60}")
        print(f"Technology has advanced! Tier {old_min} components are now obsolete.")
        print(f"New tier range: T{new_min} - T{new_max}")
        print(f"All players now have access to the new tier T{new_max}")
        print(f"{'='*60}")

        # Update all players' unlocked tiers to include the new tier
        for player in self.players:
            for part in ALL_PARTS:
                # Ensure all parts are at least at the new max tier
                if player.unlocked_tiers[part] < new_max:
                    player.unlocked_tiers[part] = new_max

    def advance_game_month(self, player: Player):
        """Advance the game month and handle global tech advancement"""
        # Advance player's month
        player.advance_month()

        # Advance global month
        self.global_month += 1
        self.months_until_tech_advance -= 1

        # Check if it's time for tech advancement
        if self.months_until_tech_advance <= 0:
            self.advance_global_tech()
            self.months_until_tech_advance = 36  # Reset counter

        # Display countdown to next tech advancement
        years_remaining = self.months_until_tech_advance // 12
        months_remaining = self.months_until_tech_advance % 12
        min_tier, max_tier = self.get_available_tier_range()

        print(f"\n📅 Global Month: {self.global_month}")
        print(f"🔬 Current Tech Level: T{min_tier}-T{max_tier}")
        if years_remaining > 0:
            print(f"⏳ Next tech advancement in {years_remaining} year(s) and {months_remaining} month(s)")
        else:
            print(f"⏳ Next tech advancement in {months_remaining} month(s)")

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
        min_tier, max_tier = self.get_available_tier_range()

        while True:
            print("\n" + "="*60)
            print("R&D MENU")
            print("="*60)
            print(f"Current tech level: T{min_tier}-T{max_tier}")
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

                    if next_tier <= max_tier and next_tier <= MAX_TIER:
                        cost, months = RND_CONFIG.get(next_tier, (0, 0))
                        print(f"{i}. {part.capitalize()} (Current: T{current_tier}, "
                              f"Next: T{next_tier}, Cost: ${cost:,}, Time: {months} months)")
                    elif next_tier > max_tier:
                        print(f"{i}. {part.capitalize()} (Current: T{current_tier}, "
                              f"Next: T{next_tier} - not yet available, wait for tech advancement)")
                    else:
                        print(f"{i}. {part.capitalize()} (Current: T{current_tier}, MAX TIER REACHED)")

                try:
                    part_choice = int(input("\nSelect part (number): ")) - 1
                    if 0 <= part_choice < len(ALL_PARTS):
                        part_type = ALL_PARTS[part_choice]
                        current_tier = player.unlocked_tiers[part_type]
                        target_tier = current_tier + 1

                        if target_tier <= MAX_TIER:
                            player.start_rnd(part_type, target_tier, min_tier, max_tier)
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
        min_tier, max_tier = self.get_available_tier_range()

        print("\n" + "="*60)
        print("CREATE PHONE BLUEPRINT")
        print("="*60)
        print(f"Current tech level: T{min_tier}-T{max_tier}")
        player.display_unlocked_tiers()

        name = input("\nEnter blueprint name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            return

        parts = {}

        print("\nEnter tier for each core part:")
        for part in CORE_PARTS:
            while True:
                try:
                    max_available = min(player.unlocked_tiers[part], max_tier)
                    tier = int(input(f"  {part.capitalize()} (T{min_tier}-T{max_available}): "))
                    if min_tier <= tier <= max_available:
                        parts[part] = tier
                        break
                    else:
                        print(f"    Invalid. Must be between {min_tier} and {max_available}")
                except ValueError:
                    print("    Invalid input")

        # Optional fingerprint
        if player.unlocked_tiers['fingerprint'] > 0:
            use_fingerprint = input("\nInclude fingerprint sensor? (y/n): ").strip().lower()
            if use_fingerprint == 'y':
                while True:
                    try:
                        max_available = min(player.unlocked_tiers['fingerprint'], max_tier)
                        tier = int(input(f"  Fingerprint tier (T{min_tier}-T{max_available}): "))
                        if min_tier <= tier <= max_available:
                            parts['fingerprint'] = tier
                            break
                        else:
                            print(f"    Invalid. Must be between {min_tier} and {max_available}")
                    except ValueError:
                        print("    Invalid input")
        else:
            print("\nFingerprint sensor not available (need to R&D first)")

        # Calculate suggested price
        suggested_cost = 0
        for part in CORE_PARTS:
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

        player.create_blueprint(name, parts, sell_price, min_tier, max_tier)

    def menu_manufacturing(self, player: Player):
        """Manufacturing menu"""
        while True:
            print("\n" + "="*60)
            print("MANUFACTURING")
            print("="*60)
            player.display_blueprints()
            player.display_manufacturing_queue()
            player.display_manufactured_phones()

            if not player.blueprints:
                print("\n❌ No blueprints available. Create a blueprint first!")
                input("\nPress Enter to continue...")
                break

            print("\nActions:")
            print("1. Start manufacturing phones")
            print("2. Back to main menu")

            choice = input("\nChoice: ").strip()

            if choice == '1':
                remaining_capacity = MANUFACTURING_LIMIT_PER_MONTH - player.manufacturing_used_this_month
                if remaining_capacity <= 0:
                    print("\n❌ No manufacturing capacity remaining this month!")
                    input("\nPress Enter to continue...")
                    continue

                print("\nSelect blueprint:")
                for i, bp in enumerate(player.blueprints, 1):
                    print(f"{i}. {bp.name} (Cost: ${bp.get_production_cost()}/unit, Profit: ${bp.sell_price - bp.get_production_cost()}/unit)")

                try:
                    bp_choice = int(input("\nBlueprint number: ")) - 1
                    if 0 <= bp_choice < len(player.blueprints):
                        blueprint = player.blueprints[bp_choice]
                        print(f"\nManufacturing capacity remaining: {remaining_capacity} units")
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

            # Display global tech info
            min_tier, max_tier = self.get_available_tier_range()
            years_remaining = self.months_until_tech_advance // 12
            months_remaining = self.months_until_tech_advance % 12

            print(f"\n📅 Global Month: {self.global_month}")
            print(f"🔬 Tech Level: T{min_tier}-T{max_tier}")
            if years_remaining > 0:
                print(f"⏳ Next tech advancement: {years_remaining}y {months_remaining}m")
            else:
                print(f"⏳ Next tech advancement: {months_remaining}m")

            print("\n--- MAIN MENU ---")
            print("1. Advance Month")
            print("2. Create Phone Blueprint")
            print("3. Manufacturing")
            print("4. R&D")
            print("5. View Status")
            print("6. Save Game")
            print("7. Next Player" if len(self.players) > 1 else "7. (Single Player)")
            print("8. Quit")

            choice = input("\nChoice: ").strip()

            if choice == '1':
                self.advance_game_month(player)
                input("\nPress Enter to continue...")

            elif choice == '2':
                self.menu_create_phone(player)

            elif choice == '3':
                self.menu_manufacturing(player)

            elif choice == '4':
                self.menu_rnd(player)

            elif choice == '5':
                player.display_status()
                player.display_unlocked_tiers()
                player.display_ongoing_rnd()
                player.display_blueprints()
                player.display_manufacturing_queue()
                player.display_manufactured_phones()
                input("\nPress Enter to continue...")

            elif choice == '6':
                filename = input("Enter filename (default: savegame.json): ").strip()
                if not filename:
                    filename = "savegame.json"
                self.save_game(filename)
                input("\nPress Enter to continue...")

            elif choice == '7':
                if len(self.players) > 1:
                    self.next_player()
                    print(f"\n>>> Switching to {self.get_current_player().name} <<<")
                    input("Press Enter to continue...")
                    return  # Return to show next player's menu
                else:
                    print("Single player mode - no other players")
                    input("\nPress Enter to continue...")

            elif choice == '8':
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
