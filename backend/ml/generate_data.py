# CreditGhost — Ultra-Realistic AA Format Data Generator
# Generates 500 users covering EVERY possible behavioral type
# Each profile looks exactly like real Setu/AA framework output
# Run: python ml/generate_data.py

import json
import random
import os
import math
import numpy as np
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

# ═══════════════════════════════════════════════════════════════
# SECTION 1 — REAL INDIAN MERCHANT DATABASE
# Every merchant, category, and amount is based on real India
# ═══════════════════════════════════════════════════════════════

MERCHANT_DB = {

    # ── TELECOM ──────────────────────────────────────────────
    "TELECOM": [
        # (merchant_name, [realistic_amounts], frequency_per_month)
        ("Jio Prepaid Recharge",    [149,179,199,209,239,299,399,479,499,599,719], 1.0),
        ("Airtel Prepaid",          [155,179,199,219,265,299,359,399,449,499,549], 1.0),
        ("Vi Prepaid",              [129,149,179,199,219,249,269,299,349,399,449], 1.0),
        ("BSNL Recharge",           [99,107,117,147,187,197,247,299,319,397],      1.0),
        ("Jio Postpaid",            [299,349,399,449,499,599,699,799,999],          1.0),
        ("Airtel Postpaid",         [299,349,399,449,499,549,599,699,799,999],      1.0),
        ("Jio Fiber",               [399,499,699,999,1499,2499],                    0.3),
        ("Airtel Xstream Fiber",    [499,599,799,999,1499],                         0.3),
        ("ACT Fibernet",            [399,499,599,699,799,999,1299],                 0.2),
    ],

    # ── UTILITY BILLS ─────────────────────────────────────────
    "UTILITY": [
        ("BESCOM Electricity",      [200,350,500,650,800,1000,1200,1500,2000,2500,3000], 1.0),
        ("TNEB Electricity",        [180,300,450,600,750,900,1100,1400,1800,2200],        1.0),
        ("MSEDCL Electricity",      [250,400,550,700,900,1100,1400,1800,2200,2800],       1.0),
        ("TSSPDCL Electricity",     [150,280,420,560,700,850,1050,1300,1700,2100],        1.0),
        ("CESC Electricity",        [200,350,500,650,800,1000,1250,1600,2000,2500],       1.0),
        ("Chennai Metro Water",     [100,150,200,250,300,350,400],                         0.7),
        ("BWSSB Water",             [80,120,160,200,250,300,380],                          0.7),
        ("Indane LPG Gas",          [750,800,850,900,950,1000,1050,1100],                 0.5),
        ("HP Gas Cylinder",         [760,810,860,910,960,1010,1060],                      0.5),
        ("Bharat Gas",              [755,805,855,905,955,1005,1055],                      0.5),
        ("Piped Gas GAIL",          [200,300,400,500,600,700,800],                        0.3),
        ("OC Water Tanker",         [300,400,500,600,700,800,1000],                       0.2),
    ],

    # ── FOOD & DELIVERY ───────────────────────────────────────
    "FOOD_DELIVERY": [
        ("Swiggy",                  [80,120,150,200,250,300,350,400,500,600,800],    2.0),
        ("Zomato",                  [75,110,140,190,240,290,340,390,480,580,750],    2.0),
        ("Dunzo",                   [50,80,100,130,160,200,250,300],                  0.5),
        ("Zepto",                   [150,200,250,300,400,500,600],                    0.8),
        ("Blinkit",                 [100,150,200,280,350,450,600],                    0.8),
        ("BigBasket Now",           [200,300,400,500,650,800,1000,1200],              0.5),
        ("Swiggy Instamart",        [120,180,250,320,420,550],                        0.6),
        ("EatSure",                 [150,200,280,350,450,600],                        0.3),
        ("Rebel Foods",             [130,180,250,320,410,550],                        0.2),
    ],

    # ── GROCERY & DAILY NEEDS ─────────────────────────────────
    "GROCERY": [
        ("BigBasket",               [300,500,700,900,1200,1500,2000,2500,3000],      1.5),
        ("DMart",                   [400,600,800,1000,1400,1800,2200,2800,3500],     1.0),
        ("More Supermarket",        [200,350,500,700,900,1200,1500],                  0.8),
        ("Reliance Smart",          [300,500,700,1000,1300,1700,2100],               0.8),
        ("Spencer's",               [250,400,600,800,1100,1400,1800],                0.5),
        ("Local Kirana Store",      [50,80,100,150,200,250,300,400,500],             3.0),
        ("Nilgiris",                [200,350,500,700,900,1200],                       0.4),
        ("Star Bazaar",             [400,600,900,1200,1600,2000],                     0.3),
        ("Lulu Hypermarket",        [500,800,1200,1600,2000,2500,3000],              0.2),
    ],

    # ── TRANSPORT ─────────────────────────────────────────────
    "TRANSPORT": [
        ("Ola Cabs",                [60,80,100,130,160,200,250,300,400,500],         3.0),
        ("Uber",                    [65,85,110,140,170,210,260,320,420,530],         2.5),
        ("Rapido Bike",             [25,35,45,55,70,85,100,120],                     2.0),
        ("Ola Auto",                [40,55,70,85,100,120,140,160],                   1.5),
        ("BMTC Bus Pass",           [400,500,700,900],                                0.1),
        ("Chennai MTC",             [10,12,15,18,20,25,30],                          5.0),
        ("Namma Metro",             [10,15,20,25,30,35,40,45,50],                    4.0),
        ("BMRCL Metro",             [10,15,20,25,30,35,40,50,60],                    3.0),
        ("Indian Railways IRCTC",   [150,250,350,500,700,1000,1500,2000],            0.3),
        ("RedBus",                  [200,350,500,700,900,1200,1500],                  0.2),
        ("IndiGo Airlines",         [2000,3000,4000,5000,6000,8000,10000],           0.1),
        ("Petrol Pump HP",          [200,300,500,700,1000,1500,2000,2500],           2.0),
        ("Petrol Pump Indian Oil",  [200,300,500,700,1000,1500,2000],                2.0),
        ("CNG Station",             [100,150,200,250,300,350,400,500],               1.0),
        ("FastTag Toll",            [30,50,75,100,150,200,250],                       1.0),
    ],

    # ── SHOPPING ──────────────────────────────────────────────
    "SHOPPING": [
        ("Amazon India",            [200,350,500,700,1000,1500,2000,3000,5000],      1.5),
        ("Flipkart",                [180,300,450,650,900,1300,1800,2500,4000],       1.2),
        ("Meesho",                  [100,150,200,280,350,450,600,800],               1.0),
        ("Myntra",                  [300,500,700,1000,1400,1800,2500,3500],          0.5),
        ("Ajio",                    [350,550,750,1050,1400,1900,2600],               0.3),
        ("Nykaa",                   [200,350,500,700,950,1300,1800],                  0.4),
        ("Mamaearth",               [150,250,350,500,700,900],                        0.3),
        ("Decathlon",               [300,500,800,1200,1800,2500,3500],               0.2),
        ("Croma",                   [500,1000,2000,3000,5000,8000,12000,20000],      0.1),
        ("Reliance Digital",        [500,1000,2000,3000,5000,8000,15000],            0.1),
        ("FirstCry",                [300,500,700,1000,1400,1900,2500],               0.2),
        ("PharmEasy",               [100,200,300,500,700,1000,1500],                  0.4),
        ("1mg",                     [100,200,350,500,800,1200],                       0.3),
        ("Lenskart",                [500,1000,1500,2000,3000,4000,5000],             0.1),
    ],

    # ── ENTERTAINMENT ─────────────────────────────────────────
    "ENTERTAINMENT": [
        ("Netflix",                 [149,199,499,649],                                0.3),
        ("Amazon Prime",            [179,299,1499],                                   0.3),
        ("Hotstar Disney+",         [149,299,499,899,1499],                          0.3),
        ("Spotify",                 [59,119,179],                                     0.4),
        ("YouTube Premium",         [129,189],                                        0.2),
        ("BookMyShow",              [150,200,300,400,500,700,900,1200],              0.4),
        ("PVR Cinemas",             [150,200,250,300,400,500,600,700],               0.3),
        ("INOX Movies",             [140,180,230,280,360,460,580],                   0.2),
        ("Gamezop",                 [10,20,30,50,100],                                0.1),
        ("MPL Sports",              [10,25,50,100,200],                               0.1),
    ],

    # ── HEALTHCARE ────────────────────────────────────────────
    "HEALTHCARE": [
        ("Apollo Pharmacy",         [50,100,150,200,300,500,700,1000,1500],          1.0),
        ("MedPlus",                 [50,100,150,200,280,400,600,900,1300],           0.8),
        ("Netmeds",                 [100,200,300,500,700,1000,1500],                  0.4),
        ("Fortis Hospital",         [500,1000,2000,3000,5000,8000,15000,25000],      0.1),
        ("Apollo Hospital",         [500,1000,2000,3000,5000,8000,12000,20000],      0.1),
        ("Local Clinic",            [100,200,300,400,500,700],                        0.3),
        ("Government Hospital",     [10,20,50,100,200],                               0.2),
        ("Dental Clinic",           [200,500,800,1200,2000,3000,5000],               0.1),
        ("Pathology Lab",           [100,200,400,700,1000,1500,2500],                0.2),
        ("HealthifyMe",             [100,200,400,800,1200,2000],                      0.1),
    ],

    # ── EDUCATION ─────────────────────────────────────────────
    "EDUCATION": [
        ("School Fees",             [1000,2000,3000,5000,7000,10000,15000],          0.3),
        ("College Fees",            [5000,10000,15000,20000,30000,50000],            0.1),
        ("BYJU's",                  [500,1000,2000,3000,5000],                        0.2),
        ("Unacademy",               [300,500,1000,2000,3000,5000],                   0.1),
        ("Coursera",                [500,1000,2000,3000,5000],                        0.1),
        ("Udemy",                   [199,299,499,799,1299],                           0.1),
        ("Tuition Fees",            [500,800,1000,1500,2000,3000],                   0.3),
        ("Stationary Shop",         [50,100,150,200,300,500],                         0.3),
    ],

    # ── FOOD (NON DELIVERY) ───────────────────────────────────
    "DINING": [
        ("Hotel/Restaurant",        [100,150,200,300,400,500,700,1000,1500],         1.5),
        ("Chai/Coffee Shop",        [20,30,40,50,60,80,100,120,150],                 5.0),
        ("Bakery",                  [50,80,100,150,200,300],                          1.0),
        ("Juice Shop",              [30,50,70,100,120],                               1.0),
        ("Street Food",             [20,30,50,80,100],                                3.0),
        ("Haldirams",               [100,150,200,300,400,600],                        0.5),
        ("MTR Restaurant",          [100,150,200,300,450,600],                        0.3),
        ("Saravana Bhavan",         [150,200,300,400,600,800],                        0.3),
        ("KFC",                     [150,250,350,500,700],                             0.4),
        ("McDonald's",              [100,150,200,280,380,500],                        0.4),
        ("Domino's Pizza",          [200,300,400,500,700,900],                        0.3),
    ],

    # ── FINANCIAL SERVICES ────────────────────────────────────
    "FINANCIAL": [
        ("LIC Premium",             [500,1000,1500,2000,3000,5000,8000,10000],       0.2),
        ("HDFC Life Insurance",     [500,1000,2000,3000,5000,8000],                  0.1),
        ("Star Health Insurance",   [500,1000,2000,3000,5000],                        0.1),
        ("Bajaj Allianz",           [500,1000,2000,3000,5000,8000],                  0.1),
        ("Mutual Fund SIP",         [500,1000,2000,3000,5000,10000],                 0.2),
        ("PPF Deposit",             [500,1000,2000,3000,5000,10000,12500],           0.1),
        ("RD Monthly",              [500,1000,2000,3000,5000],                        0.2),
        ("Gold Purchase",           [1000,2000,5000,10000,20000,50000],              0.05),
        ("Paytm Wallet Load",       [100,200,500,1000,2000],                          0.3),
        ("PhonePe Wallet",          [100,200,500,1000],                               0.2),
    ],

    # ── EMI / LOAN REPAYMENTS ─────────────────────────────────
    "EMI": [
        ("Bajaj Finance EMI",       [500,1000,1500,2000,2500,3000,3500,4000,5000],  1.0),
        ("HDFC Bank EMI",           [1000,1500,2000,2500,3000,4000,5000,7000],       1.0),
        ("ICICI Bank EMI",          [1000,1500,2000,2500,3000,4000,5000,7000],       1.0),
        ("SBI EMI",                 [500,1000,1500,2000,2500,3000,4000,5000],        1.0),
        ("Muthoot Finance",         [500,1000,1500,2000,2500,3000],                  1.0),
        ("Manappuram Gold Loan",    [500,1000,1500,2000,2500,3000],                  1.0),
        ("IIFL Finance",            [500,1000,1500,2000,2500,3000,3500],             1.0),
        ("MoneyTap EMI",            [500,1000,1500,2000,2500],                        1.0),
        ("KreditBee",               [300,500,800,1000,1500,2000],                     1.0),
        ("EarlySalary",             [500,1000,1500,2000,2500,3000],                  1.0),
        ("CASHe",                   [500,1000,1500,2000,2500],                        1.0),
    ],

    # ── P2P TRANSFERS ─────────────────────────────────────────
    "P2P_TRANSFER": [
        # Common Tamil/South Indian names
        ("Ramesh Kumar",            None),
        ("Selvam R",                None),
        ("Murugan K",               None),
        ("Lakshmi S",               None),
        ("Suresh M",                None),
        ("Priya D",                 None),
        ("Karthik N",               None),
        ("Anbu S",                  None),
        ("Deepa R",                 None),
        ("Vijay K",                 None),
        ("Sangeetha M",             None),
        ("Rajan P",                 None),
        ("Kavitha S",               None),
        ("Senthil K",               None),
        # North Indian names
        ("Rahul Sharma",            None),
        ("Priya Singh",             None),
        ("Amit Kumar",              None),
        ("Neha Verma",              None),
        ("Ravi Gupta",              None),
        ("Sunita Devi",             None),
        # Common amounts for P2P
    ],

    # ── RENT ──────────────────────────────────────────────────
    "RENT": [
        ("House Rent",              [3000,4000,5000,6000,7000,8000,10000,12000,15000,20000], 1.0),
        ("Room Rent",               [2000,2500,3000,3500,4000,5000,6000,7000],       1.0),
        ("PG Accommodation",        [3000,4000,5000,6000,7000,8000,10000],           1.0),
        ("Hostel Fees",             [3000,4000,5000,6000,7000,8000],                  1.0),
    ],

    # ── SALARY / INCOME ───────────────────────────────────────
    "SALARY": [
        ("RAJAN TRANSPORT CO",      None),
        ("KRISHNA ENTERPRISES",     None),
        ("SELVAM AGENCIES",         None),
        ("MURUGAN TEXTILES",        None),
        ("CHENNAI LOGISTICS",       None),
        ("COIMBATORE MILLS",        None),
        ("DAILY WAGE PAYMENT",      None),
        ("CONTRACTOR PAYMENT",      None),
        ("INFOSYS BPO",             None),
        ("TCS PAYROLL",             None),
        ("WIPRO SALARY",            None),
        ("HCL TECHNOLOGIES",        None),
        ("AMAZON INDIA",            None),
        ("FLIPKART SELLER",         None),
        ("SWIGGY DELIVERY",         None),
        ("OLA PARTNER",             None),
        ("UBER PARTNER",            None),
        ("ZOMATO DELIVERY",         None),
        ("FREELANCE PAYMENT",       None),
        ("GOVERNMENT SALARY",       None),
    ],

    # ── GOVERNMENT / MISC ─────────────────────────────────────
    "GOVERNMENT": [
        ("Income Tax Refund",       None),
        ("PM Kisan Samman",         None),
        ("MGNREGA Wages",           None),
        ("Scholarship Amount",      None),
        ("Property Tax",            [500,1000,2000,3000,5000,8000]),
        ("Vehicle Tax RTO",         [500,1000,1500,2000,3000]),
        ("Passport Fees",           [1000,1500,2000,3500]),
        ("GSTIN Payment",           [500,1000,2000,5000,10000]),
        ("Traffic Fine",            [500,1000,1500,2000]),
        ("BBMP Property Tax",       [500,1000,2000,3000,5000]),
    ],

    # ── ATM / CASH ────────────────────────────────────────────
    "CASH": [
        ("ATM Cash Withdrawal",     [500,1000,2000,3000,5000,10000], ),
        ("Cash Deposit",            None),
    ],
}


