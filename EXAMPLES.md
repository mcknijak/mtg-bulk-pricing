# MTG Pricer - Usage Examples

This file contains real-world examples of how to use the MTG Card Pricing Tool.

## 🆕 Key Features to Remember

- **Case insensitive**: Type card names, sets, and finishes however you want!
- **Nonfoil by default**: Unless you specify `|foil` or `|etched`, you'll get nonfoil prices
- **Efficient inventory**: Prices are fetched during template generation (no separate processing step needed!)

---

## Example 1: Price Check a Commander Deck

### Step 1: Create your decklist
Create a file called `commander_deck.txt`:

```
# My Atraxa Deck
Atraxa, Praetors' Voice
Sol Ring
Arcane Signet
Commander's Sphere
Thought Vessel
Fellwar Stone
Chromatic Lantern
Cultivate
Kodama's Reach
Rampant Growth
Swords to Plowshares
Path to Exile
Counterspell
Swan Song
Generous Gift
Cyclonic Rift
Toxic Deluge
Wrath of God
Doubling Season
Parallel Lives
Eternal Witness
Seedborn Muse
Mystical Tutor
Vampiric Tutor
Demonic Tutor
Enlightened Tutor
```

### Step 2: Get the prices
```bash
python mtg_pricer.py -i commander_deck.txt -o commander_prices.csv
```

### Result
The output CSV will show min/max **nonfoil** prices for each card across all printings. This is perfect for most Commander decks where nonfoil cards are the norm!

---

## Example 2: Value Your Modern Deck

### Step 1: Create a precise decklist with specific printings
Create a file called `modern_deck.txt`:

```
# Mainboard - All nonfoil (default behavior)
Ragavan, Nimble Pilferer|MH2|138
Ragavan, Nimble Pilferer|MH2|138
Ragavan, Nimble Pilferer|MH2|138
Ragavan, Nimble Pilferer|MH2|138
Dragon's Rage Channeler|MH2|121
Dragon's Rage Channeler|MH2|121
Dragon's Rage Channeler|MH2|121
Dragon's Rage Channeler|MH2|121
Ledger Shredder|SNC|46
Ledger Shredder|SNC|46
Ledger Shredder|SNC|46
Ledger Shredder|SNC|46
Lightning Bolt|MH2|130
Lightning Bolt|MH2|130
Lightning Bolt|MH2|130
Lightning Bolt|MH2|130
```

**Note:** Since we didn't specify a finish, these will all return nonfoil prices (the default).

### Step 2: Get the prices
```bash
python mtg_pricer.py -i modern_deck.txt -o modern_prices.csv
```

---

## Example 3: Track Your Expensive Cards

### expensive_cards.txt
```
# Power Nine
Black Lotus|LEA|232
Mox Sapphire|LEA|265
Mox Jet|LEA|264
Mox Ruby|LEA|266
Mox Pearl|LEA|263
Mox Emerald|LEA|262
Time Walk|LEA|290
Timetwister|LEA|293
Ancestral Recall|LEA|161

# Other Valuable Cards
Tarmogoyf|FUT|153
Dark Confidant|RAV|81
Liliana of the Veil|ISD|105
Snapcaster Mage|ISD|78
Force of Will|ALL|55
Gaea's Cradle|USG|321
```

```bash
python mtg_pricer.py -i expensive_cards.txt -o valuable_cards.csv
```

---

## Example 4: Inventory Mode - Value Your Entire Collection (Efficient!)

### Step 1: Generate templates with prices included
```bash
python mtg_pricer.py --inventory-mode --sets MH3 MH2 BLB LCI WOE -o my_collection_template.csv
```

This creates a CSV with ALL cards from those sets **with prices already populated**! 

**What you get:**
- Every card from the specified sets
- Each finish type (nonfoil, foil, etched) gets its own row
- Prices are already filled in
- Just need to add quantities

### Step 2: Fill in your inventory
Open `my_collection_template.csv` in Excel or Google Sheets. The template will look like this:

```
card_name,set,collector_number,rarity,finish,unit_price,quantity
"Ragavan, Nimble Pilferer",MH2,138,mythic,nonfoil,$65.00,
"Ragavan, Nimble Pilferer",MH2,138,mythic,foil,$150.00,
"Solitude",MH2,32,rare,nonfoil,$8.50,
"Solitude",MH2,32,rare,foil,$25.00,
"Solitude",MH2,32,rare,etched,$35.00,
```

Just fill in the `quantity` column:

```
card_name,set,collector_number,rarity,finish,unit_price,quantity
"Ragavan, Nimble Pilferer",MH2,138,mythic,nonfoil,$65.00,2
"Ragavan, Nimble Pilferer",MH2,138,mythic,foil,$150.00,1
"Solitude",MH2,32,rare,nonfoil,$8.50,4
"Solitude",MH2,32,rare,foil,$25.00,
"Solitude",MH2,32,rare,etched,$35.00,
```

