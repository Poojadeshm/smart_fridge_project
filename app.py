from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, date, timedelta
from translations import TRANSLATIONS, LANG_NAMES
from functools import wraps
import json, os

app = Flask(__name__)
app.secret_key = "shelfwise2025"
DATA_FILE = "products.json"

# Simple user database (in production, use proper database and password hashing)
USERS = {
    "admin": "admin123",
    "user": "user123"
}

# ── SHELF LIFE (days) ──────────────────────────────────────────────────────
SHELF_LIFE = {
    "milk":3,"doodh":3,"dudh":3,"cream":5,"butter":30,"cheese":14,
    "paneer":4,"yogurt":7,"dahi":5,"curd":5,"bread":6,"pav":4,"roti":2,
    "egg":21,"anda":21,"inda":21,"chicken":2,"mutton":2,"fish":2,
    "tomato":5,"tamatar":5,"onion":30,"pyaz":30,"dungri":30,
    "potato":14,"aloo":14,"batata":14,"carrot":10,"gajar":10,
    "spinach":4,"palak":4,"cabbage":7,"capsicum":7,"broccoli":5,
    "apple":14,"seb":14,"banana":5,"kela":5,"kandu":5,
    "mango":5,"aam":5,"keri":5,"orange":10,"grapes":7,"papaya":5,
    "juice":3,"rice":365,"chawal":365,"flour":180,"atta":180,
    "maida":180,"oil":365,"tel":365,"ghee":180,"sugar":730,
    "cheeni":730,"dal":180,"noodles":180,"maggi":180,"pasta":365,
    "biscuit":90,"chocolate":180,"chips":60,"sauce":30,"ketchup":30,
    "pickle":180,"achar":180,"jam":90,"honey":730,"shehad":730,
    "moisturizer":365,"lotion":365,"sunscreen":180,"face wash":365,
    "toner":365,"serum":365,"scrub":180,"lipstick":365,"lip gloss":180,
    "foundation":180,"concealer":365,"mascara":90,"kajal":180,
    "eyeliner":180,"eyeshadow":730,"shampoo":365,"conditioner":365,
    "hair oil":365,"body wash":365,"soap":365,"deodorant":365,
    "perfume":730,"nail polish":365,"tablet":365,"capsule":365,
    "syrup":180,"ointment":365,"tea":730,"coffee":365,"oats":365,
    "default_Food":7,"default_Cosmetics":365,
    "default_Medicine":365,"default_Groceries":90,"default_Jewelry":730,
}

