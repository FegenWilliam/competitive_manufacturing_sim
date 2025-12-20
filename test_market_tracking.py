#!/usr/bin/env python3
"""
Test script for new market tracking system with phone lifecycle
"""

from manufacturing_sim import (
    Game, Player, PhoneBlueprint, CustomerMarket, MARKET_SIZE
)

def test_market_initialization():
    """Test market initialization with 20,000 people"""
    print("="*60)
    print("Testing Market Initialization")
    print("="*60)

    market = CustomerMarket()
    market.initialize_market()

    # Verify total people
    total_people = sum(g.count for g in market.customer_groups)
    print(f"\nTotal people: {total_people}")
    assert total_people == MARKET_SIZE, f"Expected {MARKET_SIZE}, got {total_people}"

    # Verify nobody owns phones initially
    people_with_phones = sum(g.count for g in market.customer_groups if g.owned_phone_company is not None)
    print(f"People with phones: {people_with_phones}")
    assert people_with_phones == 0, "Initially nobody should own phones"

    print("\n✓ Market initialization test passed!")

def test_lifecycle_calculation():
    """Test phone lifecycle calculation"""
    print("\n" + "="*60)
    print("Testing Phone Lifecycle Calculation")
    print("="*60)

    market = CustomerMarket()

    # Create a midrange phone (T3 parts, normal quality)
    phone_midrange = PhoneBlueprint(
        name="Midrange Phone",
        ram_tier=3, soc_tier=3, screen_tier=3, battery_tier=3,
        camera_tier=3, casing_tier=3, storage_tier=3,
        fingerprint_tier=0, sell_price=500
    )

    # Test base lifecycle (20 months for non-gamers)
    lifecycle_normal = market.calculate_phone_lifecycle(phone_midrange, "All-Rounder")
    print(f"\nMidrange phone, All-Rounder: {lifecycle_normal} months (expected 20)")
    assert lifecycle_normal == 20, f"Expected 20 months, got {lifecycle_normal}"

    # Test gamer lifecycle (16 months)
    lifecycle_gamer = market.calculate_phone_lifecycle(phone_midrange, "Gamer")
    print(f"Midrange phone, Gamer: {lifecycle_gamer} months (expected 16)")
    assert lifecycle_gamer == 16, f"Expected 16 months, got {lifecycle_gamer}"

    # Create a high-tier phone (T4 parts should add months)
    phone_premium = PhoneBlueprint(
        name="Premium Phone",
        ram_tier=4, soc_tier=4, screen_tier=4, battery_tier=4,
        camera_tier=4, casing_tier=4, storage_tier=4,
        fingerprint_tier=0, sell_price=800
    )

    lifecycle_premium = market.calculate_phone_lifecycle(phone_premium, "All-Rounder")
    print(f"\nPremium phone (T4), All-Rounder: {lifecycle_premium} months (expected 27: 20 base + 7 parts)")
    assert lifecycle_premium == 27, f"Expected 27 months, got {lifecycle_premium}"

    # Create a high quality phone
    phone_quality = PhoneBlueprint(
        name="Quality Phone",
        ram_tier=3, soc_tier=3, screen_tier=3, battery_tier=3,
        camera_tier=3, casing_tier=3, storage_tier=3,
        fingerprint_tier=0, sell_price=600,
        ram_quality="High", soc_quality="High", screen_quality="High",
        battery_quality="High", camera_quality="High", casing_quality="High",
        storage_quality="High"
    )

    lifecycle_quality = market.calculate_phone_lifecycle(phone_quality, "All-Rounder")
    # 20 base + 7 high quality parts + 1 extra for high quality battery = 28
    print(f"\nHigh quality phone, All-Rounder: {lifecycle_quality} months (expected 28: 20 + 7 quality + 1 battery)")
    assert lifecycle_quality == 28, f"Expected 28 months, got {lifecycle_quality}"

    print("\n✓ Lifecycle calculation test passed!")

def test_simple_purchase_flow():
    """Test basic purchase and ownership tracking"""
    print("\n" + "="*60)
    print("Testing Purchase and Ownership Tracking")
    print("="*60)

    # Create game
    game = Game()
    player = Player("Test Player")
    game.players.append(player)

    # Initialize market
    game.customer_market.initialize_market()
    game.customer_market.current_month = 1

    # Create phone blueprint
    player.create_blueprint(
        "Budget Phone",
        {
            'ram': 1, 'soc': 1, 'screen': 1, 'battery': 1,
            'camera': 1, 'casing': 1, 'storage': 1
        },
        sell_price=100,
        global_tech_level=1
    )

    # Manufacture phones
    player.manufactured_phones = {"Budget Phone": 5000}
    print(f"\nManufactured {player.manufactured_phones['Budget Phone']} Budget Phones")

    # Simulate first month purchases
    print("\n--- Month 1 Purchases ---")
    initial_money = player.money
    game.customer_market.simulate_purchases(game.players, game.global_tech_level)

    # Check that sales happened
    revenue = player.money - initial_money
    people_with_phones = sum(g.count for g in game.customer_market.customer_groups
                            if g.owned_phone_company is not None)

    print(f"\nRevenue: ${revenue:,}")
    print(f"People with phones: {people_with_phones}")

    assert revenue > 0, "Expected some sales to occur"
    assert people_with_phones > 0, "Expected some people to own phones"

    # Simulate month 2 - should have fewer sales (only new buyers who couldn't buy before)
    print("\n--- Month 2 Purchases ---")
    game.customer_market.current_month = 2
    player.manufactured_phones = {"Budget Phone": 5000}
    month2_revenue = player.money
    game.customer_market.simulate_purchases(game.players, game.global_tech_level)
    month2_revenue = player.money - month2_revenue

    print(f"Revenue: ${month2_revenue:,}")
    print(f"Month 2 revenue should be less than Month 1 (people already own phones)")

    print("\n✓ Purchase and ownership tracking test passed!")

if __name__ == "__main__":
    test_market_initialization()
    test_lifecycle_calculation()
    test_simple_purchase_flow()

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
