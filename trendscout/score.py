"""Scoring algorithms for app trend analysis."""

import logging
import re
from typing import List, Optional

from .models import AppPageData, RawAppRecord, ScoredAppRecord

logger = logging.getLogger(__name__)


class AppScorer:
    """Computes demand, monetization, complexity, and moat risk scores for apps."""
    
    # Keywords for low complexity scoring
    LOW_COMPLEXITY_KEYWORDS = [
        "counter", "timer", "widget", "filter", "scanner", "qr", "pdf", 
        "noise", "ringtone", "collage", "converter", "calculator", "flashlight",
        "mirror", "ruler", "level", "compass", "magnifier", "recorder",
        "note", "memo", "reminder", "list", "simple", "basic", "easy"
    ]
    
    # High moat risk keywords (trademarked/branded)
    HIGH_MOAT_KEYWORDS = [
        "official", "disney", "marvel", "snapchat", "tiktok", "instagram",
        "facebook", "twitter", "youtube", "netflix", "spotify", "amazon",
        "google", "apple", "microsoft", "adobe", "sony", "nintendo",
        "pokemon", "star wars", "minecraft", "fortnite", "coca cola",
        "mcdonalds", "nike", "adidas", "uber", "airbnb", "tesla"
    ]
    
    def __init__(self):
        """Initialize scorer."""
        pass
    
    def compute_demand_score(
        self, 
        rank_delta7d: Optional[int], 
        rating_count: int,
        recent_reviews: Optional[List[str]] = None
    ) -> float:
        """Compute demand score based on rank movement and review activity.
        
        Args:
            rank_delta7d: Rank change over 7 days (negative = rank improved)
            rating_count: Total number of ratings
            recent_reviews: Optional list of recent reviews for velocity analysis
            
        Returns:
            Demand score from 1.0 to 5.0
        """
        score = 1.0
        
        # Base score from rank delta (primary factor)
        if rank_delta7d is not None:
            if rank_delta7d <= -10:  # Rank improved significantly
                score += 2.0
            elif rank_delta7d <= -5:  # Rank improved moderately  
                score += 1.5
            elif rank_delta7d <= -1:  # Rank improved slightly
                score += 1.0
            elif rank_delta7d == 0:  # No rank change
                score += 0.5
            elif rank_delta7d <= 5:  # Rank declined slightly
                score += 0.0
            else:  # Rank declined significantly
                score -= 0.5
        
        # Bonus from rating volume (secondary factor)
        if rating_count >= 10000:
            score += 1.0
        elif rating_count >= 1000:
            score += 0.5
        elif rating_count >= 100:
            score += 0.25
        
        # Bonus from review velocity if available
        if recent_reviews and len(recent_reviews) >= 3:
            score += 0.5
        
        # Clamp to valid range
        return max(1.0, min(5.0, score))
    
    def compute_monetization_score(
        self, 
        price: float, 
        has_iap: bool,
        description: str = ""
    ) -> float:
        """Compute monetization score based on pricing model and IAP presence.
        
        Args:
            price: App price (0.0 for free)
            has_iap: Whether app has in-app purchases
            description: App description for additional signals
            
        Returns:
            Monetization score from 1.0 to 5.0
        """
        if price > 0:
            # Paid app
            if has_iap:
                return 5.0  # Paid + IAP = maximum monetization
            else:
                return 3.0  # Paid only = moderate monetization
        else:
            # Free app
            if has_iap:
                # Check for multiple IAP or paywall indicators
                desc_lower = description.lower()
                paywall_indicators = [
                    "premium", "pro", "subscription", "upgrade", "unlock",
                    "paywall", "purchase", "buy", "payment", "billing"
                ]
                
                indicator_count = sum(1 for indicator in paywall_indicators 
                                    if indicator in desc_lower)
                
                if indicator_count >= 3:
                    return 4.0  # Free + multiple IAP signals = high monetization
                else:
                    return 3.0  # Free + basic IAP = moderate monetization
            else:
                return 1.0  # Free without IAP = minimal monetization
    
    def compute_low_complexity_score(self, name: str, description: str = "") -> float:
        """Compute low complexity score based on app name and description.
        
        Apps with simple functionality are easier to replicate.
        
        Args:
            name: App name
            description: App description
            
        Returns:
            Low complexity score from 1.0 to 5.0 (higher = simpler/easier to build)
        """
        text_to_analyze = f"{name} {description}".lower()
        
        # Count matching keywords
        keyword_matches = sum(1 for keyword in self.LOW_COMPLEXITY_KEYWORDS 
                            if keyword in text_to_analyze)
        
        # Base score
        if keyword_matches >= 3:
            return 5.0  # Very simple utility
        elif keyword_matches >= 2:
            return 4.0  # Simple utility
        elif keyword_matches >= 1:
            return 3.0  # Moderate complexity
        else:
            # Check for additional complexity indicators
            complexity_indicators = [
                "ai", "ml", "machine learning", "neural", "algorithm",
                "analytics", "complex", "advanced", "professional",
                "enterprise", "business", "workflow", "integration"
            ]
            
            complexity_matches = sum(1 for indicator in complexity_indicators 
                                   if indicator in text_to_analyze)
            
            if complexity_matches >= 2:
                return 1.0  # High complexity
            elif complexity_matches >= 1:
                return 2.0  # Moderate complexity
            else:
                return 2.5  # Default moderate complexity
    
    def compute_moat_risk_score(self, name: str, description: str = "") -> float:
        """Compute moat risk score based on brand/trademark exposure.
        
        Higher score = higher risk of trademark/brand issues.
        
        Args:
            name: App name
            description: App description
            
        Returns:
            Moat risk score from 1.0 to 5.0 (higher = more risky)
        """
        text_to_analyze = f"{name} {description}".lower()
        
        # Count high-risk brand keywords
        brand_matches = sum(1 for keyword in self.HIGH_MOAT_KEYWORDS 
                           if keyword in text_to_analyze)
        
        if brand_matches >= 2:
            return 5.0  # Very high brand risk
        elif brand_matches >= 1:
            return 4.0  # High brand risk
        else:
            # Check for generic trademark indicators
            trademark_indicators = [
                "tm", "®", "©", "trademark", "copyright", "patent",
                "licensed", "authorized", "certified", "verified"
            ]
            
            trademark_matches = sum(1 for indicator in trademark_indicators 
                                  if indicator in text_to_analyze)
            
            if trademark_matches >= 1:
                return 3.0  # Moderate trademark risk
            else:
                return 1.0  # Low risk (generic concept)
    
    def compute_total_score(
        self, 
        demand: float, 
        monetization: float, 
        low_complexity: float, 
        moat_risk: float
    ) -> float:
        """Compute total weighted score.
        
        Formula: 0.35*Demand + 0.25*Monetization + 0.25*LowComplexity + 0.15*(5 - MoatRisk)
        
        Args:
            demand: Demand score (1-5)
            monetization: Monetization score (1-5) 
            low_complexity: Low complexity score (1-5)
            moat_risk: Moat risk score (1-5)
            
        Returns:
            Total weighted score
        """
        total = (
            0.35 * demand +
            0.25 * monetization + 
            0.25 * low_complexity +
            0.15 * (5.0 - moat_risk)
        )
        
        return round(total, 2)
    
    def score_app(
        self, 
        raw_record: RawAppRecord,
        app_data: AppPageData,
        rank_delta7d: Optional[int] = None
    ) -> ScoredAppRecord:
        """Score a single app with all metrics.
        
        Args:
            raw_record: Raw app record from RSS
            app_data: Scraped app page data
            rank_delta7d: Optional rank change over 7 days
            
        Returns:
            Complete scored app record
        """
        try:
            # Compute individual scores
            demand = self.compute_demand_score(
                rank_delta7d, 
                app_data.rating_count, 
                app_data.recent_reviews
            )
            
            monetization = self.compute_monetization_score(
                app_data.price,
                app_data.has_iap,
                description=""  # We only have desc_len, not full text
            )
            
            low_complexity = self.compute_low_complexity_score(
                raw_record.name,
                description=""  # Could be enhanced with full description
            )
            
            moat_risk = self.compute_moat_risk_score(
                raw_record.name,
                description=""
            )
            
            total = self.compute_total_score(demand, monetization, low_complexity, moat_risk)
            
            # Create scored record
            scored_record = ScoredAppRecord(
                # Copy all fields from raw record
                category=raw_record.category,
                country=raw_record.country,
                chart=raw_record.chart,
                rank=raw_record.rank,
                app_id=raw_record.app_id,
                name=raw_record.name,
                rss_url=raw_record.rss_url,
                fetched_at=raw_record.fetched_at,
                raw_data=raw_record.raw_data,
                
                # Add app page data
                bundle_id=app_data.bundle_id,
                price=app_data.price,
                has_iap=app_data.has_iap,
                rating_count=app_data.rating_count,
                rating_avg=app_data.rating_avg,
                desc_len=app_data.desc_len,
                rank_delta7d=rank_delta7d,
                
                # Add computed scores
                demand=demand,
                monetization=monetization,
                low_complexity=low_complexity,
                moat_risk=moat_risk,
                total=total
            )
            
            logger.debug(
                f"Scored app {raw_record.app_id}: "
                f"D={demand:.1f} M={monetization:.1f} "
                f"C={low_complexity:.1f} R={moat_risk:.1f} T={total:.2f}"
            )
            
            return scored_record
            
        except Exception as e:
            logger.error(f"Error scoring app {raw_record.app_id}: {e}")
            raise
    
    def score_apps(
        self, 
        raw_records: List[RawAppRecord],
        app_data_map: dict[str, AppPageData],
        rank_deltas: Optional[dict[str, int]] = None
    ) -> List[ScoredAppRecord]:
        """Score multiple apps efficiently.
        
        Args:
            raw_records: List of raw app records
            app_data_map: Map of app_id -> AppPageData
            rank_deltas: Optional map of app_id -> rank_delta7d
            
        Returns:
            List of scored app records
        """
        scored_records = []
        
        for raw_record in raw_records:
            app_id = raw_record.app_id
            
            if app_id not in app_data_map:
                logger.warning(f"No app data found for {app_id}, skipping")
                continue
            
            app_data = app_data_map[app_id]
            rank_delta = rank_deltas.get(app_id) if rank_deltas else None
            
            try:
                scored_record = self.score_app(raw_record, app_data, rank_delta)
                scored_records.append(scored_record)
            except Exception as e:
                logger.error(f"Failed to score app {app_id}: {e}")
                continue
        
        logger.info(f"Successfully scored {len(scored_records)}/{len(raw_records)} apps")
        return scored_records