JEWELRY_OXIDATION = {
    "silver":{"icon":"🥈","stages":[
        {"days":0,  "en":"Brand New",    "hi":"बिल्कुल नया",    "gu":"બિલ્કુલ નવું",    "color_en":"Brilliant silver shine",    "color_hi":"चमकदार चांदी",           "color_gu":"ચળકતી ચાંદી",           "pct":100,"dot":"#e8e8e8",
         "care_en":"Keep in anti-tarnish pouch. Avoid moisture.",
         "care_hi":"एंटी-टार्निश पाउच में रखें। नमी से बचाएं।",
         "care_gu":"એન્ટી-ટાર્નિશ પાઉચમાં રાખો. ભેજથી બચાવો."},
        {"days":30, "en":"Slight Dull",  "hi":"थोड़ी फीकी",     "gu":"થોડી ઝાંખી",      "color_en":"Slightly less bright",     "color_hi":"थोड़ी कम चमकदार",        "color_gu":"થોડી ઓછી ચળકાટ",       "pct":85,"dot":"#d4d4c0",
         "care_en":"Wipe with soft cloth. Store with silica gel.",
         "care_hi":"मुलायम कपड़े से पोंछें। सिलिका जेल के साथ रखें।",
         "care_gu":"નરમ કપડાથી સાફ કરો. સિલિકા જેલ સાથે રાખો."},
        {"days":90, "en":"Light Tarnish","hi":"हल्का कालापन",   "gu":"હળવો કાળો ડાઘ",  "color_en":"Yellowish tint appearing", "color_hi":"पीलापन आने लगा",         "color_gu":"પીળાશ આવવા લાગી",      "pct":65,"dot":"#c8c0a0",
         "care_en":"Polish with silver cloth. Baking soda + water paste.",
         "care_hi":"सिल्वर क्लॉथ से पॉलिश करें। बेकिंग सोडा + पानी का पेस्ट।",
         "care_gu":"સિલ્વર ક્લૉથથી પૉલિશ કરો. બેકિંગ સોડા + પાણીનો પેસ્ટ."},
        {"days":180,"en":"Tarnishing",   "hi":"काली पड़ रही है", "gu":"કાળી પડી રહી છે","color_en":"Yellow-brown patches",     "color_hi":"पीले-भूरे धब्बे",        "color_gu":"પીળા-ભૂરા ડાઘ",        "pct":45,"dot":"#b0a070",
         "care_en":"Soak in lemon juice + salt 10 mins.",
         "care_hi":"नींबू के रस + नमक में 10 मिनट भिगोएं।",
         "care_gu":"લીંબુ + મીઠામાં 10 મિનિટ બોળો."},
        {"days":270,"en":"Heavy Tarnish","hi":"बहुत काली",       "gu":"ઘણી કાળી",        "color_en":"Dark brown coating",       "color_hi":"गहरा भूरा लेप",          "color_gu":"ઘેરો ભૂરો ડાઘ",        "pct":25,"dot":"#806040",
         "care_en":"Professional cleaning or aluminum foil + baking soda bath.",
         "care_hi":"प्रोफेशनल सफाई या एल्युमिनियम फॉयल + बेकिंग सोडा।",
         "care_gu":"પ્રૉફેશનલ સફાઈ અથવા અૅલ્યૂમિનિયમ ફૉઇલ + બેકિંગ સોડા."},
        {"days":365,"en":"Oxidized",     "hi":"पूरी काली",       "gu":"સંપૂર્ણ કાળી",    "color_en":"Fully black oxidized",     "color_hi":"पूरी तरह काली",          "color_gu":"સંપૂર્ણ કાળી",         "pct":10,"dot":"#333",
         "care_en":"Immediate professional polish or silver dip cleaner.",
         "care_hi":"तुरंत प्रोफेशनल पॉलिश या सिल्वर डिप क्लीनर।",
         "care_gu":"તુરત પ્રૉફેશનલ પૉલિશ અથવા સિલ્વર ડિપ ક્લીનર."},
    ]},
    "gold":{"icon":"🥇","stages":[
        {"days":0,  "en":"Brand New",  "hi":"बिल्कुल नया","gu":"બિલ્કુલ નવું","color_en":"Brilliant warm gold","color_hi":"चमकदार सोना","color_gu":"ચળકતું સોનું","pct":100,"dot":"#f0d060",
         "care_en":"Avoid harsh chemicals. Remove before swimming.",
         "care_hi":"कठोर रसायनों से बचें। तैरने से पहले उतारें।",
         "care_gu":"કઠોર રસાયણોથી બચો. તરવા પહેલાં ઉતારો."},
        {"days":60, "en":"Slight Dull","hi":"थोड़ी फीकी","gu":"થોડી ઝાંખી","color_en":"Minor dust/oils","color_hi":"थोड़ी धूल/तेल","color_gu":"થોડી ધૂળ/તેલ","pct":88,"dot":"#d4b848",
         "care_en":"Wipe with soft lint-free cloth after each wear.",
         "care_hi":"हर बार पहनने के बाद मुलायम कपड़े से पोंछें।",
         "care_gu":"દર વખત પહેર્યા પછી નરમ કપડાથી સાફ કરો."},
        {"days":180,"en":"Dull Sheen", "hi":"फीकी चमक","gu":"ઝાંખી ચળકાટ","color_en":"Less reflective","color_hi":"कम चमकदार","color_gu":"ઓછી ચળકાટ","pct":72,"dot":"#c09830",
         "care_en":"Warm soapy water with soft brush. Pat dry.",
         "care_hi":"गर्म साबुन के पानी से नरम ब्रश से साफ करें।",
         "care_gu":"ગરમ સાબુ પાણીથી નરમ બ્રશ વડે સાફ કરો."},
        {"days":365,"en":"Worn Look",  "hi":"पुरानी लग रही है","gu":"જૂની લાગે છે","color_en":"Oils built up, dull","color_hi":"तेल जमा, फीकी","color_gu":"તેલ જામ્યું, ઝાંખી","pct":55,"dot":"#a07820",
         "care_en":"Professional ultrasonic cleaning recommended.",
         "care_hi":"प्रोफेशनल अल्ट्रासोनिक सफाई की सलाह।",
         "care_gu":"પ્રૉફેશનલ અલ્ટ્રાસોનિક સફાઈ ભલામણ."},
        {"days":730,"en":"Faded","hi":"बहुत फीकी","gu":"ઘણી ઝાંખી","color_en":"Base metal showing (if plated)","color_hi":"नीचे की धातु दिख रही है","color_gu":"નીચેની ધાતુ દેખાય છે","pct":30,"dot":"#806010",
         "care_en":"Re-plating may be needed for gold-plated jewelry.",
         "care_hi":"गोल्ड-प्लेटेड के लिए री-प्लेटिंग की जरूरत हो सकती है।",
         "care_gu":"ગૉલ્ડ-પ્લેટેડ માટે ફરી પ્લેટિંગ કરાવવી પડે."},
    ]},
    "copper":{"icon":"🟤","stages":[
        {"days":0,  "en":"Brand New","hi":"बिल्कुल नया","gu":"બિલ્કુલ નવું","color_en":"Bright reddish-orange","color_hi":"चमकदार लाल-नारंगी","color_gu":"ચળકતો લાલ-નારંગી","pct":100,"dot":"#e07040",
         "care_en":"Apply clear nail polish to slow oxidation.",
         "care_hi":"ऑक्सीडेशन धीमा करने के लिए क्लियर नेल पॉलिश लगाएं।",
         "care_gu":"ઑક્સિડેશન ધીમું કરવા ક્લિયર નેઇલ પૉલિશ લગાવો."},
        {"days":45, "en":"Browning","hi":"भूरा पड़ रहा है","gu":"ભૂરો પડી રહ્યો છે","color_en":"Brown patches forming","color_hi":"भूरे धब्बे बन रहे हैं","color_gu":"ભૂરા ડાઘ પડવા લાગ્યા","pct":55,"dot":"#904020",
         "care_en":"Lemon + salt rub, rinse and dry immediately.",
         "care_hi":"नींबू + नमक रगड़ें, तुरंत धोएं और सुखाएं।",
         "care_gu":"લીંબુ + મીઠું ઘસો, તરત ધોઈ સૂકવો."},
        {"days":180,"en":"Green Patina","hi":"हरा हो गया","gu":"લીલો થઈ ગયો","color_en":"Green-blue verdigris","color_hi":"हरा-नीला रंग","color_gu":"લીલો-વાદળી રંગ","pct":15,"dot":"#406040",
         "care_en":"White vinegar + salt paste, scrub gently.",
         "care_hi":"सफेद सिरका + नमक का पेस्ट, धीरे से रगड़ें।",
         "care_gu":"સફેદ સરકો + મીઠાનો પેસ્ટ, હળવેથી ઘસો."},
    ]},
    "brass":{"icon":"🔶","stages":[
        {"days":0,  "en":"Brand New","hi":"बिल्कुल नया","gu":"બિલ્કુલ નવું","color_en":"Bright yellow-gold","color_hi":"चमकदार पीला-सोना","color_gu":"ચળકતું પીળું-સોનું","pct":100,"dot":"#e8c040",
         "care_en":"Lacquer coating extends life significantly.",
         "care_hi":"लैकर कोटिंग जीवन काफी बढ़ाती है।",
         "care_gu":"લૅકર કોટિંગ આયુ ઘણી વધારે છે."},
        {"days":90, "en":"Tarnishing","hi":"काली पड़ रही है","gu":"કાળી પડી રહી છે","color_en":"Darker yellow-brown","color_hi":"गहरा पीला-भूरा","color_gu":"ઘેરો પીળો-ભૂરો","pct":55,"dot":"#a07820",
         "care_en":"Lemon juice + baking soda paste, rinse well.",
         "care_hi":"नींबू का रस + बेकिंग सोडा पेस्ट, अच्छे से धोएं।",
         "care_gu":"લીંબુ + બેકિંગ સોડા પેસ્ટ, સારી રીતે ધોઓ."},
        {"days":365,"en":"Oxidized","hi":"पूरी काली","gu":"સંપૂર્ણ કાળી","color_en":"Dark brown/black","color_hi":"गहरा भूरा/काला","color_gu":"ઘેરો ભૂરો/કાળો","pct":15,"dot":"#404010",
         "care_en":"Brasso or Flitz metal polish for heavy tarnish.",
         "care_hi":"भारी कालेपन के लिए Brasso या Flitz पॉलिश।",
         "care_gu":"ભારે ડાઘ માટે Brasso અથવા Flitz પૉલિશ."},
    ]},
}

