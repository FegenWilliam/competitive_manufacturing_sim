#!/usr/bin/env python3
"""
Competitive Phone Manufacturing Simulation
A game where up to 4 players compete to be the manufacturing leader of phones.
"""

import json
import os
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


# Quality tier enum
class Quality(Enum):
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"


# Game constants
CORE_PARTS = ['ram', 'soc', 'screen', 'battery', 'camera', 'casing', 'storage']
OPTIONAL_PARTS = ['fingerprint']
ALL_PARTS = CORE_PARTS + OPTIONAL_PARTS
MAX_TIER = 10
MAX_BLUEPRINTS = 10
STARTING_MONEY = 100000
MANUFACTURING_LIMIT_PER_MONTH = 1000

# Phone scoring weights (points per tier)
SCORING_WEIGHTS = {
    'soc': 5,
    'battery': 4,
    'screen': 3,
    'ram': 3,
    'camera': 2,
    'storage': 2,
    'casing': 1,
    'fingerprint': 0  # Optional part, doesn't contribute to tier scoring
}

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

# Part costs per tier (differentiated by component type)
# Hierarchy: SoC > Screen > RAM > Storage > Battery > Camera > Casing
PART_COSTS = {
    'soc': {
        1: 15, 2: 40, 3: 80, 4: 160, 5: 320,
        6: 600, 7: 1000, 8: 1600, 9: 2500, 10: 4000
    },
    'screen': {
        1: 12, 2: 30, 3: 65, 4: 130, 5: 260,
        6: 480, 7: 800, 8: 1300, 9: 2000, 10: 3200
    },
    'ram': {
        1: 8, 2: 20, 3: 45, 4: 90, 5: 180,
        6: 350, 7: 600, 8: 1000, 9: 1600, 10: 2600
    },
    'storage': {
        1: 7, 2: 18, 3: 40, 4: 80, 5: 160,
        6: 300, 7: 520, 8: 900, 9: 1450, 10: 2400
    },
    'battery': {
        1: 5, 2: 15, 3: 35, 4: 70, 5: 140,
        6: 260, 7: 450, 8: 780, 9: 1250, 10: 2100
    },
    'camera': {
        1: 4, 2: 12, 3: 28, 4: 60, 5: 120,
        6: 230, 7: 400, 8: 700, 9: 1100, 10: 1900
    },
    'casing': {
        1: 3, 2: 8, 3: 20, 4: 45, 5: 90,
        6: 180, 7: 320, 8: 560, 9: 900, 10: 1500
    },
    'fingerprint': {
        1: 3, 2: 8, 3: 18, 4: 40, 5: 80,
        6: 150, 7: 270, 8: 470, 9: 750, 10: 1250
    },
}

# Customer tier distribution (fixed percentages)
CUSTOMER_TIER_DISTRIBUTION = {
    'Entry Level': 0.15,  # 15%
    'Budget': 0.30,       # 30%
    'Midrange': 0.40,     # 40%
    'High End': 0.10,     # 10%
    'Flagship': 0.05,     # 5%
}

# Market size - fixed at 20,000 people
MARKET_SIZE = 20000

# Phone lifecycle constants (in months)
BASE_REPLACEMENT_TIME = 20  # Default replacement time
GAMER_REPLACEMENT_TIME = 16  # Gamers replace faster
CAMERA_CHECK_INTERVAL = 3  # Camera enthusiasts check every 3 months

# Customer types and their preferences (weights for each component)
CUSTOMER_TYPES = {
    'Gamer': {
        'soc': 10,      # Highest priority
        'ram': 8,
        'battery': 6,
        'screen': 4,
        'storage': 3,
        'camera': 2,
        'casing': 1,
    },
    'Camera Enthusiast': {
        'camera': 10,   # Highest priority
        'screen': 5,
        'storage': 4,
        'soc': 3,
        'battery': 3,
        'ram': 2,
        'casing': 2,
    },
    'Social Media User': {
        'camera': 8,
        'screen': 7,
        'battery': 7,
        'storage': 4,
        'soc': 3,
        'ram': 2,
        'casing': 3,
    },
    'Storage Seeker': {
        'storage': 10,  # Highest priority
        'soc': 4,
        'ram': 4,
        'battery': 4,
        'camera': 3,
        'screen': 3,
        'casing': 2,
    },
    'Design Lover': {
        'casing': 10,   # Highest priority
        'screen': 7,
        'camera': 5,
        'battery': 3,
        'soc': 3,
        'ram': 2,
        'storage': 2,
    },
    'Value Hunter': {
        # Balanced, but cares about price-to-performance
        'soc': 6,
        'ram': 5,
        'battery': 5,
        'storage': 5,
        'camera': 4,
        'screen': 4,
        'casing': 3,
    },
    'Battery Enthusiast': {
        'battery': 10,  # Highest priority
        'soc': 4,
        'screen': 4,
        'ram': 3,
        'storage': 3,
        'camera': 3,
        'casing': 2,
    },
    'Performance Seeker': {
        'soc': 9,
        'ram': 9,
        'storage': 5,
        'battery': 4,
        'screen': 3,
        'camera': 2,
        'casing': 2,
    },
    'Display Enthusiast': {
        'screen': 10,   # Highest priority
        'camera': 5,
        'casing': 5,
        'battery': 4,
        'soc': 3,
        'ram': 3,
        'storage': 2,
    },
    'All-Rounder': {
        # Balanced preferences
        'soc': 5,
        'ram': 5,
        'battery': 5,
        'screen': 5,
        'camera': 5,
        'storage': 5,
        'casing': 5,
    },
}


@dataclass
class CustomerGroup:
    """
    Represents a group of similar customers in the market.
    Groups customers by tier, type, and phone ownership for efficiency.
    """
    tier: str  # Entry Level, Budget, Midrange, High End, Flagship
    customer_type: str  # Gamer, Camera Enthusiast, etc.
    count: int  # Number of customers in this group

    # Phone ownership (None if no phone owned)
    owned_phone_company: Optional[str] = None  # Player name
    owned_phone_blueprint: Optional[str] = None  # Blueprint name
    purchase_month: Optional[int] = None  # When they bought it
    last_camera_check_month: Optional[int] = None  # For camera enthusiasts

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return CustomerGroup(**data)

    def evaluate_phone(self, phone: 'PhoneBlueprint') -> float:
        """
        Evaluate a phone based on customer preferences.
        Returns a satisfaction score.
        """
        preferences = CUSTOMER_TYPES[self.customer_type]
        score = 0

        # Evaluate each component based on preferences
        score += phone.soc_tier * preferences['soc']
        score += phone.ram_tier * preferences['ram']
        score += phone.battery_tier * preferences['battery']
        score += phone.screen_tier * preferences['screen']
        score += phone.camera_tier * preferences['camera']
        score += phone.storage_tier * preferences['storage']
        score += phone.casing_tier * preferences['casing']

        # Value hunters also consider price (lower price = better for them)
        if self.customer_type == 'Value Hunter':
            # Normalize price impact (assuming max reasonable price is 5000)
            price_penalty = phone.sell_price / 5000 * 20
            score -= price_penalty

        return score