# ═══════════════════════════════════════════════════════════════
# SECTION 2 — 12 BEHAVIORAL ARCHETYPES
# Every possible type of Indian microfinance customer
# ═══════════════════════════════════════════════════════════════

ARCHETYPES = {

    # ─── EXCELLENT PROFILES (Score 750-900) ──────────────────

    "disciplined_salaried": {
        "description":          "Office worker, stable salary, very disciplined",
        "weight":               0.08,
        "expected_score_range": (780, 900),
        "monthly_income":       (18000, 45000),
        "income_type":          "SALARY",
        "income_day_range":     (1, 5),        # salary comes early month
        "income_consistency":   0.97,          # almost always on time
        "income_variation":     0.05,          # very little variation
        "monthly_txn_count":    (30, 55),
        "recharge_probability": 0.98,
        "recharge_same_amount": True,
        "bills_paid_rate":      0.95,
        "savings_rate":         (0.18, 0.30),
        "has_sip":              True,
        "has_insurance":        True,
        "emi_probability":      0.45,
        "emi_to_income_ratio":  (0.10, 0.28),
        "spike_probability":    0.05,
        "failed_txn_rate":      0.01,
        "night_txn_ratio":      0.04,
        "cash_usage":           0.10,
        "merchant_categories":  [
            ("TELECOM",1),("UTILITY",2),("GROCERY",3),
            ("TRANSPORT",3),("FOOD_DELIVERY",2),("DINING",2),
            ("SHOPPING",1),("HEALTHCARE",0.5),("ENTERTAINMENT",1),
            ("FINANCIAL",1),("RENT",0.7)
        ],
        "has_rent":             0.60,
    },

    "consistent_gig_worker": {
        "description":          "Ola/Swiggy/Zomato delivery, consistent income",
        "weight":               0.10,
        "expected_score_range": (640, 790),
        "monthly_income":       (10000, 22000),
        "income_type":          "GIG",
        "income_day_range":     (1, 28),       # income comes throughout month
        "income_consistency":   0.88,
        "income_variation":     0.15,
        "monthly_txn_count":    (25, 45),
        "recharge_probability": 0.95,
        "recharge_same_amount": True,
        "bills_paid_rate":      0.80,
        "savings_rate":         (0.08, 0.18),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.25,
        "emi_to_income_ratio":  (0.10, 0.25),
        "spike_probability":    0.10,
        "failed_txn_rate":      0.03,
        "night_txn_ratio":      0.12,          # gig workers work nights
        "cash_usage":           0.15,
        "merchant_categories":  [
            ("TELECOM",1),("UTILITY",1.5),("GROCERY",2),
            ("TRANSPORT",1),("FOOD_DELIVERY",1.5),("DINING",2),
            ("SHOPPING",0.5),("HEALTHCARE",0.3),
        ],
        "has_rent":             0.70,
    },

    "small_business_owner": {
        "description":          "Kirana/tea stall/small shop owner",
        "weight":               0.09,
        "expected_score_range": (620, 800),
        "monthly_income":       (15000, 50000),
        "income_type":          "BUSINESS",
        "income_day_range":     (1, 28),       # business income daily/weekly
        "income_consistency":   0.72,
        "income_variation":     0.25,
        "monthly_txn_count":    (40, 80),      # high txn volume for business
        "recharge_probability": 0.98,
        "recharge_same_amount": False,
        "bills_paid_rate":      0.82,
        "savings_rate":         (0.12, 0.28),
        "has_sip":              False,
        "has_insurance":        True,
        "emi_probability":      0.40,
        "emi_to_income_ratio":  (0.10, 0.30),
        "spike_probability":    0.12,
        "failed_txn_rate":      0.02,
        "night_txn_ratio":      0.06,
        "cash_usage":           0.30,          # businesses use more cash
        "merchant_categories":  [
            ("TELECOM",1),("UTILITY",2),("GROCERY",4),
            ("TRANSPORT",2),("DINING",1),("SHOPPING",1),
            ("GOVERNMENT",0.3),("FINANCIAL",0.5),
        ],
        "has_rent":             0.50,
    },

    # ─── GOOD PROFILES (Score 600-750) ───────────────────────

    "stable_auto_driver": {
        "description":          "Auto driver with consistent routes and income",
        "weight":               0.09,
        "expected_score_range": (580, 720),
        "monthly_income":       (8000, 18000),
        "income_type":          "GIG",
        "income_day_range":     (1, 28),
        "income_consistency":   0.80,
        "income_variation":     0.20,
        "monthly_txn_count":    (15, 30),
        "recharge_probability": 0.90,
        "recharge_same_amount": True,
        "bills_paid_rate":      0.72,
        "savings_rate":         (0.05, 0.14),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.20,
        "emi_to_income_ratio":  (0.10, 0.22),
        "spike_probability":    0.12,
        "failed_txn_rate":      0.04,
        "night_txn_ratio":      0.08,
        "cash_usage":           0.25,
        "merchant_categories":  [
            ("TELECOM",1),("UTILITY",1),("GROCERY",2),
            ("TRANSPORT",1),("FOOD_DELIVERY",1),("DINING",2),
            ("HEALTHCARE",0.3),
        ],
        "has_rent":             0.65,
    },

    "factory_worker": {
        "description":          "Factory/mill worker with regular wages",
        "weight":               0.09,
        "expected_score_range": (540, 700),
        "monthly_income":       (9000, 20000),
        "income_type":          "SALARY",
        "income_day_range":     (1, 10),
        "income_consistency":   0.85,
        "income_variation":     0.08,
        "monthly_txn_count":    (15, 30),
        "recharge_probability": 0.88,
        "recharge_same_amount": True,
        "bills_paid_rate":      0.75,
        "savings_rate":         (0.06, 0.16),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.35,
        "emi_to_income_ratio":  (0.15, 0.30),
        "spike_probability":    0.15,
        "failed_txn_rate":      0.05,
        "night_txn_ratio":      0.06,
        "cash_usage":           0.20,
        "merchant_categories":  [
            ("TELECOM",1),("UTILITY",1.5),("GROCERY",2),
            ("TRANSPORT",2),("DINING",1.5),("HEALTHCARE",0.4),
            ("SHOPPING",0.3),
        ],
        "has_rent":             0.55,
    },

    # ─── MEDIUM PROFILES (Score 450-600) ─────────────────────

    "irregular_daily_wage": {
        "description":          "Construction/seasonal worker, irregular income",
        "weight":               0.10,
        "expected_score_range": (380, 560),
        "monthly_income":       (5000, 14000),
        "income_type":          "DAILY_WAGE",
        "income_day_range":     (1, 28),
        "income_consistency":   0.55,
        "income_variation":     0.40,
        "monthly_txn_count":    (8, 22),
        "recharge_probability": 0.68,
        "recharge_same_amount": False,
        "bills_paid_rate":      0.50,
        "savings_rate":         (0.01, 0.08),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.15,
        "emi_to_income_ratio":  (0.10, 0.20),
        "spike_probability":    0.25,
        "failed_txn_rate":      0.10,
        "night_txn_ratio":      0.15,
        "cash_usage":           0.40,
        "merchant_categories":  [
            ("TELECOM",0.7),("GROCERY",2),("DINING",1.5),
            ("P2P_TRANSFER",2),("CASH",1),
        ],
        "has_rent":             0.60,
    },

    "college_student": {
        "description":          "College student, part-time work or family support",
        "weight":               0.08,
        "expected_score_range": (350, 530),
        "monthly_income":       (2000, 8000),
        "income_type":          "TRANSFER",  # family sends money
        "income_day_range":     (1, 10),
        "income_consistency":   0.60,
        "income_variation":     0.35,
        "monthly_txn_count":    (20, 45),
        "recharge_probability": 0.75,
        "recharge_same_amount": False,
        "bills_paid_rate":      0.30,
        "savings_rate":         (0.00, 0.06),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.10,
        "emi_to_income_ratio":  (0.10, 0.20),
        "spike_probability":    0.30,
        "failed_txn_rate":      0.12,
        "night_txn_ratio":      0.28,          # students are night owls
        "cash_usage":           0.15,
        "merchant_categories":  [
            ("TELECOM",1),("FOOD_DELIVERY",3),("DINING",2),
            ("ENTERTAINMENT",2),("SHOPPING",2),("P2P_TRANSFER",3),
            ("EDUCATION",0.5),
        ],
        "has_rent":             0.70,
    },

    "housewife_managing": {
        "description":          "Homemaker managing household with husband's income",
        "weight":               0.07,
        "expected_score_range": (500, 670),
        "monthly_income":       (12000, 30000),  # household budget received
        "income_type":          "TRANSFER",
        "income_day_range":     (1, 7),
        "income_consistency":   0.88,
        "income_variation":     0.10,
        "monthly_txn_count":    (20, 40),
        "recharge_probability": 0.92,
        "recharge_same_amount": True,
        "bills_paid_rate":      0.85,
        "savings_rate":         (0.08, 0.20),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.10,
        "emi_to_income_ratio":  (0.05, 0.15),
        "spike_probability":    0.10,
        "failed_txn_rate":      0.03,
        "night_txn_ratio":      0.04,
        "cash_usage":           0.25,
        "merchant_categories":  [
            ("TELECOM",1),("UTILITY",2),("GROCERY",4),
            ("HEALTHCARE",0.8),("EDUCATION",0.5),("DINING",1),
            ("SHOPPING",1),
        ],
        "has_rent":             0.20,
    },

    # ─── POOR PROFILES (Score 300-450) ───────────────────────

    "over_indebted": {
        "description":          "Person with too many loans, struggling to repay",
        "weight":               0.08,
        "expected_score_range": (300, 440),
        "monthly_income":       (8000, 20000),
        "income_type":          "SALARY",
        "income_day_range":     (1, 10),
        "income_consistency":   0.75,
        "income_variation":     0.12,
        "monthly_txn_count":    (15, 30),
        "recharge_probability": 0.70,
        "recharge_same_amount": False,
        "bills_paid_rate":      0.40,          # can't pay bills — too much EMI
        "savings_rate":         (0.00, 0.03),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.95,          # definitely has EMIs
        "emi_to_income_ratio":  (0.45, 0.70), # very high EMI burden
        "spike_probability":    0.08,
        "failed_txn_rate":      0.15,          # fails because EMI drains account
        "night_txn_ratio":      0.08,
        "cash_usage":           0.20,
        "merchant_categories":  [
            ("TELECOM",0.8),("GROCERY",1.5),("DINING",1),
            ("TRANSPORT",1.5),("EMI",2),
        ],
        "has_rent":             0.50,
    },

    "seasonal_migrant_worker": {
        "description":          "Migrant worker, income very seasonal",
        "weight":               0.07,
        "expected_score_range": (320, 480),
        "monthly_income":       (4000, 15000),
        "income_type":          "SEASONAL",
        "income_day_range":     (1, 28),
        "income_consistency":   0.40,          # 3-4 months no income
        "income_variation":     0.60,
        "monthly_txn_count":    (5, 18),
        "recharge_probability": 0.55,
        "recharge_same_amount": False,
        "bills_paid_rate":      0.35,
        "savings_rate":         (0.00, 0.05),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.10,
        "emi_to_income_ratio":  (0.10, 0.20),
        "spike_probability":    0.20,
        "failed_txn_rate":      0.18,
        "night_txn_ratio":      0.20,
        "cash_usage":           0.50,          # migrant workers use cash
        "merchant_categories":  [
            ("TELECOM",0.5),("GROCERY",1.5),("P2P_TRANSFER",3),
            ("CASH",2),("DINING",1),
        ],
        "has_rent":             0.30,
    },

    "financially_stressed": {
        "description":          "Person facing financial crisis, erratic behavior",
        "weight":               0.07,
        "expected_score_range": (300, 420),
        "monthly_income":       (5000, 12000),
        "income_type":          "IRREGULAR",
        "income_day_range":     (1, 28),
        "income_consistency":   0.45,
        "income_variation":     0.50,
        "monthly_txn_count":    (8, 20),
        "recharge_probability": 0.50,
        "recharge_same_amount": False,
        "bills_paid_rate":      0.25,
        "savings_rate":         (0.00, 0.02),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.30,
        "emi_to_income_ratio":  (0.30, 0.60),
        "spike_probability":    0.35,
        "failed_txn_rate":      0.22,
        "night_txn_ratio":      0.22,
        "cash_usage":           0.45,
        "merchant_categories":  [
            ("TELECOM",0.5),("GROCERY",1),("P2P_TRANSFER",2),
            ("CASH",2),("DINING",0.5),
        ],
        "has_rent":             0.55,
    },

    "new_to_banking": {
        "description":          "Recently opened account, very little history",
        "weight":               0.08,
        "expected_score_range": (350, 520),
        "monthly_income":       (6000, 18000),
        "income_type":          "MIXED",
        "income_day_range":     (1, 20),
        "income_consistency":   0.65,
        "income_variation":     0.30,
        "monthly_txn_count":    (5, 15),       # very low activity
        "recharge_probability": 0.70,
        "recharge_same_amount": False,
        "bills_paid_rate":      0.55,
        "savings_rate":         (0.02, 0.10),
        "has_sip":              False,
        "has_insurance":        False,
        "emi_probability":      0.05,
        "emi_to_income_ratio":  (0.05, 0.15),
        "spike_probability":    0.15,
        "failed_txn_rate":      0.08,
        "night_txn_ratio":      0.12,
        "cash_usage":           0.60,          # still prefers cash
        "merchant_categories":  [
            ("TELECOM",0.8),("GROCERY",1.5),("DINING",1),
            ("CASH",2),
        ],
        "has_rent":             0.40,
        "account_age_months_override": (1, 6),  # brand new account
    },
}