RECIPES = {
    "milk":  [{"name_en":"Kheer","name_hi":"खीर","name_gu":"ખીર","time":"30 min","emoji":"🍚","ingredients":"Milk, Rice, Sugar, Cardamom","tip_en":"Use full-fat milk for creamier texture.","tip_hi":"मलाईदार खीर के लिए फुल-फैट दूध इस्तेमाल करें।","tip_gu":"ક્રીમી ખીર માટે ફુલ-ફેટ દૂધ વાપરો."},
              {"name_en":"Homemade Paneer","name_hi":"घर का पनीर","name_gu":"ઘરનું પનીર","time":"20 min","emoji":"🧀","ingredients":"Milk, Lemon juice","tip_en":"Boil milk, add lemon, strain through muslin.","tip_hi":"दूध उबालें, नींबू डालें, मलमल से छानें।","tip_gu":"દૂધ ઉકાળો, લીંબુ નાખો, મસ્લિનથી ગાળો."},
              {"name_en":"Chai","name_hi":"चाय","name_gu":"ચા","time":"5 min","emoji":"☕","ingredients":"Milk, Tea leaves, Sugar, Ginger","tip_en":"Add cardamom for masala chai flavor.","tip_hi":"मसाला चाय के लिए इलायची डालें।","tip_gu":"મસાલા ચા માટે એલચી ઉમેરો."},
              {"name_en":"White Sauce Pasta","name_hi":"व्हाइट सॉस पास्ता","name_gu":"વ્હાઇટ સૉસ પાસ્તા","time":"25 min","emoji":"🍝","ingredients":"Milk, Butter, Flour, Pasta, Cheese","tip_en":"Stir continuously to avoid lumps.","tip_hi":"गांठ से बचने के लिए लगातार हिलाते रहें।","tip_gu":"ગઠ્ઠા ટાળવા સતત હલાવો."}],
    "bread": [{"name_en":"French Toast","name_hi":"फ्रेंच टोस्ट","name_gu":"ફ્રેન્ચ ટોસ્ટ","time":"10 min","emoji":"🍞","ingredients":"Bread, Egg, Milk, Sugar, Cinnamon","tip_en":"Soak bread 30 seconds each side.","tip_hi":"ब्रेड को दोनों तरफ 30 सेकंड भिगोएं।","tip_gu":"બ્રેડ બંને બાજુ 30 સેકન્ડ ડૂબાડો."},
               {"name_en":"Bread Upma","name_hi":"ब्रेड उपमा","name_gu":"બ્રેડ ઉપમા","time":"15 min","emoji":"🫓","ingredients":"Bread, Onion, Tomato, Mustard, Curry leaves","tip_en":"Toast bread cubes separately first.","tip_hi":"ब्रेड क्यूब्स पहले अलग से टोस्ट करें।","tip_gu":"બ્રેડ ક્યૂબ્સ પહેલાં અલગ ટોસ્ટ કરો."},
               {"name_en":"Bread Pakora","name_hi":"ब्रेड पकोड़ा","name_gu":"બ્રેડ ભજિયાં","time":"20 min","emoji":"🟡","ingredients":"Bread, Besan, Potato, Spices, Oil","tip_en":"Add ajwain to batter for digestion.","tip_hi":"पाचन के लिए बेसन में अजवाइन डालें।","tip_gu":"પાચન માટે ખીરામાં અજમો ઉમેરો."}],
    "egg":   [{"name_en":"Masala Omelette","name_hi":"मसाला ऑमलेट","name_gu":"મસાલા ઑમ્લેટ","time":"8 min","emoji":"🍳","ingredients":"Eggs, Onion, Tomato, Green chilli, Coriander","tip_en":"Add a splash of water for fluffier omelette.","tip_hi":"फुलाने के लिए थोड़ा पानी मिलाएं।","tip_gu":"ફ્લફી ઑમ્લેટ માટે થોડું પાણી ઉમેરો."},
               {"name_en":"Egg Bhurji","name_hi":"अंडा भुर्जी","name_gu":"ઇંડા ભૂર્જી","time":"12 min","emoji":"🥘","ingredients":"Eggs, Onion, Tomato, Spices, Butter","tip_en":"Cook on low heat, stir constantly.","tip_hi":"धीमी आंच पर पकाएं, लगातार हिलाते रहें।","tip_gu":"ધીમી આંચ પર રાંધો, સતત હલાવો."}],
    "banana":[{"name_en":"Banana Smoothie","name_hi":"केला स्मूदी","name_gu":"કેળાની સ્મૂધી","time":"5 min","emoji":"🥤","ingredients":"Banana, Milk, Honey, Ice","tip_en":"Freeze overripe bananas for creamier result.","tip_hi":"ज्यादा पके केले फ्रीज करें — क्रीमी होगी।","tip_gu":"વધારે પાકેલ કેળ ફ્રીઝ કરો — ક્રીમી બને."},
               {"name_en":"Banana Pancake","name_hi":"केला पैनकेक","name_gu":"કેળા પૅનકૅક","time":"15 min","emoji":"🥞","ingredients":"Banana, Egg, Oats","tip_en":"Just 3 ingredients — naturally sweet!","tip_hi":"सिर्फ 3 सामग्री — प्राकृतिक रूप से मीठा!","tip_gu":"ફક્ત 3 સામગ્રી — કુદરતી મીઠો!"}],
    "tomato":[{"name_en":"Tomato Soup","name_hi":"टमाटर सूप","name_gu":"ટામેટાનો સૂપ","time":"20 min","emoji":"🍅","ingredients":"Tomatoes, Onion, Garlic, Cream, Basil","tip_en":"Roast tomatoes first for deeper flavor.","tip_hi":"गहरे स्वाद के लिए टमाटर पहले भूनें।","tip_gu":"ઊંડા સ્વાદ માટે ટામેટાં પહેલાં શેકો."},
               {"name_en":"Tomato Chutney","name_hi":"टमाटर चटनी","name_gu":"ટામેટાની ચટણી","time":"15 min","emoji":"🫙","ingredients":"Tomatoes, Garlic, Red chilli, Oil, Mustard","tip_en":"Add tamarind for extra tanginess.","tip_hi":"खट्टापन बढ़ाने के लिए इमली डालें।","tip_gu":"ખટાશ માટે આમલી ઉમેરો."}],
    "yogurt":[{"name_en":"Raita","name_hi":"रायता","name_gu":"રાઈતું","time":"5 min","emoji":"🥗","ingredients":"Yogurt, Cucumber, Cumin, Salt, Coriander","tip_en":"Squeeze out cucumber water before mixing.","tip_hi":"मिलाने से पहले खीरे का पानी निचोड़ें।","tip_gu":"મિક્સ કરતાં પહેલાં કાકડીનું પાણી નિચોવો."},
               {"name_en":"Lassi","name_hi":"लस्सी","name_gu":"લસ્સી","time":"5 min","emoji":"🥛","ingredients":"Yogurt, Sugar/Salt, Cardamom, Ice","tip_en":"Sweet: add rose water. Salty: add cumin.","tip_hi":"मीठी: गुलाब जल। नमकीन: जीरा डालें।","tip_gu":"મીઠી: ગુલાબ જળ. ખારી: જીરૂ ઉમેરો."}],
}

