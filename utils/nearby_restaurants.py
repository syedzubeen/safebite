import os
import httpx

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")


def _extract_location(message: str) -> str:
    """Use AI to extract a clean location string from a message."""
    from utils.ai_client import ask
    prompt = f"""Extract the location (city, neighbourhood, or area) from this message.
Return ONLY the location string, nothing else. If no location found, return empty string.

Message: {message}

Examples:
"team lunch at karim's, old delhi" → "Old Delhi, India"
"ordering from paradise, hyderabad" → "Hyderabad, India"
"lunch at poke place on 5th street" → ""
"belgian waffle, nfc, new delhi" → "NFC, New Delhi, India"
"""
    result = ask(prompt)
    if not result:
        return ""
    result = result.strip()
    return result if len(result) < 100 else ""


def find_nearby_gluten_free(restaurant_name: str, location_context: str = "", radius_km: int = 5) -> list[dict]:
    """
    Search Google Maps via SerpAPI for gluten-free friendly restaurants
    near the given restaurant, within radius_km.
    Returns a list of dicts with name, address, rating, and map link.
    """
    try:
        # Extract clean location string using AI
        location = _extract_location(location_context) if location_context else ""
        geo_query = f"{restaurant_name} {location}".strip() if location else restaurant_name

        # First get coordinates of the original restaurant
        geo_params = {
            "engine": "google_maps",
            "q": geo_query,
            "api_key": SERPAPI_KEY,
            "type": "search",
        }
        geo_response = httpx.get("https://serpapi.com/search", params=geo_params, timeout=15)
        geo_data = geo_response.json()

        # Extract GPS coordinates from first result
        gps = None
        local_results = geo_data.get("local_results", [])
        if local_results:
            gps = local_results[0].get("gps_coordinates")

        # Search for nearby gluten-free restaurants
        nearby_params = {
            "engine": "google_maps",
            "q": "gluten free restaurant",
            "api_key": SERPAPI_KEY,
            "type": "search",
            "radius": radius_km * 1000,  # metres
        }

        if gps:
            nearby_params["ll"] = f"@{gps['latitude']},{gps['longitude']},14z"
        else:
            # Fall back to location-based search using full context
            fallback_location = location_context or restaurant_name
            nearby_params["q"] = f"gluten free restaurant near {fallback_location}"

        nearby_response = httpx.get("https://serpapi.com/search", params=nearby_params, timeout=15)
        nearby_data = nearby_response.json()

        results = []
        for place in nearby_data.get("local_results", [])[:5]:
            place_id = place.get("place_id", "")
            gps_coords = place.get("gps_coordinates", {})
            # Build maps link from place_id or GPS coordinates
            if place_id:
                maps_link = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            elif gps_coords:
                lat = gps_coords.get("latitude", "")
                lng = gps_coords.get("longitude", "")
                name_encoded = place.get("title", "").replace(" ", "+")
                maps_link = f"https://www.google.com/maps/search/{name_encoded}/@{lat},{lng},17z"
            else:
                name_encoded = place.get("title", "").replace(" ", "+")
                addr_encoded = place.get("address", "").replace(" ", "+")
                maps_link = f"https://www.google.com/maps/search/{name_encoded}+{addr_encoded}"
            results.append({
                "name": place.get("title", "Unknown"),
                "address": place.get("address", ""),
                "rating": place.get("rating"),
                "maps_link": maps_link,
            })

        return results

    except Exception as e:
        print(f"[nearby] error: {e}")
        return []


def format_nearby_suggestions(restaurant_name: str, nearby: list[dict]) -> str:
    if not nearby:
        return (
            f"Unfortunately, I couldn't find any gluten-free friendly restaurants "
            f"near *{restaurant_name}*. You may want to suggest a different venue or eat beforehand."
        )

    lines = [f"Nothing safe at *{restaurant_name}* for celiac disease.\n"]
    lines.append("Here are nearby gluten-friendly alternatives you could suggest to your team:\n")

    for i, place in enumerate(nearby, 1):
        rating_str = f" ({place['rating']}⭐)" if place.get("rating") else ""
        address_str = f" — {place['address']}" if place.get("address") else ""
        maps_str = f" | <{place['maps_link']}|View on Maps>" if place.get("maps_link") else ""
        lines.append(f"{i}. *{place['name']}*{rating_str}{address_str}{maps_str}")

    lines.append("\n_You can share one of these with your colleague as an alternative venue._")
    return "\n".join(lines)