# ═══════════════════════════════════════════════════════════════
# SECTION 3 — REALISTIC TRANSACTION GENERATOR
# ═══════════════════════════════════════════════════════════════

def get_random_time(night_probability=0.08):
    """Generates a realistic transaction timestamp."""
    is_night = random.random() < night_probability

    if is_night:
        hour = random.choices(
            [22, 23, 0, 1, 2, 3],
            weights=[25, 25, 20, 15, 10, 5]
        )[0]
    else:
        # Peak hours weighted realistically
        hour = random.choices(
            list(range(24)),
            weights=[1,1,1,1,1,2,3,5,7,8,8,7,
                     8,8,7,6,7,8,9,8,6,5,4,2]
        )[0]

    return f"{hour:02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"


def get_merchant(category, profile=None):
    """Returns (merchant_name, amount, mode) for a category."""
    merchants = MERCHANT_DB.get(category, MERCHANT_DB["DINING"])
    entry     = random.choice(merchants)

    if category == "P2P_TRANSFER":
        name   = entry[0]
        amount = round(random.uniform(100, 3000), 0)
        mode   = "UPI"

    elif category in ["SALARY", "GOVERNMENT"]:
        name   = entry[0]
        amount = None  # set by caller
        mode   = random.choice(["NEFT", "IMPS"]) \
                 if category == "SALARY" else "NEFT"

    elif category == "CASH":
        name   = entry[0]
        amounts= [500,1000,2000,3000,5000,10000]
        amount = random.choice(amounts)
        mode   = "ATM"

    else:
        name, amounts, _ = entry
        if amounts:
            base   = random.choice(amounts)
            # Add ±8% realistic variation
            amount = round(base * random.uniform(0.92, 1.08), 2)
        else:
            amount = round(random.uniform(100, 1000), 2)

        # Mode based on category
        if category in ["UTILITY", "EMI"]:
            mode = random.choice(["UPI", "NACH", "NEFT"])
        else:
            mode = "UPI"

    return name, amount, mode


