"""
AI Travel Service — AWS Bedrock (Amazon Nova Pro) backend.

Replaces the previous Groq/OpenAI-compatible client with native boto3
Bedrock Runtime calls so the service runs entirely within the AWS VPC
with no external API key dependencies.
"""

import asyncio
import json
from decimal import Decimal
from functools import lru_cache
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings


# ---------------------------------------------------------------------------
# Bedrock runtime client — one per Lambda / process (module-level singleton)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name=settings.bedrock_region)


# ---------------------------------------------------------------------------
# Public service class
# ---------------------------------------------------------------------------

class TravelAIService:
    """
    Wraps all AI travel planning operations.

    Each public method first tries to call Amazon Bedrock Nova Pro;
    if Bedrock is unavailable or returns invalid JSON the method falls
    back to curated static responses so the endpoint never returns a 5xx.
    """

    # ------------------------------------------------------------------ #
    # Public methods                                                       #
    # ------------------------------------------------------------------ #

    async def generate_itinerary(self, payload) -> dict[str, Any]:
        fallback = self._fallback_itinerary(payload)
        prompt = (
            "Create a detailed travel itinerary as strict JSON with keys "
            "trip_summary, day_wise_plan, estimated_budget_breakdown, travel_tips. "
            "day_wise_plan must be an array of objects with day, title, morning, afternoon, evening. "
            "IMPORTANT: Always mention specific real place names, landmark names, restaurant names, "
            "and attraction names for the destination — never use generic descriptions. "
            f"Destination: {payload.destination}. Budget: ${payload.budget}. Days: {payload.days}. "
            f"Interests: {', '.join(payload.interests) or 'general sightseeing'}."
        )
        generated = await self._complete_json(prompt, fallback)
        return self._normalize_itinerary(generated, fallback)

    async def chat(self, payload) -> dict[str, Any]:
        fallback = self._fallback_chat(payload.question)
        prompt = (
            "You are a concise AI travel assistant. Return strict JSON with one key: answer. "
            f"Answer this traveler question with actionable advice: {payload.question}"
        )
        return await self._complete_json(prompt, fallback)

    async def optimize_budget(self, payload) -> dict[str, Any]:
        daily = self._money(payload.budget / payload.days)
        fallback = {
            "budget_saving_suggestions": [
                f"Target an average daily spend near {daily} in {payload.destination}.",
                "Book refundable lodging early, then recheck prices two weeks before travel.",
                "Use public transit or day passes for routine transfers.",
                "Choose one paid anchor activity per day and fill the rest with free neighborhoods, markets, and viewpoints.",
                "Track meals separately so dining does not absorb the activity budget.",
            ]
        }
        prompt = (
            "Return strict JSON with key budget_saving_suggestions as an array of strings. "
            f"Optimize a {payload.days}-day trip to {payload.destination} with total budget {payload.budget}."
        )
        generated = await self._complete_json(prompt, fallback)
        suggestions = generated.get("budget_saving_suggestions")
        if isinstance(suggestions, dict):
            suggestions = [f"{key.replace('_', ' ').title()}: {value}" for key, value in suggestions.items()]
        if not isinstance(suggestions, list):
            return fallback
        return {"budget_saving_suggestions": [str(item) for item in suggestions]}

    async def compare_destinations(self, payload) -> dict[str, Any]:
        fallback = {
            "cost_comparison": {
                payload.destination_a: "Often best for travelers who prioritize local dining, transit, and compact daily routes.",
                payload.destination_b: "Often best when flight pricing or hotel availability is stronger for your dates.",
            },
            "weather_comparison": {
                payload.destination_a: "Check month-specific forecasts before booking outdoor-heavy days.",
                payload.destination_b: "Compare seasonal rain, heat, and daylight against your planned activities.",
            },
            "activity_comparison": {
                payload.destination_a: "Strong choice for culture, food, walking routes, and neighborhood exploration.",
                payload.destination_b: "Strong choice for varied attractions, shopping, nightlife, and day trips.",
            },
            "best_choice": (
                f"Choose {payload.destination_a} for a slower culture-focused trip; choose "
                f"{payload.destination_b} if logistics and prices are better for your dates."
            ),
        }
        prompt = (
            "Compare two destinations for a traveler. Return strict JSON with keys cost_comparison, "
            "weather_comparison, activity_comparison, best_choice. Each comparison must be an object. "
            f"Destination A: {payload.destination_a}. Destination B: {payload.destination_b}."
        )
        generated = await self._complete_json(prompt, fallback)
        return self._normalize_comparison(generated, fallback)

    async def packing_list(self, payload) -> dict[str, Any]:
        fallback = {
            "packing_list": [
                {"category": "Documents", "items": ["Passport or government ID", "Travel insurance", "Booking confirmations", "Emergency contacts"]},
                {"category": "Clothing", "items": ["Comfortable walking shoes", "Layered outfits", "Weather-appropriate outerwear", "Sleepwear"]},
                {"category": "Health", "items": ["Prescription medication", "Basic first-aid kit", "Sunscreen", "Reusable water bottle"]},
                {"category": "Electronics", "items": ["Phone charger", "Power bank", "Universal adapter", "Offline maps"]},
                {"category": "Destination Specific", "items": [f"Month-aware outfit plan for {payload.travel_month}", f"Small day bag for {payload.destination}"]},
            ]
        }
        prompt = (
            "Return strict JSON with key packing_list. packing_list must be an array of objects with "
            "category and items array. "
            f"Destination: {payload.destination}. Travel month: {payload.travel_month}."
        )
        generated = await self._complete_json(prompt, fallback)
        return self._normalize_packing_list(generated, fallback)

    # ------------------------------------------------------------------ #
    # Bedrock invocation                                                   #
    # ------------------------------------------------------------------ #

    async def _complete_json(self, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
        """
        Call Bedrock Nova Pro via the Converse API, run in a thread pool
        so we don't block the async event loop.
        """
        try:
            result = await asyncio.to_thread(self._invoke_bedrock, prompt)
            return result
        except Exception:
            return fallback

    def _invoke_bedrock(self, prompt: str) -> dict[str, Any]:
        """
        Synchronous Bedrock Converse call (executed in a thread pool).
        Uses the Converse API which is model-agnostic and handles
        streaming, retries, and request/response marshalling.
        """
        client = _get_bedrock_client()
        system_prompt = (
            "You are a production travel-planning API. "
            "Return valid JSON only, with no markdown, no code fences, no explanation. "
            "Your entire response must be a single JSON object."
        )
        try:
            response = client.converse(
                modelId=settings.bedrock_model_id,
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={
                    "temperature": 0.35,
                    "maxTokens": settings.bedrock_max_tokens,
                },
            )
            text = response["output"]["message"]["content"][0]["text"]
            return self._parse_json(text)
        except (ClientError, BotoCoreError, KeyError, IndexError, TypeError, json.JSONDecodeError):
            raise

    # ------------------------------------------------------------------ #
    # JSON parsing                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start < 0 or end <= start:
                raise
            return json.loads(content[start:end])

    # ------------------------------------------------------------------ #
    # Fallback responses (unchanged from Groq version)                    #
    # ------------------------------------------------------------------ #

    def _fallback_itinerary(self, payload) -> dict[str, Any]:
        dest = payload.destination.strip().lower()
        interests = payload.interests or ["sightseeing", "food", "culture"]
        per_day = payload.budget / payload.days if payload.days else Decimal("0")

        generic_activities = {
            "morning": [
                "Kick off the morning with a guided walking tour of the historic district, discovering hidden alleyways.",
                "Visit the local central market to experience the morning bustle and sample fresh regional pastries.",
                "Take an early morning stroll through the city's largest botanical gardens and scenic park paths.",
                "Head to a prominent museum or cultural center early to beat the crowds and enjoy the exhibitions.",
                "Embark on a scenic hike or viewpoint trail to capture panoramic views of the entire area.",
                "Explore the local architecture, capturing photos of historic monuments and plazas in the soft morning light.",
            ],
            "afternoon": [
                "Grab a casual lunch at a highly-rated local bistro, followed by a leisurely coffee at an artisan café.",
                "Spend the afternoon exploring specialty shops, art galleries, and boutique retail districts.",
                "Participate in a hands-on themed experience or food-tasting tour to experience the local culture.",
                "Relax by a scenic river or lake, optionally taking a boat cruise or renting a bicycle.",
                "Dive into a shopping spree or visit a famous landmark tower for an elevated city view.",
                "Attend a brief cultural performance or visit a secondary museum focusing on local history.",
            ],
            "evening": [
                "Enjoy a fine dining experience featuring traditional cuisine, then take a peaceful twilight walk.",
                "Head to a popular sunset viewpoint, followed by dinner at a lively neighborhood night market.",
                "Experience the local nightlife, checking out a cozy lounge, live music venue, or theater performance.",
                "Unwind with a casual dinner at a street food alley, followed by dessert at a famous sweet shop.",
                "Take a guided evening ghost tour or harbor walk to see the city landmarks lit up at night.",
                "Dine at a rooftop restaurant overlooking the skyline, followed by a relaxing evening walk back to the hotel.",
            ],
        }

        custom_plans: dict[int, dict[str, str]] = {}

        if "kyoto" in dest:
            custom_plans = {
                1: {"title": "Kyoto Day 1: Historic Higashiyama", "morning": "Beat the crowds at Kiyomizu-dera Temple, admiring the wooden stage and panoramic city views.", "afternoon": "Stroll down the historic streets of Sannenzaka and Ninenzaka, stopping for traditional matcha tea.", "evening": "Walk through Gion district, Kyoto's famous geisha quarter, and enjoy a traditional Kaiseki dinner."},
                2: {"title": "Kyoto Day 2: Arashiyama Bamboo Grove", "morning": "Walk through the towering Arashiyama Bamboo Grove early, then visit the peaceful Tenryu-ji Temple.", "afternoon": "Cross the Togetsukyo Bridge and visit the monkey park with views of the river.", "evening": "Dine at a scenic riverside restaurant in Arashiyama, enjoying local specialties."},
                3: {"title": "Kyoto Day 3: Fushimi Inari Shrine", "morning": "Hike through the thousands of vibrant red Torii gates at Fushimi Inari Taisha Shrine.", "afternoon": "Travel south to the Fushimi Sake District, visiting a historic brewery museum.", "evening": "Head to Pontocho Alley for dinner in a narrow, atmospheric street packed with traditional izakayas."},
                4: {"title": "Kyoto Day 4: Golden Pavilion", "morning": "Visit Kinkaku-ji (the Golden Pavilion) to see the stunning gold-leaf temple reflected in the pond.", "afternoon": "Explore the famous rock Zen garden at Ryoan-ji Temple, contemplating its beauty.", "evening": "Enjoy a modern Japanese dinner in the bustling Kawaramachi shopping and dining district."},
                5: {"title": "Kyoto Day 5: Nishiki Market", "morning": "Explore Nijo Castle, famous for its squeaking 'nightingale floors' and beautiful palace gardens.", "afternoon": "Dive into Nishiki Market, a narrow five-block street packed with local delicacies.", "evening": "Wrap up your Kyoto trip with a scenic sunset walk along the Kamogawa River."},
            }
        elif "munnar" in dest:
            custom_plans = {
                1: {"title": "Munnar Day 1: Tea Gardens", "morning": "Visit the sprawling Lockhart Tea Museum and take a guided walk through green tea plantations.", "afternoon": "Explore Mattupetty Dam and take a scenic boat ride surrounded by wild hills.", "evening": "Head to Echo Point to hear your voice echo across the lake, followed by local snacks."},
                2: {"title": "Munnar Day 2: Eravikulam National Park", "morning": "Take an early safari bus to Eravikulam National Park to spot the rare Nilgiri Tahr.", "afternoon": "Visit the gorgeous Lakkam Waterfalls, enjoying a refreshing foot dip in the cool water.", "evening": "Stroll through Munnar Town market, shopping for fresh spices and homemade chocolates."},
                3: {"title": "Munnar Day 3: Prehistoric Dolmens", "morning": "Drive to Marayoor to see natural sandalwood forests and prehistoric stone dolmens.", "afternoon": "Visit Kanthalloor, famous for its organic fruit orchards and cool climate.", "evening": "Enjoy a traditional Kerala dinner served on a banana leaf at a local restaurant."},
                4: {"title": "Munnar Day 4: Sunrise & Lake", "morning": "Wake up early for a drive to Top Station to witness the spectacular sunrise over the clouds.", "afternoon": "Visit Kundala Lake for a unique pedal boat experience among the trees.", "evening": "Relax at a local cafe enjoying hot piping cardamom tea and banana fritters."},
                5: {"title": "Munnar Day 5: Jeep Safari", "morning": "Take an adventurous jeep ride to Kolukkumalai, the highest tea estate in the world.", "afternoon": "Tour the century-old orthodox tea factory and learn about traditional tea processing.", "evening": "Watch the sunset from the hilltop, enjoying the panoramic views of the valleys."},
            }
        elif "varkala" in dest:
            custom_plans = {
                1: {"title": "Varkala Day 1: Papanasam Beach & Cliffs", "morning": "Start at Papanasam Beach — the sacred beach believed to wash away sins — for a morning swim and sunrise views from the iconic Red Cliffs.", "afternoon": "Walk the North Cliff promenade, browse the Tibetan Market stalls, and lunch at Café del Mar or Abba Restaurant with cliff-top sea views.", "evening": "Watch the sunset from the clifftop viewpoint near Helipad Beach, then dine at Darjeeling Café for fresh seafood."},
                2: {"title": "Varkala Day 2: Sivagiri Mutt & Backwaters", "morning": "Visit Sivagiri Mutt, the samadhi and cultural center of saint Sree Narayana Guru, followed by Janardana Swami Temple overlooking the Arabian Sea.", "afternoon": "Take a Kerala backwater canoe tour through the Varkala Canal and Azhimala Lake, spotting kingfishers and coconut palms.", "evening": "Return to the cliff for yoga at one of the beachside studios, then enjoy a thali dinner at Juice Shack or Soul & Surf restaurant."},
                3: {"title": "Varkala Day 3: Anchuthengu Fort & Kappil Beach", "morning": "Drive 12 km to explore the ruins of Anchuthengu Fort, a 17th-century Dutch and British coastal fortification with panoramic sea views.", "afternoon": "Head to Kappil Beach and Kappil Lake, where the backwaters meet the sea — enjoy a boat ride across the serene lagoon.", "evening": "Back on North Cliff, catch the last sunset at Black Beach, then celebrate with fresh grilled tiger prawns at Clafouti Restaurant."},
                4: {"title": "Varkala Day 4: Ayurvedic Wellness", "morning": "Book a traditional Abhyanga (full body oil massage) at one of the authentic Ayurvedic centers on the cliff — Krishnatheeram or Eden Garden Ayurveda.", "afternoon": "Explore the Varkala Market town for local spices, banana chips, and Kerala handicrafts — pick up aromatic coconut oil and coir products.", "evening": "Meditate at Varkala Beach during golden hour, then enjoy a farewell Kerala fish curry dinner at the German Bakery or Abba Restaurant."},
                5: {"title": "Varkala Day 5: Lighthouse & Marine Drive", "morning": "Visit the Varkala Lighthouse for a panoramic 360-degree view of the coast and backwaters from the top.", "afternoon": "Spend the afternoon at Odayam Beach, a quieter stretch south of the cliffs loved by surfers and backpackers.", "evening": "Enjoy a final cliff-top bonfire dinner at one of the beach shacks — the Rock n Roll Café hosts live music on weekends."},
            }
        elif "goa" in dest:
            custom_plans = {
                1: {"title": "Goa Day 1: North Goa Beaches", "morning": "Start at Calangute Beach, Goa's most popular beach, then walk south to Baga Beach to see the famous beach shacks.", "afternoon": "Explore the Fort Aguada ruins overlooking the Arabian Sea, then visit Sinquerim Beach.", "evening": "Head to Tito's Lane in Baga for dinner at Fiesta restaurant, followed by live music at Cavala Bar."},
                2: {"title": "Goa Day 2: Old Goa Heritage", "morning": "Explore the UNESCO World Heritage Site of Old Goa — visit the Basilica of Bom Jesus (St. Francis Xavier's tomb) and Se Cathedral.", "afternoon": "Stroll through Fontainhas, Panjim's Latin Quarter with its Portuguese-era houses and art galleries.", "evening": "Cruise on the Mandovi River at sunset, watching the light show on the banks, then dinner at Viva Panjim."},
                3: {"title": "Goa Day 3: South Goa Serenity", "morning": "Drive to Palolem Beach in South Goa — one of India's most beautiful crescent-shaped beaches, ideal for kayaking.", "afternoon": "Visit Cotigao Wildlife Sanctuary for a jungle walk spotting gaur, spotted deer, and giant Malabar squirrels.", "evening": "Sunset yoga at Butterfly Beach (accessible only by boat), followed by seafood barbecue at The Ourem 88 in Chaudi."},
            }
        elif "jaipur" in dest:
            custom_plans = {
                1: {"title": "Jaipur Day 1: Amber Fort & Nahargarh", "morning": "Take an elephant ride up to the magnificent Amber Fort (Amer Fort), exploring its Sheesh Mahal (Palace of Mirrors) and Ganesh Pol gateway.", "afternoon": "Visit the Jaigarh Fort above Amber to see the world's largest wheeled cannon, Jaivana, with panoramic views.", "evening": "Watch the sunset from Nahargarh Fort, then dinner at Peacock Rooftop Restaurant for traditional Rajasthani thali."},
                2: {"title": "Jaipur Day 2: Pink City Heritage", "morning": "Photograph the iconic Hawa Mahal (Palace of Winds) facade, then explore the City Palace Museum and Chandra Mahal.", "afternoon": "Visit Jantar Mantar, the 18th-century astronomical observatory — a UNESCO World Heritage Site — and Birla Mandir temple.", "evening": "Shop for block-print textiles, blue pottery, and gemstones at Johari Bazaar and Bapu Bazaar, then dinner at Suvarna Mahal."},
                3: {"title": "Jaipur Day 3: Markets & Local Life", "morning": "Explore Sisodia Rani Garden and Galta Ji (Monkey Temple) for a spiritual sunrise experience with mountain views.", "afternoon": "Visit the Albert Hall Museum for Rajasthani art and artifacts, then explore Tripolia Bazaar for lac bangles.", "evening": "Attend the Chokhi Dhani cultural village for folk dance, camel rides, and a traditional Rajasthani dinner on the floor."},
            }

        day_wise_plan = []
        for day in range(1, payload.days + 1):
            if day in custom_plans:
                plan = custom_plans[day]
                day_wise_plan.append({"day": day, "title": plan["title"], "morning": plan["morning"], "afternoon": plan["afternoon"], "evening": plan["evening"]})
            else:
                focus = interests[(day - 1) % len(interests)]
                m_act = generic_activities["morning"][(day - 1) % len(generic_activities["morning"])]
                a_act = generic_activities["afternoon"][(day - 1) % len(generic_activities["afternoon"])]
                e_act = generic_activities["evening"][(day - 1) % len(generic_activities["evening"])]
                day_wise_plan.append({"day": day, "title": f"{payload.destination.title()} Day {day}: {focus.title()}", "morning": m_act, "afternoon": a_act, "evening": e_act})

        return {
            "trip_summary": (
                f"{payload.days} days in {payload.destination} with a total budget of {self._money(payload.budget)}. "
                "The plan balances anchor activities, flexible exploration, and daily recovery time."
            ),
            "day_wise_plan": day_wise_plan,
            "estimated_budget_breakdown": {
                "lodging": self._money(payload.budget * Decimal("0.40")),
                "food": self._money(payload.budget * Decimal("0.25")),
                "activities": self._money(payload.budget * Decimal("0.20")),
                "transport": self._money(payload.budget * Decimal("0.15")),
                "daily_target": self._money(per_day),
            },
            "travel_tips": [
                "Book timed-entry attractions before arrival.",
                "Group nearby activities to reduce transit time.",
                "Keep one flexible block every two days for weather or fatigue.",
                "Download offline maps and save hotel details locally.",
            ],
        }

    def _fallback_chat(self, question: str) -> dict[str, Any]:
        q = question.strip().lower()
        if q in {"hi", "hello", "hey", "hi!", "hello!", "hey!"}:
            ans = "Hello! I am your AI Travel Assistant powered by Amazon Bedrock. How can I help you plan your next trip?"
        elif "munnar" in q:
            ans = "Munnar is a gorgeous hill station in Kerala, India, famous for its lush tea plantations. Highlights include Eravikulam National Park, Mattupetty Dam, Echo Point, and Lakkam Waterfalls."
        elif "kyoto" in q:
            ans = "Kyoto is the cultural heart of Japan. Key highlights include Fushimi Inari Shrine, Kiyomizu-dera Temple, Kinkaku-ji (Golden Pavilion), and the Arashiyama Bamboo Grove."
        elif "budget" in q:
            ans = "To optimize your travel budget: 1) Book lodging early with free cancellation, 2) Use public transit passes, 3) Enjoy local street markets for lunch, 4) Choose one paid anchor activity per day."
        elif "weather" in q:
            ans = "Weather patterns vary by destination! For tropical hill stations like Munnar, October to March is ideal. For Kyoto, spring (April) and autumn (November) are magical."
        elif "pack" in q or "packing" in q:
            ans = "A standard packing checklist: 1) Essential documents, 2) Weather-appropriate clothing, 3) Personal toiletries and medications, 4) Universal power adapter and power bank."
        else:
            ans = (
                f"For your travel question about '{question}': I recommend checking local transport passes, "
                "booking main attractions in advance, and allocating about 40% of your budget for lodging, "
                "25% for dining, and 20% for activities."
            )
        return {"answer": ans}

    # ------------------------------------------------------------------ #
    # Normalizers (unchanged from Groq version)                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _normalize_itinerary(generated: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        summary = generated.get("trip_summary", fallback["trip_summary"])
        if isinstance(summary, dict):
            summary = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in summary.items())
        if not isinstance(summary, str):
            summary = fallback["trip_summary"]

        raw_days = generated.get("day_wise_plan", fallback["day_wise_plan"])
        day_wise_plan = []
        if isinstance(raw_days, dict):
            raw_days = list(raw_days.values())
        if isinstance(raw_days, list):
            for index, item in enumerate(raw_days, start=1):
                if isinstance(item, str):
                    day_wise_plan.append({"day": index, "title": f"Day {index}", "morning": item, "afternoon": "Explore nearby areas.", "evening": "Flexible evening for dinner and rest."})
                    continue
                if not isinstance(item, dict):
                    continue
                day_number = item.get("day", index)
                if isinstance(day_number, str):
                    digits = "".join(c for c in day_number if c.isdigit())
                    day_number = int(digits) if digits else index
                activities = item.get("activities")
                activity_text = "; ".join(str(a) for a in activities) if isinstance(activities, list) else str(activities or "")
                day_wise_plan.append({
                    "day": int(day_number),
                    "title": str(item.get("title") or item.get("theme") or f"Day {index}"),
                    "morning": str(item.get("morning") or item.get("morning_activity") or activity_text or fallback["day_wise_plan"][0]["morning"]),
                    "afternoon": str(item.get("afternoon") or item.get("afternoon_activity") or activity_text or fallback["day_wise_plan"][0]["afternoon"]),
                    "evening": str(item.get("evening") or item.get("evening_activity") or item.get("night") or fallback["day_wise_plan"][0]["evening"]),
                })
        if not day_wise_plan:
            day_wise_plan = fallback["day_wise_plan"]

        raw_budget = generated.get("estimated_budget_breakdown", fallback["estimated_budget_breakdown"])
        budget = {str(k): str(v) for k, v in raw_budget.items()} if isinstance(raw_budget, dict) else fallback["estimated_budget_breakdown"]

        raw_tips = generated.get("travel_tips", fallback["travel_tips"])
        if isinstance(raw_tips, dict):
            tips = [f"{k.replace('_', ' ').title()}: {v}" for k, v in raw_tips.items()]
        elif isinstance(raw_tips, list):
            tips = [str(t) for t in raw_tips]
        elif isinstance(raw_tips, str):
            tips = [raw_tips]
        else:
            tips = fallback["travel_tips"]

        return {"trip_summary": summary, "day_wise_plan": day_wise_plan, "estimated_budget_breakdown": budget, "travel_tips": tips}

    @staticmethod
    def _normalize_comparison(generated: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        def as_string_map(value, fallback_value):
            if isinstance(value, dict):
                return {str(k): str(v) for k, v in value.items()}
            if isinstance(value, str):
                return {"summary": value}
            return fallback_value

        return {
            "cost_comparison": as_string_map(generated.get("cost_comparison"), fallback["cost_comparison"]),
            "weather_comparison": as_string_map(generated.get("weather_comparison"), fallback["weather_comparison"]),
            "activity_comparison": as_string_map(generated.get("activity_comparison"), fallback["activity_comparison"]),
            "best_choice": str(generated.get("best_choice") or fallback["best_choice"]),
        }

    @staticmethod
    def _normalize_packing_list(generated: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        raw_list = generated.get("packing_list", fallback["packing_list"])
        if isinstance(raw_list, dict):
            packing_list = [{"category": str(cat), "items": [str(i) for i in items] if isinstance(items, list) else [str(items)]} for cat, items in raw_list.items()]
        elif isinstance(raw_list, list):
            packing_list = []
            for index, item in enumerate(raw_list, start=1):
                if isinstance(item, dict):
                    items = item.get("items", [])
                    packing_list.append({"category": str(item.get("category") or f"Group {index}"), "items": [str(e) for e in items] if isinstance(items, list) else [str(items)]})
                else:
                    packing_list.append({"category": "General", "items": [str(item)]})
        else:
            packing_list = fallback["packing_list"]
        return {"packing_list": packing_list or fallback["packing_list"]}

    @staticmethod
    def _money(value: Decimal) -> str:
        return f"${value.quantize(Decimal('0.01'))}"
