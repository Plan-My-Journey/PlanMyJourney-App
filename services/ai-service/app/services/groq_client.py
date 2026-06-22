import json
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.ai import (
    BudgetOptimizerRequest,
    ChatRequest,
    DestinationCompareRequest,
    ItineraryRequest,
    PackingListRequest,
)


class TravelAIService:
    async def generate_itinerary(self, payload: ItineraryRequest) -> dict[str, Any]:
        fallback = self._fallback_itinerary(payload)
        prompt = (
            "Create a practical travel itinerary as strict JSON with keys "
            "trip_summary, day_wise_plan, estimated_budget_breakdown, travel_tips. "
            "day_wise_plan must be an array of objects with day, title, morning, afternoon, evening. "
            f"Destination: {payload.destination}. Budget: {payload.budget}. Days: {payload.days}. "
            f"Interests: {', '.join(payload.interests) or 'general sightseeing'}."
        )
        generated = await self._complete_json(prompt, fallback)
        return self._normalize_itinerary(generated, fallback)

    async def chat(self, payload: ChatRequest) -> dict[str, Any]:
        fallback = self._fallback_chat(payload.question)
        prompt = (
            "You are a concise AI travel assistant. Return strict JSON with one key: answer. "
            f"Answer this traveler question with actionable advice: {payload.question}"
        )
        return await self._complete_json(prompt, fallback)

    async def optimize_budget(self, payload: BudgetOptimizerRequest) -> dict[str, Any]:
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

    async def compare_destinations(self, payload: DestinationCompareRequest) -> dict[str, Any]:
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

    async def packing_list(self, payload: PackingListRequest) -> dict[str, Any]:
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

    async def _complete_json(self, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
        if not settings.groq_api_key:
            return fallback

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.groq_model,
            "temperature": 0.35,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "You are a production travel-planning API. Return valid JSON only, with no markdown.",
                },
                {"role": "user", "content": prompt},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=settings.groq_timeout_seconds) as client:
                response = await client.post(settings.groq_base_url, headers=headers, json=body)
                response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._parse_json(content)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError):
            return fallback

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

    def _fallback_itinerary(self, payload: ItineraryRequest) -> dict[str, Any]:
        dest = payload.destination.strip().lower()
        interests = payload.interests or ["sightseeing", "food", "culture"]
        per_day = payload.budget / payload.days if payload.days else Decimal("0")
        
        # Varied generic activities to use if not a specific destination
        generic_activities = {
            "morning": [
                "Kick off the morning with a guided walking tour of the historic district, discovering hidden alleyways.",
                "Visit the local central market to experience the morning bustle and sample fresh regional pastries.",
                "Take an early morning stroll through the city's largest botanical gardens and scenic park paths.",
                "Head to a prominent museum or cultural center early to beat the crowds and enjoy the exhibitions.",
                "Embark on a scenic hike or viewpoint trail to capture panoramic views of the entire area.",
                "Explore the local architecture, capturing photos of historic monuments and plazas in the soft morning light."
            ],
            "afternoon": [
                "Grab a casual lunch at a highly-rated local bistro, followed by a leisurely coffee at an artisan café.",
                "Spend the afternoon exploring specialty shops, art galleries, and boutique retail districts.",
                "Participate in a hands-on themed experience or food-tasting tour to experience the local culture.",
                "Relax by a scenic river or lake, optionally taking a boat cruise or renting a bicycle.",
                "Dive into a shopping spree or visit a famous landmark tower for an elevated city view.",
                "Attend a brief cultural performance or visit a secondary museum focusing on local history."
            ],
            "evening": [
                "Enjoy a fine dining experience featuring traditional cuisine, then take a peaceful twilight walk.",
                "Head to a popular sunset viewpoint, followed by dinner at a lively neighborhood night market.",
                "Experience the local nightlife, checking out a cozy lounge, live music venue, or theater performance.",
                "Unwind with a casual dinner at a street food alley, followed by dessert at a famous sweet shop.",
                "Take a guided evening ghost tour or harbor walk to see the city landmarks lit up at night.",
                "Dine at a rooftop restaurant overlooking the skyline, followed by a relaxing evening walk back to the hotel."
            ]
        }

        # Destination-specific custom day plans
        custom_plans = {}
        
        # KYOTO CUSTOM ITINERARY
        if "kyoto" in dest:
            custom_plans = {
                1: {
                    "title": "Kyoto Day 1: Historic Higashiyama",
                    "morning": "Beat the crowds at Kiyomizu-dera Temple, admiring the wooden stage and panoramic city views.",
                    "afternoon": "Stroll down the historic streets of Sannenzaka and Ninenzaka, stopping for traditional matcha tea.",
                    "evening": "Walk through Gion district, Kyoto's famous geisha quarter, and enjoy a traditional Kaiseki dinner."
                },
                2: {
                    "title": "Kyoto Day 2: Arashiyama Bamboo Grove",
                    "morning": "Walk through the towering Arashiyama Bamboo Grove early, then visit the peaceful Tenryu-ji Temple.",
                    "afternoon": "Cross the Togetsukyo Bridge and visit the monkey park with views of the river.",
                    "evening": "Dine at a scenic riverside restaurant in Arashiyama, enjoying local specialties."
                },
                3: {
                    "title": "Kyoto Day 3: Fushimi Inari Shrine",
                    "morning": "Hike through the thousands of vibrant red Torii gates at Fushimi Inari Taisha Shrine.",
                    "afternoon": "Travel south to the Fushimi Sake District, visiting a historic brewery museum.",
                    "evening": "Head to Pontocho Alley for dinner in a narrow, atmospheric street packed with traditional izakayas."
                },
                4: {
                    "title": "Kyoto Day 4: Golden Pavilion",
                    "morning": "Visit Kinkaku-ji (the Golden Pavilion) to see the stunning gold-leaf temple reflected in the pond.",
                    "afternoon": "Explore the famous rock Zen garden at Ryoan-ji Temple, contemplating its beauty.",
                    "evening": "Enjoy a modern Japanese dinner in the bustling Kawaramachi shopping and dining district."
                },
                5: {
                    "title": "Kyoto Day 5: Nishiki Market",
                    "morning": "Explore Nijo Castle, famous for its squeaking 'nightingale floors' and beautiful palace gardens.",
                    "afternoon": "Dive into Nishiki Market, a narrow five-block street packed with local delicacies.",
                    "evening": "Wrap up your Kyoto trip with a scenic sunset walk along the Kamogawa River."
                }
            }
        
        # MUNNAR CUSTOM ITINERARY
        elif "munnar" in dest:
            custom_plans = {
                1: {
                    "title": "Munnar Day 1: Tea Gardens",
                    "morning": "Visit the sprawling Lockhart Tea Museum and take a guided walk through green tea plantations.",
                    "afternoon": "Explore Mattupetty Dam and take a scenic boat ride surrounded by wild hills.",
                    "evening": "Head to Echo Point to hear your voice echo across the lake, followed by local snacks."
                },
                2: {
                    "title": "Munnar Day 2: Eravikulam National Park",
                    "morning": "Take an early safari bus to Eravikulam National Park to spot the rare Nilgiri Tahr.",
                    "afternoon": "Visit the gorgeous Lakkam Waterfalls, enjoying a refreshing foot dip in the cool water.",
                    "evening": "Stroll through Munnar Town market, shopping for fresh spices and homemade chocolates."
                },
                3: {
                    "title": "Munnar Day 3: pre-historic Dolmens",
                    "morning": "Drive to Marayoor to see natural sandalwood forests and prehistoric stone dolmens.",
                    "afternoon": "Visit Kanthalloor, famous for its organic fruit orchards and cool climate.",
                    "evening": "Enjoy a traditional Kerala dinner served on a banana leaf at a local restaurant."
                },
                4: {
                    "title": "Munnar Day 4: Sunrise & Lake",
                    "morning": "Wake up early for a drive to Top Station to witness the spectacular sunrise over the clouds.",
                    "afternoon": "Visit Kundala Lake for a unique pedal boat experience among the trees.",
                    "evening": "Relax at a local cafe enjoying hot piping cardamom tea and banana fritters."
                },
                5: {
                    "title": "Munnar Day 5: Jeep Safari",
                    "morning": "Take an adventurous bumpy jeep ride to Kolukkumalai, the highest tea estate in the world.",
                    "afternoon": "Tour the century-old orthodox tea factory and learn about traditional tea processing.",
                    "evening": "Watch the sunset from the hilltop, enjoying the panoramic views of the valleys."
                }
            }

        # Generate day-wise plan
        day_wise_plan = []
        for day in range(1, payload.days + 1):
            if day in custom_plans:
                plan = custom_plans[day]
                day_wise_plan.append({
                    "day": day,
                    "title": plan["title"],
                    "morning": plan["morning"],
                    "afternoon": plan["afternoon"],
                    "evening": plan["evening"]
                })
            else:
                focus = interests[(day - 1) % len(interests)]
                m_act = generic_activities["morning"][(day - 1) % len(generic_activities["morning"])].replace("historic district", f"historic {focus} district").replace("exhibitions", f"exhibitions related to {focus}")
                a_act = generic_activities["afternoon"][(day - 1) % len(generic_activities["afternoon"])].replace("specialty shops", f"specialty shops celebrating {focus}").replace("themed experience", f"themed {focus} experience")
                e_act = generic_activities["evening"][(day - 1) % len(generic_activities["evening"])].replace("traditional cuisine", f"delicious meals highlighting local {focus}")
                
                day_wise_plan.append({
                    "day": day,
                    "title": f"{payload.destination.title()} day {day}: {focus.title()}",
                    "morning": m_act,
                    "afternoon": a_act,
                    "evening": e_act
                })

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
        
        if q in ["hi", "hello", "hey", "hi!", "hello!", "hey!"]:
            ans = "Hello! I am your AI Travel Assistant. How can I help you plan your next trip today? Ask me about destinations, budgets, packing lists, or weather!"
        elif "munnar" in q:
            ans = "Munnar is a gorgeous hill station in Kerala, India, famous for its lush tea plantations. Highlights include Eravikulam National Park (home to Nilgiri Tahr), Mattupetty Dam, Echo Point, and Lakkam Waterfalls. A budget of $100 to $150 per day works great for a comfortable trip including a private jeep safari."
        elif "kyoto" in q:
            ans = "Kyoto is the cultural heart of Japan! Key highlights include the stunning Fushimi Inari Shrine (famous for its thousands of red torii gates), Kiyomizu-dera Temple, Kinkaku-ji (Golden Pavilion), and the Arashiyama Bamboo Grove. An average budget of $120–$180 per day covers mid-range hotels, delicious food, and local transit."
        elif "budget" in q:
            ans = "To optimize your travel budget, I suggest: 1) Booking lodging with free cancellation at least a month early, 2) Using public rail or bus passes instead of taxis, 3) Enjoying local street markets for lunch, and 4) Choosing one paid anchor activity per day alongside free sightseeing."
        elif "weather" in q:
            ans = "Weather patterns vary by destination! For tropical hill stations like Munnar, October to March is the best time (dry and cool). For Kyoto, spring (April cherry blossoms) and autumn (November foliage) are absolute magic. Let me know where you're heading for specific advice!"
        elif "pack" in q or "packing" in q:
            ans = "A standard travel packing checklist includes: 1) Essential documents (passport, visas, insurance), 2) Layered, weather-appropriate clothing and comfortable walking shoes, 3) Personal toiletries and prescription meds, and 4) Universal power adapter and a portable power bank."
        else:
            ans = (
                f"That sounds like an exciting travel query! For your question about '{question}', "
                f"I recommend checking local transport passes, booking main attractions in advance, and "
                f"allocating about 40% of your budget for lodging, 25% for dining, and 20% for activities."
            )
            
        return {"answer": ans}

    @staticmethod
    def _normalize_itinerary(generated: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        summary = generated.get("trip_summary", fallback["trip_summary"])
        if isinstance(summary, dict):
            summary = ", ".join(f"{key.replace('_', ' ')}: {value}" for key, value in summary.items())
        if not isinstance(summary, str):
            summary = fallback["trip_summary"]

        raw_days = generated.get("day_wise_plan", fallback["day_wise_plan"])
        day_wise_plan = []
        if isinstance(raw_days, dict):
            raw_days = list(raw_days.values())
        if isinstance(raw_days, list):
            for index, item in enumerate(raw_days, start=1):
                if isinstance(item, str):
                    day_wise_plan.append(
                        {
                            "day": index,
                            "title": f"Day {index}",
                            "morning": item,
                            "afternoon": "Explore nearby areas at a comfortable pace.",
                            "evening": "Keep the evening flexible for dinner and rest.",
                        }
                    )
                    continue
                if not isinstance(item, dict):
                    continue
                day_number = item.get("day", index)
                if isinstance(day_number, str):
                    digits = "".join(character for character in day_number if character.isdigit())
                    day_number = int(digits) if digits else index
                activities = item.get("activities")
                if isinstance(activities, list):
                    activity_text = "; ".join(str(activity) for activity in activities)
                else:
                    activity_text = str(activities or "")
                day_wise_plan.append(
                    {
                        "day": int(day_number),
                        "title": str(item.get("title") or item.get("theme") or f"Day {index}"),
                        "morning": str(item.get("morning") or item.get("morning_activity") or activity_text or fallback["day_wise_plan"][0]["morning"]),
                        "afternoon": str(item.get("afternoon") or item.get("afternoon_activity") or activity_text or fallback["day_wise_plan"][0]["afternoon"]),
                        "evening": str(item.get("evening") or item.get("evening_activity") or item.get("night") or fallback["day_wise_plan"][0]["evening"]),
                    }
                )
        if not day_wise_plan:
            day_wise_plan = fallback["day_wise_plan"]

        raw_budget = generated.get("estimated_budget_breakdown", fallback["estimated_budget_breakdown"])
        if isinstance(raw_budget, dict):
            budget = {str(key): str(value) for key, value in raw_budget.items()}
        else:
            budget = fallback["estimated_budget_breakdown"]

        raw_tips = generated.get("travel_tips", fallback["travel_tips"])
        if isinstance(raw_tips, dict):
            tips = [f"{key.replace('_', ' ').title()}: {value}" for key, value in raw_tips.items()]
        elif isinstance(raw_tips, list):
            tips = [str(tip) for tip in raw_tips]
        elif isinstance(raw_tips, str):
            tips = [raw_tips]
        else:
            tips = fallback["travel_tips"]

        return {
            "trip_summary": summary,
            "day_wise_plan": day_wise_plan,
            "estimated_budget_breakdown": budget,
            "travel_tips": tips,
        }

    @staticmethod
    def _normalize_comparison(generated: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        def as_string_map(value: Any, fallback_value: dict[str, str]) -> dict[str, str]:
            if isinstance(value, dict):
                return {str(key): str(item) for key, item in value.items()}
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
            packing_list = [
                {"category": str(category), "items": [str(item) for item in items] if isinstance(items, list) else [str(items)]}
                for category, items in raw_list.items()
            ]
        elif isinstance(raw_list, list):
            packing_list = []
            for index, item in enumerate(raw_list, start=1):
                if isinstance(item, dict):
                    items = item.get("items", [])
                    packing_list.append(
                        {
                            "category": str(item.get("category") or f"Group {index}"),
                            "items": [str(entry) for entry in items] if isinstance(items, list) else [str(items)],
                        }
                    )
                else:
                    packing_list.append({"category": "General", "items": [str(item)]})
        else:
            packing_list = fallback["packing_list"]

        return {"packing_list": packing_list or fallback["packing_list"]}

    @staticmethod
    def _money(value: Decimal) -> str:
        return f"${value.quantize(Decimal('0.01'))}"