TOXIC_INFO = {
    "Food":     [{"name":"MSG (E621)","risk":"high"},{"name":"Sodium Benzoate","risk":"moderate"},
                 {"name":"Artificial Colors","risk":"high"},{"name":"Trans Fat","risk":"high"},{"name":"HFCS","risk":"high"}],
    "Cosmetics":[{"name":"Parabens","risk":"high"},{"name":"SLS/SLES","risk":"moderate"},
                 {"name":"Formaldehyde","risk":"critical"},{"name":"Phthalates","risk":"high"},{"name":"Mercury","risk":"critical"}],
    "Groceries":[{"name":"BHA/BHT","risk":"moderate"},{"name":"Sodium Nitrate","risk":"high"}],
    "Medicine": [{"name":"Expired Compounds","risk":"critical"}],
    "Jewelry":  [{"name":"Nickel Allergy","risk":"high"},{"name":"Lead in Plating","risk":"critical"},{"name":"Cadmium","risk":"critical"}],
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            flash("success|Login successful! Welcome back.")
            return redirect(url_for("index"))
        else:
            flash("error|Invalid username or password. Please try again.")
            return redirect(url_for("login"))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("success|You have been logged out successfully.")
    return redirect(url_for("login"))

def get_lang():
    return session.get("lang", "en")

def t(key):
    lang = get_lang()
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))