def generate_income_transactions(archetype_name, profile,
                                 month_start, base_income,
                                 txn_counter):
    """Generates income/credit transactions for one month."""
    transactions = []
    income_type  = profile["income_type"]

    # Check if income arrives this month
    consistency = profile["income_consistency"]
    if random.random() > consistency:
        return transactions, txn_counter  # no income this month

    # Income amount with variation
    variation    = profile["income_variation"]
    income_amount= base_income * random.uniform(
        1 - variation, 1 + variation * 0.5
    )
    income_amount= round(income_amount, 2)

    if income_type == "SALARY":
        # Single salary credit early month
        day    = random.randint(*profile["income_day_range"])
        date   = month_start + timedelta(days=day - 1)
        merchant, _, mode = get_merchant("SALARY")

        transactions.append({
            "date":             date.strftime("%Y-%m-%d"),
            "time":             get_random_time(0.02),
            "amount":           income_amount,
            "type":             "CREDIT",
            "mode":             mode,
            "merchantName":     merchant,
            "merchantCategory": "SALARY",
            "transactionStatus": "SUCCESS",
            "remarks":          f"SALARY/{month_start.strftime('%b%Y').upper()}",
        })
        txn_counter += 1

    elif income_type in ["GIG", "DAILY_WAGE", "BUSINESS"]:
        # Multiple small credits throughout month
        num_credits = random.randint(4, 15)
        for _ in range(num_credits):
            day     = random.randint(1, 28)
            date    = month_start + timedelta(days=day - 1)
            amount  = round(income_amount / num_credits
                            * random.uniform(0.7, 1.4), 2)
            merchant, _, mode = get_merchant("SALARY")

            transactions.append({
                "date":             date.strftime("%Y-%m-%d"),
                "time":             get_random_time(0.15),
                "amount":           amount,
                "type":             "CREDIT",
                "mode":             "UPI",
                "merchantName":     merchant,
                "merchantCategory": "SALARY",
                "transactionStatus": "SUCCESS",
                "remarks":          f"UPI/PAYMENT/{day}",
            })
            txn_counter += 1

    elif income_type == "TRANSFER":
        # Family transfer
        day    = random.randint(*profile["income_day_range"])
        date   = month_start + timedelta(days=day - 1)
        sender = random.choice(["Father", "Husband",
                                 "Brother", "Mother"])
        transactions.append({
            "date":             date.strftime("%Y-%m-%d"),
            "time":             get_random_time(0.05),
            "amount":           income_amount,
            "type":             "CREDIT",
            "mode":             "UPI",
            "merchantName":     sender,
            "merchantCategory": "P2P_TRANSFER",
            "transactionStatus": "SUCCESS",
            "remarks":          f"UPI/FAMILY/TRANSFER",
        })
        txn_counter += 1

    elif income_type == "SEASONAL":
        # Only some months have income
        if random.random() < 0.60:  # 60% months have income
            day  = random.randint(1, 28)
            date = month_start + timedelta(days=day - 1)
            merchant, _, _ = get_merchant("SALARY")
            transactions.append({
                "date":             date.strftime("%Y-%m-%d"),
                "time":             get_random_time(0.10),
                "amount":           income_amount,
                "type":             "CREDIT",
                "mode":             "NEFT",
                "merchantName":     merchant,
                "merchantCategory": "SALARY",
                "transactionStatus": "SUCCESS",
                "remarks":          "SEASONAL/WAGES",
            })
            txn_counter += 1

    else:  # MIXED / IRREGULAR
        # Unpredictable mix
        num_credits = random.randint(1, 5)
        for _ in range(num_credits):
            day    = random.randint(1, 28)
            date   = month_start + timedelta(days=day - 1)
            amount = round(income_amount / num_credits
                           * random.uniform(0.5, 1.5), 2)
            merchant, _, _ = get_merchant("SALARY")
            transactions.append({
                "date":             date.strftime("%Y-%m-%d"),
                "time":             get_random_time(0.12),
                "amount":           amount,
                "type":             "CREDIT",
                "mode":             random.choice(["UPI","NEFT","IMPS"]),
                "merchantName":     merchant,
                "merchantCategory": "SALARY",
                "transactionStatus": "SUCCESS",
                "remarks":          "MISC/INCOME",
            })
            txn_counter += 1

    return transactions, txn_counter


