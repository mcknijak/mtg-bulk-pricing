#!/usr/bin/env python3
"""
MTG Card Pricing Tool
A comprehensive script to retrieve Magic: The Gathering card prices from Scryfall.
"""

import argparse
from abc import ABC, abstractmethod
import csv
import json
import os
import sys
import time
import re
from typing import List, Dict, Optional, Tuple
import requests # type: ignore
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

class CardParser(ABC):
    """Base class for card list parsers."""
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the file format."""
        pass
    
    @abstractmethod
    def parse(self, file_path: str) -> List[Tuple[str, Optional[str], Optional[str], Optional[str], int]]:
        """
        Parse the file and return list of cards.
        
        Returns:
            List of (card_name, set_code, collector_number, foil, quantity) tuples
        """
        pass
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Card Parser base Class."""
        pass


class StandardTextParser(CardParser):
    """Parser for standard pipe-delimited format."""
    
    def can_parse(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # If we see a pipe delimiter, it's standard format
                        return '|' in line
                return True  # Empty file, assume standard
        except Exception:
            return False
    
    def parse(self, file_path: str) -> List[Tuple[str, Optional[str], Optional[str], Optional[str], int]]:
        cards = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse using existing logic
                        parts = [p.strip() for p in line.split('|')]
                        card_name = parts[0]
                        set_code = parts[1].upper() if len(parts) > 1 and parts[1] else None
                        collector_number = parts[2] if len(parts) > 2 and parts[2] else None
                        foil = parts[3].lower() if len(parts) > 3 and parts[3] else None
                        
                        cards.append((card_name, set_code, collector_number, foil, 1))
        except Exception as e:
            print(f"Error parsing standard text format: {e}", file=sys.stderr)
        
        return cards
    
    @property
    def format_name(self) -> str:
        return "Standard Text Format"


class DeckExportTextParser(CardParser):
    """Parser for Archidekt/Moxfield text export format."""
    
    def can_parse(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Check for deck export format: number card (SET)
                        return re.match(r'^\d+x?\s+.+\([A-Z0-9]{3,4}\)', line, re.IGNORECASE)
                        # Check first non-comment line
            return False
        except Exception:
            return False
    
    def parse(self, file_path: str) -> List[Tuple[str, Optional[str], Optional[str], Optional[str], int]]:
        cards = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Pattern 1: quantity card_name (set) collector_number [*F*|*E*]
                    pattern_full = r'^(\d+)x?\s+(.+?)\s+\(([A-Z0-9]{3,4})\)\s+(\d+[a-z]?)\s*(\*F\*|\*E\*|\[F\]|\[E\]|foil|etched)?$'
                    match = re.match(pattern_full, line, re.IGNORECASE)
                    
                    if match:
                        quantity = int(match.group(1))
                        card_name = match.group(2).strip()
                        set_code = match.group(3).upper()
                        collector_number = match.group(4)
                        foil = self._parse_finish(match.group(5))
                        
                        for _ in range(quantity):
                            cards.append((card_name, set_code, collector_number, foil, 1))
                        continue
                    
                    # Pattern 2: quantity card_name (set) [*F*|*E*]
                    pattern_set = r'^(\d+)x?\s+(.+?)\s+\(([A-Z0-9]{3,4})\)\s*(\*F\*|\*E\*|\[F\]|\[E\]|foil|etched)?$'
                    match = re.match(pattern_set, line, re.IGNORECASE)
                    
                    if match:
                        quantity = int(match.group(1))
                        card_name = match.group(2).strip()
                        set_code = match.group(3).upper()
                        foil = self._parse_finish(match.group(4))
                        
                        for _ in range(quantity):
                            cards.append((card_name, set_code, None, foil, 1))
                        continue
                    
                    # Pattern 3: quantity card_name [*F*|*E*]
                    pattern_simple = r'^(\d+)x?\s+(.+?)\s*(\*F\*|\*E\*|\[F\]|\[E\]|foil|etched)?$'
                    match = re.match(pattern_simple, line, re.IGNORECASE)
                    
                    if match:
                        quantity = int(match.group(1))
                        card_name = match.group(2).strip()
                        foil = self._parse_finish(match.group(3))
                        
                        for _ in range(quantity):
                            cards.append((card_name, None, None, foil, 1))
                        continue
                    
                    print(f"Warning: Could not parse line: {line}", file=sys.stderr)
        
        except Exception as e:
            print(f"Error parsing deck export text: {e}", file=sys.stderr)
        
        return cards
    
    def _parse_finish(self, finish_marker: Optional[str]) -> Optional[str]:
        """Parse finish marker into standard format."""
        if not finish_marker:
            return None
        
        finish_marker_lower = finish_marker.lower()
        if '*f*' in finish_marker_lower or '[f]' in finish_marker_lower or finish_marker_lower == 'foil':
            return 'foil'
        elif '*e*' in finish_marker_lower or '[e]' in finish_marker_lower or finish_marker_lower == 'etched':
            return 'etched'
        return None
    
    @property
    def format_name(self) -> str:
        return "Deck Export Text Format (Archidekt/Moxfield)"


class ArchidektCSVParser(CardParser):
    """Parser for Archidekt CSV export format."""
    
    def can_parse(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip().lower()
                return 'card name' in first_line and 'edition' in first_line
        except Exception:
            return False
    
    def parse(self, file_path: str) -> List[Tuple[str, Optional[str], Optional[str], Optional[str], int]]:
        cards = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    quantity = int(row.get('Count', row.get('Quantity', '1')))
                    card_name = row.get('Card Name', row.get('Name', '')).strip()
                    
                    # Archidekt uses "Edition" for set name
                    set_code = row.get('Edition', '').strip().upper() or None
                    collector_number = row.get('Collector Number', '').strip() or None
                    
                    # Foil handling
                    foil_value = row.get('Foil', '').strip().lower()
                    foil = 'foil' if foil_value in ['yes', 'true', '1', 'foil'] else None
                    
                    if card_name:
                        for _ in range(quantity):
                            cards.append((card_name, set_code, collector_number, foil, 1))
        
        except Exception as e:
            print(f"Error parsing Archidekt CSV: {e}", file=sys.stderr)
        
        return cards
    
    @property
    def format_name(self) -> str:
        return "Archidekt CSV"


class MoxfieldCSVParser(CardParser):
    """Parser for Moxfield CSV export format."""
    
    def can_parse(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip().lower()
                return 'tradelist count' in first_line and 'collector number' in first_line
        except Exception:
            return False
    
    def parse(self, file_path: str) -> List[Tuple[str, Optional[str], Optional[str], Optional[str], int]]:
        cards = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    quantity = int(row.get('Count', '1'))
                    card_name = row.get('Name', '').strip()
                    set_code = row.get('Edition', '').strip().upper() or None
                    collector_number = row.get('Collector Number', '').strip() or None
                    
                    # Foil handling
                    foil_value = row.get('Foil', '').strip().lower()
                    if foil_value in ['foil', 'etched']:
                        foil = foil_value
                    else:
                        foil = None
                    
                    if card_name:
                        for _ in range(quantity):
                            cards.append((card_name, set_code, collector_number, foil, 1))
        
        except Exception as e:
            print(f"Error parsing Moxfield CSV: {e}", file=sys.stderr)
        
        return cards
    
    @property
    def format_name(self) -> str:
        return "Moxfield CSV"


class GenericCSVParser(CardParser):
    """Parser for generic CSV format."""
    
    def can_parse(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip().lower()
                if first_line.count(',') >= 1:
                    parts = first_line.split(',')
                    return parts[0].strip() in ['count', 'quantity', 'qty', 'amount']
            return False
        except Exception:
            return False
    
    def parse(self, file_path: str) -> List[Tuple[str, Optional[str], Optional[str], Optional[str], int]]:
        cards = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) < 2:
                        continue
                    
                    quantity = int(row[0]) if row[0].isdigit() else 1
                    card_name = row[1].strip()
                    set_code = row[2].strip().upper() if len(row) > 2 and row[2] else None
                    collector_number = row[3].strip() if len(row) > 3 and row[3] else None
                    foil = row[4].strip().lower() if len(row) > 4 and row[4] else None
                    
                    if card_name:
                        for _ in range(quantity):
                            cards.append((card_name, set_code, collector_number, foil, 1))
        
        except Exception as e:
            print(f"Error parsing generic CSV: {e}", file=sys.stderr)
        
        return cards
    
    @property
    def format_name(self) -> str:
        return "Generic CSV"


class ParserFactory:
    """Factory class to detect and return the appropriate parser."""
    
    # Order matters! Check most specific formats first
    PARSERS = [
        MoxfieldCSVParser(),
        ArchidektCSVParser(),
        DeckExportTextParser(),
        GenericCSVParser(),
        StandardTextParser(),  # Fallback - always matches
    ]
    
    @classmethod
    def get_parser(cls, file_path: str) -> CardParser:
        """
        Detect file format and return appropriate parser.
        
        Args:
            file_path: Path to the input file
            
        Returns:
            CardParser instance for the detected format
        """
        for parser in cls.PARSERS:
            if parser.can_parse(file_path):
                return parser
        
        # Should never reach here since StandardTextParser always matches
        return StandardTextParser()

def convert_parsed_cards_to_strings(parsed_cards: List[Tuple[str, Optional[str], Optional[str], Optional[str], int]], 
                                   set_filter: Optional[str] = None) -> List[str]:
    """
    Convert parsed card tuples to internal string format.
    
    Args:
        parsed_cards: List of (card_name, set_code, collector_number, foil, quantity) tuples
        set_filter: Optional set code to apply if card doesn't have one
        
    Returns:
        List of card strings in internal format (card_name|set|number|foil)
    """
    cards_to_process = []
    
    for card_name, set_code, collector_number, foil, qty in parsed_cards:
        # Apply set filter if provided and card doesn't have a set
        if set_filter and not set_code:
            set_code = set_filter
        
        # Build the card string in our internal format
        card_str = card_name
        if set_code:
            card_str += f"|{set_code}"
        if collector_number:
            card_str += f"|{collector_number}"
        if foil:
            card_str += f"|{foil}"
        
        cards_to_process.append(card_str)
    
    return cards_to_process


def process_card_list(input_file: str, output_file: str, set_filter: Optional[str] = None):
    """Process a card list and generate pricing CSV."""
    
    api = ScryfallAPI()
    pricer = CardPricer(api)
    
    # Detect format and parse
    parser = ParserFactory.get_parser(input_file)
    print(f"Detected format: {parser.format_name}")
    
    parsed_cards = parser.parse(input_file)
    cards_to_process = convert_parsed_cards_to_strings(parsed_cards, set_filter)
    
    if not cards_to_process:
        print("No cards found in input file.", file=sys.stderr)
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
        
        # If specific printing requested (set + collector number), just return that one price
        if set_code and collector_number:
            card = price_data[0]
            
            results.append({
                'card_name': card['card_name'],
                'set': card['set'],
                'collector_number': card['collector_number'],
                'finish': card['finish'],
                'price': f"${card['price']:.2f}" if card['price'] else 'N/A',
                'min_price': '',
                'max_price': '',
                'min_printing': '',
                'max_printing': ''
            })
        else:
            # Get cheapest and most expensive for general searches
            cheapest, most_expensive = pricer.get_cheapest_and_most_expensive(price_data)
            
            if cheapest and most_expensive:
                results.append({
                    'card_name': cheapest['card_name'],
                    'set': set_code or 'Multiple',
                    'collector_number': collector_number or 'Multiple',
                    'finish': foil or 'nonfoil',
                    'price': '',  # Leave blank for range searches
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
                    'finish': foil or 'nonfoil',
                    'price': 'No Price Data',
                    'min_price': '',
                    'max_price': '',
                    'min_printing': '',
                    'max_printing': ''
                })
    
    # Write results to CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['card_name', 'set', 'collector_number', 'finish', 
                         'price', 'min_price', 'max_price', 'min_printing', 'max_printing']
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
        print("Current Prices are included - just add quantities and run calculate-value mode")
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

def generate_buylist(inventory_file: str, set_codes: List[str], output_file: str):
    """
    Generate a buylist of cards NOT in inventory for specified sets.
    Shows what cards user needs to complete their collection.
    
    Args:
        inventory_file: Path to existing inventory CSV (with quantities)
        set_codes: List of set codes to check completeness for
        output_file: Path to output buylist CSV
    """
    
    api = ScryfallAPI()
    
    # Read existing inventory to get what user already has
    owned_cards = {}  # Key: (set, collector_number, finish), Value: quantity
    
    try:
        with open(inventory_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                quantity_str = row.get('quantity', '').strip()
                if quantity_str and quantity_str.isdigit() and int(quantity_str) > 0:
                    set_code = row.get('set', '').strip().upper()
                    collector_number = row.get('collector_number', '').strip()
                    finish = row.get('finish', 'nonfoil').strip().lower()
                    quantity = int(quantity_str)
                    
                    key = (set_code, collector_number, finish)
                    owned_cards[key] = owned_cards.get(key, 0) + quantity
    except FileNotFoundError:
        print(f"Inventory file not found: {inventory_file}")
        print("Generating buylist for entire sets...")
    except Exception as e:
        print(f"Error reading inventory file: {e}", file=sys.stderr)
        print("Generating buylist for entire sets...")
    
    # Get all cards from specified sets
    all_cards_needed = []
    total_cost = 0
    
    for set_code in set_codes:
        print(f"Fetching cards from set: {set_code}")
        cards = api.get_set_cards(set_code)
        
        for card in cards:
            card_name = card.get('name')
            set_code_upper = card.get('set').upper()
            collector_number = card.get('collector_number')
            rarity = card.get('rarity')
            finishes = card.get('finishes', [])
            
            prices = api.extract_prices(card)
            
            # Check each finish
            for finish in finishes:
                # Determine price for this finish
                if finish == 'nonfoil':
                    price = prices['usd']
                elif finish == 'foil':
                    price = prices['usd_foil']
                elif finish == 'etched':
                    price = prices['usd_etched']
                else:
                    price = None
                
                # Check if user already owns this card in this finish
                key = (set_code_upper, collector_number, finish)
                owned_quantity = owned_cards.get(key, 0)
                
                # Collectors typically want 1 of each finish
                needed_quantity = 1 - owned_quantity
                
                if needed_quantity > 0:
                    unit_price = price if price else 0
                    total_price = unit_price * needed_quantity
                    
                    all_cards_needed.append({
                        'card_name': card_name,
                        'set': set_code_upper,
                        'collector_number': collector_number,
                        'rarity': rarity,
                        'finish': finish,
                        'owned': owned_quantity,
                        'needed': needed_quantity,
                        'unit_price': f"${unit_price:.2f}" if price else 'N/A',
                        'total_price': f"${total_price:.2f}" if price else 'N/A'
                    })
                    
                    if price:
                        total_cost += total_price
    
    # Sort by set, then collector number, then finish
    all_cards_needed.sort(key=lambda x: (x['set'], 
                                          int(''.join(filter(str.isdigit, x['collector_number'])) or '0'),
                                          x['finish']))
    
    # Write buylist
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['card_name', 'set', 'collector_number', 'rarity', 'finish',
                         'owned', 'needed', 'unit_price', 'total_price']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_cards_needed)
        
        print(f"\nBuylist written to {output_file}")
        print(f"Total cards needed: {len(all_cards_needed)}")
        print(f"Total estimated cost: ${total_cost:.2f}")
        
        # Provide some helpful statistics
        by_rarity = {}
        for card in all_cards_needed:
            rarity = card['rarity']
            by_rarity[rarity] = by_rarity.get(rarity, 0) + 1
        
        print(f"\nBreakdown by rarity:")
        for rarity, count in sorted(by_rarity.items()):
            print(f"  {rarity.capitalize()}: {count}")
        
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
  python mtg_pricer.py -i cards.txt -o prices.csv --set one
  
  # Generate inventory template with prices
  python mtg_pricer.py --inventory-mode --sets MH3 OTJ -o template.csv
  
  # Calculate inventory value from filled template
  python mtg_pricer.py --calculate-value -i filled_template.csv -o inventory_value.csv

  # Generate buylist for missing cards from inventory
  python mtg_pricer.py --buylist -i my_inventory.csv --sets MH3 -o buylist.csv
  
  # Generate complete buylist for sets (no inventory file)
  python mtg_pricer.py --buylist --sets MH3 BLB -o complete_buylist.csv

Supported Input Formats (Auto-detected):
  
  Standard Format:
    Card Name
    Card Name|SET
    Card Name|SET|123
    Card Name|SET|123|foil
  
  Archidekt/Moxfield Text Export:
    1 Card Name (SET) 123
    1 Card Name (SET) 123 *F*
    1 Card Name (SET) 123 *E*
    4 Card Name (SET)
    1 Card Name
  
  Archidekt CSV Export:
    Required Columns: Count, Card Name, Edition, Collector Number, Foil
  
  Moxfield CSV Export:
    Required Columns: Count, Name, Edition, Collector Number, Foil
  
  Generic CSV:
    Columns: Quantity, Card Name, Set Code, Collector Number, Finish

Notes:
  - All formats are case insensitive
  - Nonfoil is default when finish not specified
  - *F* = foil, *E* = etched
  - Comments start with #
        """
    )
    
    # Mode selection (optional - defaults to price-list mode)
    mode_group = parser.add_mutually_exclusive_group(required=False)
    mode_group.add_argument('--inventory-mode', action='store_true',
                           help='Generate inventory template for specified sets')
    mode_group.add_argument('--calculate-value', action='store_true',
                           help='Calculate total value from filled inventory template')
    mode_group.add_argument('--buylist', action='store_true',
                           help='Generate buylist of missing cards from sets')
    
    # Input/output files
    parser.add_argument('-i', '--input',
                       help='Input file (txt or csv)')
    parser.add_argument('-o', '--output', required=True,
                       help='Output CSV file')
    parser.add_argument('--set', dest='set_filter',
                       help='Filter cards to specific set (case insensitive)')
    
    # Inventory mode arguments
    parser.add_argument('--sets', nargs='+',
                       help='Set codes for inventory mode (case insensitive)')
    
    args = parser.parse_args()
    
    # Validate arguments based on mode
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

    elif args.buylist:
        if not args.sets:
            parser.error("--buylist requires --sets")
        # Input is optional - if not provided, assumes complete buylist
        sets_upper = [s.upper() for s in args.sets]
        generate_buylist(args.input if args.input else None, sets_upper, args.output)
    
    else:
        # Default mode: price list
        if not args.input:
            parser.error("price list mode requires --input")
        process_card_list(args.input, args.output, args.set_filter.upper() if args.set_filter else None)


if __name__ == '__main__':
    main()
