"""
response_formatter.py
Converts backend recommendation JSON into a natural, conversational message.
Supports:
- Mood-aware tone
- Style adjectives (soft, crunchy, cheesy, etc.)
- Contextual explanations, including cuisine/dish fallbacks.
"""

from typing import List, Dict, Any

def _select_intro(attributes: Dict[str, Any]) -> str:
    mood = (attributes.get("mood") or "").lower()
    styles = attributes.get("food_style") or []

    if mood:
        MOOD_TEMPLATES = {
            "comfort food": "Sounds like you need something warm and comforting today. Since South Indian foods are light weight I am recommending South Indian Restaurants for you. Here are some cozy picks:",
            "sad": "Rough day? may be South Indian foods suits you well as this makes you fresh as they are light weight foods. Here are some comforting food options to lift your mood: ",
            "tired": "You must be exhausted may be South Indian foods suits you well as this makes you fresh as they are light weight foods.here are some easy, soothing meals nearby: ",
            "celebration": "Nice! Here are some places perfect for a celebration:",
            "hangout": "Looking for a chill hangout spot? Try these:",
            "spicy craving": "Craving something spicy? These places should hit the spot! chineese, north indian foods are more spicier and suits your mood well",
        }
        for key, text in MOOD_TEMPLATES.items():
            if key in mood:
                return text

    if styles:
        s_text = ", ".join(str(s) for s in styles)
        return f"Here are some places that match your craving for something {s_text}:"

    return "Here are some great options I found for you!"

def _build_global_explanation(attributes: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
    if not recommendations:
        return ""

    parts: List[str] = []

    veg_only = attributes.get("veg_only")
    raw_query = attributes.get("raw_query") or ""
    requested_cuisine = attributes.get("cuisine") or attributes.get("inferred_cuisine_from_dish")
    requested_dish = attributes.get("dish")
    inferred_cuisine = attributes.get("inferred_cuisine_from_dish")
    fallback_type = attributes.get("_fallback_type")
    dish_fallback = attributes.get("_dish_fallback")

    dish_text = None
    if requested_dish:
        if isinstance(requested_dish, list):
            dish_text = ", ".join(str(d) for d in requested_dish)
        else:
            dish_text = str(requested_dish)

    if veg_only:
        parts.append(
            "You asked for pure vegetarian options, so I'm only showing places that look vegetarian / pure-veg."
        )

    if fallback_type == "cuisine_family_fallback" and requested_cuisine:
        top_cat = (recommendations[0].get("category") or "").strip()
        if dish_text:
            if top_cat:
                parts.append(
                    f"I couldn't find restaurants clearly labelled as {requested_cuisine} "
                    f"for {dish_text}, so I'm recommending the closest matches like "
                    f"**{top_cat}** that should feel similar."
                )
            else:
                parts.append(
                    f"I couldn't find restaurants clearly labelled as {requested_cuisine} "
                    f"for {dish_text}, so I'm recommending the closest cuisine matches instead."
                )
        else:
            if top_cat:
                parts.append(
                    f"I couldn't find restaurants clearly labelled as {requested_cuisine} nearby, "
                    f"so I'm recommending the closest matches like {top_cat} that should feel similar."
                )
            else:
                parts.append(
                    f"I couldn't find restaurants clearly labelled as {requested_cuisine} nearby, "
                    "so I'm recommending the closest cuisine matches instead."
                )

    elif dish_text and inferred_cuisine:
        parts.append(
            f"Since {dish_text} is usually a {inferred_cuisine} dish, "
            f"I'm prioritising strong **{inferred_cuisine} restaurants that are likely to serve it."
        )

    if dish_fallback and not (fallback_type == "cuisine_family_fallback" and dish_text and inferred_cuisine):
        if dish_text and inferred_cuisine:
            parts.append(
                f"so I'm showing well-rated {inferred_cuisine} options where you're likely to get it."
            )
        else:
            dish_label = dish_text or raw_query
            parts.append(
                "so these are the best matches based on cuisine, style and reviews."
            )

    if not parts:
        return ""

    return " ".join(parts)

def generate_user_message(query: str, attributes: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
    if not recommendations:
        return (
            f"Sorry, I couldn't find anything matching **\"{query}\"**.\n"
            "Want to try changing cuisine, dish, style (soft / spicy / cheesy), or budget?"
        )

    intro = _select_intro(attributes)
    message = f"🍽️ {intro}\n\n"

    # Add ONLY global explanation
    global_explanation = _build_global_explanation(attributes, recommendations)
    if global_explanation:
        message += global_explanation + "\n\n"

    # ❌ DO NOT add hotel names, distances, ratings, popularity  
    # ❌ DO NOT add per‑hotel reasoning  
    # Message ends here

    return message

def format_recommendation_list(query: str, attributes: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
    return generate_user_message(query, attributes, recommendations)