def generate_user_transactions(archetype_name, profile,
                               months=3):
    """
    Generates complete 3-month transaction history
    for one user. Returns list of transaction dicts.
    """
    all_transactions = []
    txn_counter      = 1

    # Base income for this user
    base_income = random.uniform(*profile["monthly_income"])

    # Starting balance
    current_balance = random.uniform(300, 8000)

    # Start 3 months ago
    today       = datetime.now().replace(hour=0, minute=0,
                                          second=0, microsecond=0)
    start_date  = today - timedelta(days=months * 30)
    start_date  = start_date.replace(day=1)

    for month_num in range(months):
        month_start = start_date + timedelta(days=month_num * 30)

        # ── INCOME ─────────────────────────────────────────
        income_txns, txn_counter = generate_income_transactions(
            archetype_name, profile, month_start,
            base_income, txn_counter
        )

        for t in income_txns:
            current_balance += t["amount"]
            t["currentBalance"] = round(current_balance, 2)
            t["id"] = f"TXN{txn_counter:06d}"
            t["reference"] = f"REF{random.randint(10**9, 10**10-1)}"
            t.setdefault("transactionStatus", "SUCCESS")
            txn_counter += 1

        all_transactions.extend(income_txns)

        # ── RECHARGE ───────────────────────────────────────
        if random.random() < profile["recharge_probability"]:
            merchant, amount, mode = get_merchant("TELECOM")

            # Same amount every month if consistent
            if profile["recharge_same_amount"] and month_num > 0:
                # Find last month's recharge amount
                prev = [t for t in all_transactions
                        if t.get("merchantCategory") == "TELECOM"]
                if prev:
                    amount = prev[-1]["amount"]

            day    = random.randint(1, 28)
            date   = month_start + timedelta(days=day - 1)
            is_failed = random.random() < profile["failed_txn_rate"]

            if not is_failed:
                current_balance -= amount

            all_transactions.append({
                "id":              f"TXN{txn_counter:06d}",
                "date":            date.strftime("%Y-%m-%d"),
                "time":            get_random_time(0.03),
                "amount":          round(amount, 2),
                "type":            "DEBIT",
                "mode":            "UPI",
                "currentBalance":  round(max(0, current_balance), 2),
                "merchantName":    merchant,
                "merchantCategory":"TELECOM",
                "transactionStatus":"FAILED" if is_failed else "SUCCESS",
                "remarks":         f"UPI/{merchant.replace(' ','_')}/PREPAID",
                "reference":       f"REF{random.randint(10**9,10**10-1)}",
            })
            txn_counter += 1

        # ── UTILITY BILLS ──────────────────────────────────
        expected_bills = 2.5  # electricity + water + gas
        actual_bills   = int(expected_bills * profile["bills_paid_rate"]
                             * random.uniform(0.8, 1.2))
        actual_bills   = max(0, min(4, actual_bills))

        for _ in range(actual_bills):
            merchant, amount, mode = get_merchant("UTILITY")
            day  = random.randint(5, 25)
            date = month_start + timedelta(days=day - 1)
            current_balance -= amount

            all_transactions.append({
                "id":               f"TXN{txn_counter:06d}",
                "date":             date.strftime("%Y-%m-%d"),
                "time":             get_random_time(0.02),
                "amount":           round(amount, 2),
                "type":             "DEBIT",
                "mode":             mode,
                "currentBalance":   round(max(0, current_balance), 2),
                "merchantName":     merchant,
                "merchantCategory": "UTILITY",
                "transactionStatus":"SUCCESS",
                "remarks":          f"BILL/{merchant.replace(' ','_')}/PAYMENT",
                "reference":        f"REF{random.randint(10**9,10**10-1)}",
            })
            txn_counter += 1

        # ── RENT ───────────────────────────────────────────
        if random.random() < profile.get("has_rent", 0.5):
            merchant, amount, mode = get_merchant("RENT")
            rent_amount = random.choice([3000,4000,5000,6000,
                                          7000,8000,10000,12000])
            day  = random.randint(1, 5)  # paid early month
            date = month_start + timedelta(days=day - 1)
            current_balance -= rent_amount

            all_transactions.append({
                "id":               f"TXN{txn_counter:06d}",
                "date":             date.strftime("%Y-%m-%d"),
                "time":             get_random_time(0.03),
                "amount":           float(rent_amount),
                "type":             "DEBIT",
                "mode":             "UPI",
                "currentBalance":   round(max(0, current_balance), 2),
                "merchantName":     merchant,
                "merchantCategory": "RENT",
                "transactionStatus":"SUCCESS",
                "remarks":          "UPI/RENT/MONTHLY",
                "reference":        f"REF{random.randint(10**9,10**10-1)}",
            })
            txn_counter += 1

        # ── EMI ────────────────────────────────────────────
        if random.random() < profile["emi_probability"]:
            merchant, _, _ = get_merchant("EMI")
            emi_amount = round(
                base_income * random.uniform(*profile["emi_to_income_ratio"])
            , 0)
            day  = random.randint(3, 7)
            date = month_start + timedelta(days=day - 1)
            current_balance -= emi_amount

            all_transactions.append({
                "id":               f"TXN{txn_counter:06d}",
                "date":             date.strftime("%Y-%m-%d"),
                "time":             get_random_time(0.02),
                "amount":           emi_amount,
                "type":             "DEBIT",
                "mode":             "NACH",
                "currentBalance":   round(max(0, current_balance), 2),
                "merchantName":     merchant,
                "merchantCategory": "EMI",
                "transactionStatus":"SUCCESS",
                "remarks":          f"NACH/EMI/{merchant.replace(' ','_')}",
                "reference":        f"REF{random.randint(10**9,10**10-1)}",
            })
            txn_counter += 1

        # ── INSURANCE / SIP ────────────────────────────────
        if profile.get("has_sip") and random.random() < 0.90:
            sip_amount = random.choice([500,1000,2000,3000,5000])
            day  = random.randint(5, 10)
            date = month_start + timedelta(days=day - 1)
            current_balance -= sip_amount

            all_transactions.append({
                "id":               f"TXN{txn_counter:06d}",
                "date":             date.strftime("%Y-%m-%d"),
                "time":             get_random_time(0.02),
                "amount":           float(sip_amount),
                "type":             "DEBIT",
                "mode":             "NACH",
                "currentBalance":   round(max(0, current_balance), 2),
                "merchantName":     "Mutual Fund SIP",
                "merchantCategory": "FINANCIAL",
                "transactionStatus":"SUCCESS",
                "remarks":          "NACH/SIP/MUTUAL_FUND",
                "reference":        f"REF{random.randint(10**9,10**10-1)}",
            })
            txn_counter += 1

        # ── DAILY TRANSACTIONS ─────────────────────────────
        daily_count = random.randint(*profile["monthly_txn_count"])

        for _ in range(daily_count):
            # Pick category weighted by profile
            categories = profile["merchant_categories"]
            cat_names  = [c[0] for c in categories]
            cat_weights= [c[1] for c in categories]
            category   = random.choices(cat_names,
                                         weights=cat_weights)[0]

            merchant, amount, mode = get_merchant(category)

            if amount is None:
                amount = round(random.uniform(100, 2000), 2)

            # Spending spike
            if random.random() < profile["spike_probability"]:
                amount = round(amount * random.uniform(2.0, 4.5), 2)

            # Night transaction
            is_night  = random.random() < profile["night_txn_ratio"]
            is_failed = random.random() < profile["failed_txn_rate"]

            day  = random.randint(1, 28)
            date = month_start + timedelta(days=day - 1)

            # Cash usage — some transactions are cash (no UPI)
            if random.random() < profile["cash_usage"] \
               and category not in ["EMI","UTILITY","TELECOM"]:
                # Skip — cash transaction, not on UPI
                continue

            if not is_failed:
                current_balance -= amount
            else:
                # Failed — no balance change but record it
                pass

            txn_type = "CREDIT" if category in ["SALARY","GOVERNMENT"] \
                       and random.random() < 0.1 else "DEBIT"

            all_transactions.append({
                "id":               f"TXN{txn_counter:06d}",
                "date":             date.strftime("%Y-%m-%d"),
                "time":             get_random_time(
                                        profile["night_txn_ratio"]
                                        if is_night else 0.05
                                    ),
                "amount":           round(amount, 2),
                "type":             txn_type,
                "mode":             mode,
                "currentBalance":   round(max(-500, current_balance), 2),
                "merchantName":     merchant,
                "merchantCategory": category,
                "transactionStatus":"FAILED" if is_failed else "SUCCESS",
                "remarks":          f"UPI/{merchant.replace(' ','_')}/{category}",
                "reference":        f"REF{random.randint(10**9,10**10-1)}",
            })
            txn_counter += 1

    # Sort chronologically
    all_transactions.sort(key=lambda x: (x["date"], x["time"]))

    # Re-assign sequential IDs
    for i, t in enumerate(all_transactions, 1):
        t["id"] = f"TXN{i:06d}"

    return all_transactions


