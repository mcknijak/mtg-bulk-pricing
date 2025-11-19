#!/usr/bin/env python3
"""
MTG Card Pricing Tool
A comprehensive script to retrieve Magic: The Gathering card prices from TCGPlayer or Card Kingdom APIs.
"""

import argparse
import csv
import json
import os
import sys
import time
from typing import List, Dict, Optional, Tuple
import requests
from pathlib import Path


class MTGPricingAPI:
    """Base class for MTG pricing API interactions."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.rate_limit_delay = 0.1  # 100ms between requests
        
    def _rate_limit(self):
        """Implement rate limiting to avoid API throttling."""
        time.sleep(self.rate_limit_delay)


class ScryfallAPI(MTGPricingAPI):
    """
    Scryfall API wrapper - free, no API key required.
    """
    
    BASE_URL = "https://api.scryfall.com"
    
    def __init__(self):
        super().__init__()
        self.rate_limit_delay = 0.1  # Scryfall requests 50-100ms between calls
        
    def search_card(self, card_name: str, set_code: Optional[str] = None) -> List[Dict]:
        """Search for a card by name, optionally filtered by set."""
        self._rate_limit()
        
        query = f'!"{card_name}"'
        if set_code:
            query += f' set:{set_code}'
            
        params = {
            'q': query,
            'unique': 'prints',
            'order': 'released'
        }
        
        try:
            response = self.session.get(f"{self.BASE_URL}/cards/search", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise
        except Exception as e:
            print(f"Error searching for card '{card_name}': {e}", file=sys.stderr)
            return []
    
    def get_card_by_set_number(self, set_code: str, collector_number: str, 
                                foil: Optional[bool] = None) -> Optional[Dict]:
        """Get a specific card by set code and collector number."""
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/cards/{set_code.lower()}/{collector_number}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting card {set_code}/{collector_number}: {e}", file=sys.stderr)
            return None
    
    def get_set_cards(self, set_code: str) -> List[Dict]:
        """Get all cards from a specific set."""
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/cards/search"
            params = {
                'q': f'set:{set_code}',
                'unique': 'prints',
                'order': 'set'
            }
            
            all_cards = []
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            all_cards.extend(data.get('data', []))
            
            # Handle pagination
            while data.get('has_more'):
                self._rate_limit()
                next_url = data.get('next_page')
                response = self.session.get(next_url)
                response.raise_for_status()
                data = response.json()
                all_cards.extend(data.get('data', []))
            
            return all_cards
        except Exception as e:
            print(f"Error getting cards from set {set_code}: {e}", file=sys.stderr)
            return []
    
    def extract_prices(self, card: Dict, foil_preference: Optional[str] = None) -> Dict[str, float]:
        """
        Extract pricing information from a card object.
        
        Args:
            card: Scryfall card object
            foil_preference: 'foil', 'nonfoil', or None for both
            
        Returns:
            Dictionary with price information
        """
        prices = card.get('prices', {})
        result = {
            'usd': prices.get('usd'),
            'usd_foil': prices.get('usd_foil'),
            'usd_etched': prices.get('usd_etched')
        }
        
        # Convert strings to floats, handle None
        for key in result:
            if result[key]:
                try:
                    result[key] = float(result[key])
                except (ValueError, TypeError):
                    result[key] = None
        
        return result


class CardPricer:
    """Main class for handling card pricing operations."""
    
    def __init__(self, api: MTGPricingAPI):
        self.api = api
        
    def parse_card_input(self, line: str) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        """
        Parse a card input line.
        
        Formats supported:
        - "Card Name"
        - "Card Name|SET"
        - "Card Name|SET|123"
        - "Card Name|SET|123|foil"
        
        Returns:
            (card_name, set_code, collector_number, foil)
        """
        parts = [p.strip() for p in line.split('|')]
        
        card_name = parts[0]
        set_code = parts[1].upper() if len(parts) > 1 and parts[1] else None  # Convert to uppercase
        collector_number = parts[2] if len(parts) > 2 else None
        foil = parts[3].lower() if len(parts) > 3 and parts[3] else None  # Convert to lowercase
        
        return card_name, set_code, collector_number, foil
    
    def get_price_for_card(self, card_name: str, set_code: Optional[str] = None,
                          collector_number: Optional[str] = None, 
                          foil: Optional[str] = None) -> List[Dict]:
        """
        Get pricing for a card.
        
        Returns:
            List of price dictionaries with card info
        """
        if set_code and collector_number:
            # Specific printing requested
            card = self.api.get_card_by_set_number(set_code, collector_number, foil)
            if card:
                prices = self.api.extract_prices(card, foil)
                return [{
                    'card_name': card.get('name'),
                    'set': card.get('set').upper(),
                    'collector_number': card.get('collector_number'),
                    'finish': self._determine_finish(card, foil),
                    'price': self._get_relevant_price(prices, foil)
                }]
            return []
        
        # Search for all printings
        cards = self.api.search_card(card_name, set_code)
        
        if not cards:
            return []
        
        # Get prices for all printings
        price_data = []
        for card in cards:
            prices = self.api.extract_prices(card)
            
            # Handle nonfoil
            if prices['usd'] is not None:
                price_data.append({
                    'card_name': card.get('name'),
                    'set': card.get('set').upper(),
                    'collector_number': card.get('collector_number'),
                    'finish': 'nonfoil',
                    'price': prices['usd']
                })
            
            # Handle foil
            if prices['usd_foil'] is not None:
                price_data.append({
                    'card_name': card.get('name'),
                    'set': card.get('set').upper(),
                    'collector_number': card.get('collector_number'),
                    'finish': 'foil',
                    'price': prices['usd_foil']
                })
            
            # Handle etched
            if prices['usd_etched'] is not None:
                price_data.append({
                    'card_name': card.get('name'),
                    'set': card.get('set').upper(),
                    'collector_number': card.get('collector_number'),
                    'finish': 'etched',
                    'price': prices['usd_etched']
                })
        
        # Filter by foil preference if specified, default to nonfoil
        if foil:
            price_data = [p for p in price_data if p['finish'] == foil]
        else:
            # Default to nonfoil only when not specified
            price_data = [p for p in price_data if p['finish'] == 'nonfoil']
        
        return price_data
    
    def _determine_finish(self, card: Dict, foil_pref: Optional[str]) -> str:
        """Determine the finish type for a card."""
        if foil_pref:
            return foil_pref
        # Always default to nonfoil when not specified
        return 'nonfoil'
    
    def _get_relevant_price(self, prices: Dict, foil_pref: Optional[str]) -> Optional[float]:
        """Get the relevant price based on foil preference."""
        if foil_pref == 'foil':
            return prices['usd_foil']
        elif foil_pref == 'etched':
            return prices['usd_etched']
        elif foil_pref == 'nonfoil':
            return prices['usd']
        else:
            # Return first available price
            return prices['usd'] or prices['usd_foil'] or prices['usd_etched']
    
    def get_cheapest_and_most_expensive(self, price_data: List[Dict]) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Find the cheapest and most expensive printings from price data."""
        if not price_data:
            return None, None
        
        valid_prices = [p for p in price_data if p['price'] is not None]
        
        if not valid_prices:
            return None, None
        
        cheapest = min(valid_prices, key=lambda x: x['price'])
        most_expensive = max(valid_prices, key=lambda x: x['price'])
        
        return cheapest, most_expensive