def load_products():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f: return json.load(f)
    return []

def save_products(products):
    with open(DATA_FILE,"w") as f: json.dump(products, f, indent=2, default=str)

def auto_shelf_days(name, category):
    nl = name.lower()
    for k,v in SHELF_LIFE.items():
        if not k.startswith("default_") and k in nl: return v
    return SHELF_LIFE.get(f"default_{category}", 7)

def detect_metal(name):
    nl = name.lower()
    for m in ["silver","gold","platinum","copper","brass"]:
        if m in nl: return m
    # Gujarati/Hindi keywords
    if any(x in nl for x in ["chandi","चांदी","ચાંદી"]): return "silver"
    if any(x in nl for x in ["sona","सोना","સોનું"]): return "gold"
    if any(x in nl for x in ["tamba","तांबा","તાંબુ"]): return "copper"
    return None

def detect_jewelry_type(name):
    nl = name.lower()
    types = {"earring":"🪬","vali":"🪬","bali":"🪬","baali":"🪬","necklace":"📿",
             "haar":"📿","mala":"📿","bracelet":"💫","bangle":"💫","kada":"💫",
             "ring":"💍","anguthi":"💍","vatla":"💍","anklet":"✨","pajeb":"✨",
             "chain":"⛓️","pendant":"💎","brooch":"🌸"}
    for k,v in types.items():
        if k in nl: return k, v
    return "jewelry","💍"

