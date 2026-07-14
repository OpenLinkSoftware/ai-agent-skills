#!/usr/bin/env python3
"""
Generate RDF-Turtle Knowledge Graph for 'The Great Blogging Collapse' study.
Data source: Google Sheets spreadsheet by Daniel Stancil.
Output: $LLM_ROOT/DeepSeek/rdf/great-blogging-collapse-study-deepseek_v4pro-1.ttl
"""

import datetime
from textwrap import dedent

# ── All blog data extracted from the spreadsheet ──────────────────────────────
blogs = [
    {"name": "What Mommy Does", "url": "https://www.whatmommydoes.com", "niche": "Parenting",
     "total_2022": 48200, "total_2026": 42300, "total_delta": -12.2,
     "seo_2022": 20200, "seo_2026": 25900, "seo_delta": 28.2,
     "seo_share_2022": 42, "seo_share_2026": 61,
     "seo_traj": "Growing", "total_traj": "Stable",
     "income": 100000, "income_year": 2016,
     "monetization": ["Sponsored", "Affiliate", "Ads"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "HCU Survived", "verified": "2026-04", "final_url": "https://www.whatmommydoes.com/", "new_brand": ""},
    {"name": "Crochet365Knittoo", "url": "https://www.crochet365knittoo.com", "niche": "DIY & Crafts",
     "total_2022": 342800, "total_2026": 368700, "total_delta": 7.6,
     "seo_2022": 30300, "seo_2026": 128400, "seo_delta": 323.8,
     "seo_share_2022": 9, "seo_share_2026": 35,
     "seo_traj": "Growing", "total_traj": "Stable",
     "income": 150000, "income_year": 2020,
     "monetization": ["Ads", "Products", "Affiliate"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "HCU Survived", "verified": "2026-04", "final_url": "https://www.crochet365knittoo.com/", "new_brand": ""},
    {"name": "Hangry Woman", "url": "https://hangrywoman.com", "niche": "Food & Recipes",
     "total_2022": 13200, "total_2026": 11600, "total_delta": -12.1,
     "seo_2022": 9524, "seo_2026": 4200, "seo_delta": -55.9,
     "seo_share_2022": 72, "seo_share_2026": 36,
     "seo_traj": "Declining", "total_traj": "Stable",
     "income": 103000, "income_year": 2020,
     "monetization": ["Ads", "Affiliate", "Coaching"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "HCU Survived", "verified": "2026-04", "final_url": "https://hangrywoman.com/", "new_brand": "Glucose Guide app"},
    {"name": "Pulling Curls", "url": "https://www.pullingcurls.com", "niche": "Parenting",
     "total_2022": 23600, "total_2026": 48900, "total_delta": 107.2,
     "seo_2022": 9900, "seo_2026": 9400, "seo_delta": -5.1,
     "seo_share_2022": 42, "seo_share_2026": 19,
     "seo_traj": "Stable", "total_traj": "Growing",
     "income": 90000, "income_year": 2017,
     "monetization": ["Products", "Affiliate", "Ads"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.pullingcurls.com/", "new_brand": ""},
    {"name": "Dangerous Business", "url": "https://www.dangerous-business.com", "niche": "Travel",
     "total_2022": 117800, "total_2026": 136000, "total_delta": 15.4,
     "seo_2022": 89900, "seo_2026": 95500, "seo_delta": 6.2,
     "seo_share_2022": 76, "seo_share_2026": 70,
     "seo_traj": "Stable", "total_traj": "Growing",
     "income": 220000, "income_year": 2022,
     "monetization": ["Ads", "Affiliate"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.dangerous-business.com/", "new_brand": ""},
    {"name": "GetOnMyPlate", "url": "https://getonmyplate.com", "niche": "Food & Recipes",
     "total_2022": 159300, "total_2026": 195400, "total_delta": 22.7,
     "seo_2022": 68117, "seo_2026": 61700, "seo_delta": -9.4,
     "seo_share_2022": 43, "seo_share_2026": 32,
     "seo_traj": "Stable", "total_traj": "Growing",
     "income": 75000, "income_year": 2022,
     "monetization": ["Ads", "Products", "Affiliate"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://getonmyplate.com/", "new_brand": ""},
    {"name": "Chelsea Joy Eats", "url": "https://www.chelseajoyeats.com", "niche": "Food & Recipes",
     "total_2022": 4700, "total_2026": 13000, "total_delta": 176.6,
     "seo_2022": 4528, "seo_2026": 6600, "seo_delta": 45.8,
     "seo_share_2022": 96, "seo_share_2026": 51,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 10000, "income_year": 2021,
     "monetization": ["Ads", "Affiliate"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.chelseajoyeats.com/", "new_brand": ""},
    {"name": "The Realistic Mama", "url": "https://www.therealisticmama.com", "niche": "Parenting",
     "total_2022": 7500, "total_2026": 36700, "total_delta": 389.3,
     "seo_2022": 2300, "seo_2026": 21300, "seo_delta": 826.1,
     "seo_share_2022": 31, "seo_share_2026": 58,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 240000, "income_year": 2021,
     "monetization": ["Products", "Affiliate", "Ads"],
     "status": "Unverified", "hcu": "Unaffected", "confidence": "Unknown",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.therealisticmama.com/", "new_brand": ""},
    {"name": "Lifestyle with Leah", "url": "https://www.lifestylewithleah.com", "niche": "Parenting",
     "total_2022": 8000, "total_2026": 10200, "total_delta": 27.5,
     "seo_2022": 302, "seo_2026": 3100, "seo_delta": 926.5,
     "seo_share_2022": 4, "seo_share_2026": 30,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 8000, "income_year": 2020,
     "monetization": ["Ads", "Sponsorships", "Affiliate"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.lifestylewithleah.com/", "new_brand": ""},
    {"name": "Minimize My Mess", "url": "https://minimizemymess.com", "niche": "Lifestyle & Fashion",
     "total_2022": 8200, "total_2026": 149000, "total_delta": 1717.1,
     "seo_2022": 1600, "seo_2026": 40400, "seo_delta": 2425.0,
     "seo_share_2022": 20, "seo_share_2026": 27,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": None, "income_year": None,
     "monetization": ["Ads (Mediavine)", "Digital products"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://minimizemymess.com/", "new_brand": ""},
    {"name": "Mom Beach", "url": "https://www.mombeach.com", "niche": "Parenting",
     "total_2022": 8600, "total_2026": 17000, "total_delta": 97.7,
     "seo_2022": 3300, "seo_2026": 9500, "seo_delta": 187.9,
     "seo_share_2022": 38, "seo_share_2026": 56,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 130000, "income_year": 2020,
     "monetization": ["Products", "Services", "Affiliate"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.mombeach.com/", "new_brand": ""},
    {"name": "Another Mommy Blogger", "url": "https://anothermommyblogger.com", "niche": "Parenting",
     "total_2022": 9900, "total_2026": 35300, "total_delta": 256.6,
     "seo_2022": 82, "seo_2026": 4800, "seo_delta": 5753.7,
     "seo_share_2022": 1, "seo_share_2026": 14,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 40000, "income_year": 2020,
     "monetization": ["Ads", "Affiliate", "Amazon"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://anothermommyblogger.com/", "new_brand": ""},
    {"name": "Cassie Scroggins", "url": "https://www.cassiescroggins.com", "niche": "Parenting",
     "total_2022": 10300, "total_2026": 33400, "total_delta": 224.3,
     "seo_2022": 3600, "seo_2026": 21700, "seo_delta": 502.8,
     "seo_share_2022": 35, "seo_share_2026": 65,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 80000, "income_year": 2020,
     "monetization": ["Ads", "Affiliate", "Amazon"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.cassiescroggins.com/", "new_brand": ""},
    {"name": "Living The Dream", "url": "https://www.livingthedreamrtw.com", "niche": "Travel",
     "total_2022": 14100, "total_2026": 22600, "total_delta": 60.3,
     "seo_2022": 8800, "seo_2026": 10700, "seo_delta": 21.6,
     "seo_share_2022": 62, "seo_share_2026": 47,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 100000, "income_year": 2022,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Verified",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.livingthedreamrtw.com/", "new_brand": ""},
    {"name": "The Fiery Vegetarian", "url": "https://www.thefieryvegetarian.com", "niche": "Food & Recipes",
     "total_2022": 44700, "total_2026": 194400, "total_delta": 334.9,
     "seo_2022": 24805, "seo_2026": 80500, "seo_delta": 224.5,
     "seo_share_2022": 55, "seo_share_2026": 41,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 23750, "income_year": 2021,
     "monetization": ["Ads", "Affiliate"],
     "status": "Unverified", "hcu": "Unaffected", "confidence": "Unknown",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.thefieryvegetarian.com/", "new_brand": ""},
    {"name": "Mommy on Purpose", "url": "https://mommyonpurpose.com", "niche": "Parenting",
     "total_2022": 61300, "total_2026": 72500, "total_delta": 18.3,
     "seo_2022": 23100, "seo_2026": 27100, "seo_delta": 17.3,
     "seo_share_2022": 38, "seo_share_2026": 37,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 60000, "income_year": 2017,
     "monetization": ["Ads", "Affiliate", "Amazon"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://mommyonpurpose.com/", "new_brand": ""},
    {"name": "Stephanies Sweets", "url": "https://stephaniessweets.com", "niche": "Food & Recipes",
     "total_2022": 61500, "total_2026": 110600, "total_delta": 79.8,
     "seo_2022": 19400, "seo_2026": 24300, "seo_delta": 25.3,
     "seo_share_2022": 32, "seo_share_2026": 22,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 100000, "income_year": 2022,
     "monetization": ["Ads", "Coaching", "Affiliate"],
     "status": "Unverified", "hcu": "Unaffected", "confidence": "Unknown",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://stephaniessweets.com/", "new_brand": ""},
    {"name": "Johnny Africa", "url": "https://johnnyafrica.com", "niche": "Travel",
     "total_2022": 73900, "total_2026": 137100, "total_delta": 85.5,
     "seo_2022": 36100, "seo_2026": 73500, "seo_delta": 103.6,
     "seo_share_2022": 49, "seo_share_2026": 54,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": None, "income_year": None,
     "monetization": ["Ads", "Affiliate", "Trip Planning"],
     "status": "Alive", "hcu": "Hit", "confidence": "Verified",
     "story": "HCU Survived", "verified": "2026-04", "final_url": "https://johnnyafrica.com/", "new_brand": ""},
    {"name": "Kitchen Sanctuary", "url": "https://www.kitchensanctuary.com", "niche": "Food & Recipes",
     "total_2022": 1420000, "total_2026": 3200000, "total_delta": 125.4,
     "seo_2022": 950000, "seo_2026": 2400000, "seo_delta": 152.6,
     "seo_share_2022": 67, "seo_share_2026": 75,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 220000, "income_year": 2018,
     "monetization": ["Affiliate", "Ads", "Sponsorships"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.kitchensanctuary.com/", "new_brand": "Nicky's Kitchen Sanctuary"},
    {"name": "PinchOfYum", "url": "https://pinchofyum.com", "niche": "Food & Recipes",
     "total_2022": 2900000, "total_2026": 4000000, "total_delta": 37.9,
     "seo_2022": 1300000, "seo_2026": 2200000, "seo_delta": 69.2,
     "seo_share_2022": 45, "seo_share_2026": 55,
     "seo_traj": "Growing", "total_traj": "Growing",
     "income": 700000, "income_year": 2016,
     "monetization": ["Affiliate", "Sponsorships", "Ads"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://pinchofyum.com/", "new_brand": ""},
    {"name": "iLikeToDabble", "url": "https://iliketodabble.com", "niche": "Finance",
     "total_2022": 15750, "total_2026": 82000, "total_delta": 420.6,
     "seo_2022": 2600, "seo_2026": 1400, "seo_delta": -46.2,
     "seo_share_2022": 17, "seo_share_2026": 2,
     "seo_traj": "Declining", "total_traj": "Growing",
     "income": 30000, "income_year": 2019,
     "monetization": ["Affiliate", "Sponsorships"],
     "status": "Unverified", "hcu": "Unaffected", "confidence": "Unknown",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://iliketodabble.com/", "new_brand": ""},
    {"name": "RyRob", "url": "https://ryrob.com", "niche": "Blogging & Online Business",
     "total_2022": 150000, "total_2026": 175400, "total_delta": 16.9,
     "seo_2022": 130000, "seo_2026": 75000, "seo_delta": -42.3,
     "seo_share_2022": 87, "seo_share_2026": 43,
     "seo_traj": "Declining", "total_traj": "Growing",
     "income": 420000, "income_year": 2021,
     "monetization": ["Affiliate", "Courses"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Estimated",
     "story": "Consistent Grower", "verified": "2026-04", "final_url": "https://www.ryrob.com/", "new_brand": ""},
    {"name": "The Huntswoman", "url": "https://thehuntswoman.com", "niche": "Lifestyle & Fashion",
     "total_2022": 17300, "total_2026": 12800, "total_delta": -26.0,
     "seo_2022": 7100, "seo_2026": 6800, "seo_delta": -4.2,
     "seo_share_2022": 41, "seo_share_2026": 53,
     "seo_traj": "Stable", "total_traj": "Declining",
     "income": 38000, "income_year": 2021,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://thehuntswoman.com/", "new_brand": ""},
    {"name": "Budgets Are Sexy", "url": "https://budgetsaresexy.com", "niche": "Finance",
     "total_2022": 62700, "total_2026": 43600, "total_delta": -30.5,
     "seo_2022": 7800, "seo_2026": 6800, "seo_delta": -12.8,
     "seo_share_2022": 12, "seo_share_2026": 16,
     "seo_traj": "Stable", "total_traj": "Declining",
     "income": None, "income_year": None,
     "monetization": ["Ads", "Affiliate", "Sponsorships"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://budgetsaresexy.com/", "new_brand": ""},
    {"name": "SwoodsonSays", "url": "https://swoodsonsays.com", "niche": "DIY & Crafts",
     "total_2022": 62000, "total_2026": 43500, "total_delta": -29.8,
     "seo_2022": 14700, "seo_2026": 22700, "seo_delta": 54.4,
     "seo_share_2022": 24, "seo_share_2026": 52,
     "seo_traj": "Growing", "total_traj": "Declining",
     "income": 52000, "income_year": 2019,
     "monetization": ["Ads", "Affiliate"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://swoodsonsays.com/", "new_brand": ""},
    {"name": "AnnaInTheHouse", "url": "https://annainthehouse.com", "niche": "Lifestyle & Fashion",
     "total_2022": 73300, "total_2026": 22300, "total_delta": -69.6,
     "seo_2022": 6200, "seo_2026": 18300, "seo_delta": 195.2,
     "seo_share_2022": 8, "seo_share_2026": 82,
     "seo_traj": "Growing", "total_traj": "Declining",
     "income": 120000, "income_year": 2021,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://annainthehouse.com/", "new_brand": ""},
    {"name": "The Professional Hobo", "url": "https://www.theprofessionalhobo.com", "niche": "Travel",
     "total_2022": 28700, "total_2026": 14700, "total_delta": -48.8,
     "seo_2022": 25300, "seo_2026": 10300, "seo_delta": -59.3,
     "seo_share_2022": 88, "seo_share_2026": 70,
     "seo_traj": "Declining", "total_traj": "Declining",
     "income": 50000, "income_year": 2019,
     "monetization": ["Affiliate", "Ads", "Services"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://www.theprofessionalhobo.com/", "new_brand": ""},
    {"name": "Anastasia Blogger", "url": "https://anastasiablogger.com", "niche": "Blogging & Online Business",
     "total_2022": 29000, "total_2026": 17000, "total_delta": -41.4,
     "seo_2022": 3700, "seo_2026": 1500, "seo_delta": -59.5,
     "seo_share_2022": 13, "seo_share_2026": 9,
     "seo_traj": "Declining", "total_traj": "Declining",
     "income": None, "income_year": None,
     "monetization": ["Courses", "Affiliate", "Ads"],
     "status": "Alive", "hcu": "Hit", "confidence": "Verified",
     "story": "Went Off-Blog (Courses)", "verified": "2026-04", "final_url": "https://anastasiablogger.com/", "new_brand": ""},
    {"name": "Income Diary", "url": "https://incomediary.com", "niche": "Blogging & Online Business",
     "total_2022": 74800, "total_2026": 30900, "total_delta": -58.7,
     "seo_2022": 30228, "seo_2026": 25100, "seo_delta": -17.0,
     "seo_share_2022": 40, "seo_share_2026": 81,
     "seo_traj": "Declining", "total_traj": "Declining",
     "income": None, "income_year": None,
     "monetization": ["Affiliate", "Ads", "Sponsored"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://incomediary.com/", "new_brand": ""},
    {"name": "Fork In The Road", "url": "https://www.forkintheroad.co", "niche": "Food & Recipes",
     "total_2022": 94700, "total_2026": 35700, "total_delta": -62.3,
     "seo_2022": 43700, "seo_2026": 17800, "seo_delta": -59.3,
     "seo_share_2022": 46, "seo_share_2026": 50,
     "seo_traj": "Declining", "total_traj": "Declining",
     "income": 37592, "income_year": 2021,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://www.forkintheroad.co/", "new_brand": ""},
    {"name": "Two Wandering Soles", "url": "https://www.twowanderingsoles.com", "niche": "Travel",
     "total_2022": 135300, "total_2026": 85400, "total_delta": -36.9,
     "seo_2022": 100400, "seo_2026": 26700, "seo_delta": -73.4,
     "seo_share_2022": 74, "seo_share_2026": 31,
     "seo_traj": "Declining", "total_traj": "Declining",
     "income": 210000, "income_year": 2019,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://www.twowanderingsoles.com/", "new_brand": ""},
    {"name": "Midwest Foodie Blog", "url": "https://midwestfoodieblog.com", "niche": "Food & Recipes",
     "total_2022": 258000, "total_2026": 134000, "total_delta": -48.1,
     "seo_2022": 201000, "seo_2026": 71000, "seo_delta": -64.7,
     "seo_share_2022": 78, "seo_share_2026": 53,
     "seo_traj": "Declining", "total_traj": "Declining",
     "income": 250000, "income_year": 2022,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Unaffected", "confidence": "Verified",
     "story": "HCU Survived", "verified": "2026-04", "final_url": "https://midwestfoodieblog.com/", "new_brand": ""},
    {"name": "Making Sense of Cents", "url": "https://www.makingsenseofcents.com", "niche": "Finance",
     "total_2022": 350000, "total_2026": 250000, "total_delta": -28.6,
     "seo_2022": 30000, "seo_2026": 24000, "seo_delta": -20.0,
     "seo_share_2022": 9, "seo_share_2026": 10,
     "seo_traj": "Declining", "total_traj": "Declining",
     "income": 1500000, "income_year": 2018,
     "monetization": ["Affiliate", "Courses", "Sponsorships"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "Went Off-Blog (Courses)", "verified": "2026-04", "final_url": "https://www.makingsenseofcents.com/", "new_brand": ""},
    {"name": "Show me the Yummy", "url": "https://showmetheyummy.com", "niche": "Food & Recipes",
     "total_2022": 600000, "total_2026": 371600, "total_delta": -38.1,
     "seo_2022": 249000, "seo_2026": 166600, "seo_delta": -33.1,
     "seo_share_2022": 42, "seo_share_2026": 45,
     "seo_traj": "Declining", "total_traj": "Declining",
     "income": 150000, "income_year": 2016,
     "monetization": ["Affiliate", "Ads"],
     "status": "Unverified", "hcu": "Hit", "confidence": "Unknown",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://showmetheyummy.com/", "new_brand": ""},
    {"name": "JessicaGavin.com", "url": "https://www.jessicagavin.com", "niche": "Food & Recipes",
     "total_2022": 2500000, "total_2026": 809300, "total_delta": -67.6,
     "seo_2022": 1800000, "seo_2026": 540000, "seo_delta": -70.0,
     "seo_share_2022": 72, "seo_share_2026": 67,
     "seo_traj": "Declining", "total_traj": "Declining",
     "income": 50000, "income_year": 2017,
     "monetization": ["Ads", "Affiliate", "Sponsorships"],
     "status": "Unverified", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "", "new_brand": ""},
    {"name": "Blog Ambitious", "url": "https://blogambitious.com", "niche": "Blogging & Online Business",
     "total_2022": 4500, "total_2026": 2200, "total_delta": -51.1,
     "seo_2022": 3400, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 76, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": None, "income_year": None,
     "monetization": ["Ads", "Affiliate (Mediavine, LTK)"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Verified",
     "story": "Went Off-Blog (Video/Podcast)", "verified": "2026-04", "final_url": "https://blogambitious.com/", "new_brand": ""},
    {"name": "About Social Anxiety", "url": "https://www.aboutsocialanxiety.com", "niche": "Health & Wellness",
     "total_2022": 22700, "total_2026": 13100, "total_delta": -42.3,
     "seo_2022": 21100, "seo_2026": 1400, "seo_delta": -93.4,
     "seo_share_2022": 93, "seo_share_2026": 11,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 15000, "income_year": 2021,
     "monetization": ["Ads", "Affiliate"],
     "status": "Unverified", "hcu": "Hit", "confidence": "Unknown",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "", "new_brand": ""},
    {"name": "Project Financially Free", "url": "https://www.projectfinanciallyfree.com", "niche": "Finance",
     "total_2022": 24000, "total_2026": 10200, "total_delta": -57.5,
     "seo_2022": 14520, "seo_2026": 167, "seo_delta": -98.8,
     "seo_share_2022": 61, "seo_share_2026": 2,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 48000, "income_year": 2021,
     "monetization": ["Affiliate", "Display ads", "Sponsorships"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://www.projectfinanciallyfree.com/", "new_brand": ""},
    {"name": "Create And Go", "url": "https://createandgo.com", "niche": "Blogging & Online Business",
     "total_2022": 26000, "total_2026": 8700, "total_delta": -66.5,
     "seo_2022": 8000, "seo_2026": 553, "seo_delta": -93.1,
     "seo_share_2022": 31, "seo_share_2026": 6,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 972000, "income_year": 2021,
     "monetization": ["Courses", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Verified",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://createandgo.com/", "new_brand": ""},
    {"name": "Money from Side Hustle", "url": "https://moneyfromsidehustle.com", "niche": "Finance",
     "total_2022": 26500, "total_2026": 19000, "total_delta": -28.3,
     "seo_2022": 7400, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 28, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 43000, "income_year": 2021,
     "monetization": ["Affiliate"],
     "status": "Alive", "hcu": "Hit", "confidence": "Verified",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://moneyfromsidehustle.com/", "new_brand": ""},
    {"name": "Wealthy Nickel", "url": "https://wealthynickel.com", "niche": "Finance",
     "total_2022": 35000, "total_2026": 20400, "total_delta": -41.7,
     "seo_2022": 35000, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 100, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 36500, "income_year": 2020,
     "monetization": ["Affiliate", "Sponsorships"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://wealthynickel.com/", "new_brand": ""},
    {"name": "Swift Salary", "url": "https://www.swiftsalary.com", "niche": "Finance",
     "total_2022": 80000, "total_2026": 25000, "total_delta": -68.8,
     "seo_2022": 10000, "seo_2026": 83, "seo_delta": -99.2,
     "seo_share_2022": 13, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 60000, "income_year": 2022,
     "monetization": ["Affiliate", "Ads", "Sponsorships"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Claimed",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://www.swiftsalary.com/", "new_brand": ""},
    {"name": "World Travel Family", "url": "https://worldtravelfamily.com", "niche": "Travel",
     "total_2022": 95400, "total_2026": 31400, "total_delta": -67.1,
     "seo_2022": 76600, "seo_2026": 11000, "seo_delta": -85.6,
     "seo_share_2022": 80, "seo_share_2026": 35,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 15000, "income_year": 2021,
     "monetization": ["Ads", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://worldtravelfamily.com/", "new_brand": ""},
    {"name": "The Money Ninja", "url": "https://themoneyninja.com", "niche": "Finance",
     "total_2022": 100000, "total_2026": 26600, "total_delta": -73.4,
     "seo_2022": 25000, "seo_2026": 85, "seo_delta": -99.7,
     "seo_share_2022": 25, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 130000, "income_year": 2020,
     "monetization": ["Affiliate", "Sponsorships"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://themoneyninja.com/", "new_brand": ""},
    {"name": "Travel Mexico Solo", "url": "https://travelmexicosolo.com", "niche": "Travel",
     "total_2022": 115000, "total_2026": 66800, "total_delta": -41.9,
     "seo_2022": 35200, "seo_2026": 3300, "seo_delta": -90.6,
     "seo_share_2022": 31, "seo_share_2026": 5,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 230000, "income_year": 2022,
     "monetization": ["Sponsored", "Ads", "Affiliate"],
     "status": "Alive", "hcu": "Hit", "confidence": "Estimated",
     "story": "Went Off-Blog (Courses)", "verified": "2026-04", "final_url": "https://travelmexicosolo.com/", "new_brand": ""},
    {"name": "Local Adventurer", "url": "https://localadventurer.com", "niche": "Travel",
     "total_2022": 155800, "total_2026": 58000, "total_delta": -62.8,
     "seo_2022": 115900, "seo_2026": 18900, "seo_delta": -83.7,
     "seo_share_2022": 74, "seo_share_2026": 33,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 300000, "income_year": 2019,
     "monetization": ["Sponsored", "Ads", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Decline / Survived", "verified": "2026-04", "final_url": "https://localadventurer.com/", "new_brand": ""},
    {"name": "The Savvy Couple", "url": "https://thesavvycouple.com", "niche": "Finance",
     "total_2022": 200000, "total_2026": 55900, "total_delta": -72.1,
     "seo_2022": 100000, "seo_2026": 255, "seo_delta": -99.7,
     "seo_share_2022": 50, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Declining",
     "income": 170000, "income_year": 2019,
     "monetization": ["Affiliate", "Sponsorships"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://thesavvycouple.com/", "new_brand": ""},
    {"name": "Just a Girl and her Blog", "url": "https://justagirlandherblog.com", "niche": "DIY & Crafts",
     "total_2022": 1000000, "total_2026": 148200, "total_delta": -85.2,
     "seo_2022": 110000, "seo_2026": 113000, "seo_delta": 2.7,
     "seo_share_2022": 11, "seo_share_2026": 76,
     "seo_traj": "Stable", "total_traj": "Collapsed",
     "income": 500000, "income_year": 2016,
     "monetization": ["Products", "Affiliate", "Amazon"],
     "status": "Rebranded", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Full Rebrand", "verified": "2026-04", "final_url": "https://justagirlandherblog.com/", "new_brand": "Abby Organizes"},
    {"name": "Bee Money Savvy", "url": "https://www.beemoneysavvy.com", "niche": "Finance",
     "total_2022": 30000, "total_2026": 6200, "total_delta": -79.3,
     "seo_2022": 1000, "seo_2026": 2800, "seo_delta": 180.0,
     "seo_share_2022": 3, "seo_share_2026": 45,
     "seo_traj": "Growing", "total_traj": "Collapsed",
     "income": 60000, "income_year": 2022,
     "monetization": ["Affiliate", "Sponsored", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://www.beemoneysavvy.com/", "new_brand": ""},
    {"name": "Believe in a Budget", "url": "https://believeinabudget.com", "niche": "Finance",
     "total_2022": 70000, "total_2026": 10400, "total_delta": -85.1,
     "seo_2022": 1500, "seo_2026": 2000, "seo_delta": 33.3,
     "seo_share_2022": 2, "seo_share_2026": 19,
     "seo_traj": "Growing", "total_traj": "Collapsed",
     "income": 840000, "income_year": 2020,
     "monetization": ["Affiliate", "Courses", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://believeinabudget.com/", "new_brand": ""},
    {"name": "It's a Lovely Life", "url": "https://itsalovelylife.com", "niche": "Travel",
     "total_2022": 80000, "total_2026": 13500, "total_delta": -83.1,
     "seo_2022": 1500, "seo_2026": 3200, "seo_delta": 113.3,
     "seo_share_2022": 2, "seo_share_2026": 24,
     "seo_traj": "Growing", "total_traj": "Collapsed",
     "income": 1169000, "income_year": 2019,
     "monetization": ["Courses", "Sponsored", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://itsalovelylife.com/", "new_brand": ""},
    {"name": "Start a mom blog", "url": "https://www.startamomblog.com", "niche": "Blogging & Online Business",
     "total_2022": 130000, "total_2026": 4900, "total_delta": -96.2,
     "seo_2022": 6000, "seo_2026": 1600, "seo_delta": -73.3,
     "seo_share_2022": 5, "seo_share_2026": 33,
     "seo_traj": "Declining", "total_traj": "Collapsed",
     "income": 180000, "income_year": 2017,
     "monetization": ["Affiliate", "Ebooks", "Amazon"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://startamomblog.com/", "new_brand": ""},
    {"name": "Smart Passive Income", "url": "https://www.smartpassiveincome.com", "niche": "Blogging & Online Business",
     "total_2022": 250000, "total_2026": 39000, "total_delta": -84.4,
     "seo_2022": 50000, "seo_2026": 25000, "seo_delta": -50.0,
     "seo_share_2022": 20, "seo_share_2026": 64,
     "seo_traj": "Declining", "total_traj": "Collapsed",
     "income": 1500000, "income_year": 2017,
     "monetization": ["Affiliate", "Books", "Niche sites", "Podcast"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Went Off-Blog (Video/Podcast)", "verified": "2026-04", "final_url": "https://www.smartpassiveincome.com/", "new_brand": ""},
    {"name": "Making a Millennial Millionaire", "url": "https://www.makingamillennialmillionaire.com", "niche": "Finance",
     "total_2022": 3600, "total_2026": 3, "total_delta": -99.9,
     "seo_2022": 1500, "seo_2026": 3, "seo_delta": -99.8,
     "seo_share_2022": 42, "seo_share_2026": 100,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 6000, "income_year": 2022,
     "monetization": ["Affiliate", "Sponsorships"],
     "status": "Unverified", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://www.makingamillennialmillionaire.com/", "new_brand": ""},
    {"name": "Thrifty DIY Diva", "url": "https://thriftydiydiva.com", "niche": "Food & Recipes",
     "total_2022": 3600, "total_2026": 414, "total_delta": -88.5,
     "seo_2022": 2600, "seo_2026": 414, "seo_delta": -84.1,
     "seo_share_2022": 72, "seo_share_2026": 100,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 7000, "income_year": 2022,
     "monetization": ["Ads"],
     "status": "Sold", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Sold at Peak / Exit", "verified": "2026-04", "final_url": "https://thriftydiydiva.com/", "new_brand": ""},
    {"name": "Skipblast", "url": "https://skipblast.com", "niche": "Blogging & Online Business",
     "total_2022": 4700, "total_2026": 543, "total_delta": -88.4,
     "seo_2022": 570, "seo_2026": 469, "seo_delta": -17.7,
     "seo_share_2022": 12, "seo_share_2026": 86,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": None, "income_year": None,
     "monetization": ["Ads (Ezoic)", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Verified",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://skipblast.com/", "new_brand": ""},
    {"name": "SunriseValleyFarmco", "url": "https://www.sunrisevalleyfarmco.com", "niche": "DIY & Crafts",
     "total_2022": 5000, "total_2026": 338, "total_delta": -93.2,
     "seo_2022": 337, "seo_2026": 338, "seo_delta": 0.3,
     "seo_share_2022": 7, "seo_share_2026": 100,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 17000, "income_year": 2021,
     "monetization": ["Affiliate", "Products/Services"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://www.sunrisevalleyfarmco.com/", "new_brand": ""},
    {"name": "Kate Kordsmeier", "url": "https://katekordsmeier.com", "niche": "Lifestyle & Fashion",
     "total_2022": 6300, "total_2026": 678, "total_delta": -89.2,
     "seo_2022": 874, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 14, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 250000, "income_year": 2020,
     "monetization": ["Courses", "Ads", "Affiliate"],
     "status": "Rebranded", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Full Rebrand", "verified": "2026-04", "final_url": "https://successwithsoul.co/", "new_brand": "Success With Soul"},
    {"name": "MirandaNahmias.com", "url": "https://www.mirandanahmias.com", "niche": "Blogging & Online Business",
     "total_2022": 8000, "total_2026": 90, "total_delta": -98.9,
     "seo_2022": 150, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 2, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 160000, "income_year": 2020,
     "monetization": ["Freelancing", "Affiliate", "Coaching"],
     "status": "Dead", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Domain Compromised", "verified": "2026-04", "final_url": "", "new_brand": ""},
    {"name": "Wallet Squirrel", "url": "https://walletsquirrel.com", "niche": "Finance",
     "total_2022": 8000, "total_2026": 247, "total_delta": -96.9,
     "seo_2022": 2000, "seo_2026": 51, "seo_delta": -97.5,
     "seo_share_2022": 25, "seo_share_2026": 21,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 50000, "income_year": 2021,
     "monetization": ["Dividends", "Sponsored", "Affiliate"],
     "status": "Dead", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Traffic Collapse / Dead", "verified": "2026-04", "final_url": "https://walletsquirrel.com/", "new_brand": ""},
    {"name": "Whitehat Blogging", "url": "https://whitehatblogging.com", "niche": "Blogging & Online Business",
     "total_2022": 10000, "total_2026": 0, "total_delta": -100.0,
     "seo_2022": 300, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 3, "seo_share_2026": None,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 25000, "income_year": 2022,
     "monetization": ["Affiliate", "Ads", "Sponsorships"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://whitehatblogging.com/", "new_brand": ""},
    {"name": "CatKingpin", "url": "https://catkingpin.com", "niche": "Other",
     "total_2022": 14400, "total_2026": 2800, "total_delta": -80.6,
     "seo_2022": 6000, "seo_2026": 926, "seo_delta": -84.6,
     "seo_share_2022": 42, "seo_share_2026": 33,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": None, "income_year": None,
     "monetization": ["Sponsored", "Ads", "Affiliate"],
     "status": "Sold", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Sold at Peak / Exit", "verified": "2026-04", "final_url": "https://catkingpin.com/", "new_brand": ""},
    {"name": "Fishing Munk", "url": "https://fishingmunk.com", "niche": "Other",
     "total_2022": 15000, "total_2026": 0, "total_delta": -100.0,
     "seo_2022": 8200, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 55, "seo_share_2026": None,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": None, "income_year": None,
     "monetization": ["Ads", "Affiliate"],
     "status": "Sold", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Sold at Peak / Exit", "verified": "2026-04", "final_url": "https://fishingmunk.com/", "new_brand": ""},
    {"name": "High Five Dad", "url": "https://www.highfivedad.com", "niche": "Parenting",
     "total_2022": 15000, "total_2026": 18, "total_delta": -99.9,
     "seo_2022": 941, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 6, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 45000, "income_year": 2019,
     "monetization": ["Ads", "Affiliate", "Amazon"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://www.highfivedad.com/", "new_brand": ""},
    {"name": "Unconventional Prosperity", "url": "https://www.unconventionalprosperity.com", "niche": "Finance",
     "total_2022": 15500, "total_2026": 382, "total_delta": -97.5,
     "seo_2022": 500, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 3, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 210000, "income_year": 2019,
     "monetization": ["Affiliate", "Sponsorships"],
     "status": "Dead", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Domain Compromised", "verified": "2026-04", "final_url": "https://www.unconventionalprosperity.com/", "new_brand": "MABOSBET (slot site)"},
    {"name": "Boss Girl Bloggers", "url": "https://bossgirlbloggers.com", "niche": "Blogging & Online Business",
     "total_2022": 20000, "total_2026": 82, "total_delta": -99.6,
     "seo_2022": 100, "seo_2026": 3, "seo_delta": -97.0,
     "seo_share_2022": 1, "seo_share_2026": 4,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 103000, "income_year": 2020,
     "monetization": ["Affiliate", "Sponsorships", "Ads"],
     "status": "Dead", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Domain Compromised", "verified": "2026-04", "final_url": "https://bossgirlbloggers.com/", "new_brand": ""},
    {"name": "CutNMakeCrafts", "url": "https://cutnmakecrafts.com", "niche": "DIY & Crafts",
     "total_2022": 22900, "total_2026": 670, "total_delta": -97.1,
     "seo_2022": 8500, "seo_2026": 530, "seo_delta": -93.8,
     "seo_share_2022": 37, "seo_share_2026": 79,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 82000, "income_year": 2020,
     "monetization": ["Products", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://cutnmakecrafts.com/", "new_brand": ""},
    {"name": "Love Life Be Fit", "url": "https://lovelifebefit.com", "niche": "Lifestyle & Fashion",
     "total_2022": 33500, "total_2026": 5000, "total_delta": -85.1,
     "seo_2022": 22300, "seo_2026": 334, "seo_delta": -98.5,
     "seo_share_2022": 67, "seo_share_2026": 7,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": None, "income_year": None,
     "monetization": ["Ads", "Affiliate"],
     "status": "Unverified", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://lovelifebefit.com/", "new_brand": ""},
    {"name": "Juicing for Health", "url": "https://juicing-for-health.com", "niche": "Food & Recipes",
     "total_2022": 34300, "total_2026": 5900, "total_delta": -82.8,
     "seo_2022": 29300, "seo_2026": 76, "seo_delta": -99.7,
     "seo_share_2022": 85, "seo_share_2026": 1,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 15000, "income_year": 2021,
     "monetization": ["Ads", "Affiliate"],
     "status": "Sold", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Sold at Peak / Exit", "verified": "2026-04", "final_url": "https://juicing-for-health.com/", "new_brand": ""},
    {"name": "AmyFillinger", "url": "https://www.amyfillinger.com", "niche": "Travel",
     "total_2022": 39600, "total_2026": 3700, "total_delta": -90.7,
     "seo_2022": 14600, "seo_2026": 3600, "seo_delta": -75.3,
     "seo_share_2022": 37, "seo_share_2026": 97,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 50000, "income_year": 2022,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://amyfillinger.com/", "new_brand": ""},
    {"name": "Mommy Over Work", "url": "https://mommyoverwork.com", "niche": "Lifestyle & Fashion",
     "total_2022": 39700, "total_2026": 4200, "total_delta": -89.4,
     "seo_2022": 18700, "seo_2026": 2000, "seo_delta": -89.3,
     "seo_share_2022": 47, "seo_share_2026": 48,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 55000, "income_year": 2020,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://mommyoverwork.com/", "new_brand": ""},
    {"name": "The Flooring Girl", "url": "https://theflooringgirl.com", "niche": "DIY & Crafts",
     "total_2022": 52500, "total_2026": 2400, "total_delta": -95.4,
     "seo_2022": 29600, "seo_2026": 1200, "seo_delta": -95.9,
     "seo_share_2022": 56, "seo_share_2026": 50,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 200000, "income_year": 2020,
     "monetization": ["Products", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://theflooringgirl.com/", "new_brand": ""},
    {"name": "Sadie Smiley", "url": "https://sadiesmiley.com", "niche": "Finance",
     "total_2022": 60000, "total_2026": 415, "total_delta": -99.3,
     "seo_2022": 3500, "seo_2026": 36, "seo_delta": -99.0,
     "seo_share_2022": 6, "seo_share_2026": 9,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 220000, "income_year": 2022,
     "monetization": ["Products", "Affiliate", "Sponsorships"],
     "status": "Rebranded", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Full Rebrand", "verified": "2026-04", "final_url": "https://passiveincomepathways.com/", "new_brand": "Passive Income Pathways"},
    {"name": "Own The Yard", "url": "https://www.owntheyard.com", "niche": "Other",
     "total_2022": 62500, "total_2026": 3500, "total_delta": -94.4,
     "seo_2022": 39800, "seo_2026": 1600, "seo_delta": -96.0,
     "seo_share_2022": 64, "seo_share_2026": 46,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": None, "income_year": None,
     "monetization": ["Ads", "Affiliate"],
     "status": "Unverified", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://www.owntheyard.com/", "new_brand": ""},
    {"name": "Fit Mommy in Heels", "url": "https://fitmommyinheels.com", "niche": "Lifestyle & Fashion",
     "total_2022": 65100, "total_2026": 36, "total_delta": -99.9,
     "seo_2022": 61300, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 94, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 60000, "income_year": 2018,
     "monetization": ["Sponsored", "Affiliate", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://fitmommyinheels.com/", "new_brand": ""},
    {"name": "New Middle Class Dad", "url": "https://newmiddleclassdad.com", "niche": "Finance",
     "total_2022": 74500, "total_2026": 7500, "total_delta": -89.9,
     "seo_2022": 35700, "seo_2026": 392, "seo_delta": -98.9,
     "seo_share_2022": 48, "seo_share_2026": 5,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": None, "income_year": None,
     "monetization": ["Affiliate", "Ads", "Courses"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://newmiddleclassdad.com/", "new_brand": ""},
    {"name": "KaylaSloan.com", "url": "https://kaylasloan.com", "niche": "Finance",
     "total_2022": 75000, "total_2026": 0, "total_delta": -100.0,
     "seo_2022": 9000, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 12, "seo_share_2026": None,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 130000, "income_year": 2019,
     "monetization": ["VA freelancing", "Coaching", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Went Off-Blog (Courses)", "verified": "2026-04", "final_url": "https://kaylasloan.com/", "new_brand": ""},
    {"name": "99Signals.com", "url": "https://www.99signals.com", "niche": "Blogging & Online Business",
     "total_2022": 80000, "total_2026": 5900, "total_delta": -92.6,
     "seo_2022": 20000, "seo_2026": 2800, "seo_delta": -86.0,
     "seo_share_2022": 25, "seo_share_2026": 47,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 60000, "income_year": 2019,
     "monetization": ["Affiliate", "Sponsored"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Went Off-Blog (Video/Podcast)", "verified": "2026-04", "final_url": "https://www.99signals.com/", "new_brand": ""},
    {"name": "Easy Baby Life", "url": "https://www.easybabylife.com", "niche": "Parenting",
     "total_2022": 82000, "total_2026": 8500, "total_delta": -89.6,
     "seo_2022": 54400, "seo_2026": 1100, "seo_delta": -98.0,
     "seo_share_2022": 66, "seo_share_2026": 13,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 60000, "income_year": 2017,
     "monetization": ["Ads", "Affiliate", "Amazon"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://www.easybabylife.com/", "new_brand": ""},
    {"name": "Entrepreneurs On Fire", "url": "https://www.eofire.com", "niche": "Blogging & Online Business",
     "total_2022": 85000, "total_2026": 17700, "total_delta": -79.2,
     "seo_2022": 11000, "seo_2026": 2000, "seo_delta": -81.8,
     "seo_share_2022": 13, "seo_share_2026": 11,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 1692264, "income_year": 2024,
     "monetization": ["Products", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://www.eofire.com/", "new_brand": ""},
    {"name": "Imperfect Idealist", "url": "https://imperfectidealist.com", "niche": "Health & Wellness",
     "total_2022": 96000, "total_2026": 17500, "total_delta": -81.8,
     "seo_2022": 34000, "seo_2026": 2000, "seo_delta": -94.1,
     "seo_share_2022": 35, "seo_share_2026": 11,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 16500, "income_year": 2021,
     "monetization": ["Ads", "Affiliate", "Consulting"],
     "status": "Unverified", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://imperfectidealist.com/", "new_brand": ""},
    {"name": "Matthew Woodward", "url": "https://www.matthewwoodward.co.uk", "niche": "Blogging & Online Business",
     "total_2022": 100000, "total_2026": 0, "total_delta": -100.0,
     "seo_2022": 35000, "seo_2026": 0, "seo_delta": -100.0,
     "seo_share_2022": 35, "seo_share_2026": None,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 336000, "income_year": 2017,
     "monetization": ["Internet marketing", "SEO services", "Affiliate"],
     "status": "Sold", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Sold at Peak / Exit", "verified": "2026-04", "final_url": "https://www.searchlogistics.com/", "new_brand": "Search Logistics"},
    {"name": "WPLift", "url": "https://wplift.com", "niche": "Digital & Tech",
     "total_2022": 100000, "total_2026": 23900, "total_delta": -76.1,
     "seo_2022": 58500, "seo_2026": 917, "seo_delta": -98.4,
     "seo_share_2022": 59, "seo_share_2026": 4,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 50000, "income_year": 2022,
     "monetization": ["Affiliate", "Sponsorships", "Memberships"],
     "status": "Sold", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Sold at Peak / Exit", "verified": "2026-04", "final_url": "https://wplift.com/", "new_brand": ""},
    {"name": "Fun Life Crisis", "url": "https://funlifecrisis.com", "niche": "Travel",
     "total_2022": 113300, "total_2026": 8000, "total_delta": -92.9,
     "seo_2022": 33400, "seo_2026": 3000, "seo_delta": -91.0,
     "seo_share_2022": 29, "seo_share_2026": 38,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 100000, "income_year": 2022,
     "monetization": ["Ads", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://funlifecrisis.com/", "new_brand": ""},
    {"name": "The Baller On a Budget", "url": "https://www.theballeronabudget.com", "niche": "Lifestyle & Fashion",
     "total_2022": 123300, "total_2026": 12800, "total_delta": -89.6,
     "seo_2022": 120500, "seo_2026": 12100, "seo_delta": -90.0,
     "seo_share_2022": 98, "seo_share_2026": 95,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 45620, "income_year": 2019,
     "monetization": ["Sponsored", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://www.theballeronabudget.com/", "new_brand": ""},
    {"name": "The Atlas Heart", "url": "https://theatlasheart.com", "niche": "Travel",
     "total_2022": 129200, "total_2026": 7700, "total_delta": -94.0,
     "seo_2022": 110700, "seo_2026": 5400, "seo_delta": -95.1,
     "seo_share_2022": 86, "seo_share_2026": 70,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 50000, "income_year": 2021,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://theatlasheart.com/", "new_brand": ""},
    {"name": "The Lost Gamer", "url": "https://thelostgamer.com", "niche": "Other",
     "total_2022": 134000, "total_2026": 8300, "total_delta": -93.8,
     "seo_2022": 87700, "seo_2026": 5900, "seo_delta": -93.3,
     "seo_share_2022": 65, "seo_share_2026": 71,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": None, "income_year": None,
     "monetization": ["Ads", "Affiliate"],
     "status": "Sold", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Sold at Peak / Exit", "verified": "2026-04", "final_url": "https://thelostgamer.com/", "new_brand": ""},
    {"name": "Chic Pursuit", "url": "https://chicpursuit.com", "niche": "Lifestyle & Fashion",
     "total_2022": 144600, "total_2026": 10500, "total_delta": -92.7,
     "seo_2022": 88500, "seo_2026": 4000, "seo_delta": -95.5,
     "seo_share_2022": 61, "seo_share_2026": 38,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 150000, "income_year": 2020,
     "monetization": ["Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://chicpursuit.com/", "new_brand": ""},
    {"name": "This Online World", "url": "https://thisonlineworld.com", "niche": "Finance",
     "total_2022": 150000, "total_2026": 12600, "total_delta": -91.6,
     "seo_2022": 120000, "seo_2026": 15, "seo_delta": -100.0,
     "seo_share_2022": 80, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 92000, "income_year": 2021,
     "monetization": ["Affiliate", "Courses", "Sponsorships"],
     "status": "Sold", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Sold at Peak / Exit", "verified": "2026-04", "final_url": "https://www.webmonkey.com/", "new_brand": "WebMonkey"},
    {"name": "A2ZHealthy", "url": "https://a2zhealthy.com", "niche": "Health & Wellness",
     "total_2022": 154600, "total_2026": 718, "total_delta": -99.5,
     "seo_2022": 2000, "seo_2026": 718, "seo_delta": -64.1,
     "seo_share_2022": 1, "seo_share_2026": 100,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 96000, "income_year": 2022,
     "monetization": ["Ads"],
     "status": "Sold", "hcu": "Severely Hit", "confidence": "Unknown",
     "story": "Sold at Peak / Exit", "verified": "2026-04", "final_url": "https://a2zhealthy.com/", "new_brand": ""},
    {"name": "Thyme and Joy", "url": "https://thymeandjoy.com", "niche": "Food & Recipes",
     "total_2022": 168500, "total_2026": 39700, "total_delta": -76.4,
     "seo_2022": 43925, "seo_2026": 5400, "seo_delta": -87.7,
     "seo_share_2022": 26, "seo_share_2026": 14,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 110000, "income_year": 2022,
     "monetization": ["Affiliate", "Ads"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Went Off-Blog (Video/Podcast)", "verified": "2026-04", "final_url": "https://thymeandjoy.com/", "new_brand": ""},
    {"name": "BloggersPassion", "url": "https://bloggerspassion.com", "niche": "Blogging & Online Business",
     "total_2022": 180000, "total_2026": 37400, "total_delta": -79.2,
     "seo_2022": 120000, "seo_2026": 2800, "seo_delta": -97.7,
     "seo_share_2022": 67, "seo_share_2026": 7,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 160000, "income_year": 2021,
     "monetization": ["Affiliate", "Courses", "Sponsorships"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://bloggerspassion.com/", "new_brand": ""},
    {"name": "FinMasters", "url": "https://finmasters.com", "niche": "Finance",
     "total_2022": 180000, "total_2026": 38500, "total_delta": -78.6,
     "seo_2022": 102900, "seo_2026": 17500, "seo_delta": -83.0,
     "seo_share_2022": 57, "seo_share_2026": 45,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 72000, "income_year": 2021,
     "monetization": ["Affiliate", "Digital products"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Went Off-Blog (Video/Podcast)", "verified": "2026-04", "final_url": "https://finmasters.com/", "new_brand": ""},
    {"name": "MelyssaGriffin.com", "url": "https://www.melyssagriffin.com", "niche": "Blogging & Online Business",
     "total_2022": 200000, "total_2026": 12400, "total_delta": -93.8,
     "seo_2022": 15000, "seo_2026": 929, "seo_delta": -93.8,
     "seo_share_2022": 8, "seo_share_2026": 7,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 2000000, "income_year": 2016,
     "monetization": ["Courses", "Affiliate"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Went Off-Blog (Courses)", "verified": "2026-04", "final_url": "https://melyssagriffin.com/", "new_brand": ""},
    {"name": "One Hour Professor", "url": "https://onehourprofessor.com", "niche": "Blogging & Online Business",
     "total_2022": 250000, "total_2026": 56300, "total_delta": -77.5,
     "seo_2022": 70000, "seo_2026": 191, "seo_delta": -99.7,
     "seo_share_2022": 28, "seo_share_2026": 0,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 175000, "income_year": 2021,
     "monetization": ["Affiliate", "Courses"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://onehourprofessor.com/", "new_brand": ""},
    {"name": "Club Thrifty", "url": "https://clubthrifty.com", "niche": "Finance",
     "total_2022": 350000, "total_2026": 3800, "total_delta": -98.9,
     "seo_2022": 32000, "seo_2026": 868, "seo_delta": -97.3,
     "seo_share_2022": 9, "seo_share_2026": 23,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 1000000, "income_year": 2019,
     "monetization": ["Affiliate", "Sponsorships"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://clubthrifty.com/", "new_brand": ""},
    {"name": "Well Kept Wallet", "url": "https://wellkeptwallet.com", "niche": "Finance",
     "total_2022": 380000, "total_2026": 90000, "total_delta": -76.3,
     "seo_2022": 300000, "seo_2026": 619, "seo_delta": -99.8,
     "seo_share_2022": 79, "seo_share_2026": 1,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": 120000, "income_year": 2017,
     "monetization": ["Affiliate", "Services", "Sponsorships"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "HCU Collapse", "verified": "2026-04", "final_url": "https://wellkeptwallet.com/", "new_brand": ""},
    {"name": "Authority Hacker", "url": "https://authorityhacker.com", "niche": "Blogging & Online Business",
     "total_2022": 503400, "total_2026": 44000, "total_delta": -91.3,
     "seo_2022": 282600, "seo_2026": 3400, "seo_delta": -98.8,
     "seo_share_2022": 56, "seo_share_2026": 8,
     "seo_traj": "Collapsed", "total_traj": "Collapsed",
     "income": None, "income_year": None,
     "monetization": ["Courses", "Affiliate", "Podcast"],
     "status": "Alive", "hcu": "Severely Hit", "confidence": "Estimated",
     "story": "Went Off-Blog (Courses)", "verified": "2026-04", "final_url": "https://authorityhacker.com/", "new_brand": ""},
]

# ── Canonical vocabulary ─────────────────────────────────────────────────────

NICHE_MAP = {
    "Parenting": "parenting",
    "DIY & Crafts": "diy-crafts",
    "Food & Recipes": "food-recipes",
    "Travel": "travel",
    "Lifestyle & Fashion": "lifestyle-fashion",
    "Finance": "finance",
    "Blogging & Online Business": "blogging-online-business",
    "Health & Wellness": "health-wellness",
    "Digital & Tech": "digital-tech",
    "Other": "other",
}

STATUS_TYPES = ["Alive", "Unverified", "Rebranded", "Sold", "Dead"]
HCU_IMPACTS = ["Unaffected", "Hit", "Severely Hit"]
CONFIDENCE_LEVELS = ["Estimated", "Verified", "Unknown", "Claimed"]
STORY_TYPES = [
    "HCU Survived", "Consistent Grower", "HCU Decline / Survived",
    "HCU Collapse", "Went Off-Blog (Courses)", "Went Off-Blog (Video/Podcast)",
    "Full Rebrand", "Sold at Peak / Exit", "Traffic Collapse / Dead",
    "Domain Compromised",
]
TRAJECTORIES = ["Growing", "Stable", "Declining", "Collapsed"]

def esc(s):
    """Escape a string for Turtle."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

def safe_url(url):
    """Return a valid xsd:anyURI or empty."""
    if url and url.strip():
        return f'<{url.strip()}>'
    return None

def fmt_int(v):
    """Format integer for Turtle."""
    if v is None:
        return None
    return str(int(v))

def fmt_float(v):
    """Format float, handling None."""
    if v is None:
        return None
    return str(v)

# ── Generate Turtle ──────────────────────────────────────────────────────────

def generate_ttl():
    lines = []
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Prefixes
    lines.append("@prefix : <#> .")
    lines.append("@prefix schema: <http://schema.org/> .")
    lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    lines.append("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    lines.append("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
    lines.append("@prefix dcterms: <http://purl.org/dc/terms/> .")
    lines.append("@prefix prov: <http://www.w3.org/ns/prov#> .")
    lines.append("@prefix foaf: <http://xmlns.com/foaf/0.1/> .")
    lines.append("")

    # ── Document entity ─────────────────────────────────────────────────
    lines.append("<> a schema:CreativeWork ;")
    lines.append('    schema:name "The Great Blogging Collapse — Knowledge Graph"@en ;')
    lines.append('    schema:description "RDF Knowledge Graph representing the study of 100 blogs\' traffic, SEO, and monetization changes between April 2022 and April 2026, examining the impact of Google\'s Helpful Content Update (HCU). Generated from structured spreadsheet data by Daniel Stancil."@en ;')
    lines.append(f'    schema:dateCreated "{now}"^^xsd:dateTime ;')
    lines.append(f'    schema:dateModified "{now}"^^xsd:dateTime ;')
    lines.append('    schema:author <https://linkedin.com/in/kidehen#this> ;')
    lines.append('    schema:about :study ;')
    lines.append('    prov:wasGeneratedBy :kgGenerationActivity .')
    lines.append("")

    # ── Generation Activity ─────────────────────────────────────────────
    lines.append(":kgGenerationActivity a prov:Activity ;")
    lines.append('    prov:startedAtTime "2026-06-30T00:00:00Z"^^xsd:dateTime ;')
    lines.append(f'    prov:endedAtTime "{now}"^^xsd:dateTime ;')
    lines.append('    prov:wasAssociatedWith :generatorAgent ;')
    lines.append('    prov:used <https://docs.google.com/spreadsheets/d/1q7KcGcFnfvwoBRZW2ir2-hfOh-zVmLIOS_P6PJdzAbc> ;')
    lines.append('    prov:generated <great-blogging-collapse-study-deepseek_v4pro-1.ttl> .')
    lines.append("")

    lines.append(":generatorAgent a schema:SoftwareApplication, prov:Agent ;")
    lines.append('    schema:name "DeepSeek V4 Pro via Claude Code"@en ;')
    lines.append('    schema:version "deepseek-v4-pro" ;')
    lines.append("""    schema:description "AI agent that generated this Knowledge Graph from the Great Blogging Collapse spreadsheet data."@en ;""")
    lines.append('    schema:operatingSystem "macOS" .')
    lines.append("")

    # ── The Study ──────────────────────────────────────────────────────
    lines.append(":study a schema:Dataset, schema:ScholarlyArticle ;")
    lines.append('    schema:name "The Great Blogging Collapse: What Happened to 100 Successful Blogs? [Study]"@en ;')
    lines.append('    schema:headline "The Great Blogging Collapse"@en ;')
    lines.append('    schema:author :danielStancil ;')
    lines.append('    schema:url <https://danielstanica.com/posts/Great-Blogging-Collapse> ;')
    lines.append('    schema:dateCreated "2026-04"^^xsd:gYearMonth ;')
    lines.append('    schema:description "A data-driven study analyzing traffic and SEO changes across 98 successful blogs between April 2022 and April 2026, examining the devastating impact of Google\'s Helpful Content Update (HCU) on independent content creators. The study categorizes blogs by niche, survival status, and monetization strategy."@en ;')
    lines.append('    schema:about :hcUpdate, :blogMonetization, :seoTraffic, :bloggingIndustry ;')
    lines.append('    schema:citation <https://docs.google.com/spreadsheets/d/1q7KcGcFnfvwoBRZW2ir2-hfOh-zVmLIOS_P6PJdzAbc> ;')
    lines.append(f'    schema:dateModified "{now}"^^xsd:dateTime ;')

    # Link all blog entities
    blog_refs = []
    for i, b in enumerate(blogs):
        slug = b["name"].lower().replace(" ", "-").replace("'", "").replace(".", "")
        blog_refs.append(f":blog-{slug}")
    for ref in blog_refs:
        lines.append(f'    schema:hasPart {ref} ;')
    lines[-1] = lines[-1].rstrip(" ;") + " ."
    lines.append("")

    # ── Study Author ───────────────────────────────────────────────────
    lines.append(":danielStancil a schema:Person ;")
    lines.append('    schema:name "Daniel Stancil"@en ;')
    lines.append('    schema:url <https://danielstanica.com> ;')
    lines.append('    schema:description "Independent researcher and blogger who conducted the Great Blogging Collapse study, analyzing 98 blogs to understand the impact of Google\'s Helpful Content Update."@en .')
    lines.append("")

    # ── Concept Entities ───────────────────────────────────────────────
    lines.append("# ── Core Concepts ─────────────────────────────────────────────")
    lines.append("")
    lines.append(":hcUpdate a schema:Event ;")
    lines.append('    schema:name "Google Helpful Content Update (HCU)"@en ;')
    lines.append('    schema:description "A series of Google search algorithm updates starting in 2022 aimed at rewarding people-first content and devaluing content created primarily for search engines. The study examines the cumulative impact of these updates on independent blogs."@en ;')
    lines.append('    schema:startDate "2022-08"^^xsd:gYearMonth ;')
    lines.append('    schema:organizer :googleEntity .')
    lines.append("")

    lines.append(":googleEntity a schema:Organization ;")
    lines.append('    schema:name "Google"@en ;')
    lines.append('    schema:url <https://www.google.com/> .')
    lines.append("")

    lines.append(":blogMonetization a schema:DefinedTerm ;")
    lines.append('    schema:name "Blog Monetization"@en ;')
    lines.append('    schema:description "Methods by which independent bloggers generate revenue from their content, including display advertising, affiliate marketing, sponsored content, digital products, courses, coaching, and services."@en .')
    lines.append("")

    lines.append(":seoTraffic a schema:DefinedTerm ;")
    lines.append('    schema:name "SEO Traffic"@en ;')
    lines.append('    schema:description "Website visitors originating from organic search engine results, as distinct from direct, referral, social, or paid traffic sources."@en .')
    lines.append("")

    lines.append(":bloggingIndustry a schema:DefinedTerm ;")
    lines.append('    schema:name "Independent Blogging Industry"@en ;')
    lines.append('    schema:description "The ecosystem of independently-owned content websites that generate revenue through advertising, affiliate marketing, and digital products, relying substantially on organic search traffic for audience acquisition."@en .')
    lines.append("")

    # ── Niche Categories ───────────────────────────────────────────────
    lines.append("# ── Niche Categories ──────────────────────────────────────────")
    lines.append("")
    niche_labels = {
        "parenting": "Parenting",
        "diy-crafts": "DIY & Crafts",
        "food-recipes": "Food & Recipes",
        "travel": "Travel",
        "lifestyle-fashion": "Lifestyle & Fashion",
        "finance": "Finance",
        "blogging-online-business": "Blogging & Online Business",
        "health-wellness": "Health & Wellness",
        "digital-tech": "Digital & Tech",
        "other": "Other",
    }
    for slug, label in niche_labels.items():
        lines.append(f":niche-{slug} a schema:DefinedTerm ;")
        lines.append(f'    schema:name "{label}"@en ;')
        lines.append(f'    schema:termCode "{slug}" .')
        lines.append("")

    # ── Status Groups ──────────────────────────────────────────────────
    lines.append("# ── Status Groups ─────────────────────────────────────────────")
    lines.append("")
    for s in STATUS_TYPES:
        slug = s.lower().replace(" ", "-")
        lines.append(f":status-{slug} a schema:DefinedTerm ;")
        lines.append(f'    schema:name "{s}"@en ;')
        lines.append(f'    schema:description "Blog operational status: {s}."@en .')
        lines.append("")

    # ── HCU Impact Levels ──────────────────────────────────────────────
    lines.append("# ── HCU Impact Levels ─────────────────────────────────────────")
    lines.append("")
    for h in HCU_IMPACTS:
        slug = h.lower().replace(" ", "-")
        desc_map = {
            "Unaffected": "Blog traffic was not materially affected by the Google HCU.",
            "Hit": "Blog experienced measurable traffic decline attributable to the HCU.",
            "Severely Hit": "Blog experienced severe (>70%%) traffic decline attributable to the HCU.",
        }
        lines.append(f":hcu-{slug} a schema:DefinedTerm ;")
        lines.append(f'    schema:name "{h}"@en ;')
        lines.append(f'    schema:description "{desc_map[h]}"@en .')
        lines.append("")

    # ── Data Confidence Levels ─────────────────────────────────────────
    lines.append("# ── Data Confidence Levels ────────────────────────────────────")
    lines.append("")
    for c in CONFIDENCE_LEVELS:
        slug = c.lower().replace(" ", "-")
        lines.append(f":confidence-{slug} a schema:DefinedTerm ;")
        lines.append(f'    schema:name "{c}"@en .')
        lines.append("")

    # ── Story Types ───────────────────────────────────────────────────
    lines.append("# ── Story Types ───────────────────────────────────────────────")
    lines.append("")
    for s in STORY_TYPES:
        slug = s.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "-")
        lines.append(f":story-{slug} a schema:DefinedTerm ;")
        lines.append(f'    schema:name "{s}"@en .')
        lines.append("")

    # ── Traffic Trajectories ───────────────────────────────────────────
    lines.append("# ── Traffic Trajectories ──────────────────────────────────────")
    lines.append("")
    for t in TRAJECTORIES:
        slug = t.lower()
        lines.append(f":trajectory-{slug} a schema:DefinedTerm ;")
        lines.append(f'    schema:name "{t}"@en .')
        lines.append("")

    # ── Monetization Methods (distinct) ────────────────────────────────
    lines.append("# ── Monetization Methods ──────────────────────────────────────")
    lines.append("")
    # Collect all distinct monetization methods
    all_methods = set()
    for b in blogs:
        for m in b["monetization"]:
            all_methods.add(m.strip())
    method_slugs = {}
    for m in sorted(all_methods):
        slug = m.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "-").replace(",", "")
        method_slugs[m] = slug
        lines.append(f":monetization-{slug} a schema:DefinedTerm ;")
        lines.append(f'    schema:name "{m}"@en .')
        lines.append("")

    # ── Blog Entities ─────────────────────────────────────────────────
    lines.append("# ═══════════════════════════════════════════════════════════════════")
    lines.append(f"# ── Blog Entities ({len(blogs)} blogs) {'─'*38}")
    lines.append("# ═══════════════════════════════════════════════════════════════════")
    lines.append("")

    for i, b in enumerate(blogs):
        name = b["name"]
        slug = name.lower().replace(" ", "-").replace("'", "").replace(".", "").replace("&", "and")
        niche_slug = NICHE_MAP.get(b["niche"], "other")
        status_slug = b["status"].lower().replace(" ", "-")
        hcu_slug = b["hcu"].lower().replace(" ", "-")
        conf_slug = b["confidence"].lower().replace(" ", "-")
        story_slug = b["story"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "-")

        lines.append(f"# Blog {i+1}: {name}")
        lines.append(f":blog-{slug} a schema:Blog, schema:WebSite ;")
        lines.append(f'    schema:name "{esc(name)}"@en ;')

        if b["url"]:
            lines.append(f'    schema:url <{b["url"]}> ;')

        if b["final_url"] and b["final_url"] != b["url"]:
            lines.append(f'    schema:sameAs <{b["final_url"]}> ;')

        lines.append(f'    schema:about :niche-{niche_slug} ;')

        # Build traffic PropertyValue list dynamically (skip None values)
        pv_items = []
        # Required fields (always present)
        pv_items.append(f'    schema:additionalProperty [ a schema:PropertyValue ;')
        pv_items.append(f'        schema:name "Total Traffic Apr 2022"@en ;')
        pv_items.append(f'        schema:value {fmt_int(b["total_2022"])} ;')
        pv_items.append(f'        schema:unitText "monthly pageviews"@en ]')

        pv_items.append(f'        , [ a schema:PropertyValue ;')
        pv_items.append(f'        schema:name "Total Traffic Apr 2026"@en ;')
        pv_items.append(f'        schema:value {fmt_int(b["total_2026"])} ;')
        pv_items.append(f'        schema:unitText "monthly pageviews"@en ]')

        pv_items.append(f'        , [ a schema:PropertyValue ;')
        pv_items.append(f'        schema:name "Total Traffic Change"@en ;')
        pv_items.append(f'        schema:value {fmt_float(b["total_delta"])} ;')
        pv_items.append(f'        schema:unitText "percent"@en ]')

        pv_items.append(f'        , [ a schema:PropertyValue ;')
        pv_items.append(f'        schema:name "SEO Traffic Apr 2022"@en ;')
        pv_items.append(f'        schema:value {fmt_int(b["seo_2022"])} ;')
        pv_items.append(f'        schema:unitText "monthly pageviews"@en ]')

        pv_items.append(f'        , [ a schema:PropertyValue ;')
        pv_items.append(f'        schema:name "SEO Traffic Apr 2026"@en ;')
        pv_items.append(f'        schema:value {fmt_int(b["seo_2026"])} ;')
        pv_items.append(f'        schema:unitText "monthly pageviews"@en ]')

        pv_items.append(f'        , [ a schema:PropertyValue ;')
        pv_items.append(f'        schema:name "SEO Traffic Change"@en ;')
        pv_items.append(f'        schema:value {fmt_float(b["seo_delta"])} ;')
        pv_items.append(f'        schema:unitText "percent"@en ]')

        pv_items.append(f'        , [ a schema:PropertyValue ;')
        pv_items.append(f'        schema:name "SEO Share 2022"@en ;')
        pv_items.append(f'        schema:value {fmt_float(b["seo_share_2022"])} ;')
        pv_items.append(f'        schema:unitText "percent"@en ]')

        # Optional: SEO Share 2026 may be None for collapsed domains
        if b["seo_share_2026"] is not None:
            pv_items.append(f'        , [ a schema:PropertyValue ;')
            pv_items.append(f'        schema:name "SEO Share 2026"@en ;')
            pv_items.append(f'        schema:value {fmt_float(b["seo_share_2026"])} ;')
            pv_items.append(f'        schema:unitText "percent"@en ]')

        # Close the additionalProperty list
        pv_items[-1] = pv_items[-1] + " ;"
        lines.extend(pv_items)

        # Traffic trajectories
        seo_traj_slug = b["seo_traj"].lower()
        total_traj_slug = b["total_traj"].lower()
        lines.append(f'    :seoTrafficTrajectory :trajectory-{seo_traj_slug} ;')
        lines.append(f'    :totalTrafficTrajectory :trajectory-{total_traj_slug} ;')

        # Income
        if b["income"] is not None:
            lines.append(f'    schema:value [ a schema:MonetaryAmount ;')
            lines.append(f'        schema:value {fmt_int(b["income"])} ;')
            lines.append(f'        schema:currency "USD"')
            if b["income_year"] is not None:
                lines.append(f'        ; schema:validThrough "{b["income_year"]}-12-31"^^xsd:date')
            lines.append(f' ] ;')

        # Monetization
        for m in b["monetization"]:
            m_clean = m.strip()
            m_slug = method_slugs.get(m_clean, m_clean.lower().replace(" ", "-"))
            lines.append(f'    schema:offers :monetization-{m_slug} ;')

        # Status, HCU, Confidence, Story
        lines.append(f'    :blogStatus :status-{status_slug} ;')
        lines.append(f'    :hcuImpact :hcu-{hcu_slug} ;')
        lines.append(f'    :dataConfidence :confidence-{conf_slug} ;')
        lines.append(f'    :storyType :story-{story_slug} ;')

        # Last verified
        if b["verified"]:
            lines.append(f'    schema:dateModified "{b["verified"]}-01"^^xsd:date ;')

        # New brand (for rebranded blogs)
        if b["new_brand"]:
            lines.append(f'    schema:alternateName "{esc(b["new_brand"])}"@en ;')

        # Close (remove trailing ; from last property)
        # The last statement should end with .
        # Find the last line added and replace trailing ; with .
        lines[-1] = lines[-1].rstrip(" ;") + " ."
        lines.append("")

    # ── Ontology Entity ───────────────────────────────────────────────
    lines.append("# ═══════════════════════════════════════════════════════════════════")
    lines.append("# ── Ontology Declaration ───────────────────────────────────────")
    lines.append("# ═══════════════════════════════════════════════════════════════════")
    lines.append("")
    lines.append(":bloggingCollapseOntology a owl:Ontology ;")
    lines.append('    schema:name "Great Blogging Collapse Study Ontology"@en ;')
    lines.append('    rdfs:label "Great Blogging Collapse Study Ontology"@en ;')
    lines.append('    rdfs:comment "Lightweight ontology defining custom properties for the Great Blogging Collapse study by Daniel Stancil. Models blog traffic trajectories, HCU impact classification, operational status, data confidence, and narrative story types for independent content websites."@en ;')
    lines.append('    schema:description "Custom RDF vocabulary for the Great Blogging Collapse study of 98 blogs analyzed across the April 2022 to April 2026 period. Extends schema.org with study-specific properties for classifying blog survival outcomes after Google\'s Helpful Content Update."@en ;')
    lines.append('    schema:dateCreated "2026-06-30"^^xsd:date ;')
    lines.append('    rdfs:seeAlso <http://dbpedia.org/resource/Blog>,')
    lines.append('                <http://dbpedia.org/resource/Web_traffic>,')
    lines.append('                <http://dbpedia.org/resource/Search_engine_optimization> .')
    lines.append("")

    # ── Custom Property Definitions ────────────────────────────────────
    lines.append("# ── Custom Property Definitions ─────────────────────────────────")
    lines.append("")

    custom_props = [
        (":seoTrafficTrajectory", "SEO Traffic Trajectory",
         "Classification of the 4-year trend in organic search traffic: Growing, Stable, Declining, or Collapsed.",
         "schema:Blog", ":trajectory",
         "<http://dbpedia.org/resource/Web_traffic>",
         "The trajectory of organic search traffic over time, as a categorical classification."),
        (":totalTrafficTrajectory", "Total Traffic Trajectory",
         "Classification of the 4-year trend in total website traffic: Growing, Stable, Declining, or Collapsed.",
         "schema:Blog", ":trajectory",
         "<http://dbpedia.org/resource/Web_traffic>",
         "The trajectory of total website traffic over time, as a categorical classification."),
        (":blogStatus", "Blog Operational Status",
         "Current operational status of the blog: Alive, Unverified, Rebranded, Sold, or Dead.",
         "schema:Blog", ":status",
         "<http://dbpedia.org/resource/Blog>",
         "Whether the blog is still actively operating, has been sold, rebranded, or is defunct."),
        (":hcuImpact", "HCU Impact Level",
         "Severity of Google Helpful Content Update impact on the blog: Unaffected, Hit, or Severely Hit.",
         "schema:Blog", ":hcuImpactLevel",
         "<http://dbpedia.org/resource/Search_engine_optimization>",
         "The degree to which the blog's traffic was affected by Google's Helpful Content Update algorithm changes."),
        (":dataConfidence", "Data Confidence Level",
         "Author confidence in the reported traffic and income data: Estimated, Verified, Unknown, or Claimed.",
         "schema:Blog", ":confidence",
         "<http://dbpedia.org/resource/Data_quality>",
         "How reliable the reported figures are, based on the study author's sourcing methodology."),
        (":storyType", "Blog Story Type",
         "Narrative classification of the blog's outcome: HCU Survived, Consistent Grower, HCU Decline / Survived, HCU Collapse, Went Off-Blog, Full Rebrand, Sold at Peak / Exit, Traffic Collapse / Dead, or Domain Compromised.",
         "schema:Blog", ":storyType",
         "<http://dbpedia.org/resource/Blog>",
         "The high-level narrative arc describing the blog's trajectory and ultimate fate."),
    ]
    for prop_id, name, desc, domain, range_, dbr_seealso, gap_note in custom_props:
        lines.append(f"{prop_id} a rdf:Property ;")
        lines.append(f'    rdfs:label "{name}"@en ;')
        lines.append(f'    rdfs:comment "{desc} {gap_note}"@en ;')
        lines.append(f"    rdfs:domain {domain} ;")
        lines.append(f"    rdfs:range {range_} ;")
        lines.append(f"    rdfs:isDefinedBy :bloggingCollapseOntology ;")
        lines.append(f"    rdfs:seeAlso {dbr_seealso} .")
        lines.append("")

    # ── Aggregate Statistics ───────────────────────────────────────────
    lines.append("# ── Aggregate Study Statistics ────────────────────────────────")
    lines.append("")

    # Count by status
    status_counts = {}
    for b in blogs:
        s = b["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    for s, count in sorted(status_counts.items()):
        slug = s.lower().replace(" ", "-")
        lines.append(f":stat-status-{slug} a schema:Observation ;")
        lines.append(f'    schema:name "Blogs with status: {s}"@en ;')
        lines.append(f'    schema:observedNode :study ;')
        lines.append(f'    schema:measuredProperty :blogStatus ;')
        lines.append(f'    schema:measuredValue {count} ;')
        lines.append(f'    schema:value :status-{slug} .')
        lines.append("")

    # Count by HCU impact
    hcu_counts = {}
    for b in blogs:
        h = b["hcu"]
        hcu_counts[h] = hcu_counts.get(h, 0) + 1
    for h, count in sorted(hcu_counts.items()):
        slug = h.lower().replace(" ", "-")
        lines.append(f":stat-hcu-{slug} a schema:Observation ;")
        lines.append(f'    schema:name "Blogs with HCU impact: {h}"@en ;')
        lines.append(f'    schema:observedNode :study ;')
        lines.append(f'    schema:measuredProperty :hcuImpact ;')
        lines.append(f'    schema:measuredValue {count} ;')
        lines.append(f'    schema:value :hcu-{slug} .')
        lines.append("")

    # Count by niche
    niche_counts = {}
    for b in blogs:
        n = b["niche"]
        niche_counts[n] = niche_counts.get(n, 0) + 1
    for n, count in sorted(niche_counts.items(), key=lambda x: -x[1]):
        slug = NICHE_MAP[n]
        lines.append(f":stat-niche-{slug} a schema:Observation ;")
        lines.append(f'    schema:name "Blogs in niche: {n}"@en ;')
        lines.append(f'    schema:observedNode :study ;')
        lines.append(f'    schema:measuredProperty schema:about ;')
        lines.append(f'    schema:measuredValue {count} ;')
        lines.append(f'    schema:value :niche-{slug} .')
        lines.append("")

    # Aggregate financials
    total_income = sum(b["income"] for b in blogs if b["income"] is not None)
    incomes_with_data = [b for b in blogs if b["income"] is not None]
    lines.append(f":stat-total-income a schema:Observation ;")
    lines.append(f'    schema:name "Total Reported Income (all blogs)"@en ;')
    lines.append(f'    schema:observedNode :study ;')
    lines.append(f'    schema:measuredValue {total_income} ;')
    lines.append(f'    schema:unitText "USD"@en ;')
    lines.append(f'    schema:description "Sum of most recent reported annual income across {len(incomes_with_data)} blogs that disclosed income data."@en .')
    lines.append("")

    # Traffic aggregate
    total_traffic_2022 = sum(b["total_2022"] for b in blogs)
    total_traffic_2026 = sum(b["total_2026"] for b in blogs)
    lines.append(f":stat-total-traffic-2022 a schema:Observation ;")
    lines.append(f'    schema:name "Aggregate Total Traffic Apr 2022"@en ;')
    lines.append(f'    schema:observedNode :study ;')
    lines.append(f'    schema:measuredValue {total_traffic_2022} ;')
    lines.append(f'    schema:unitText "monthly pageviews"@en .')
    lines.append("")
    lines.append(f":stat-total-traffic-2026 a schema:Observation ;")
    lines.append(f'    schema:name "Aggregate Total Traffic Apr 2026"@en ;')
    lines.append(f'    schema:observedNode :study ;')
    lines.append(f'    schema:measuredValue {total_traffic_2026} ;')
    lines.append(f'    schema:unitText "monthly pageviews"@en .')
    lines.append("")

    # Top/bottom performers
    sorted_by_delta = sorted(blogs, key=lambda b: b["total_delta"])
    worst = sorted_by_delta[:5]
    best = sorted_by_delta[-5:]
    lines.append("# ── Top 5 Biggest Losers by Total Traffic Δ ─────────────────")
    for b in worst:
        slug = b["name"].lower().replace(" ", "-").replace("'", "").replace(".", "")
        lines.append(f":study schema:hasPart :blog-{slug} .")
    lines.append("")
    lines.append("# ── Top 5 Biggest Gainers by Total Traffic Δ ────────────────")
    for b in best:
        slug = b["name"].lower().replace(" ", "-").replace("'", "").replace(".", "")
        lines.append(f":study schema:hasPart :blog-{slug} .")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    ttl = generate_ttl()
    output_path = os.environ.get("OUTPUT_PATH", os.path.join(
        os.environ.get("LLM_ROOT", os.path.join(os.path.expanduser("~"), "Documents", "LLMs")),
        "DeepSeek/rdf/great-blogging-collapse-study-deepseek_v4pro-1.ttl"))
    with open(output_path, "w") as f:
        f.write(ttl)
    print(f"✅ Written {len(ttl):,} chars to {output_path}")
    print(f"   {ttl.count(chr(10)):,} lines")
