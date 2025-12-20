"""
Test script for ownership guardrails (lifecycle constraints and group consolidation)
"""
import sys
sys.path.append('.')

from manufacturing_sim import (
    Player, PhoneBlueprint, CustomerMarket, Game,
    MARKET_SIZE
)


def test_lifecycle_constraints():
    """Test that lifecycle is constrained between 6 and 30 months"""
    print("=" * 60)
    print("Testing Lifecycle Constraints (6-30 months)")
    print("=" * 60)

    market = CustomerMarket()

    # Test 1: Very low quality phone with low tier parts (should hit minimum of 6 months)
    low_quality_phone = PhoneBlueprint(
        name="Terrible Phone",
        ram_tier=1, ram_quality="Low",
        soc_tier=1, soc_quality="Low",
        screen_tier=1, screen_quality="Low",
        storage_tier=1, storage_quality="Low",
        battery_tier=1, battery_quality="Low",
        camera_tier=1, camera_quality="Low",
        casing_tier=1, casing_quality="Low",
        fingerprint_tier=0, fingerprint_quality="Normal",
        sell_price=50
    )

    lifecycle_low = market.calculate_phone_lifecycle(low_quality_phone, "Gamer")
    print(f"\nTerrible phone (T1 all Low quality), Gamer:")
    print(f"  Lifecycle: {lifecycle_low} months")
    print(f"  Expected: 6 months (minimum constraint)")
    assert lifecycle_low == 6, f"Expected 6 months (minimum), got {lifecycle_low}"
    print("  ✓ Minimum constraint working")

    # Test 2: Very high quality phone with high tier parts (should hit maximum of 30 months)
    high_quality_phone = PhoneBlueprint(
        name="Premium Phone",
        ram_tier=5, ram_quality="High",
        soc_tier=5, soc_quality="High",
        screen_tier=5, screen_quality="High",
        storage_tier=5, storage_quality="High",
        battery_tier=5, battery_quality="High",  # Gets +2 for battery
        camera_tier=5, camera_quality="High",
        casing_tier=5, casing_quality="High",
        fingerprint_tier=5, fingerprint_quality="High",
        sell_price=5000
    )

    # Base: 20, Parts tier bonus: 8 * 2 = 16, Quality bonus: 8 + 1 (battery) = 9
    # Total would be 20 + 16 + 9 = 45 months, but should be capped at 30
    lifecycle_high = market.calculate_phone_lifecycle(high_quality_phone, "All-Rounder")
    print(f"\nPremium phone (T5 all High quality), All-Rounder:")
    print(f"  Lifecycle: {lifecycle_high} months")
    print(f"  Expected: 30 months (maximum constraint)")
    print(f"  Without cap would be: 20 base + 16 tier + 9 quality = 45 months")
    assert lifecycle_high == 30, f"Expected 30 months (maximum), got {lifecycle_high}"
    print("  ✓ Maximum constraint working")

    print("\n✓ Lifecycle constraints test passed!")


def test_customer_group_consolidation():
    """Test that customer groups are consolidated to prevent proliferation"""
    print("\n" + "=" * 60)
    print("Testing Customer Group Consolidation")
    print("=" * 60)

    # Create a game with minimal setup
    game = Game()
    player = Player("Test Company")
    game.players.append(player)

    # Initialize market
    game.customer_market.initialize_market()
    initial_groups = len(game.customer_market.customer_groups)
    print(f"\nInitial customer groups: {initial_groups}")

    # Create a simple budget phone
    budget_phone = PhoneBlueprint(
        name="Test Phone",
        ram_tier=2, ram_quality="Normal",
        soc_tier=2, soc_quality="Normal",
        screen_tier=2, screen_quality="Normal",
        storage_tier=2, storage_quality="Normal",
        battery_tier=2, battery_quality="Normal",
        camera_tier=2, camera_quality="Normal",
        casing_tier=2, casing_quality="Normal",
        fingerprint_tier=0, fingerprint_quality="Normal",
        sell_price=200
    )
    player.blueprints.append(budget_phone)

    # Manufacture phones for multiple months and observe group consolidation
    print("\nSimulating purchases over multiple months...")

    for month in range(1, 6):
        # Manufacture enough phones
        player.manufactured_phones["Test Phone"] = 10000

        game.customer_market.current_month = month
        game.customer_market.simulate_purchases([player], global_tech_level=1)

        group_count = len(game.customer_market.customer_groups)
        people_with_phones = sum(g.count for g in game.customer_market.customer_groups
                                 if g.owned_phone_company is not None)

        print(f"\n  Month {month}:")
        print(f"    Customer groups: {group_count}")
        print(f"    People with phones: {people_with_phones}")

    # Check that groups aren't growing exponentially
    final_groups = len(game.customer_market.customer_groups)
    print(f"\nFinal customer groups: {final_groups}")
    print(f"Groups created/merged: {final_groups - initial_groups} net change")

    # The number of groups should not explode - with consolidation,
    # we should have roughly the same number or a controlled increase
    assert final_groups < initial_groups * 3, \
        f"Too many groups created: {final_groups} (started with {initial_groups})"

    print("\n✓ Customer group consolidation test passed!")

    # Verify groups are actually being consolidated
    # Count groups by unique (tier, customer_type, owned_phone, purchase_month)
    unique_combos = set()
    for group in game.customer_market.customer_groups:
        combo = (group.tier, group.customer_type, group.owned_phone_company,
                 group.owned_phone_blueprint, group.purchase_month)
        unique_combos.add(combo)

    # Number of groups should equal number of unique combinations
    assert len(unique_combos) == final_groups, \
        f"Groups not properly consolidated: {len(unique_combos)} unique combos but {final_groups} groups"

    print("✓ Groups are properly consolidated (no duplicates)")