@dataclass
class Customer:
    """Represents a customer in the market (DEPRECATED - use CustomerGroup instead)"""
    tier: str  # Entry Level, Budget, Midrange, High End, Flagship
    customer_type: str  # Gamer, Camera Enthusiast, etc.

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return Customer(**data)

    def evaluate_phone(self, phone: 'PhoneBlueprint') -> float:
        """
        Evaluate a phone based on customer preferences.
        Returns a satisfaction score.
        """
        preferences = CUSTOMER_TYPES[self.customer_type]
        score = 0

        # Evaluate each component based on preferences
        score += phone.soc_tier * preferences['soc']
        score += phone.ram_tier * preferences['ram']
        score += phone.battery_tier * preferences['battery']
        score += phone.screen_tier * preferences['screen']
        score += phone.camera_tier * preferences['camera']
        score += phone.storage_tier * preferences['storage']
        score += phone.casing_tier * preferences['casing']

        # Value hunters also consider price (lower price = better for them)
        if self.customer_type == 'Value Hunter':
            # Normalize price impact (assuming max reasonable price is 5000)
            price_penalty = phone.sell_price / 5000 * 20
            score -= price_penalty

        return score


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
    # Quality tiers for each component
    ram_quality: str = "Normal"
    soc_quality: str = "Normal"
    screen_quality: str = "Normal"
    battery_quality: str = "Normal"
    camera_quality: str = "Normal"
    casing_quality: str = "Normal"
    storage_quality: str = "Normal"
    fingerprint_quality: str = "Normal"

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return PhoneBlueprint(**data)

    def get_production_cost(self):
        """Calculate the cost to manufacture one unit with quality multipliers"""
        def apply_quality_multiplier(base_cost, quality):
            """Apply quality multiplier: Low=0.5x, Normal=1.0x, High=1.5x"""
            if quality == "Low":
                return base_cost * 0.5
            elif quality == "High":
                return base_cost * 1.5
            else:  # Normal
                return base_cost

        cost = 0
        cost += apply_quality_multiplier(PART_COSTS['ram'][self.ram_tier], self.ram_quality)
        cost += apply_quality_multiplier(PART_COSTS['soc'][self.soc_tier], self.soc_quality)
        cost += apply_quality_multiplier(PART_COSTS['screen'][self.screen_tier], self.screen_quality)
        cost += apply_quality_multiplier(PART_COSTS['battery'][self.battery_tier], self.battery_quality)
        cost += apply_quality_multiplier(PART_COSTS['camera'][self.camera_tier], self.camera_quality)
        cost += apply_quality_multiplier(PART_COSTS['casing'][self.casing_tier], self.casing_quality)
        cost += apply_quality_multiplier(PART_COSTS['storage'][self.storage_tier], self.storage_quality)
        if self.fingerprint_tier > 0:
            cost += apply_quality_multiplier(PART_COSTS['fingerprint'][self.fingerprint_tier], self.fingerprint_quality)
        return int(cost)

    def get_repair_return_rate(self):
        """
        Calculate the probability that a device will be returned for repairs.
        Based on screen and casing quality:
        - T1 screen + T1 casing: 5% return rate
        - Each tier upgrade reduces by 0.25% per part
        - T6 (Flagship): 2.5% return rate
        - T10: 0% return rate
        - High quality screen/casing: additional -0.25% each
        """
        base_rate = 5.0  # 5% base return rate
        screen_reduction = (self.screen_tier - 1) * 0.25
        casing_reduction = (self.casing_tier - 1) * 0.25

        # Additional reduction for high quality components
        if self.screen_quality == "High":
            screen_reduction += 0.25
        if self.casing_quality == "High":
            casing_reduction += 0.25

        return_rate = base_rate - screen_reduction - casing_reduction
        return max(0.0, return_rate)  # Never go below 0%

    def get_repair_cost(self):
        """Calculate the cost to repair one unit (25% of production cost)"""
        return int(self.get_production_cost() * 0.25)

    def calculate_score(self):
        """Calculate the phone's quality score based on component tiers and weights"""
        score = 0
        score += self.soc_tier * SCORING_WEIGHTS['soc']
        score += self.battery_tier * SCORING_WEIGHTS['battery']
        score += self.screen_tier * SCORING_WEIGHTS['screen']
        score += self.ram_tier * SCORING_WEIGHTS['ram']
        score += self.camera_tier * SCORING_WEIGHTS['camera']
        score += self.storage_tier * SCORING_WEIGHTS['storage']
        score += self.casing_tier * SCORING_WEIGHTS['casing']
        # Fingerprint doesn't contribute to tier scoring
        return score

    def get_tier_name(self, global_tech_level: int = 1):
        """Determine the phone's market tier based on score and global tech level"""
        score = self.calculate_score()

        # Calculate threshold shift based on tech advancement
        # Each tech level increase shifts thresholds by 20 points
        threshold_shift = (global_tech_level - 1) * 20

        # Define tier thresholds (base values + shift)
        entry_level_max = 20 + threshold_shift
        budget_max = 40 + threshold_shift
        midrange_max = 60 + threshold_shift
        high_end_max = 80 + threshold_shift
        flagship_max = 100 + threshold_shift

        if score <= entry_level_max:
            return "Entry Level"
        elif score <= budget_max:
            return "Budget"
        elif score <= midrange_max:
            return "Midrange"
        elif score <= high_end_max:
            return "High End"
        else:
            return "Flagship"

    def display(self, global_tech_level: int = 1):
        """Display blueprint details"""
        def quality_symbol(quality):
            """Return a short symbol for quality"""
            if quality == "Low":
                return "L"
            elif quality == "High":
                return "H"
            else:
                return "N"

        score = self.calculate_score()
        tier_name = self.get_tier_name(global_tech_level)

        print(f"\n  Blueprint: {self.name}")
        print(f"  Market Tier: {tier_name} (Score: {score})")
        print(f"  RAM: T{self.ram_tier}({quality_symbol(self.ram_quality)}) | SoC: T{self.soc_tier}({quality_symbol(self.soc_quality)}) | Screen: T{self.screen_tier}({quality_symbol(self.screen_quality)}) | Storage: T{self.storage_tier}({quality_symbol(self.storage_quality)})")
        print(f"  Battery: T{self.battery_tier}({quality_symbol(self.battery_quality)}) | Camera: T{self.camera_tier}({quality_symbol(self.camera_quality)}) | Casing: T{self.casing_tier}({quality_symbol(self.casing_quality)})")
        if self.fingerprint_tier > 0:
            print(f"  Fingerprint: T{self.fingerprint_tier}({quality_symbol(self.fingerprint_quality)})")
        else:
            print(f"  Fingerprint: None")
        print(f"  Quality: L=Low (0.5x cost), N=Normal (1x cost), H=High (1.5x cost)")
        print(f"  Production Cost: ${self.get_production_cost()} | Sell Price: ${self.sell_price}")
        print(f"  Profit per unit: ${self.sell_price - self.get_production_cost()}")
        print(f"  Repair Return Rate: {self.get_repair_return_rate():.2f}%")


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

        # Track sold devices and repairs (blueprint_name -> quantity)
        self.sold_devices: Dict[str, int] = {}  # Total devices sold (for calculating repair returns)
        self.pending_repairs: Dict[str, int] = {}  # Devices awaiting repair decision

        # Brand reputation system (0-100, starts at 50)
        self.brand_reputation: float = 50.0

        # Price history tracking: blueprint_name -> [(month, price), ...]
        self.price_history: Dict[str, List[tuple]] = {}

        # Track rejected repairs this month (for brand penalty calculation)
        self.rejected_repairs_this_month: int = 0

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
            'sold_devices': self.sold_devices,
            'pending_repairs': self.pending_repairs,
            'brand_reputation': self.brand_reputation,
            'price_history': self.price_history,
            'rejected_repairs_this_month': self.rejected_repairs_this_month,
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
        player.sold_devices = data.get('sold_devices', {})
        player.pending_repairs = data.get('pending_repairs', {})
        player.brand_reputation = data.get('brand_reputation', 50.0)
        player.price_history = data.get('price_history', {})
        player.rejected_repairs_this_month = data.get('rejected_repairs_this_month', 0)
        return player

    def display_status(self):
        """Display player's current status"""
        print(f"\n{'='*60}")
        print(f"Player: {self.name}")
        print(f"Month: {self.current_month} | Money: ${self.money:,}")
        print(f"Brand Reputation: {self.brand_reputation:.1f}/100")
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

    def display_blueprints(self, global_tech_level: int = 1):
        """Display all phone blueprints"""
        if not self.blueprints:
            print("\n--- No phone blueprints created ---")
            return

        print("\n--- Phone Blueprints ---")
        for i, bp in enumerate(self.blueprints, 1):
            print(f"\n{i}. ", end="")
            bp.display(global_tech_level)

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

    def display_pending_repairs(self):
        """Display devices pending repair"""
        if not self.pending_repairs:
            print("\n--- No Pending Repairs ---")
            return

        print("\n--- Pending Repairs ---")
        total_repair_cost = 0
        for blueprint_name, quantity in self.pending_repairs.items():
            # Find the blueprint to show repair cost
            blueprint = None
            for bp in self.blueprints:
                if bp.name == blueprint_name:
                    blueprint = bp
                    break
            if blueprint:
                repair_cost_per_unit = blueprint.get_repair_cost()
                total_cost = repair_cost_per_unit * quantity
                total_repair_cost += total_cost
                return_rate = blueprint.get_repair_return_rate()
                print(f"  {blueprint_name}: {quantity} units @ ${repair_cost_per_unit}/unit = ${total_cost:,} total (Return rate: {return_rate:.2f}%)")

        if total_repair_cost > 0:
            print(f"\n  Total repair cost if fixing all: ${total_repair_cost:,}")

    def complete_manufacturing(self):
        """Complete manufacturing items that are ready (separate from advancing month)"""
        completed_manufacturing = []
        new_queue = []

        for blueprint_name, quantity, months_remaining in self.manufacturing_queue:
            if months_remaining <= 0:
                # Manufacturing is complete
                completed_manufacturing.append((blueprint_name, quantity))
                if blueprint_name not in self.manufactured_phones:
                    self.manufactured_phones[blueprint_name] = 0
                self.manufactured_phones[blueprint_name] += quantity
            else:
                # Still in progress
                new_queue.append((blueprint_name, quantity, months_remaining))

        self.manufacturing_queue = new_queue
        return completed_manufacturing

    def advance_month(self):
        """Advance to next month and update R&D projects (manufacturing is handled separately)"""
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

        # Decrement manufacturing queue timers (actual completion happens in complete_manufacturing)
        new_queue = []
        for blueprint_name, quantity, months_remaining in self.manufacturing_queue:
            new_queue.append((blueprint_name, quantity, months_remaining - 1))
        self.manufacturing_queue = new_queue

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
                        quality: Dict[str, str] = None,
                        min_tier: int = 1, max_tier: int = MAX_TIER,
                        global_tech_level: int = 1) -> bool:
        """Create a new phone blueprint"""
        # Check if max blueprints reached
        if len(self.blueprints) >= MAX_BLUEPRINTS:
            print(f"❌ Maximum blueprint limit reached ({MAX_BLUEPRINTS})! Delete a blueprint to create a new one.")
            return False

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

        # Set default quality to Normal if not provided
        if quality is None:
            quality = {}
        for part in CORE_PARTS + OPTIONAL_PARTS:
            if part not in quality:
                quality[part] = "Normal"

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
            sell_price=sell_price,
            ram_quality=quality['ram'],
            soc_quality=quality['soc'],
            screen_quality=quality['screen'],
            battery_quality=quality['battery'],
            camera_quality=quality['camera'],
            casing_quality=quality['casing'],
            storage_quality=quality['storage'],
            fingerprint_quality=quality['fingerprint']
        )

        self.blueprints.append(blueprint)

        # Track the initial price for brand reputation monitoring
        self.track_blueprint_price(name, sell_price)

        print(f"\n✓ Created blueprint: {name}")
        blueprint.display(global_tech_level)
        return True

    def delete_blueprint(self, blueprint_name: str) -> bool:
        """Delete a phone blueprint"""
        # Find blueprint
        blueprint = None
        for bp in self.blueprints:
            if bp.name == blueprint_name:
                blueprint = bp
                break

        if not blueprint:
            print(f"❌ Blueprint '{blueprint_name}' not found!")
            return False

        # Check if there are manufactured phones
        if blueprint_name in self.manufactured_phones and self.manufactured_phones[blueprint_name] > 0:
            print(f"❌ Cannot delete blueprint '{blueprint_name}': {self.manufactured_phones[blueprint_name]} units in inventory!")
            print("   Sell all units before deleting the blueprint.")
            return False

        # Check if there are pending repairs
        if blueprint_name in self.pending_repairs and self.pending_repairs[blueprint_name] > 0:
            print(f"❌ Cannot delete blueprint '{blueprint_name}': {self.pending_repairs[blueprint_name]} units awaiting repair!")
            print("   Repair or reject all repairs before deleting the blueprint.")
            return False

        # Check if there are ongoing manufacturing jobs
        for name, quantity, months_remaining in self.manufacturing_queue:
            if name == blueprint_name:
                print(f"❌ Cannot delete blueprint '{blueprint_name}': {quantity} units being manufactured!")
                print("   Wait for manufacturing to complete before deleting the blueprint.")
                return False

        # Delete the blueprint
        self.blueprints.remove(blueprint)

        # Clean up related data
        if blueprint_name in self.manufactured_phones:
            del self.manufactured_phones[blueprint_name]
        if blueprint_name in self.sold_devices:
            del self.sold_devices[blueprint_name]
        if blueprint_name in self.price_history:
            del self.price_history[blueprint_name]

        print(f"\n✓ Deleted blueprint: {blueprint_name}")
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

        # First month: instant manufacturing (0 months), after that: 1 month
        if self.current_month == 1:
            months_to_complete = 0
            print(f"\n✓ Started manufacturing {quantity}x {blueprint_name}")
            print(f"  Parts cost: ${total_cost:,}")
            print(f"  Will complete instantly (ready to sell this month)")
            print(f"  Remaining balance: ${self.money:,}")
            print(f"  Manufacturing capacity used: {self.manufacturing_used_this_month}/{MANUFACTURING_LIMIT_PER_MONTH}")
        else:
            months_to_complete = 1
            print(f"\n✓ Started manufacturing {quantity}x {blueprint_name}")
            print(f"  Parts cost: ${total_cost:,}")
            print(f"  Will complete at end of month (ready to sell next month)")
            print(f"  Remaining balance: ${self.money:,}")
            print(f"  Manufacturing capacity used: {self.manufacturing_used_this_month}/{MANUFACTURING_LIMIT_PER_MONTH}")

        self.manufacturing_queue.append((blueprint_name, quantity, months_to_complete))
        return True

    def generate_monthly_repairs(self):
        """
        Generate repair returns based on sold devices.
        Called at the start of each month to simulate device failures.
        """
        new_repairs = {}

        for blueprint_name, sold_count in self.sold_devices.items():
            if sold_count <= 0:
                continue

            # Find the blueprint to get return rate
            blueprint = None
            for bp in self.blueprints:
                if bp.name == blueprint_name:
                    blueprint = bp
                    break

            if not blueprint:
                continue

            # Calculate how many devices return for repair
            return_rate = blueprint.get_repair_return_rate()
            if return_rate > 0:
                # Use probabilistic calculation: sold_count * (return_rate / 100)
                expected_repairs = sold_count * (return_rate / 100.0)
                # Add some randomness but keep it reasonable
                repairs_this_month = int(expected_repairs)
                # Add fractional chance (e.g., 2.7 expected = 2 guaranteed + 70% chance of 1 more)
                if random.random() < (expected_repairs - repairs_this_month):
                    repairs_this_month += 1

                if repairs_this_month > 0:
                    new_repairs[blueprint_name] = repairs_this_month

        # Add new repairs to pending repairs
        for blueprint_name, count in new_repairs.items():
            if blueprint_name not in self.pending_repairs:
                self.pending_repairs[blueprint_name] = 0
            self.pending_repairs[blueprint_name] += count

        return new_repairs

    def repair_devices(self, blueprint_name: str, quantity: int) -> bool:
        """
        Repair a specified quantity of devices for a given blueprint.
        Returns True if successful, False otherwise.
        """
        # Check if there are pending repairs for this blueprint
        if blueprint_name not in self.pending_repairs or self.pending_repairs[blueprint_name] <= 0:
            print(f"❌ No pending repairs for {blueprint_name}")
            return False

        # Check quantity
        if quantity <= 0:
            print(f"❌ Invalid quantity: {quantity}")
            return False

        if quantity > self.pending_repairs[blueprint_name]:
            print(f"❌ Only {self.pending_repairs[blueprint_name]} units need repair")
            return False

        # Find the blueprint
        blueprint = None
        for bp in self.blueprints:
            if bp.name == blueprint_name:
                blueprint = bp
                break

        if not blueprint:
            print(f"❌ Blueprint '{blueprint_name}' not found!")
            return False

        # Calculate repair cost
        repair_cost_per_unit = blueprint.get_repair_cost()
        total_cost = repair_cost_per_unit * quantity

        # Check funds
        if self.money < total_cost:
            print(f"❌ Insufficient funds. Need ${total_cost:,}, have ${self.money:,}")
            return False

        # Complete the repair
        self.money -= total_cost
        self.pending_repairs[blueprint_name] -= quantity

        # Remove from pending if none left
        if self.pending_repairs[blueprint_name] <= 0:
            del self.pending_repairs[blueprint_name]

        print(f"\n✓ Repaired {quantity}x {blueprint_name}")
        print(f"  Repair cost: ${total_cost:,}")
        print(f"  Remaining balance: ${self.money:,}")
        return True

    def repair_all_devices(self) -> bool:
        """
        Repair all pending devices.
        Returns True if successful, False otherwise.
        """
        if not self.pending_repairs:
            print("❌ No pending repairs")
            return False

        # Calculate total cost
        total_cost = 0
        repair_list = []
        for blueprint_name, quantity in self.pending_repairs.items():
            blueprint = None
            for bp in self.blueprints:
                if bp.name == blueprint_name:
                    blueprint = bp
                    break
            if blueprint:
                repair_cost = blueprint.get_repair_cost() * quantity
                total_cost += repair_cost
                repair_list.append((blueprint_name, quantity, repair_cost))

        # Check funds
        if self.money < total_cost:
            print(f"❌ Insufficient funds. Need ${total_cost:,}, have ${self.money:,}")
            return False

        # Complete all repairs
        self.money -= total_cost
        self.pending_repairs.clear()

        print(f"\n✓ Repaired all devices:")
        for blueprint_name, quantity, cost in repair_list:
            print(f"  - {quantity}x {blueprint_name}: ${cost:,}")
        print(f"\n  Total repair cost: ${total_cost:,}")
        print(f"  Remaining balance: ${self.money:,}")
        return True

    def reject_repairs(self, blueprint_name: str, quantity: int) -> bool:
        """
        Reject repairs for a specified quantity of devices.
        This removes the devices from pending repairs without paying,
        but incurs a brand reputation penalty.
        Returns True if successful, False otherwise.
        """
        # Check if there are pending repairs for this blueprint
        if blueprint_name not in self.pending_repairs or self.pending_repairs[blueprint_name] <= 0:
            print(f"❌ No pending repairs for {blueprint_name}")
            return False

        # Check quantity
        if quantity <= 0:
            print(f"❌ Invalid quantity: {quantity}")
            return False

        if quantity > self.pending_repairs[blueprint_name]:
            print(f"❌ Only {self.pending_repairs[blueprint_name]} units pending repair")
            return False

        # Reject the repairs
        self.pending_repairs[blueprint_name] -= quantity

        # Remove from pending if none left
        if self.pending_repairs[blueprint_name] <= 0:
            del self.pending_repairs[blueprint_name]

        # Track rejected repairs for brand penalty (applied at month end)
        self.rejected_repairs_this_month += quantity

        print(f"\n⚠️  Rejected repairs for {quantity}x {blueprint_name}")
        print(f"  Brand reputation will be affected (-1 per device, max -10 per month)")
        print(f"  Total rejected this month: {self.rejected_repairs_this_month}")
        return True

    def calculate_brand_reputation_changes(self, global_tech_level: int):
        """
        Calculate and apply monthly brand reputation changes based on:
        1. Build quality - cheap casing on flagship phones (-1 per month)
        2. Component quality - low quality parts (-2), high quality parts (+2)
        3. Price reliability - price swings over 3 months (-2 per month)
        4. Rejected repairs (-1 per device, max -10 per month)
        """
        reputation_changes = []
        total_change = 0

        # 1. Check build quality - penalize cheap casing on flagship phones
        for blueprint in self.blueprints:
            tier_name = blueprint.get_tier_name(global_tech_level)

            # If it's a flagship/high-end phone with low-tier casing, penalize
            if tier_name in ["Flagship", "High End"]:
                # Entry-level casing is T1-T2
                if blueprint.casing_tier <= 2:
                    reputation_changes.append(f"  Cheap casing on {tier_name} phone '{blueprint.name}': -1")
                    total_change -= 1

        # 2. Check component quality for each product
        low_quality_count = 0
        high_quality_count = 0

        for blueprint in self.blueprints:
            # Check if any component uses low quality
            if any([
                blueprint.ram_quality == "Low",
                blueprint.soc_quality == "Low",
                blueprint.screen_quality == "Low",
                blueprint.battery_quality == "Low",
                blueprint.camera_quality == "Low",
                blueprint.casing_quality == "Low",
                blueprint.storage_quality == "Low",
                blueprint.fingerprint_quality == "Low" if blueprint.fingerprint_tier > 0 else False
            ]):
                low_quality_count += 1

            # Check if any component uses high quality
            if any([
                blueprint.ram_quality == "High",
                blueprint.soc_quality == "High",
                blueprint.screen_quality == "High",
                blueprint.battery_quality == "High",
                blueprint.camera_quality == "High",
                blueprint.casing_quality == "High",
                blueprint.storage_quality == "High",
                blueprint.fingerprint_quality == "High" if blueprint.fingerprint_tier > 0 else False
            ]):
                high_quality_count += 1

        # Apply quality-based reputation changes (per product)
        if low_quality_count > 0:
            penalty = low_quality_count * 2
            reputation_changes.append(f"  Low quality components in {low_quality_count} product(s): -{penalty}")
            total_change -= penalty

        if high_quality_count > 0:
            bonus = high_quality_count * 2
            reputation_changes.append(f"  High quality components in {high_quality_count} product(s): +{bonus}")
            total_change += bonus

        # 3. Check price reliability - look for price swings over last 3 months
        for blueprint_name, price_records in self.price_history.items():
            # Only check if we have at least 3 months of data
            if len(price_records) >= 3:
                # Get the last 3 prices
                recent_prices = [price for _, price in price_records[-3:]]

                # Calculate if there's a significant swing (more than 20% change between any consecutive months)
                has_swing = False
                for i in range(len(recent_prices) - 1):
                    price1, price2 = recent_prices[i], recent_prices[i + 1]
                    if price1 > 0:  # Avoid division by zero
                        percent_change = abs(price2 - price1) / price1 * 100
                        if percent_change > 20:
                            has_swing = True
                            break

                if has_swing:
                    reputation_changes.append(f"  Unreliable pricing for '{blueprint_name}': -2")
                    total_change -= 2

        # 4. Apply rejected repairs penalty (capped at -10 per month)
        if self.rejected_repairs_this_month > 0:
            penalty = min(self.rejected_repairs_this_month, 10)
            reputation_changes.append(f"  Rejected {self.rejected_repairs_this_month} repairs: -{penalty}")
            total_change -= penalty

        # Apply the changes
        old_reputation = self.brand_reputation
        self.brand_reputation = max(0, min(100, self.brand_reputation + total_change))

        # Reset monthly counter
        self.rejected_repairs_this_month = 0

        # Display changes if any
        if reputation_changes:
            print(f"\n📊 Brand Reputation Changes for {self.name}:")
            for change in reputation_changes:
                print(change)
            print(f"  Total change: {total_change:+.1f}")
            print(f"  Brand reputation: {old_reputation:.1f} → {self.brand_reputation:.1f}")

        return total_change

    def track_blueprint_price(self, blueprint_name: str, price: int):
        """Track price history for a blueprint"""
        if blueprint_name not in self.price_history:
            self.price_history[blueprint_name] = []

        # Add current month and price
        self.price_history[blueprint_name].append((self.current_month, price))

        # Keep only last 3 months of history
        if len(self.price_history[blueprint_name]) > 3:
            self.price_history[blueprint_name] = self.price_history[blueprint_name][-3:]