# ═══════════════════════════════════════════════════════════════
# SECTION 4 — AA JSON BUILDER
# Wraps transactions in exact Setu/AA framework format
# ═══════════════════════════════════════════════════════════════

BANKS = {
    "disciplined_salaried":   ("HDFC Bank",    "HDFC"),
    "consistent_gig_worker":  ("SBI",          "SBIN"),
    "small_business_owner":   ("Canara Bank",  "CNRB"),
    "stable_auto_driver":     ("SBI",          "SBIN"),
    "factory_worker":         ("Indian Bank",  "IDIB"),
    "irregular_daily_wage":   ("SBI",          "SBIN"),
    "college_student":        ("SBI",          "SBIN"),
    "housewife_managing":     ("Indian Bank",  "IDIB"),
    "over_indebted":          ("Axis Bank",    "UTIB"),
    "seasonal_migrant_worker":("Bank of India","BKID"),
    "financially_stressed":   ("UCO Bank",     "UCBA"),
    "new_to_banking":         ("Paytm Bank",   "PYTM"),
}

BRANCHES = [
    "Chennai Central", "Coimbatore RS Puram", "Madurai Main",
    "Trichy Cantonment", "Salem Junction", "Tirunelveli Court",
    "Bangalore Koramangala", "Bangalore Jayanagar", "Mysore Main",
    "Mumbai Andheri East", "Mumbai Dadar", "Pune Camp",
    "Hyderabad Secunderabad", "Vijayawada Besant Road",
    "Delhi Connaught Place", "Noida Sector 18",
    "Kolkata Park Street", "Ahmedabad CG Road",
]