def get_jewelry_stage(metal, days_owned):
    if metal not in JEWELRY_OXIDATION: return None
    stages = JEWELRY_OXIDATION[metal]["stages"]
    cur = stages[0]
    for s in stages:
        if days_owned >= s["days"]: cur = s
    return cur

def get_status(expiry_str):
    try:
        exp = datetime.strptime(expiry_str,"%Y-%m-%d").date()
        today = date.today()
        diff = (exp - today).days
        lang = get_lang()
        if diff < 0:   return "expired", abs(diff), TRANSLATIONS[lang].get("notif_expired","").replace("{n}",str(abs(diff))).replace("{s}","s" if abs(diff)>1 else "")
        elif diff == 0: return "today",   0,          TRANSLATIONS[lang].get("notif_today","")
        elif diff <= 2: return "critical", diff,       TRANSLATIONS[lang].get("auto_expiry_critical","").replace("{n}",str(diff)).replace("{s}","s" if diff>1 else "")
        elif diff <= 7: return "warning",  diff,       TRANSLATIONS[lang].get("auto_expiry_warning","").replace("{n}",str(diff))
        else:           return "good",     diff,       TRANSLATIONS[lang].get("auto_expiry_good","").replace("{n}",str(diff))
    except: return "unknown",0,""

def get_recipes_for(name):
    nl = name.lower()
    for k,v in RECIPES.items():
        if k in nl: return v
    return []

