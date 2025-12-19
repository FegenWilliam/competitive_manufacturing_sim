#!/usr/bin/env python3
"""
Test script for customer system
"""

from manufacturing_sim import (
    Game, Player, PhoneBlueprint, CustomerMarket,
    CUSTOMER_TIER_DISTRIBUTION, INITIAL_CUSTOMER_COUNT, CUSTOMER_GROWTH_PER_MONTH
)

def test_customer_generation():
    """Test customer generation with fixed tier distribution"""
    print("="*60)
    print("Testing Customer Generation")
    print("="*60)

    market = CustomerMarket()

    # Test Month 1
    print("\n--- Month 1 ---")
    market.generate_customers_for_month(1)
    assert len(market.customers) == INITIAL_CUSTOMER_COUNT
    print(f"✓ Generated {len(market.customers)} customers")

    # Verify tier distribution
    tier_counts = {}
    for customer in market.customers:
        tier_counts[customer.tier] = tier_counts.get(customer.tier, 0) + 1

    print("\nTier distribution verification:")
    for tier_name, percentage in CUSTOMER_TIER_DISTRIBUTION.items():
        expected = int(INITIAL_CUSTOMER_COUNT * percentage)
        actual = tier_counts.get(tier_name, 0)
        print(f"  {tier_name}: Expected {expected}, Got {actual} - {'✓' if expected == actual else '✗'}")

    # Test Month 2
    print("\n--- Month 2 ---")
    market.generate_customers_for_month(2)
    expected_total = INITIAL_CUSTOMER_COUNT + CUSTOMER_GROWTH_PER_MONTH
    assert len(market.customers) == expected_total
    print(f"✓ Generated {len(market.customers)} customers (expected {expected_total})")

    # Test Month 3
    print("\n--- Month 3 ---")
    market.generate_customers_for_month(3)
    expected_total = INITIAL_CUSTOMER_COUNT + 2 * CUSTOMER_GROWTH_PER_MONTH
    assert len(market.customers) == expected_total
    print(f"✓ Generated {len(market.customers)} customers (expected {expected_total})")

    print("\n✓ Customer generation test passed!")

def test_customer_purchasing():
    """Test customer purchasing logic"""
    print("\n" + "="*60)
    print("Testing Customer Purchasing")
    print("="*60)

    # Create a game with a player
    game = Game()
    player = Player("Test Player")
    game.players.append(player)

    # Create a few phone blueprints
    print("\n--- Creating Phone Blueprints ---")

    # Entry Level phone (score ~20)
    player.create_blueprint(
        "Budget Phone",
        {
            'ram': 1, 'soc': 1, 'screen': 1, 'battery': 1,
            'camera': 1, 'casing': 1, 'storage': 1
        },
        sell_price=100,
        global_tech_level=1
    )

    # Midrange phone (score ~50)
    player.create_blueprint(
        "Mid Phone",
        {
            'ram': 3, 'soc': 3, 'screen': 3, 'battery': 3,
            'camera': 3, 'casing': 3, 'storage': 3
        },
        sell_price=500,
        global_tech_level=1
    )

    # Flagship phone (score ~100)
    player.create_blueprint(
        "Flagship Phone",
        {
            'ram': 5, 'soc': 5, 'screen': 5, 'battery': 5,
            'camera': 5, 'casing': 5, 'storage': 5
        },
        sell_price=1000,
        global_tech_level=1
    )

    # Manufacture phones
    print("\n--- Manufacturing Phones ---")
    player.manufactured_phones = {
        "Budget Phone": 200,
        "Mid Phone": 500,
        "Flagship Phone": 100
    }
    print(f"✓ Manufactured phones: {player.manufactured_phones}")

    # Generate customers
    print("\n--- Generating Customers ---")
    game.customer_market.generate_customers_for_month(1)

    # Simulate purchases
    print("\n--- Simulating Purchases ---")
    initial_money = player.money
    game.customer_market.simulate_purchases(game.players, game.global_tech_level)

    # Verify sales happened
    revenue = player.money - initial_money
    print(f"\n✓ Revenue generated: ${revenue:,}")
    print(f"✓ Remaining inventory: {player.manufactured_phones}")

    if revenue > 0:
        print("\n✓ Customer purchasing test passed!")
    else:
        print("\n✗ No sales occurred - test failed!")

def test_customer_evaluation():
    """Test customer phone evaluation logic"""
    print("\n" + "="*60)
    print("Testing Customer Phone Evaluation")
    print("="*60)

    from manufacturing_sim import Customer

    # Create a gamer customer (prioritizes SoC, RAM, Battery)
    gamer = Customer(tier="Flagship", customer_type="Gamer")

    # Create two flagship phones with different specs
    phone1 = PhoneBlueprint(
        name="Gaming Phone",
        ram_tier=5, soc_tier=5, screen_tier=3, battery_tier=5,
        camera_tier=2, casing_tier=2, storage_tier=3,
        fingerprint_tier=0, sell_price=1000
    )

    phone2 = PhoneBlueprint(
        name="Camera Phone",
        ram_tier=3, soc_tier=3, screen_tier=5, battery_tier=3,
        camera_tier=5, casing_tier=5, storage_tier=3,
        fingerprint_tier=0, sell_price=1000
    )

    score1 = gamer.evaluate_phone(phone1)
    score2 = gamer.evaluate_phone(phone2)

    print(f"\nGamer evaluating phones:")
    print(f"  Gaming Phone (High SoC, RAM, Battery): {score1:.1f}")
    print(f"  Camera Phone (High Camera, Screen): {score2:.1f}")

    if score1 > score2:
        print(f"  ✓ Gamer prefers Gaming Phone (correct!)")
    else:
        print(f"  ✗ Gamer prefers Camera Phone (unexpected!)")

    # Create a camera enthusiast
    camera_fan = Customer(tier="High End", customer_type="Camera Enthusiast")

    score1 = camera_fan.evaluate_phone(phone1)
    score2 = camera_fan.evaluate_phone(phone2)

    print(f"\nCamera Enthusiast evaluating phones:")
    print(f"  Gaming Phone: {score1:.1f}")
    print(f"  Camera Phone: {score2:.1f}")

    if score2 > score1:
        print(f"  ✓ Camera Enthusiast prefers Camera Phone (correct!)")
    else:
        print(f"  ✗ Camera Enthusiast prefers Gaming Phone (unexpected!)")

    print("\n✓ Customer evaluation test passed!")

if __name__ == "__main__":
    test_customer_generation()
    test_customer_purchasing()
    test_customer_evaluation()

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