def process_card_list(input_file: str, output_file: str, set_filter: Optional[str] = None):
    """Process a card list and generate pricing CSV."""
    
    api = ScryfallAPI()
    pricer = CardPricer(api)
    
    # Read input file
    cards_to_process = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    cards_to_process.append(line)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process cards
    results = []
    total_cards = len(cards_to_process)
    
    for idx, card_line in enumerate(cards_to_process, 1):
        print(f"Processing {idx}/{total_cards}: {card_line}")
        
        card_name, set_code, collector_number, foil = pricer.parse_card_input(card_line)
        
        # Apply set filter if provided and not already specified
        if set_filter and not set_code:
            set_code = set_filter.upper()
        
        price_data = pricer.get_price_for_card(card_name, set_code, collector_number, foil)
        
        if not price_data:
            results.append({
                'card_name': card_name,
                'set': set_code or 'N/A',
                'collector_number': collector_number or 'N/A',
                'finish': foil or 'N/A',
                'min_price': 'Not Found',
                'max_price': 'Not Found',
                'min_printing': 'N/A',
                'max_printing': 'N/A'
            })
            continue
        
        if set_code and collector_number:
            # Specific card requested
            card = price_data[0]
            results.append({
                'card_name': card['card_name'],
                'set': card['set'],
                'collector_number': card['collector_number'],
                'finish': card['finish'],
                'min_price': f"${card['price']:.2f}" if card['price'] else 'N/A',
                'max_price': f"${card['price']:.2f}" if card['price'] else 'N/A',
                'min_printing': f"{card['set']} #{card['collector_number']} ({card['finish']})",
                'max_printing': f"{card['set']} #{card['collector_number']} ({card['finish']})"
            })
        else:
            # Get cheapest and most expensive
            cheapest, most_expensive = pricer.get_cheapest_and_most_expensive(price_data)
            
            if cheapest and most_expensive:
                results.append({
                    'card_name': cheapest['card_name'],
                    'set': set_code or 'Multiple',
                    'collector_number': 'Multiple' if not collector_number else collector_number,
                    'finish': foil or 'Multiple',
                    'min_price': f"${cheapest['price']:.2f}",
                    'max_price': f"${most_expensive['price']:.2f}",
                    'min_printing': f"{cheapest['set']} #{cheapest['collector_number']} ({cheapest['finish']})",
                    'max_printing': f"{most_expensive['set']} #{most_expensive['collector_number']} ({most_expensive['finish']})"
                })
            else:
                results.append({
                    'card_name': card_name,
                    'set': set_code or 'N/A',
                    'collector_number': collector_number or 'N/A',
                    'finish': foil or 'N/A',
                    'min_price': 'No Price Data',
                    'max_price': 'No Price Data',
                    'min_printing': 'N/A',
                    'max_printing': 'N/A'
                })
    
    # Write results to CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['card_name', 'set', 'collector_number', 'finish', 
                         'min_price', 'max_price', 'min_printing', 'max_printing']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nResults written to {output_file}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