def get_notifications(products):
    notifs = []
    today = date.today()
    lang = get_lang()
    T = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    for p in products:
        try:
            exp = datetime.strptime(p["expiry"],"%Y-%m-%d").date()
            diff = (exp - today).days
            recipes = get_recipes_for(p["name"])
            rname = recipes[0].get(f"name_{lang}", recipes[0]["name_en"]) if recipes else ""
            rtxt = f" {T.get('try_making','')} {rname}!" if rname else ""
            if diff < 0:
                notifs.append({"type":"expired","icon":"💀",
                    "title":f"{p['name']} — {T['notif_expired'].replace('{n}',str(abs(diff))).replace('{s}','s' if abs(diff)>1 else '')}",
                    "msg":T["notif_expired_msg"],"product":p})
            elif diff == 0:
                notifs.append({"type":"critical","icon":"🚨",
                    "title":f"{p['name']} — {T['notif_today']}",
                    "msg":T["notif_today_msg"]+rtxt,"product":p})
            elif diff == 1:
                notifs.append({"type":"warning","icon":"⚠️",
                    "title":f"{p['name']} — {T['notif_tomorrow']}",
                    "msg":T["notif_tomorrow_msg"]+rtxt,"product":p})
            elif diff <= 3:
                notifs.append({"type":"soon","icon":"🕐",
                    "title":f"{p['name']} — {T['notif_soon'].replace('{n}',str(diff))}",
                    "msg":T["notif_soon_msg"]+rtxt,"product":p})
            if p.get("category")=="Jewelry" and p.get("purchase_date"):
                pd = datetime.strptime(p["purchase_date"],"%Y-%m-%d").date()
                days_owned = (today-pd).days
                metal = detect_metal(p["name"])
                if metal:
                    stage = get_jewelry_stage(metal, days_owned)
                    if stage and stage["pct"] <= 50:
                        notifs.append({"type":"jewelry","icon":JEWELRY_OXIDATION[metal]["icon"],
                            "title":f"{p['name']} — {T['notif_jewelry']}",
                            "msg":stage.get(f"care_{lang}", stage["care_en"]),"product":p})
        except: pass
    return notifs

@app.route("/set-lang/<lang>")
@login_required
def set_lang(lang):
    if lang in ["en","hi","gu"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))

