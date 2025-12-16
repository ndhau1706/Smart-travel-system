"""
Data preprocessing service for loading and preparing restaurant data.
"""
import json
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any
from config import settings
from database import db_manager
from utils import normalize_text


class DataPreprocessor:
    """Handles data loading and preprocessing."""
    
    def __init__(self):
        self.restaurants_path = settings.RESTAURANTS_JSON_PATH
        
    async def load_restaurants(self) -> List[Dict[str, Any]]:
        """Load restaurants from JSON file."""
        json_path = Path(self.restaurants_path)
        
        if not json_path.exists():
            raise FileNotFoundError(f"Restaurant data not found: {self.restaurants_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def preprocess_restaurant(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess a single restaurant entry.
        
        Args:
            restaurant: Raw restaurant data
            
        Returns:
            Preprocessed restaurant data
        """
        # Extract and normalize data
        processed = {
            'name': restaurant.get('name', ''),
            'address': restaurant.get('address', ''),
            'phone': restaurant.get('phone', ''),
            'website': restaurant.get('website', ''),
            'category': restaurant.get('category', ''),
            'rating': restaurant.get('rating', 0.0),
            'rating_count': restaurant.get('rating_count', 0),
            'price_level': restaurant.get('price_level', ''),
            'food_tags': json.dumps(restaurant.get('food_tags', []), ensure_ascii=False),
            'coordinates_lat': restaurant.get('coordinates', {}).get('lat'),
            'coordinates_lon': restaurant.get('coordinates', {}).get('lon'),
            'opening_hours': json.dumps(restaurant.get('opening_hours', {}), ensure_ascii=False),
            'comments': json.dumps(restaurant.get('comments', []), ensure_ascii=False),
            'location_summary': restaurant.get('location_summary', ''),
            'type_summary': restaurant.get('type_summary', ''),
            'contact_summary': restaurant.get('contact_summary', '')
        }
        
        return processed
    
    def create_searchable_text(self, restaurant: Dict[str, Any]) -> str:
        """
        Create searchable text from restaurant data.
        Normalizes to lowercase for case-insensitive matching.
        
        Args:
            restaurant: Restaurant data
            
        Returns:
            Combined searchable text (lowercase)
        """
        parts = []
        
        # Add name (lowercase for case-insensitive matching)
        if restaurant.get('name'):
            parts.append(restaurant['name'].lower())
        
        # Add food tags (lowercase)
        food_tags = restaurant.get('food_tags', [])
        if isinstance(food_tags, str):
            try:
                food_tags = json.loads(food_tags)
            except:
                food_tags = []
        if food_tags:
            parts.extend([tag.lower() if isinstance(tag, str) else tag for tag in food_tags])
        
        # Add category (lowercase)
        if restaurant.get('category'):
            parts.append(restaurant['category'].lower())
        
        # Add location summary (lowercase)
        if restaurant.get('location_summary'):
            parts.append(restaurant['location_summary'].lower())
        
        # Add address (lowercase)
        if restaurant.get('address'):
            parts.append(restaurant['address'].lower())
        
        # Add comments text
        comments = restaurant.get('comments', [])
        if isinstance(comments, str):
            try:
                comments = json.loads(comments)
            except:
                comments = []
        
        for comment in comments[:3]:  # Only first 3 comments
            if isinstance(comment, dict) and comment.get('text'):
                # Limit comment length
                comment_text = comment['text'][:200]
                parts.append(comment_text)
        
        # Combine and normalize
        text = ' '.join(parts)
        return normalize_text(text)
    
    async def save_to_database(self, restaurants: List[Dict[str, Any]]):
        """
        Save preprocessed restaurants to database.
        
        Args:
            restaurants: List of preprocessed restaurant data
        """
        async with db_manager.get_connection() as db:
            # Clear existing data
            await db.execute("DELETE FROM restaurants")
            
            # Insert new data
            for restaurant in restaurants:
                await db.execute("""
                    INSERT INTO restaurants (
                        name, address, phone, website, category,
                        rating, rating_count, price_level, food_tags,
                        coordinates_lat, coordinates_lon, opening_hours,
                        comments, location_summary, type_summary, contact_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    restaurant['name'],
                    restaurant['address'],
                    restaurant['phone'],
                    restaurant['website'],
                    restaurant['category'],
                    restaurant['rating'],
                    restaurant['rating_count'],
                    restaurant['price_level'],
                    restaurant['food_tags'],
                    restaurant['coordinates_lat'],
                    restaurant['coordinates_lon'],
                    restaurant['opening_hours'],
                    restaurant['comments'],
                    restaurant['location_summary'],
                    restaurant['type_summary'],
                    restaurant['contact_summary']
                ))
            
            await db.commit()
    
    async def load_from_database(self) -> List[Dict[str, Any]]:
        """
        Load restaurants from database.
        
        Returns:
            List of restaurant data
        """
        async with db_manager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM restaurants") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def initialize_data(self):
        """
        Initialize data: load from JSON, preprocess, and save to database.
        """
        print("Loading restaurant data from JSON...")
        raw_data = await self.load_restaurants()
        print(f"Loaded {len(raw_data)} restaurants")
        
        print("Preprocessing restaurant data...")
        processed_data = [self.preprocess_restaurant(r) for r in raw_data]
        
        print("Saving to database...")
        await self.save_to_database(processed_data)
        print("Data initialization complete!")
        
        return processed_data


# Global instance
data_preprocessor = DataPreprocessor()