### Step 3: Calculate total value (instant!)
```bash
python mtg_pricer.py --calculate-value -i my_collection_template.csv -o collection_value.csv
```

The script will calculate the total value **instantly** - no API calls needed!

**Output shows:**
```
Total cards: 7
Total inventory value: $314.00
```

### Why This Workflow Is Better:
- ✅ **Single API pass**: Only hits Scryfall once during template generation
- ✅ **See prices while inventorying**: Make better decisions about what to track
- ✅ **Instant calculations**: Value calculation is pure math, no waiting
- ✅ **Separate foil tracking**: Each finish gets its own row, easier to manage

---

## Example 5: Case Insensitivity - Type However You Want!

The script is completely case insensitive. All of these work identically:

### comparison.txt
```
# Different capitalizations - all work the same!
lightning bolt
Lightning Bolt
LIGHTNING BOLT
LiGhTnInG bOlT

# Set codes - case doesn't matter
counterspell|ice
Counterspell|ICE
COUNTERSPELL|Ice

# Finish types - also case insensitive
Tarmogoyf|fut|153|foil
tarmogoyf|FUT|153|FOIL
TARMOGOYF|Fut|153|Foil
```

```bash
python mtg_pricer.py -i comparison.txt -o prices.csv
```

All entries will be processed correctly regardless of capitalization!

**Command line is also case insensitive:**
```bash
# All of these work
python mtg_pricer.py -i cards.txt -o prices.csv --set mh3
python mtg_pricer.py -i cards.txt -o prices.csv --set MH3
python mtg_pricer.py -i cards.txt -o prices.csv --set Mh3
```

---

## Example 6: Compare Printings of the Same Card

Want to see price differences across different sets?

### comparison.txt
```
Lightning Bolt
Lightning Bolt|LEA
Lightning Bolt|M10
Lightning Bolt|M11
Lightning Bolt|2XM
Lightning Bolt|2XM|140|foil
Lightning Bolt|MH2|130
Lightning Bolt|MH2|367|foil
Lightning Bolt|MH2|367|etched
```

```bash
python mtg_pricer.py -i comparison.txt -o bolt_comparison.csv
```

**Results:**
- First entry returns cheapest/most expensive **nonfoil** printings across all sets
- Next entries show specific set printings (nonfoil by default unless specified)
- Foil and etched entries show those specific prices

This is great for comparing value between different versions!

---

## Example 7: Set-Specific Pricing

Only interested in cards from Modern Horizons 3?

### mh3_wants.txt
```
�Flare of Denial
Emrakul the World Anew
Tamiyo Inquisitive Student // Tamiyo Seasoned Scholar
Psychic Frog
Eldrazi Linebreaker
Ugin's Labyrinth
Nulldrifter
Sink into Stupor // Awaken the Cursed
Ugin's Binding
Volatile Stormdrake
```

```bash
python mtg_pricer.py -i mh3_wants.txt -o mh3_prices.csv --set MH3
```

This ensures you only see MH3 printings (nonfoil by default), even if cards appear in other sets. Note: `--set MH3` and `--set mh3` work the same!

---

## Example 8: Foil vs Nonfoil Comparison

Want to see the foil premium on expensive cards?

### foil_comparison.txt
```
Tarmogoyf|FUT|153|nonfoil
Tarmogoyf|FUT|153|foil
Dark Confidant|RAV|81|nonfoil
Dark Confidant|RAV|81|foil
Liliana of the Veil|ISD|105|nonfoil
Liliana of the Veil|ISD|105|foil
```

```bash
python mtg_pricer.py -i foil_comparison.txt -o foil_prices.csv
```

**Results show:**
- Exact prices for both nonfoil and foil versions
- Easy to see the foil premium (difference in price)
- Each finish gets its own row in the output

**Tip:** If you just put `Tarmogoyf|FUT|153` without specifying finish, you'd only get the nonfoil price (default behavior).

---

## Example 9: Bulk Commons and Uncommons

### bulk_cards.txt
```
# Just card names, get cheapest nonfoil printing (default)
Llanowar Elves
Counterspell
Lightning Bolt
Birds of Paradise
Path to Exile
Brainstorm
Ponder
Preordain
Fatal Push
Opt
```

```bash
python mtg_pricer.py -i bulk_cards.txt -o bulk_prices.csv
```

The min_price column will show you the cheapest **nonfoil** version available across all sets.

---

## Example 10: Track Sealed Product Value (Efficient!)