@app.route("/")
@login_required
def index():
    products = load_products()
    today = date.today()
    lang = get_lang()
    for p in products:
        status, days, msg = get_status(p["expiry"])
        p["status"] = status; p["days_left"] = days; p["status_msg"] = msg
        p["recipes"] = get_recipes_for(p["name"]) if p.get("category") in ["Food","Groceries"] else []
        p["toxic"] = TOXIC_INFO.get(p.get("category","Food"),[])
        if p.get("category") == "Jewelry":
            metal = detect_metal(p["name"])
            _, jicon = detect_jewelry_type(p["name"])
            p["metal"] = metal; p["jicon"] = jicon
            if metal and p.get("purchase_date"):
                try:
                    pd = datetime.strptime(p["purchase_date"],"%Y-%m-%d").date()
                    p["days_owned"] = (today-pd).days
                    p["oxidation"] = JEWELRY_OXIDATION.get(metal)
                    p["current_stage"] = get_jewelry_stage(metal, p["days_owned"])
                except: pass
    products.sort(key=lambda x:(0 if x["status"]=="expired" else 1 if x["status"]=="today" else 2 if x["status"]=="critical" else 3 if x["status"]=="warning" else 4))
    notifications = get_notifications(products)
    T = TRANSLATIONS[lang]
    return render_template("index.html",
        products=products, notifications=notifications,
        total=len(products),
        expired=sum(1 for p in products if p["status"]=="expired"),
        critical=sum(1 for p in products if p["status"] in ["today","critical"]),
        good=sum(1 for p in products if p["status"]=="good"),
        jewelry=sum(1 for p in products if p.get("category")=="Jewelry"),
        lang=lang, T=T, TRANSLATIONS=TRANSLATIONS)

@app.route("/form")
@login_required
def form():
    lang = get_lang()
    return render_template("form.html", lang=lang, T=TRANSLATIONS[lang], TRANSLATIONS=TRANSLATIONS)

@app.route("/add", methods=["POST"])
@login_required
def add_product():
    lang = get_lang()
    T = TRANSLATIONS[lang]
    name = request.form.get("name","").strip()
    category = request.form.get("category","Food")
    purchase = request.form.get("purchase_date","") or date.today().strftime("%Y-%m-%d")
    expiry_override = request.form.get("expiry_override","")
    note = request.form.get("note","").strip()
    price = request.form.get("price","0") or "0"
    if not name:
        flash(f"error|{T['flash_error_name']}")
        return redirect(url_for("form"))
    if expiry_override:
        expiry = expiry_override
    else:
        try: pd = datetime.strptime(purchase,"%Y-%m-%d").date()
        except: pd = date.today()
        expiry = (pd + timedelta(days=auto_shelf_days(name,category))).strftime("%Y-%m-%d")
    products = load_products()
    products.append({"id":int(datetime.now().timestamp()*1000),"name":name,"category":category,
        "expiry":expiry,"purchase_date":purchase,"note":note,"price":price,
        "added":date.today().strftime("%Y-%m-%d")})
    save_products(products)
    flash(f"success|{name} {T['flash_success']} {expiry}")
    return redirect(url_for("index"))

@app.route("/delete/<int:pid>")
@login_required
def delete_product(pid):
    save_products([p for p in load_products() if p["id"]!=pid])
    return redirect(url_for("index"))

@app.route("/api/shelf-info")
def shelf_info():
    name = request.args.get("name","")
    category = request.args.get("category","Food")
    purchase = request.args.get("purchase", date.today().strftime("%Y-%m-%d"))
    days = auto_shelf_days(name, category)
    try:
        pd = datetime.strptime(purchase,"%Y-%m-%d").date()
        expiry = (pd+timedelta(days=days)).strftime("%Y-%m-%d")
        diff = (pd+timedelta(days=days)-date.today()).days
    except: expiry=""; diff=days
    metal = detect_metal(name)
    ox_stages = None
    if metal and category=="Jewelry":
        try:
            pd2 = datetime.strptime(purchase,"%Y-%m-%d").date()
            days_owned=(date.today()-pd2).days
            stage = get_jewelry_stage(metal, days_owned)
            ox_stages = {"metal":metal,"icon":JEWELRY_OXIDATION[metal]["icon"],
                         "stages":JEWELRY_OXIDATION[metal]["stages"],"current":stage}
        except: pass
    return jsonify({"shelf_days":days,"expiry":expiry,"days_remaining":diff,
                    "metal":metal,"oxidation":ox_stages})

if __name__ == "__main__":
    app.run(debug=True)