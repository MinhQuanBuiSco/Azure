"""Prompt templates for common travel planning scenarios."""


def weekend_getaway_prompt(destination: str) -> str:
    """Generate prompt for planning a weekend getaway."""
    return f"""Plan a perfect weekend getaway to {destination}.

Please help me plan by:
1. Searching for flights departing Friday evening and returning Sunday night
2. Finding a centrally located hotel (2 nights)
3. Checking the weather forecast
4. Suggesting must-see attractions that can be covered in 2 days
5. Recommending restaurants for Friday dinner, Saturday meals, and Sunday brunch
6. Calculating a reasonable budget

Focus on efficiency - I want to maximize my short time there while still enjoying the experience without rushing."""


def family_vacation_prompt(destination: str, adults: int = 2, children: int = 2) -> str:
    """Generate prompt for planning a family vacation."""
    return f"""Plan a family-friendly vacation to {destination} for {adults} adults and {children} children.

Please help me plan by:
1. Searching for family-friendly flights with good timing
2. Finding hotels with family amenities (pool, connecting rooms, kids' activities)
3. Checking the weather and best time to visit
4. Suggesting kid-friendly attractions and activities
5. Recommending family restaurants with children's menus
6. Getting visa requirements for the whole family
7. Calculating budget including child-specific costs

Priorities: Safety, convenience, activities suitable for children, not too much walking, mix of educational and fun experiences."""


def budget_backpacker_prompt(destination: str, days: int = 14) -> str:
    """Generate prompt for budget backpacker trip planning."""
    return f"""Plan a budget backpacker trip to {destination} for {days} days.

Please help me plan by:
1. Finding the cheapest flight options (flexible dates okay)
2. Searching for hostels, guesthouses, or budget accommodations under $30/night
3. Identifying free attractions and activities
4. Finding cheap local food spots and street food areas
5. Getting info on budget transportation (buses, trains, walking routes)
6. Checking visa requirements and costs
7. Calculating a minimal daily budget

Tips needed: Money-saving hacks, free things to do, cheap eats, hostel recommendations, local transport passes, off-peak timing."""


def luxury_escape_prompt(destination: str, days: int = 5) -> str:
    """Generate prompt for luxury travel planning."""
    return f"""Plan a luxurious {days}-day escape to {destination}.

Please help me plan by:
1. Finding business or first-class flight options
2. Searching for 5-star hotels or boutique luxury properties
3. Suggesting premium experiences (private tours, Michelin restaurants, spa treatments)
4. Arranging private transportation options
5. Recommending exclusive activities and VIP experiences
6. Checking weather for the best timing
7. Creating a detailed budget for luxury travel

Focus on: Exceptional service, unique experiences, privacy, fine dining, comfort, and creating unforgettable memories. Money is not the primary concern."""


def romantic_trip_prompt(destination: str, occasion: str = "anniversary") -> str:
    """Generate prompt for romantic trip planning."""
    return f"""Plan a romantic {occasion} trip to {destination}.

Please help me plan by:
1. Finding convenient flights for two
2. Searching for romantic hotels (boutique, scenic views, couples amenities)
3. Suggesting romantic activities and experiences (sunset spots, couples spa, scenic walks)
4. Recommending intimate restaurants for special dinners
5. Finding unique experiences to share together
6. Checking weather for romantic timing
7. Planning special surprises or celebrations
8. Calculating budget for a memorable trip

Focus on: Romance, intimacy, special moments, beautiful settings, memorable experiences, and celebrating our relationship."""