def build_aa_json(user_index, archetype_name, profile, transactions):
    """Builds exact AA framework JSON for one user."""

    if not transactions:
        return None

    credits = [t for t in transactions
               if t["type"] == "CREDIT"
               and t["transactionStatus"] == "SUCCESS"]
    debits  = [t for t in transactions
               if t["type"] == "DEBIT"
               and t["transactionStatus"] == "SUCCESS"]
    failed  = [t for t in transactions
               if t["transactionStatus"] == "FAILED"]

    total_credits = round(sum(t["amount"] for t in credits), 2)
    total_debits  = round(sum(t["amount"] for t in debits), 2)
    months        = 3

    bank_name, bank_code = BANKS.get(
        archetype_name, ("SBI", "SBIN")
    )

    # Account age
    if "account_age_months_override" in profile:
        age_months = random.randint(
            *profile["account_age_months_override"]
        )
    else:
        age_months = random.randint(6, 60)

    opening_date = (
        datetime.now() - timedelta(days=age_months * 30)
    ).strftime("%Y-%m-%d")

    account_num = f"XXXX{random.randint(1000, 9999)}"
    ifsc        = f"{bank_code}000{random.randint(1000, 9999)}"

    current_balance = transactions[-1].get("currentBalance", 0) \
                      if transactions else 0

    return {
        "consentId":  f"CONSENT-{user_index:05d}-{random.randint(10000,99999)}",
        "customerId": f"USER_{user_index:05d}",
        "fetchedAt":  datetime.now().isoformat(),
        "dataRange": {
            "from": transactions[0]["date"] if transactions else "",
            "to":   transactions[-1]["date"] if transactions else "",
        },
        "account": {
            "id":             f"ACC{random.randint(100000,999999)}",
            "type":           "SAVINGS",
            "bank":           bank_name,
            "branch":         random.choice(BRANCHES),
            "ifsc":           ifsc,
            "accountNumber":  account_num,
            "openingDate":    opening_date,
            "accountAgeMonths": age_months,
            "currentBalance": round(current_balance, 2),
            "currency":       "INR",
            "nominee":        random.choice(["REGISTERED","NOT_REGISTERED"]),
        },
        "summary": {
            "totalCredits":           total_credits,
            "totalDebits":            total_debits,
            "netSavings":             round(total_credits - total_debits, 2),
            "averageMonthlyCredit":   round(total_credits / months, 2),
            "averageMonthlyDebit":    round(total_debits / months, 2),
            "totalTransactions":      len(transactions),
            "successfulTransactions": len(credits) + len(debits),
            "failedTransactions":     len(failed),
            "failedTransactionRate":  round(
                len(failed) / len(transactions), 4
            ) if transactions else 0,
            "uniqueMerchants":        len(set(
                t["merchantName"] for t in transactions
            )),
            "uniqueCategories":       len(set(
                t["merchantCategory"] for t in transactions
            )),
            "periodMonths":           months,
        },
        "transactions": transactions,
        # Metadata for training only — removed in production
        "_meta": {
            "archetype":           archetype_name,
            "archetypeDescription":profile["description"],
            "expectedScoreRange":  profile["expected_score_range"],
        }
    }