def generate_inventory_template(set_codes: List[str], output_file: str, include_prices: bool = True):
    """Generate an inventory template CSV for the specified sets, optionally with prices already populated."""
    
    api = ScryfallAPI()
    
    all_cards = []
    for set_code in set_codes:
        print(f"Fetching cards from set: {set_code}")
        cards = api.get_set_cards(set_code)
        
        for card in cards:
            prices = api.extract_prices(card)
            
            # Add entry for each available finish
            finishes = card.get('finishes', [])
            
            for finish in finishes:
                # Determine which price to use
                if finish == 'nonfoil':
                    price = prices['usd']
                elif finish == 'foil':
                    price = prices['usd_foil']
                elif finish == 'etched':
                    price = prices['usd_etched']
                else:
                    price = None
                
                all_cards.append({
                    'card_name': card.get('name'),
                    'set': card.get('set').upper(),
                    'collector_number': card.get('collector_number'),
                    'rarity': card.get('rarity'),
                    'finish': finish,
                    'unit_price': f"${price:.2f}" if price else 'N/A',
                    'quantity': '',  # User fills this in
                })
    
    # Write template
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['card_name', 'set', 'collector_number', 'rarity', 
                         'finish', 'unit_price', 'quantity']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_cards)
        
        print(f"\nInventory template written to {output_file}")
        print(f"Total cards/finishes: {len(all_cards)}")
        print("Please fill in the 'quantity' column for cards you have.")
        print("Prices are already populated - just add quantities and run calculate-value mode!")
    except Exception as e:
        print(f"Error writing template file: {e}", file=sys.stderr)
        sys.exit(1)