class CustomerMarket:
    """Manages the customer market with persistent phone ownership tracking"""

    def __init__(self):
        self.customer_groups: List[CustomerGroup] = []
        self.current_month = 0
        self.sales_history: Dict[int, Dict[str, int]] = {}  # month -> {player_name: sales_count}
        self.is_initialized = False

    def to_dict(self):
        """Convert market to dictionary"""
        return {
            'customer_groups': [g.to_dict() for g in self.customer_groups],
            'current_month': self.current_month,
            'sales_history': self.sales_history,
            'is_initialized': self.is_initialized,
        }

    @staticmethod
    def from_dict(data):
        """Load market from dictionary"""
        market = CustomerMarket()
        market.customer_groups = [CustomerGroup.from_dict(g) for g in data.get('customer_groups', [])]
        market.current_month = data.get('current_month', 0)
        market.sales_history = data.get('sales_history', {})
        market.is_initialized = data.get('is_initialized', False)
        return market

    def initialize_market(self):
        """
        Initialize the market with 20,000 people distributed by budget tier and personality type.
        Everyone starts without owning a phone.
        """
        if self.is_initialized:
            print("\n⚠️  Market already initialized!")
            return

        print(f"\n📊 Initializing market with {MARKET_SIZE} people...")

        # Create customer groups distributed by tier and type
        customer_types_list = list(CUSTOMER_TYPES.keys())
        num_types = len(customer_types_list)

        for tier_name, tier_percentage in CUSTOMER_TIER_DISTRIBUTION.items():
            tier_count = int(MARKET_SIZE * tier_percentage)

            # Distribute evenly across customer types within each tier
            customers_per_type = tier_count // num_types
            remainder = tier_count % num_types

            for i, customer_type in enumerate(customer_types_list):
                # Add remainder to first few types to reach exact count
                count = customers_per_type + (1 if i < remainder else 0)

                if count > 0:
                    group = CustomerGroup(
                        tier=tier_name,
                        customer_type=customer_type,
                        count=count
                    )
                    self.customer_groups.append(group)

        self.is_initialized = True

        print(f"  ✓ Created {len(self.customer_groups)} customer groups")
        print(f"  Total people: {sum(g.count for g in self.customer_groups)}")

        # Display distribution
        print("\n  Distribution by tier:")
        for tier_name, percentage in CUSTOMER_TIER_DISTRIBUTION.items():
            count = sum(g.count for g in self.customer_groups if g.tier == tier_name)
            print(f"    {tier_name}: {count} ({percentage*100:.0f}%)")

        print("\n  Distribution by type:")
        for customer_type in customer_types_list:
            count = sum(g.count for g in self.customer_groups if g.customer_type == customer_type)
            percentage = (count / MARKET_SIZE * 100) if MARKET_SIZE > 0 else 0
            print(f"    {customer_type}: {count} ({percentage:.1f}%)")

    def calculate_phone_lifecycle(self, blueprint: 'PhoneBlueprint', customer_type: str) -> int:
        """
        Calculate how many months a phone should last for a given customer type.

        Base rules:
        - Default: 20 months
        - Gamer: 16 months (uses phone at max all the time)
        - Others: 20 months base

        Tier modifications (T3 is base/midrange):
        - T4 parts: +1 month per part
        - T2 parts: -1 month per part

        Quality modifications:
        - High quality: +1 month per high quality part
        - Low quality: -1 month per low quality part

        Special bonuses:
        - Battery: Extra +1 month for high quality battery (total +2)
        """
        # Start with base time
        if customer_type == 'Gamer':
            base_time = GAMER_REPLACEMENT_TIME
        else:
            base_time = BASE_REPLACEMENT_TIME

        # Count parts by tier (T3 is baseline midrange)
        tier_bonus = 0
        parts_tiers = [
            blueprint.ram_tier,
            blueprint.soc_tier,
            blueprint.screen_tier,
            blueprint.battery_tier,
            blueprint.camera_tier,
            blueprint.casing_tier,
            blueprint.storage_tier,
        ]
        if blueprint.fingerprint_tier > 0:
            parts_tiers.append(blueprint.fingerprint_tier)

        for tier in parts_tiers:
            if tier >= 4:  # T4 and above
                tier_bonus += 1
            elif tier <= 2:  # T2 and below
                tier_bonus -= 1

        # Count quality bonuses/penalties
        quality_bonus = 0
        parts_qualities = [
            blueprint.ram_quality,
            blueprint.soc_quality,
            blueprint.screen_quality,
            blueprint.battery_quality,
            blueprint.camera_quality,
            blueprint.casing_quality,
            blueprint.storage_quality,
        ]
        if blueprint.fingerprint_tier > 0:
            parts_qualities.append(blueprint.fingerprint_quality)

        for quality in parts_qualities:
            if quality == "High":
                quality_bonus += 1
            elif quality == "Low":
                quality_bonus -= 1

        # Special battery bonus (high quality battery gets extra +1, total +2)
        if blueprint.battery_quality == "High":
            quality_bonus += 1

        # Calculate total lifecycle
        total_lifecycle = base_time + tier_bonus + quality_bonus

        # Minimum 6 months
        return max(6, total_lifecycle)

    def display_customer_breakdown(self):
        """Display breakdown of customers by tier, type, and phone ownership"""
        total_people = sum(g.count for g in self.customer_groups)

        print(f"\n📊 Customer Market Analysis (Month {self.current_month}):")
        print(f"  Total people: {total_people}")

        # Count by tier
        tier_counts = {}
        for group in self.customer_groups:
            tier_counts[group.tier] = tier_counts.get(group.tier, 0) + group.count

        print("\n  By Tier:")
        for tier in ['Entry Level', 'Budget', 'Midrange', 'High End', 'Flagship']:
            count = tier_counts.get(tier, 0)
            percentage = (count / total_people * 100) if total_people > 0 else 0
            print(f"    {tier}: {count} ({percentage:.1f}%)")

        # Count by type
        type_counts = {}
        for group in self.customer_groups:
            type_counts[group.customer_type] = type_counts.get(group.customer_type, 0) + group.count

        print("\n  By Type:")
        for customer_type in sorted(CUSTOMER_TYPES.keys()):
            count = type_counts.get(customer_type, 0)
            percentage = (count / total_people * 100) if total_people > 0 else 0
            print(f"    {customer_type}: {count} ({percentage:.1f}%)")

        # Count phone ownership
        people_with_phones = sum(g.count for g in self.customer_groups if g.owned_phone_company is not None)
        people_without_phones = total_people - people_with_phones

        print("\n  Phone Ownership:")
        print(f"    With phones: {people_with_phones} ({people_with_phones/total_people*100:.1f}%)")
        print(f"    Without phones: {people_without_phones} ({people_without_phones/total_people*100:.1f}%)")

        # Show market share by company
        if people_with_phones > 0:
            company_counts = {}
            for group in self.customer_groups:
                if group.owned_phone_company:
                    company_counts[group.owned_phone_company] = company_counts.get(group.owned_phone_company, 0) + group.count

            print("\n  Market Share:")
            for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / people_with_phones * 100) if people_with_phones > 0 else 0
                print(f"    {company}: {count} ({percentage:.1f}%)")

    def simulate_purchases(self, players: List[Player], global_tech_level: int):
        """
        Simulate customer purchases with persistent phone ownership tracking.
        Customers only buy if:
        1. They don't own a phone, OR
        2. Their phone's lifecycle has expired, OR
        3. (Camera Enthusiast only) A better camera tier is available
        """
        print(f"\n🛒 Simulating customer purchases for Month {self.current_month}...")

        # Build blueprint lookup for all players
        player_blueprints = {}  # player_name -> {blueprint_name -> blueprint}
        for player in players:
            player_blueprints[player.name] = {}
            for bp in player.blueprints:
                player_blueprints[player.name][bp.name] = bp

        # Collect all available phones from all players
        available_phones = []  # List of (player, blueprint)
        inventory_tracker = {}  # (player_name, blueprint_name) -> available_count
        for player in players:
            for phone_name, quantity in player.manufactured_phones.items():
                if quantity > 0:
                    blueprint = player_blueprints[player.name].get(phone_name)
                    if blueprint:
                        available_phones.append((player, blueprint))
                        inventory_tracker[(player.name, phone_name)] = quantity

        if not available_phones:
            print("  ❌ No phones available for purchase!")
            return

        # Track sales for this month
        sales_by_player = {}
        for player in players:
            sales_by_player[player.name] = 0

        # Track sales by phone
        sales_by_phone = {}  # (player_name, phone_name) -> count

        # Track brand reputation changes based on retention
        retention_changes = {}  # player_name -> change
        for player in players:
            retention_changes[player.name] = 0

        # Process each customer group
        groups_to_split = []  # Groups that need to be split due to purchases

        for group_idx, group in enumerate(self.customer_groups):
            # Determine if this group should buy phones this month
            should_buy_count = 0  # How many in this group should buy

            if group.owned_phone_company is None:
                # No phone owned - everyone in group wants to buy
                should_buy_count = group.count
            else:
                # Check if phone lifecycle has expired
                months_owned = self.current_month - group.purchase_month

                # Get the blueprint they own
                owned_blueprint = None
                if group.owned_phone_company in player_blueprints:
                    owned_blueprint = player_blueprints[group.owned_phone_company].get(group.owned_phone_blueprint)

                if owned_blueprint:
                    lifecycle = self.calculate_phone_lifecycle(owned_blueprint, group.customer_type)

                    # Check lifecycle expiration
                    if months_owned >= lifecycle:
                        should_buy_count = group.count

                        # Track retention for brand reputation
                        if months_owned <= 12:
                            retention_changes[group.owned_phone_company] -= group.count
                        elif months_owned >= 24:
                            retention_changes[group.owned_phone_company] += group.count

                    # Special check for Camera Enthusiasts - they check every 3 months
                    elif group.customer_type == 'Camera Enthusiast':
                        # Check if it's time for camera check
                        last_check = group.last_camera_check_month or group.purchase_month
                        if self.current_month - last_check >= CAMERA_CHECK_INTERVAL:
                            # Look for better camera tier
                            current_camera_tier = owned_blueprint.camera_tier

                            # Check if any available phone has better camera
                            for player, blueprint in available_phones:
                                phone_tier = blueprint.get_tier_name(global_tech_level)
                                if phone_tier == group.tier and blueprint.camera_tier > current_camera_tier:
                                    should_buy_count = group.count
                                    # Track retention (switching before lifecycle)
                                    if months_owned <= 12:
                                        retention_changes[group.owned_phone_company] -= group.count
                                    break

                            # Update last camera check regardless of purchase
                            group.last_camera_check_month = self.current_month

            # If nobody in this group should buy, skip
            if should_buy_count == 0:
                continue

            # Find phones matching this group's tier
            matching_phones = []
            for player, blueprint in available_phones:
                phone_tier = blueprint.get_tier_name(global_tech_level)
                if phone_tier == group.tier:
                    matching_phones.append((player, blueprint))

            if not matching_phones:
                continue  # No phones available in this tier

            # Evaluate each phone based on group preferences
            best_phone = None
            best_score = -float('inf')
            best_player = None

            for player, blueprint in matching_phones:
                score = group.evaluate_phone(blueprint)

                # Apply brand reputation bonus
                brand_multiplier = 1.0 + (player.brand_reputation / 100.0 * 0.2)
                score *= brand_multiplier

                if score > best_score:
                    best_score = score
                    best_phone = blueprint
                    best_player = player

            # Purchase phones for this group
            if best_phone and best_player:
                inventory_key = (best_player.name, best_phone.name)
                available_qty = inventory_tracker.get(inventory_key, 0)

                if available_qty > 0:
                    # Determine how many can actually buy (limited by inventory)
                    actual_buy_count = min(should_buy_count, available_qty)

                    # Complete the purchases
                    best_player.manufactured_phones[best_phone.name] -= actual_buy_count
                    best_player.money += best_phone.sell_price * actual_buy_count

                    # Track sold devices for repair calculations
                    if best_phone.name not in best_player.sold_devices:
                        best_player.sold_devices[best_phone.name] = 0
                    best_player.sold_devices[best_phone.name] += actual_buy_count

                    # Track sales
                    sales_by_player[best_player.name] += actual_buy_count
                    key = (best_player.name, best_phone.name)
                    sales_by_phone[key] = sales_by_phone.get(key, 0) + actual_buy_count

                    # Update inventory tracker
                    inventory_tracker[inventory_key] -= actual_buy_count

                    # Handle group splitting if needed
                    if actual_buy_count < group.count:
                        # Split the group: some bought, some didn't
                        groups_to_split.append((group_idx, actual_buy_count, best_player.name, best_phone.name))
                    else:
                        # Everyone in the group bought
                        group.owned_phone_company = best_player.name
                        group.owned_phone_blueprint = best_phone.name
                        group.purchase_month = self.current_month
                        group.last_camera_check_month = self.current_month

        # Handle group splits (process in reverse to maintain indices)
        for group_idx, buy_count, company, blueprint_name in reversed(groups_to_split):
            original_group = self.customer_groups[group_idx]

            # Create new group for buyers
            buyer_group = CustomerGroup(
                tier=original_group.tier,
                customer_type=original_group.customer_type,
                count=buy_count,
                owned_phone_company=company,
                owned_phone_blueprint=blueprint_name,
                purchase_month=self.current_month,
                last_camera_check_month=self.current_month
            )

            # Update original group (non-buyers)
            original_group.count -= buy_count

            # Add buyer group
            self.customer_groups.append(buyer_group)

        # Apply brand reputation changes based on retention
        for player in players:
            change = retention_changes[player.name]
            if change != 0:
                player.brand_reputation = max(0, min(100, player.brand_reputation + change))
                if change < 0:
                    print(f"  ⚠️  {player.name} brand reputation: {change} (poor retention <12 months)")
                else:
                    print(f"  ✓ {player.name} brand reputation: +{change} (good retention ≥24 months)")

        # Store sales history
        self.sales_history[self.current_month] = sales_by_player

        # Display results
        print(f"\n💰 Sales Results for Month {self.current_month}:")
        total_sales = 0
        total_people = sum(g.count for g in self.customer_groups)

        for player in players:
            sales = sales_by_player[player.name]
            total_sales += sales
            revenue = sum(
                sales_by_phone.get((player.name, bp.name), 0) * bp.sell_price
                for bp in player.blueprints
            )
            print(f"  {player.name}: {sales} phones sold, ${revenue:,} revenue")

        people_with_phones = sum(g.count for g in self.customer_groups if g.owned_phone_company is not None)
        print(f"\n  Total sales: {total_sales} phones")
        print(f"  Market penetration: {people_with_phones}/{total_people} ({people_with_phones/total_people*100:.1f}%) own phones")

        # Show detailed breakdown by phone
        if sales_by_phone:
            print(f"\n  Sales by phone model:")
            for (player_name, phone_name), count in sorted(sales_by_phone.items(), key=lambda x: x[1], reverse=True):
                print(f"    {player_name} - {phone_name}: {count} units")