def test_ownership_minimum_duration():
    """Verify that customers hold phones for at least 6 months"""
    print("\n" + "=" * 60)
    print("Testing Minimum Ownership Duration")
    print("=" * 60)

    # Create a game
    game = Game()
    player = Player("Test Company")
    game.players.append(player)

    # Initialize market
    game.customer_market.initialize_market()

    # Create a low-quality phone that should last only 6 months (minimum)
    cheap_phone = PhoneBlueprint(
        name="Cheap Phone",
        ram_tier=1, ram_quality="Low",
        soc_tier=1, soc_quality="Low",
        screen_tier=1, screen_quality="Low",
        storage_tier=1, storage_quality="Low",
        battery_tier=1, battery_quality="Low",
        camera_tier=1, camera_quality="Low",
        casing_tier=1, casing_quality="Low",
        fingerprint_tier=0, fingerprint_quality="Normal",
        sell_price=50
    )
    player.blueprints.append(cheap_phone)

    # Month 1: Sell phones
    player.manufactured_phones["Cheap Phone"] = 10000
    game.customer_market.current_month = 1
    game.customer_market.simulate_purchases([player], global_tech_level=1)

    initial_sales = sum(g.count for g in game.customer_market.customer_groups
                        if g.owned_phone_company == "Test Company")

    print(f"\nMonth 1: Sold {initial_sales} phones")

    # Months 2-5: Should have no sales (phones last 6 months minimum)
    no_sales_months = []
    for month in range(2, 6):
        player.manufactured_phones["Cheap Phone"] = 10000
        game.customer_market.current_month = month

        before_sales = sum(g.count for g in game.customer_market.customer_groups
                          if g.owned_phone_company == "Test Company")

        game.customer_market.simulate_purchases([player], global_tech_level=1)

        after_sales = sum(g.count for g in game.customer_market.customer_groups
                         if g.owned_phone_company == "Test Company")

        new_sales = after_sales - before_sales
        if new_sales == 0:
            no_sales_months.append(month)

        print(f"Month {month}: {new_sales} new sales (customers still using their phones)")

    # Month 7: Should have sales again (lifecycle expired)
    player.manufactured_phones["Cheap Phone"] = 10000
    game.customer_market.current_month = 7

    # Check inventory before and after to see if phones were sold
    inventory_before = player.manufactured_phones["Cheap Phone"]

    game.customer_market.simulate_purchases([player], global_tech_level=1)

    inventory_after = player.manufactured_phones["Cheap Phone"]
    phones_sold_month_7 = inventory_before - inventory_after

    print(f"Month 7: {phones_sold_month_7} phones sold (lifecycle expired, customers buying again)")

    # Verify customers held phones for at least 6 months
    assert len(no_sales_months) >= 4, f"Expected no sales for at least 4 months (2-5)"
    assert phones_sold_month_7 > 0, "Expected sales in month 7 after lifecycle expired"

    print("\n✓ Minimum ownership duration test passed!")


if __name__ == "__main__":
    test_lifecycle_constraints()
    test_customer_group_consolidation()
    test_ownership_minimum_duration()

    print("\n" + "=" * 60)
    print("ALL OWNERSHIP GUARDRAIL TESTS PASSED!")
    print("=" * 60)
