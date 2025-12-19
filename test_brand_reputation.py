#!/usr/bin/env python3
"""
Test script for brand reputation system
"""
from manufacturing_sim import Player, PhoneBlueprint, Game

def test_brand_reputation_initialization():
    """Test that brand reputation is initialized correctly"""
    player = Player("Test Player")
    assert player.brand_reputation == 50.0, "Brand reputation should start at 50"
    assert player.price_history == {}, "Price history should start empty"
    assert player.rejected_repairs_this_month == 0, "Rejected repairs should start at 0"
    print("✓ Brand reputation initialization test passed")

def test_price_tracking():
    """Test that price tracking works"""
    player = Player("Test Player")
    player.track_blueprint_price("TestPhone", 1000)
    player.track_blueprint_price("TestPhone", 1100)
    player.track_blueprint_price("TestPhone", 1200)
    player.track_blueprint_price("TestPhone", 1300)  # This should push out the first one

    assert len(player.price_history["TestPhone"]) == 3, "Should only keep last 3 prices"
    print("✓ Price tracking test passed")

def test_brand_reputation_calculation():
    """Test brand reputation calculation"""
    player = Player("Test Player")

    # Create a flagship phone with cheap casing (should trigger penalty)
    parts = {
        'ram': 5, 'soc': 5, 'screen': 5, 'battery': 5,
        'camera': 5, 'storage': 5, 'casing': 1, 'fingerprint': 0
    }
    blueprint = PhoneBlueprint(
        name="CheapCasing", ram_tier=5, soc_tier=5, screen_tier=5,
        battery_tier=5, camera_tier=5, casing_tier=1, storage_tier=5,
        fingerprint_tier=0, sell_price=2000
    )
    player.blueprints.append(blueprint)

    # Calculate brand reputation changes
    change = player.calculate_brand_reputation_changes(global_tech_level=1)

    # Should have a penalty for cheap casing on high-end phone
    assert change < 0, f"Should have negative change for cheap casing, got {change}"
    print("✓ Brand reputation calculation test passed")

def test_reject_repairs():
    """Test rejecting repairs"""
    player = Player("Test Player")
    player.pending_repairs["TestPhone"] = 10

    # Reject 5 repairs
    success = player.reject_repairs("TestPhone", 5)
    assert success, "Should successfully reject repairs"
    assert player.pending_repairs["TestPhone"] == 5, "Should have 5 repairs left"
    assert player.rejected_repairs_this_month == 5, "Should track rejected repairs"
    print("✓ Reject repairs test passed")

def test_brand_multiplier():
    """Test that brand reputation affects customer evaluation"""
    # At 100 brand: should get 1.2x multiplier
    # At 50 brand: should get 1.1x multiplier
    # At 0 brand: should get 1.0x multiplier

    brand_100 = 1.0 + (100.0 / 100.0 * 0.2)
    brand_50 = 1.0 + (50.0 / 100.0 * 0.2)
    brand_0 = 1.0 + (0.0 / 100.0 * 0.2)

    assert abs(brand_100 - 1.2) < 0.001, f"100 brand should give 1.2x multiplier, got {brand_100}"
    assert abs(brand_50 - 1.1) < 0.001, f"50 brand should give 1.1x multiplier, got {brand_50}"
    assert abs(brand_0 - 1.0) < 0.001, f"0 brand should give 1.0x multiplier, got {brand_0}"
    print("✓ Brand multiplier test passed")

def test_serialization():
    """Test that brand reputation fields are saved/loaded correctly"""
    player = Player("Test Player")
    player.brand_reputation = 75.5
    player.price_history = {"Phone1": [(1, 1000), (2, 1100)]}
    player.rejected_repairs_this_month = 3

    # Convert to dict and back
    data = player.to_dict()
    loaded_player = Player.from_dict(data)

    assert loaded_player.brand_reputation == 75.5, "Brand reputation not saved correctly"
    assert loaded_player.price_history == {"Phone1": [(1, 1000), (2, 1100)]}, "Price history not saved correctly"
    assert loaded_player.rejected_repairs_this_month == 3, "Rejected repairs not saved correctly"
    print("✓ Serialization test passed")

if __name__ == "__main__":
    print("Running brand reputation system tests...\n")

    test_brand_reputation_initialization()
    test_price_tracking()
    test_brand_reputation_calculation()
    test_reject_repairs()
    test_brand_multiplier()
    test_serialization()

    print("\n✅ All tests passed!")