class Game:
    """Main game controller"""

    def __init__(self):
        self.players: List[Player] = []
        self.current_player_index = 0
        self.global_month = 1  # Global game month
        self.global_tech_level = 1  # Determines which 5 tiers are available (1 = tiers 1-5, 2 = tiers 2-6, etc.)
        self.months_until_tech_advance = 36  # Tech advances every 3 years (36 months)
        self.customer_market = CustomerMarket()  # Customer market
        self.players_ready_for_next_month = set()  # Track which players have advanced this turn

    def to_dict(self):
        """Convert game state to dictionary"""
        return {
            'players': [p.to_dict() for p in self.players],
            'current_player_index': self.current_player_index,
            'global_month': self.global_month,
            'global_tech_level': self.global_tech_level,
            'months_until_tech_advance': self.months_until_tech_advance,
            'customer_market': self.customer_market.to_dict(),
            'players_ready_for_next_month': list(self.players_ready_for_next_month),
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
        if 'customer_market' in data:
            game.customer_market = CustomerMarket.from_dict(data['customer_market'])
        else:
            game.customer_market = CustomerMarket()
        game.players_ready_for_next_month = set(data.get('players_ready_for_next_month', []))
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

    def advance_game_month(self):
        """Advance the game month - happens when all players are ready"""
        print(f"\n{'='*60}")
        print(f"END OF MONTH {self.global_month} REPORT")
        print(f"{'='*60}")

        # 1. Simulate customer purchases for current month (BEFORE manufacturing completes)
        if self.customer_market.customer_groups:
            self.customer_market.simulate_purchases(self.players, self.global_tech_level)
        else:
            print("\n❌ No customer data yet. Market needs to be initialized.")

        # 2. Complete manufacturing for all players (AFTER sales)
        print(f"\n--- Manufacturing Completion ---")
        any_manufacturing = False
        for player in self.players:
            completed = player.complete_manufacturing()
            if completed:
                any_manufacturing = True
                print(f"\n📦 {player.name} - Manufacturing Completed:")
                for name, qty in completed:
                    print(f"  - {qty}x {name} ready to sell!")

        if not any_manufacturing:
            print("  No manufacturing completed this month.")

        # 3. Advance global month
        self.global_month += 1
        self.months_until_tech_advance -= 1

        print(f"\n{'='*60}")
        print(f"✓ Advanced to Month {self.global_month}")
        print(f"{'='*60}")

        # 4. Advance each player's month (R&D progress, reset limits)
        for player in self.players:
            player.advance_month()

        # 4.5. Generate repair returns for each player
        print(f"\n--- Device Repairs ---")
        any_repairs = False
        for player in self.players:
            new_repairs = player.generate_monthly_repairs()
            if new_repairs:
                any_repairs = True
                print(f"\n🔧 {player.name} - Devices Returned for Repair:")
                for blueprint_name, count in new_repairs.items():
                    # Find blueprint to show repair cost
                    blueprint = None
                    for bp in player.blueprints:
                        if bp.name == blueprint_name:
                            blueprint = bp
                            break
                    if blueprint:
                        repair_cost = blueprint.get_repair_cost()
                        return_rate = blueprint.get_repair_return_rate()
                        print(f"  - {count}x {blueprint_name} (Return rate: {return_rate:.2f}%, Cost: ${repair_cost}/unit)")

        if not any_repairs:
            print("  No devices returned for repair this month.")

        # 4.6. Calculate brand reputation changes for each player
        print(f"\n--- Brand Reputation Update ---")
        any_brand_changes = False
        for player in self.players:
            change = player.calculate_brand_reputation_changes(self.global_tech_level)
            if change != 0:
                any_brand_changes = True

        if not any_brand_changes:
            print("  No brand reputation changes this month.")

        # 5. Check if it's time for tech advancement
        if self.months_until_tech_advance <= 0:
            self.advance_global_tech()
            self.months_until_tech_advance = 36  # Reset counter

        # 6. Update current month for market tracking
        self.customer_market.current_month = self.global_month

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

        # 7. Reset players ready tracking
        self.players_ready_for_next_month.clear()

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

        # Initialize the market with 20,000 people
        self.customer_market.initialize_market()
        self.customer_market.current_month = self.global_month

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

    def menu_manage_blueprints(self, player: Player):
        """Manage blueprints menu"""
        while True:
            print("\n" + "="*60)
            print("MANAGE BLUEPRINTS")
            print("="*60)
            print(f"Blueprints: {len(player.blueprints)}/{MAX_BLUEPRINTS}")
            player.display_blueprints(self.global_tech_level)

            if not player.blueprints:
                print("\n❌ No blueprints to manage!")
                input("\nPress Enter to continue...")
                break

            print("\nActions:")
            print("1. Delete blueprint")
            print("2. Back to main menu")

            choice = input("\nChoice: ").strip()

            if choice == '1':
                print("\nSelect blueprint to delete:")
                for i, bp in enumerate(player.blueprints, 1):
                    tier_name = bp.get_tier_name(self.global_tech_level)
                    print(f"{i}. {bp.name} [{tier_name}]")

                try:
                    bp_choice = int(input("\nBlueprint number (0 to cancel): ")) - 1
                    if bp_choice == -1:
                        print("❌ Cancelled")
                    elif 0 <= bp_choice < len(player.blueprints):
                        blueprint = player.blueprints[bp_choice]
                        confirm = input(f"\n⚠️  Delete '{blueprint.name}'? This cannot be undone! (y/n): ").strip().lower()
                        if confirm == 'y':
                            player.delete_blueprint(blueprint.name)
                        else:
                            print("❌ Cancelled")
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Invalid input")

            elif choice == '2':
                break

    def menu_create_phone(self, player: Player):
        """Create phone blueprint menu"""
        min_tier, max_tier = self.get_available_tier_range()

        print("\n" + "="*60)
        print("CREATE PHONE BLUEPRINT")
        print("="*60)
        print(f"Current tech level: T{min_tier}-T{max_tier}")
        print(f"Blueprints: {len(player.blueprints)}/{MAX_BLUEPRINTS}")
        player.display_unlocked_tiers()

        name = input("\nEnter blueprint name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            return

        parts = {}
        quality = {}

        print("\nEnter tier and quality for each core part:")
        print("Quality options: [L]ow (50% cheaper), [N]ormal (default), [H]igh (50% more expensive)")
        print("Note: High quality screen/casing reduces repair rate by 0.25% each")
        print()

        for part in CORE_PARTS:
            while True:
                try:
                    max_available = min(player.unlocked_tiers[part], max_tier)
                    tier = int(input(f"  {part.capitalize()} tier (T{min_tier}-T{max_available}): "))
                    if min_tier <= tier <= max_available:
                        parts[part] = tier
                        break
                    else:
                        print(f"    Invalid. Must be between {min_tier} and {max_available}")
                except ValueError:
                    print("    Invalid input")

            # Ask for quality
            while True:
                quality_choice = input(f"  {part.capitalize()} quality ([L]ow/[N]ormal/[H]igh, default N): ").strip().upper()
                if quality_choice == '' or quality_choice == 'N':
                    quality[part] = "Normal"
                    break
                elif quality_choice == 'L':
                    quality[part] = "Low"
                    break
                elif quality_choice == 'H':
                    quality[part] = "High"
                    break
                else:
                    print("    Invalid. Enter L, N, or H")

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

                # Ask for fingerprint quality
                while True:
                    quality_choice = input(f"  Fingerprint quality ([L]ow/[N]ormal/[H]igh, default N): ").strip().upper()
                    if quality_choice == '' or quality_choice == 'N':
                        quality['fingerprint'] = "Normal"
                        break
                    elif quality_choice == 'L':
                        quality['fingerprint'] = "Low"
                        break
                    elif quality_choice == 'H':
                        quality['fingerprint'] = "High"
                        break
                    else:
                        print("    Invalid. Enter L, N, or H")
            else:
                quality['fingerprint'] = "Normal"
        else:
            print("\nFingerprint sensor not available (need to R&D first)")
            quality['fingerprint'] = "Normal"

        # Calculate phone score and tier
        score = 0
        score += parts['soc'] * SCORING_WEIGHTS['soc']
        score += parts['battery'] * SCORING_WEIGHTS['battery']
        score += parts['screen'] * SCORING_WEIGHTS['screen']
        score += parts['ram'] * SCORING_WEIGHTS['ram']
        score += parts['camera'] * SCORING_WEIGHTS['camera']
        score += parts['storage'] * SCORING_WEIGHTS['storage']
        score += parts['casing'] * SCORING_WEIGHTS['casing']

        # Determine tier
        threshold_shift = (self.global_tech_level - 1) * 20
        entry_level_max = 20 + threshold_shift
        budget_max = 40 + threshold_shift
        midrange_max = 60 + threshold_shift
        high_end_max = 80 + threshold_shift

        if score <= entry_level_max:
            tier_name = "Entry Level"
        elif score <= budget_max:
            tier_name = "Budget"
        elif score <= midrange_max:
            tier_name = "Midrange"
        elif score <= high_end_max:
            tier_name = "High End"
        else:
            tier_name = "Flagship"

        print(f"\n--- Phone Quality Analysis ---")
        print(f"Quality Score: {score}")
        print(f"Market Tier: {tier_name}")
        print(f"Score breakdown:")
        print(f"  SoC: {parts['soc']} × {SCORING_WEIGHTS['soc']} = {parts['soc'] * SCORING_WEIGHTS['soc']}")
        print(f"  Battery: {parts['battery']} × {SCORING_WEIGHTS['battery']} = {parts['battery'] * SCORING_WEIGHTS['battery']}")
        print(f"  Screen: {parts['screen']} × {SCORING_WEIGHTS['screen']} = {parts['screen'] * SCORING_WEIGHTS['screen']}")
        print(f"  RAM: {parts['ram']} × {SCORING_WEIGHTS['ram']} = {parts['ram'] * SCORING_WEIGHTS['ram']}")
        print(f"  Camera: {parts['camera']} × {SCORING_WEIGHTS['camera']} = {parts['camera'] * SCORING_WEIGHTS['camera']}")
        print(f"  Storage: {parts['storage']} × {SCORING_WEIGHTS['storage']} = {parts['storage'] * SCORING_WEIGHTS['storage']}")
        print(f"  Casing: {parts['casing']} × {SCORING_WEIGHTS['casing']} = {parts['casing'] * SCORING_WEIGHTS['casing']}")

        # Calculate suggested price
        suggested_cost = 0
        for part in CORE_PARTS:
            suggested_cost += PART_COSTS[part][parts[part]]
        if 'fingerprint' in parts:
            suggested_cost += PART_COSTS['fingerprint'][parts['fingerprint']]

        print(f"\n--- Cost Analysis ---")
        print(f"Production cost per unit: ${suggested_cost}")
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

        player.create_blueprint(name, parts, sell_price, quality, min_tier, max_tier, self.global_tech_level)

    def menu_manufacturing(self, player: Player):
        """Manufacturing menu"""
        while True:
            print("\n" + "="*60)
            print("MANUFACTURING")
            print("="*60)
            player.display_blueprints(self.global_tech_level)
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
                    tier_name = bp.get_tier_name(self.global_tech_level)
                    print(f"{i}. {bp.name} [{tier_name}] (Cost: ${bp.get_production_cost()}/unit, Profit: ${bp.sell_price - bp.get_production_cost()}/unit)")

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

    def menu_repairs(self, player: Player):
        """Device repair menu"""
        while True:
            print("\n" + "="*60)
            print("DEVICE REPAIRS")
            print("="*60)
            player.display_pending_repairs()

            if not player.pending_repairs:
                print("\n✓ No devices need repair at this time!")
                input("\nPress Enter to continue...")
                break

            print("\nActions:")
            print("1. Repair specific device model")
            print("2. Repair all devices")
            print("3. Reject repair (⚠️  affects brand reputation)")
            print("4. Back to main menu")

            choice = input("\nChoice: ").strip()

            if choice == '1':
                # Select specific blueprint to repair
                print("\nSelect device model to repair:")
                blueprint_list = list(player.pending_repairs.keys())
                for i, blueprint_name in enumerate(blueprint_list, 1):
                    quantity = player.pending_repairs[blueprint_name]
                    # Find blueprint to show repair cost
                    blueprint = None
                    for bp in player.blueprints:
                        if bp.name == blueprint_name:
                            blueprint = bp
                            break
                    if blueprint:
                        repair_cost = blueprint.get_repair_cost()
                        print(f"{i}. {blueprint_name}: {quantity} units @ ${repair_cost}/unit")

                try:
                    model_choice = int(input("\nModel number: ")) - 1
                    if 0 <= model_choice < len(blueprint_list):
                        blueprint_name = blueprint_list[model_choice]
                        max_quantity = player.pending_repairs[blueprint_name]
                        print(f"\nPending repairs for {blueprint_name}: {max_quantity} units")
                        quantity = int(input(f"How many to repair (1-{max_quantity}): "))

                        if 1 <= quantity <= max_quantity:
                            player.repair_devices(blueprint_name, quantity)
                        else:
                            print(f"❌ Invalid quantity. Must be between 1 and {max_quantity}")
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Invalid input")

            elif choice == '2':
                # Repair all
                confirm = input("\nRepair all devices? This will repair all pending repairs. (y/n): ").strip().lower()
                if confirm == 'y':
                    player.repair_all_devices()
                else:
                    print("❌ Cancelled")

            elif choice == '3':
                # Reject repairs
                print("\n⚠️  WARNING: Rejecting repairs will damage your brand reputation!")
                print("Select device model to reject repairs for:")
                blueprint_list = list(player.pending_repairs.keys())
                for i, blueprint_name in enumerate(blueprint_list, 1):
                    quantity = player.pending_repairs[blueprint_name]
                    print(f"{i}. {blueprint_name}: {quantity} units")

                try:
                    model_choice = int(input("\nModel number (0 to cancel): ")) - 1
                    if model_choice == -1:
                        print("❌ Cancelled")
                    elif 0 <= model_choice < len(blueprint_list):
                        blueprint_name = blueprint_list[model_choice]
                        max_quantity = player.pending_repairs[blueprint_name]
                        print(f"\nPending repairs for {blueprint_name}: {max_quantity} units")
                        quantity = int(input(f"How many to reject (1-{max_quantity}): "))

                        if 1 <= quantity <= max_quantity:
                            confirm = input(f"\n⚠️  Are you sure you want to reject {quantity} repairs? This will hurt your brand! (y/n): ").strip().lower()
                            if confirm == 'y':
                                player.reject_repairs(blueprint_name, quantity)
                            else:
                                print("❌ Cancelled")
                        else:
                            print(f"❌ Invalid quantity. Must be between 1 and {max_quantity}")
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Invalid input")

            elif choice == '4':
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
            print(f"2. Create Phone Blueprint ({len(player.blueprints)}/{MAX_BLUEPRINTS})")
            print("3. Manage Blueprints")
            print("4. Manufacturing")
            # Show notification if there are pending repairs
            if player.pending_repairs:
                total_pending = sum(player.pending_repairs.values())
                print(f"5. Device Repairs (⚠️  {total_pending} devices awaiting repair)")
            else:
                print("5. Device Repairs")
            print("6. R&D")
            print("7. View Status")
            print("8. View Customer Market")
            print("9. Save Game")
            print("10. Next Player" if len(self.players) > 1 else "10. (Single Player)")
            print("11. Quit")

            choice = input("\nChoice: ").strip()

            if choice == '1':
                # Mark current player as ready for next month
                self.players_ready_for_next_month.add(player.name)
                print(f"\n✓ {player.name} is ready to advance to next month")

                # Check if all players are ready
                if len(self.players_ready_for_next_month) == len(self.players):
                    # All players ready - actually advance the month
                    self.advance_game_month()
                    input("\nPress Enter to continue...")
                else:
                    # Not all players ready - switch to next player
                    waiting_players = [p.name for p in self.players if p.name not in self.players_ready_for_next_month]
                    print(f"\nWaiting for: {', '.join(waiting_players)}")
                    print("\nSwitching to next player...")
                    self.next_player()
                    print(f"\n>>> Now playing as {self.get_current_player().name} <<<")
                    input("Press Enter to continue...")
                    return  # Return to show next player's menu

            elif choice == '2':
                self.menu_create_phone(player)

            elif choice == '3':
                self.menu_manage_blueprints(player)

            elif choice == '4':
                self.menu_manufacturing(player)

            elif choice == '5':
                self.menu_repairs(player)

            elif choice == '6':
                self.menu_rnd(player)

            elif choice == '7':
                player.display_status()
                player.display_unlocked_tiers()
                player.display_ongoing_rnd()
                player.display_blueprints(self.global_tech_level)
                player.display_manufacturing_queue()
                player.display_manufactured_phones()
                player.display_pending_repairs()
                input("\nPress Enter to continue...")

            elif choice == '8':
                if self.customer_market.customer_groups:
                    self.customer_market.display_customer_breakdown()
                else:
                    print("\n❌ No customer data yet. Market needs to be initialized.")
                input("\nPress Enter to continue...")

            elif choice == '9':
                filename = input("Enter filename (default: savegame.json): ").strip()
                if not filename:
                    filename = "savegame.json"
                self.save_game(filename)
                input("\nPress Enter to continue...")

            elif choice == '10':
                if len(self.players) > 1:
                    self.next_player()
                    print(f"\n>>> Switching to {self.get_current_player().name} <<<")
                    input("Press Enter to continue...")
                    return  # Return to show next player's menu
                else:
                    print("Single player mode - no other players")
                    input("\nPress Enter to continue...")

            elif choice == '11':
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