# ═══════════════════════════════════════════════════════════════
# SECTION 5 — DEMO PERSONAS
# Fixed profiles for Ramesh, Priya, Arjun
# ═══════════════════════════════════════════════════════════════

def build_demo_personas(all_profiles):
    """Extracts best matching demo personas from generated data."""

    def find_best(archetype, score_range):
        candidates = [
            p for p in all_profiles
            if p["_meta"]["archetype"] == archetype
        ]
        if not candidates:
            return None
        return random.choice(candidates[:5])

    ramesh = find_best("irregular_daily_wage", (380, 480))
    priya  = find_best("disciplined_salaried",  (780, 880))
    arjun  = find_best("college_student",        (380, 500))

    return {
        "ramesh": ramesh,
        "priya":  priya,
        "arjun":  arjun,
    }


# ═══════════════════════════════════════════════════════════════
# SECTION 6 — MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":

    os.makedirs("ml/data/aa_profiles", exist_ok=True)

    print("=" * 60)
    print("  CREDITGHOST — ULTRA-REALISTIC DATA GENERATOR")
    print("  500 Users · 12 Archetypes · AA Format")
    print("=" * 60)

    # Pick 500 archetypes by weight
    archetype_names = list(ARCHETYPES.keys())
    weights         = [ARCHETYPES[a]["weight"] for a in archetype_names]

    selected = random.choices(archetype_names, weights=weights, k=500)

    all_profiles  = []
    counts        = {}
    total_txns    = 0

    for i, archetype_name in enumerate(selected):
        profile      = ARCHETYPES[archetype_name]
        transactions = generate_user_transactions(
            archetype_name, profile, months=3
        )
        aa_json = build_aa_json(i + 1, archetype_name,
                                profile, transactions)

        if aa_json:
            all_profiles.append(aa_json)
            total_txns += len(transactions)
            counts[archetype_name] = counts.get(archetype_name, 0) + 1

        if (i + 1) % 100 == 0:
            print(f"  ✓ Generated {i+1}/500 users...")

    # Save all profiles
    main_path = "ml/data/aa_profiles/all_users.json"
    with open(main_path, "w") as f:
        json.dump(all_profiles, f, indent=2)

    # Save demo personas
    demos      = build_demo_personas(all_profiles)
    demo_path  = "ml/data/demo_personas.json"
    with open(demo_path, "w") as f:
        json.dump(demos, f, indent=2)

    # Save one sample for inspection
    sample_path = "ml/data/sample_single_user.json"
    with open(sample_path, "w") as f:
        json.dump(all_profiles[0], f, indent=2)

    # Print stats
    avg_txns = total_txns // len(all_profiles) if all_profiles else 0

    print(f"\n{'='*60}")
    print(f"  ✅ SUCCESS: {len(all_profiles)} profiles generated")
    print(f"{'='*60}")
    print(f"\n  📊 ARCHETYPE DISTRIBUTION:")
    for arch in archetype_names:
        count = counts.get(arch, 0)
        bar   = '█' * (count // 3)
        desc  = ARCHETYPES[arch]['description'][:35]
        score = ARCHETYPES[arch]['expected_score_range']
        print(f"  {arch:28s} {bar:12s} {count:3d}"
              f"  Score:{score[0]}-{score[1]}")

    print(f"\n  📈 TRANSACTION STATS:")
    print(f"  Total transactions generated : {total_txns:,}")
    print(f"  Average per user             : {avg_txns}")
    print(f"  Merchant categories used     : {len(MERCHANT_DB)}")
    print(f"  Unique merchants in DB       : "
          f"{sum(len(v) for v in MERCHANT_DB.values())}")

    print(f"\n  📁 OUTPUT FILES:")
    print(f"  {main_path}")
    print(f"  {demo_path}")
    print(f"  {sample_path}")
    print(f"\n  💡 Each profile format: Exact Setu/AA JSON")
    print(f"     Ready for your scoring formula + mock AA flow")
    print(f"{'='*60}")