After opening booster boxes, track what you pulled using the efficient new workflow:

### Step 1: Generate template with prices
```bash
python mtg_pricer.py --inventory-mode --sets BLB -o bloomburrow_pulls.csv
```

**What you get:** A CSV with every card from Bloomburrow, separated by finish (nonfoil, foil), with prices already populated!

### Step 2: Mark your pulls
Open the CSV and fill in quantities. Example:

```csv
card_name,set,collector_number,rarity,finish,unit_price,quantity
"Monstrous Rage",BLB,162,common,nonfoil,$0.15,3
"Monstrous Rage",BLB,162,common,foil,$1.50,
"Caretaker's Talent",BLB,6,rare,nonfoil,$4.50,1
"Caretaker's Talent",BLB,6,rare,foil,$12.00,
"Ygra, Eater of All",BLB,244,mythic,nonfoil,$15.00,1
"Ygra, Eater of All",BLB,244,mythic,foil,$35.00,
```

Just add quantities where you pulled cards!

### Step 3: Calculate value (instant!)
```bash
python mtg_pricer.py --calculate-value -i bloomburrow_pulls.csv -o bloomburrow_value.csv
```

**Output:**
```
Total cards: 5
Total inventory value: $24.45
```

Compare the total value to what you paid for the box!

**Old Way vs New Way:**
- ❌ Old: Generate template → Fill in → Hit API again for prices
- ✅ New: Generate template with prices → Fill in → Instant calculation

---

## Example 11: Buylist Prep

Planning to sell cards? Get current prices first:

### selling_to_store.txt
```
Ragavan, Nimble Pilferer|MH2|138|nonfoil
Force of Will|2XM|51|nonfoil
Mana Crypt|2XM|3|nonfoil
Urza's Saga|MH2|259|nonfoil
Solitude|MH2|32|nonfoil
Grief|MH2|87|nonfoil
Fury|MH2|126|nonfoil
```

```bash
python mtg_pricer.py -i selling_to_store.txt -o selling_prices.csv
```

Stores typically offer 50-70% of the market price shown.

---

## Tips for Best Results

1. **Case doesn't matter**: Type "lightning bolt", "Lightning Bolt", or "LIGHTNING BOLT" - all work!
2. **Nonfoil is default**: Unless you specify `|foil` or `|etched`, you'll get nonfoil prices
3. **Specify finish for premium cards**: Add `|foil` to see foil prices, `|etched` for etched foils
4. **Exact names still matter**: While case doesn't matter, spelling does - "Atraxa, Praetors' Voice" works, "Atraxia" doesn't
5. **Specify printings when possible**: Prices vary wildly between sets and versions
6. **Regular updates**: Run the script monthly to track value changes
7. **Bulk operations**: Process 100+ cards at once, the script handles it
8. **Inventory mode is efficient**: Prices are fetched during template generation, making it much faster
9. **Track foils separately**: In inventory mode, each finish gets its own row for precise tracking
10. **Check output**: Review the CSV for "Not Found" entries to fix typos

---

## Troubleshooting Common Scenarios

### Card not found
```
Problem: "Lightning bolt" returns "Not Found"
Solution: Check spelling - case doesn't matter but spelling does! 
"Lightning Bolt", "lightning bolt", "LIGHTNING BOLT" all work the same.
```

### Getting nonfoil when you want foil
```
Problem: Script returns nonfoil price but you want foil
Solution: The script defaults to nonfoil. Add |foil: "Card Name|SET|123|foil"
```

### Getting foil when you want nonfoil
```
Problem: You're getting foil prices unexpectedly
Solution: This shouldn't happen anymore - script defaults to nonfoil unless you specify |foil
```

### Multiple versions in same set
```
Problem: Modern Horizons 3 has multiple art variants
Solution: Use collector number: "Emrakul the World Anew|MH3|6"
```

### Set code not working
```
Problem: "--set mh3" doesn't work
Solution: This should work! Set codes are case insensitive. 
If it's not working, verify the set code at scryfall.com/sets
```

---

## Pro Tips

- **Keep a master inventory**: Use inventory mode quarterly to track collection value
- **Type naturally**: Don't worry about capitalization - the script handles it
- **Default to nonfoil**: Most cards are nonfoil, so the default saves you time
- **Inventory workflow**: Generate template with prices → Fill quantities → Instant value (much faster!)
- **Compare before buying**: Check prices before trades or purchases
- **Track sealed products**: Record box EV (expected value) vs actual pulls using inventory mode
- **Update regularly**: Prices change daily, especially for new sets - re-run monthly
- **Use comments**: Add # comments in your input files to organize sections (e.g., "# Sideboard")
- **Separate foils**: In inventory mode, each finish has its own row for precise tracking