def calculate_inventory_value(input_file: str, output_file: str):
    """Calculate total value from an inventory template that already has prices."""
    
    # Read inventory file
    inventory_items = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                quantity = row.get('quantity', '').strip()
                if quantity and quantity.isdigit() and int(quantity) > 0:
                    inventory_items.append(row)
    except Exception as e:
        print(f"Error reading inventory file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not inventory_items:
        print("No items with quantities found in inventory file.")
        sys.exit(1)
    
    # Calculate values
    results = []
    total_value = 0
    
    for item in inventory_items:
        card_name = item['card_name']
        set_code = item['set']
        collector_number = item['collector_number']
        finish = item.get('finish', 'nonfoil')
        quantity = int(item['quantity'])
        
        # Parse unit price
        unit_price_str = item.get('unit_price', 'N/A')
        if unit_price_str != 'N/A' and unit_price_str.startswith('$'):
            try:
                unit_price = float(unit_price_str.replace('$', ''))
                total_price = unit_price * quantity
                total_value += total_price
                
                results.append({
                    'card_name': card_name,
                    'set': set_code,
                    'collector_number': collector_number,
                    'rarity': item.get('rarity', 'N/A'),
                    'finish': finish,
                    'quantity': quantity,
                    'unit_price': f"${unit_price:.2f}",
                    'total_price': f"${total_price:.2f}"
                })
            except ValueError:
                results.append({
                    'card_name': card_name,
                    'set': set_code,
                    'collector_number': collector_number,
                    'rarity': item.get('rarity', 'N/A'),
                    'finish': finish,
                    'quantity': quantity,
                    'unit_price': 'Invalid Price',
                    'total_price': 'N/A'
                })
        else:
            results.append({
                'card_name': card_name,
                'set': set_code,
                'collector_number': collector_number,
                'rarity': item.get('rarity', 'N/A'),
                'finish': finish,
                'quantity': quantity,
                'unit_price': 'No Price Data',
                'total_price': 'N/A'
            })
    
    # Write results
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['card_name', 'set', 'collector_number', 'rarity', 'finish', 
                         'quantity', 'unit_price', 'total_price']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nInventory value written to {output_file}")
        print(f"Total cards: {sum(r['quantity'] for r in results)}")
        print(f"Total inventory value: ${total_value:.2f}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='MTG Card Pricing Tool - Retrieve prices for Magic: The Gathering cards',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Price a simple card list
  python mtg_pricer.py -i cards.txt -o prices.csv
  
  # Price cards from a specific set only
  python mtg_pricer.py -i cards.txt -o prices.csv --set ONE
  
  # Generate inventory template for sets
  python mtg_pricer.py --inventory-mode --sets MH3 OTJ -o template.csv
  
  # Calculate inventory value
  python mtg_pricer.py --calculate-value -i filled_template.csv -o inventory_value.csv

Card List Format:
  Card Name
  Card Name|SET
  Card Name|SET|123
  Card Name|SET|123|foil
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-i', '--input', help='Input file (txt or csv) with card names')
    mode_group.add_argument('--inventory-mode', action='store_true',
                           help='Generate inventory template for specified sets')
    mode_group.add_argument('--calculate-value', action='store_true',
                       help='Calculate total value from filled inventory template')
    
    # Common arguments
    parser.add_argument('-o', '--output', required=True,
                       help='Output CSV file')
    parser.add_argument('--set', dest='set_filter',
                       help='Filter all cards to a specific set code')
    
    # Inventory mode arguments
    parser.add_argument('--sets', nargs='+',
                       help='Set codes for inventory mode (space-separated)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.inventory_mode:
        if not args.sets:
            parser.error("--inventory-mode requires --sets")
        # Convert all set codes to uppercase
        sets_upper = [s.upper() for s in args.sets]
        generate_inventory_template(sets_upper, args.output)
    
    elif args.calculate_value:
        if not args.input:
            parser.error("--calculate-value requires --input")
        calculate_inventory_value(args.input, args.output)
    
    else:
        # Standard card list processing
        process_card_list(args.input, args.output, args.set_filter)


if __name__ == '__main__':
    main()
