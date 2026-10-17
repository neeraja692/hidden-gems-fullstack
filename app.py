from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, json
from functools import wraps
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'hidden_gems.db')
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-before-deployment')

SAMPLE_PLACES = [
    {'name':'Sewri Fort','category':'Heritage','lat':19.0006,'lng':72.8543,'budget':0,'rating':4.1,'distance_km':8.2,'visit_duration':1.5,'best_time':'Early morning (6–9am) or late afternoon','rush_info':'Quietest on weekday mornings. Avoid weekends Nov–Feb (flamingo season crowds).','description':'A historic fort area with a striking view of the creek and seasonal flamingo sightings during winter months. The fort dates back to the British colonial era and offers a peaceful escape from the city bustle.','tags':'history,nature,photography','hours':'Daytime; verify access','website':'https://www.google.com/search?q=Sewri+Fort+Mumbai','reviews':[{'user':'Priya M.','rating':5,'text':'Absolutely magical during flamingo season! The pink hues against the mangroves are breathtaking.'},{'user':'Rohan K.','rating':4,'text':'Great for photography. Early morning visits are best for the light.'},{'user':'Sanjana T.','rating':4,'text':'Hidden gem indeed. Very few tourists, peaceful and serene.'}]},
    {'name':'Banganga Tank','category':'Heritage','lat':18.9476,'lng':72.7954,'budget':0,'rating':4.4,'distance_km':4.8,'visit_duration':1.0,'best_time':'Early morning (7–9am) — best light and quietest','rush_info':'Most peaceful on weekday mornings before 9am. Avoids tourist rush at festivals.','description':'An ancient sacred water tank surrounded by temples and historic architecture in Walkeshwar, believed to be over 1000 years old. The ghats create a timeless atmosphere perfect for quiet contemplation.','tags':'history,culture,photography','hours':'Respect local customs and access','website':'https://www.google.com/search?q=Banganga+Tank+Mumbai','reviews':[{'user':'Amit S.','rating':5,'text':'One of Mumbai\'s best kept secrets. The temples and tank create an otherworldly atmosphere.'},{'user':'Leena R.','rating':4,'text':'Beautiful place, very serene. Best visited early morning.'},{'user':'Dev P.','rating':5,'text':'This place transports you back centuries. Incredible heritage.'}]},
    {'name':'Sanjay Gandhi National Park','category':'Nature','lat':19.2147,'lng':72.9106,'budget':150,'rating':4.4,'distance_km':18.5,'visit_duration':3.5,'best_time':'Morning (8–11am) for wildlife and fresh air','rush_info':'Very crowded on weekends and public holidays. Weekday mornings are ideal. Avoid afternoon heat.','description':'A vast urban national park home to over 1000 plant species, leopards, monkeys and ancient Kanheri Caves. Offers treks, nature trails and a unique glimpse of wilderness within a megacity.','tags':'nature,walking,family,trekking','hours':'Check official timings','website':'https://sgnp.maharashtra.gov.in/','reviews':[{'user':'Mehta A.','rating':5,'text':'The Kanheri Caves are spectacular. Nature walk was refreshing and educational.'},{'user':'Nikhil V.','rating':4,'text':'Great for families. Kids loved spotting the monkeys. Very well maintained.'},{'user':'Ritu S.','rating':4,'text':'Early morning safari was worth every penny. Spotted a leopard!'}]},
    {'name':'Khotachiwadi','category':'Culture','lat':18.9548,'lng':72.8180,'budget':0,'rating':4.2,'distance_km':3.1,'visit_duration':1.0,'best_time':'Late morning (10am–12pm) — good light, residents out','rush_info':'Mostly uncrowded. Avoid Sunday afternoons — small tour groups arrive. Residential area, be respectful.','description':'A charming heritage village enclave in Girgaon with 200-year-old East Indian cottages and Goan-Portuguese architecture. The winding lanes feel like a portal to Old Bombay.','tags':'culture,history,photography,walking','hours':'Residential area; visit respectfully','website':'https://www.google.com/search?q=Khotachiwadi+Mumbai','reviews':[{'user':'Clara F.','rating':5,'text':'Like stepping into another era! The colourful cottages are so photogenic.'},{'user':'Vivek B.','rating':4,'text':'Lovely architecture walk. Very peaceful and the residents are quite friendly.'},{'user':'Pooja L.','rating':5,'text':'Hidden treasure of Mumbai. An absolute must-visit for architecture lovers.'}]},
    {'name':'Aarey Forest','category':'Nature','lat':19.1484,'lng':72.8846,'budget':0,'rating':4.0,'distance_km':12.0,'visit_duration':2.0,'best_time':'Early morning (6–9am) for birds and cool air','rush_info':'Largely uncrowded. Weekend mornings see some joggers and cyclists but nothing extreme.','description':'Sprawling green lungs of the city with tribal villages, walking trails and patches of biodiversity. A rare chance to experience rural life within Mumbai city limits.','tags':'nature,walking,photography,trekking','hours':'Verify access and safety before travel','website':'https://www.google.com/search?q=Aarey+Forest+Mumbai','reviews':[{'user':'Ananya S.','rating':4,'text':'Beautiful morning walks. Very peaceful and the air is so fresh.'},{'user':'Karan M.','rating':4,'text':'Great for birdwatching. Spotted many species in a 2-hour walk.'},{'user':'Deepa N.','rating':3,'text':'A bit difficult to navigate without a guide but still a very special place.'}]},
    {'name':'Chor Bazaar','category':'Market','lat':18.9603,'lng':72.8258,'budget':500,'rating':4.0,'distance_km':2.9,'visit_duration':2.0,'best_time':'Late morning to afternoon (10am–2pm)','rush_info':'Gets very busy on Fridays and weekends. Quietest on weekday mornings. Closed on most Sundays — verify.','description':'Mumbai\'s most famous flea market, overflowing with antiques, vintage furniture, old cameras, chandeliers and curiosities from across eras. A treasure hunt experience unlike any other.','tags':'shopping,culture,food,photography','hours':'Check individual shop timings','website':'https://www.google.com/search?q=Chor+Bazaar+Mumbai','reviews':[{'user':'Farhan H.','rating':5,'text':'Found an incredible vintage camera here. Prices are negotiable and the thrill of hunting is real!'},{'user':'Zara P.','rating':4,'text':'Amazing collection of antiques. Go early and be prepared to bargain.'},{'user':'Rajan T.','rating':4,'text':'A photographer\'s dream location. Every corner is a photo opportunity.'}]},
    {'name':'Bandra Fort','category':'Viewpoint','lat':19.0434,'lng':72.8190,'budget':0,'rating':4.3,'distance_km':9.7,'visit_duration':1.0,'best_time':'Sunset (6–7:30pm) — golden light, sea link glows','rush_info':'Very crowded at sunset on weekends. For photos, arrive on a weekday 30 min before golden hour.','description':'Ruins of a 17th-century Portuguese fort perched above the Arabian Sea, offering spectacular views of the Bandra-Worli Sea Link. Sunset here is legendary among Mumbai locals.','tags':'photography,history,walking,friends','hours':'Check access and weather','website':'https://www.google.com/search?q=Bandra+Fort+Mumbai','reviews':[{'user':'Ishaan V.','rating':5,'text':'The sunset views are absolutely stunning. One of the best spots in Mumbai.'},{'user':'Mia C.','rating':5,'text':'The sea link framed by the fort ruins is just magical. Come at golden hour!'},{'user':'Aryan D.','rating':4,'text':'Great atmosphere especially in the evenings. Street food nearby is a bonus.'}]},
    {'name':'Five Gardens','category':'Garden','lat':19.0242,'lng':72.8504,'budget':0,'rating':4.2,'distance_km':6.4,'visit_duration':1.0,'best_time':'Early morning (6–8am) or late evening (6–8pm)','rush_info':'Quietest mid-morning on weekdays. Fills up with families on weekend evenings — still pleasant.','description':'A peaceful cluster of neighbourhood gardens in Matunga offering a rare green retreat. Perfect for morning walks, yoga or simply watching Mumbaikars unwind in their natural habitat.','tags':'nature,walking,family','hours':'Check local park timings','website':'https://www.google.com/search?q=Five+Gardens+Mumbai','reviews':[{'user':'Sunita R.','rating':4,'text':'Perfect morning walk spot. Clean, well-maintained and very relaxing.'},{'user':'Harish P.','rating':4,'text':'Great for families. Kids can play and elders can walk. Very community-oriented.'},{'user':'Maya S.','rating':5,'text':'My favourite quiet spot in Mumbai. The old trees are magnificent.'}]},
    {'name':'Matunga South Indian Food Walk','category':'Food','lat':19.0270,'lng':72.8500,'budget':350,'rating':4.3,'distance_km':6.8,'visit_duration':1.5,'best_time':'Breakfast to late morning (7:30–11am) for fresh dosas','rush_info':'Breakfast rush 8–10am — expect queues at iconic spots but worth it. Quieter post-11am.','description':'A culinary pilgrimage through Mumbai\'s South Indian food capital. From crisp dosas to filter coffee and idlis that melt in the mouth, Matunga\'s iconic cafes have been feeding Mumbai since the 1930s.','tags':'food,culture,friends,family','hours':'Depends on individual venues','website':'https://www.google.com/search?q=Matunga+South+Indian+restaurants','reviews':[{'user':'Lakshmi V.','rating':5,'text':'Best dosas outside Tamil Nadu! The filter coffee at Ram Ashraya is life-changing.'},{'user':'Suresh K.','rating':5,'text':'Incredible food trail. So many authentic places to try.'},{'user':'Preethi M.','rating':4,'text':'Worth the trip. The old-school charm of these cafes is as nourishing as the food.'}]},
    {'name':'Carter Road Promenade','category':'Waterfront','lat':19.0680,'lng':72.8220,'budget':0,'rating':4.3,'distance_km':10.2,'visit_duration':1.0,'best_time':'Evening (5:30–7:30pm) for the sunset sea breeze','rush_info':'Weekday evenings are lovely. Weekend evenings are buzzing but still great.','description':'A beloved Bandra seafront promenade where joggers, couples, families and street food vendors share the same beautiful stretch. The sunsets paint the sky in shades of gold and pink.','tags':'walking,food,friends,family,photography','hours':'Public access may vary','website':'https://www.google.com/search?q=Carter+Road+Promenade','reviews':[{'user':'Naina S.','rating':5,'text':'Evening walks here are just perfect. The vibe is great and the pav bhaji carts are a must!'},{'user':'Kabir R.','rating':4,'text':'Best walking route in Bandra. Perfect for sunset watching.'},{'user':'Tara M.','rating':4,'text':'Great energy, lovely people. The sea breeze makes everything better.'}]},
    {'name':'Dr. Bhau Daji Lad Museum','category':'Museum','lat':18.9790,'lng':72.8330,'budget':100,'rating':4.4,'distance_km':4.6,'visit_duration':2.0,'best_time':'Late morning (10am–12pm) — uncrowded and well lit','rush_info':'Rarely crowded. Weekday mornings are blissfully quiet. Closed on Wednesdays — verify.','description':'Mumbai\'s oldest museum, beautifully restored to its Victorian glory, exploring the city\'s history through decorative arts, maps and artefacts. A must for anyone curious about the city\'s layered past.','tags':'history,culture,family','hours':'Check official timings and ticket prices','website':'https://www.bdlmuseum.org/','reviews':[{'user':'Shreya A.','rating':5,'text':'Beautifully curated museum. The restoration is impeccable and the collections are fascinating.'},{'user':'Vikram N.','rating':5,'text':'Best kept secret in Byculla. A proper museum experience in a stunning colonial building.'},{'user':'Anjali K.','rating':4,'text':'Very informative and well-organized. The scale models of old Bombay are incredible.'}]},
    {'name':'Global Vipassana Pagoda','category':'Architecture','lat':19.2289,'lng':72.8050,'budget':0,'rating':4.5,'distance_km':25.0,'visit_duration':2.5,'best_time':'Morning (8am–12pm) — cool, uncrowded, great light','rush_info':'Busy on weekends and Buddhist holidays. Weekday mornings are very peaceful. Ferry timings vary — check.','description':'A magnificent meditation dome and architectural marvel near Gorai, inspired by the Shwedagon Pagoda in Myanmar. The world\'s largest stone dome is truly awe-inspiring and the ferry ride adds to the experience.','tags':'culture,architecture,family,photography','hours':'Check official visitor information','website':'https://www.globalpagoda.org/','reviews':[{'user':'Om S.','rating':5,'text':'Breathtaking architecture. The meditation hall inside is unlike anything I\'ve experienced.'},{'user':'Riya P.','rating':5,'text':'The ferry ride + the pagoda = unforgettable day. Go early to beat the crowds.'},{'user':'Dinesh V.','rating':4,'text':'Very peaceful and spiritually uplifting. A true architectural wonder.'}]},
    {'name':'Dharavi Art District','category':'Culture','lat':19.0413,'lng':72.8532,'budget':0,'rating':4.1,'distance_km':7.3,'visit_duration':2.0,'best_time':'Late morning (10am–1pm) — artisans actively working','rush_info':'Best on weekdays when workshops are open. Weekend tours exist but book ahead. Avoid public holidays.','description':'Beyond the stereotypes, Dharavi buzzes with creativity — home to potters, leather craftspeople, recyclers and artists. Guided walks reveal a thriving micro-economy and remarkable human stories.','tags':'culture,art,photography,friends','hours':'Book a guided tour for best experience','website':'https://www.google.com/search?q=Dharavi+tour+Mumbai','reviews':[{'user':'Sasha W.','rating':5,'text':'Eye-opening experience. The creativity and enterprise here will genuinely move you.'},{'user':'Aditya P.','rating':4,'text':'Take a guided tour — makes all the difference. Came away with deep respect for the community.'},{'user':'Elena B.','rating':5,'text':'One of the most memorable experiences of my Mumbai trip. A must-do.'}]},
    {'name':'Worli Sea Face','category':'Waterfront','lat':19.0121,'lng':72.8156,'budget':0,'rating':4.2,'distance_km':5.8,'visit_duration':1.0,'best_time':'Sunrise (6–7:30am) or sunset (6–7:30pm)','rush_info':'Very quiet early mornings — fishermen and joggers only. Evening crowds build after 6pm but still manageable.','description':'A classic Mumbai promenade with unobstructed views of the Bandra-Worli Sea Link from the Worli side. Watch fishermen cast their nets as the city skyline glitters behind you.','tags':'walking,photography,friends,family,nature','hours':'Public area; best at dusk','website':'https://www.google.com/search?q=Worli+Sea+Face+Mumbai','reviews':[{'user':'Raj K.','rating':4,'text':'The sea link views are incredible. Morning walks here are so peaceful and refreshing.'},{'user':'Priyanka D.','rating':5,'text':'Perfect spot for an evening stroll. The fishermen and sea link together make for beautiful photos.'},{'user':'Akash M.','rating':4,'text':'Underrated waterfront. Less crowded than Marine Drive, more character.'}]},
    {'name':'Sassoon Dock','category':'Culture','lat':18.9118,'lng':72.8326,'budget':0,'rating':3.9,'distance_km':2.1,'visit_duration':1.0,'best_time':'Dawn to early morning (5–8am) — only time it\'s truly alive','rush_info':'Only worth visiting at 5–7am when fishing boats unload. Dead and closed later in the day.','description':'Mumbai\'s oldest wet dock comes alive before dawn when fishing boats return with the catch. The vibrant chaos of colour, light, fish and people makes for extraordinary early-morning photography.','tags':'photography,culture,food','hours':'Best visited 5am–8am on weekdays','website':'https://www.google.com/search?q=Sassoon+Dock+Mumbai','reviews':[{'user':'Parag V.','rating':5,'text':'Wake up at 4am for this — completely worth it. Raw, authentic Mumbai at its most alive.'},{'user':'Neha R.','rating':4,'text':'An overwhelming sensory experience. The colours are just stunning.'},{'user':'Chris L.','rating':5,'text':'Best photography location I\'ve found in Mumbai. Pure, unfiltered city life.'}]},
    {'name':'Juhu Beach Sunset Walk','category':'Waterfront','lat':19.1075,'lng':72.8263,'budget':150,'rating':4.0,'distance_km':13.2,'visit_duration':1.5,'best_time':'Sunset (5:30–7:30pm) — street food + sea + sky','rush_info':'Very crowded on weekends and holidays at sunset. Weekday evenings are much calmer and equally beautiful.','description':'Mumbai\'s most famous beach transforms at sunset — the sky turns amber and the street food vendors fire up their stalls. Pav bhaji, bhel puri and sugarcane juice make it a feast for all senses.','tags':'food,friends,family,walking,photography','hours':'Best at sunset; 5pm–8pm','website':'https://www.google.com/search?q=Juhu+Beach+Mumbai','reviews':[{'user':'Sneha B.','rating':4,'text':'The street food here is unmatched. Pav bhaji by the sea = happiness.'},{'user':'Rahul D.','rating':4,'text':'Classic Mumbai experience. The sunset combined with bhel puri is perfect.'},{'user':'Aditi M.','rating':3,'text':'Can get very crowded on weekends. Weekday evenings are much better.'}]},
    {'name':'Elephanta Caves','category':'Heritage','lat':18.9633,'lng':72.9315,'budget':600,'rating':4.6,'distance_km':10.0,'visit_duration':3.0,'best_time':'Morning (9am–12pm) — beat the heat and tourist groups','rush_info':'Can get crowded by late morning on weekends. Take the first or second ferry. Avoid holiday weekends.','description':'UNESCO World Heritage rock-cut cave temples dedicated to Lord Shiva, carved in the 5th–8th centuries. Accessible by ferry from Gateway of India, the journey and the caves together make for an unforgettable day.','tags':'history,culture,architecture,family','hours':'Tue–Sun; check ferry timings','website':'https://www.google.com/search?q=Elephanta+Caves+Mumbai','reviews':[{'user':'Rahul S.','rating':5,'text':'Absolutely spectacular. The main Shiva sculpture is one of the great works of Indian art.'},{'user':'Jennifer K.','rating':5,'text':'Ferry ride + caves = perfect day trip. The monkeys add to the adventure!'},{'user':'Ishita P.','rating':4,'text':'Worth every bit of effort. The sculptures are breathtaking.'}]},
    {'name':'Colaba Causeway','category':'Market','lat':18.9215,'lng':72.8322,'budget':400,'rating':4.1,'distance_km':1.5,'visit_duration':1.5,'best_time':'Late morning to afternoon (11am–3pm)','rush_info':'Busy most of the day. Quieter on weekday mornings. Avoid peak hours 12–2pm on weekends.','description':'Mumbai\'s most famous street market stretching through the city\'s southernmost neighbourhood. Jewellery, clothes, antiques and handicrafts jostle for space in a lively bazaar atmosphere.','tags':'shopping,culture,food,friends','hours':'Daily except Sunday; check timings','website':'https://www.google.com/search?q=Colaba+Causeway+Mumbai','reviews':[{'user':'Sara J.','rating':4,'text':'Great for souvenirs and unique finds. Bargaining is essential and part of the fun.'},{'user':'Nikhil A.','rating':4,'text':'Wonderful street market energy. The nearby cafes are also great.'},{'user':'Priya V.','rating':5,'text':'Found the most beautiful silver jewellery here. The whole area has amazing food too.'}]},
    {'name':'Haji Ali Dargah','category':'Heritage','lat':18.9827,'lng':72.8091,'budget':0,'rating':4.5,'distance_km':5.2,'visit_duration':1.0,'best_time':'Morning (7–10am) or late afternoon (4–6pm) — peaceful','rush_info':'Very crowded on Thursdays and Fridays (prayer days). Monday–Wednesday mornings are quietest. Causeway floods at high tide — check tides.','description':'A stunning 15th-century mosque and tomb on a tiny islet connected to land by a narrow causeway. At high tide the causeway submerges, creating the illusion of a floating shrine.','tags':'history,culture,architecture,photography','hours':'Open daily; check prayer times and tides','website':'https://www.google.com/search?q=Haji+Ali+Dargah+Mumbai','reviews':[{'user':'Omar F.','rating':5,'text':'Architecturally stunning. The walk along the causeway with the sea on both sides is unforgettable.'},{'user':'Anita R.','rating':5,'text':'One of Mumbai\'s most iconic and spiritual places. The atmosphere is deeply moving.'},{'user':'Marcus T.','rating':4,'text':'Absolutely beautiful. The white marble against the blue sea is extraordinary.'}]},
    {'name':'Versova Village','category':'Culture','lat':19.1315,'lng':72.8096,'budget':200,'rating':4.0,'distance_km':15.7,'visit_duration':1.5,'best_time':'Lunch (12–2pm) for fresh catch, or sunset (5:30–7pm)','rush_info':'Never very crowded — that\'s the point! Slightly busier on weekend lunch and evenings. Very laid-back vibe always.','description':'A genuine fishing village tucked into the northern suburbs, with fresh seafood restaurants, beautiful sunsets and a bohemian arts community. Far less touristy than Juhu, far more authentic.','tags':'food,culture,walking,photography,friends','hours':'Best at lunch or sunset','website':'https://www.google.com/search?q=Versova+Village+Mumbai','reviews':[{'user':'Alex T.','rating':5,'text':'The fresh fish thali here is one of the best meals I\'ve had in Mumbai.'},{'user':'Kavya M.','rating':4,'text':'Lovely and authentic. The sunset from the beach is gorgeous.'},{'user':'Rishi N.','rating':4,'text':'Hidden gem! Great seafood and a very different side of Mumbai.'}]}
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL, home_location TEXT DEFAULT '', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS saved_places (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, place_name TEXT NOT NULL,
      UNIQUE(user_id, place_name), FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS itineraries (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL,
      trip_date TEXT DEFAULT '', group_size INTEGER DEFAULT 1, budget REAL DEFAULT 0,
      start_location TEXT DEFAULT '', notes TEXT DEFAULT '', created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS itinerary_stops (
      id INTEGER PRIMARY KEY AUTOINCREMENT, itinerary_id INTEGER NOT NULL, place_name TEXT NOT NULL,
      visit_date TEXT DEFAULT '', start_time TEXT DEFAULT '', end_time TEXT DEFAULT '',
      transport TEXT DEFAULT 'public', estimated_cost REAL DEFAULT 0, entry_cost REAL DEFAULT 0,
      notes TEXT DEFAULT '', sort_order INTEGER DEFAULT 0,
      FOREIGN KEY(itinerary_id) REFERENCES itineraries(id) ON DELETE CASCADE
    );
    ''')
    conn.commit()
    cols = [c[1] for c in conn.execute('PRAGMA table_info(itinerary_stops)').fetchall()]
    if 'entry_cost' not in cols:
        conn.execute('ALTER TABLE itinerary_stops ADD COLUMN entry_cost REAL DEFAULT 0')
        conn.commit()
    conn.close()

init_db()

def safe_int(val, default=1):
    try: return int(val)
    except (ValueError, TypeError): return default

def safe_float(val, default=0.0):
    try: return float(val)
    except (ValueError, TypeError): return default

def time_order(best_time):
    t = (best_time or '').lower()
    if any(k in t for k in ['dawn', 'early morning', '5am', '6am']): return 0
    if any(k in t for k in ['morning', '7am', '8am', '9am']): return 1
    if any(k in t for k in ['late morning', '10am', '11am']): return 2
    if any(k in t for k in ['afternoon', 'midday', 'noon', '12pm']): return 3
    if 'anytime' in t: return 2
    if any(k in t for k in ['evening', '4pm', '5pm', 'sunset', 'dusk']): return 5
    if any(k in t for k in ['late evening', 'night', '7pm']): return 6
    return 3

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please sign in to access your saved trips.', 'info')
            return redirect(url_for('login', next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def current_user():
    if not session.get('user_id'): return None
    conn = get_db(); user = conn.execute('SELECT id,name,email,home_location FROM users WHERE id=?',(session['user_id'],)).fetchone(); conn.close()
    return user

@app.context_processor
def inject_user(): return {'current_user': current_user()}

@app.route('/')
def index():
    return render_template('index.html', places=SAMPLE_PLACES[:6])

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password',''); confirm=request.form.get('confirm_password','')
        if not name or not email or len(password)<8:
            flash('Enter your name and email, and use a password with at least 8 characters.', 'error')
        elif password != confirm:
            flash('Passwords do not match.', 'error')
        else:
            conn=get_db()
            try:
                cur=conn.execute('INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)',(name,email,generate_password_hash(password),datetime.now().isoformat()))
                conn.commit(); session['user_id']=cur.lastrowid; flash('Account created. Welcome to Roamly!', 'success'); return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError: flash('An account with that email already exists. Please sign in.', 'error')
            finally: conn.close()
    return render_template('auth.html', mode='signup')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        conn=get_db(); user=conn.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone(); conn.close()
        if user and check_password_hash(user['password_hash'],password):
            session.clear(); session['user_id']=user['id']; flash('You are signed in.', 'success'); return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Email or password is incorrect.', 'error')
    return render_template('auth.html', mode='login')

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        flash('If an account with that email exists, a reset link has been sent. Check your inbox.', 'info')
        return redirect(url_for('login'))
    return render_template('auth.html', mode='forgot')

@app.route('/logout')
def logout(): session.clear(); flash('You have been signed out.', 'info'); return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn=get_db(); trips=conn.execute('SELECT * FROM itineraries WHERE user_id=? ORDER BY created_at DESC',(session['user_id'],)).fetchall(); saved=conn.execute('SELECT * FROM saved_places WHERE user_id=?',(session['user_id'],)).fetchall(); conn.close()
    return render_template('dashboard.html', trips=trips, saved=saved)

@app.route('/discover')
def discover():
    q=request.args.get('q','').strip().lower(); category=request.args.get('category','All'); budget=request.args.get('budget','Any'); maxdist=request.args.get('distance','Any'); interest=request.args.get('interest','Any')
    filtered=[]
    for p in SAMPLE_PLACES:
        if q and q not in (p['name']+' '+p['category']+' '+p['description']+' '+p['tags']).lower(): continue
        if category!='All' and p['category']!=category: continue
        if budget=='Free' and p['budget']>0: continue
        if budget=='Under ₹300' and p['budget']>=300: continue
        if budget=='Under ₹600' and p['budget']>=600: continue
        if maxdist!='Any' and p['distance_km']>float(maxdist): continue
        if interest!='Any' and interest.lower() not in p['tags'].lower(): continue
        filtered.append(p)
    return render_template('discover.html', places=filtered, all_places=SAMPLE_PLACES, categories=sorted(set(p['category'] for p in SAMPLE_PLACES)), filters={'q':request.args.get('q',''),'category':category,'budget':budget,'distance':maxdist,'interest':interest})

@app.route('/map')
def map_view(): return render_template('map.html', places=SAMPLE_PLACES)

@app.route('/finder')
def finder():
    return render_template('finder.html', places_json=json.dumps(SAMPLE_PLACES))

@app.route('/save-place/<path:place_name>', methods=['POST'])
@login_required
def save_place(place_name):
    conn=get_db()
    try: conn.execute('INSERT OR IGNORE INTO saved_places(user_id,place_name) VALUES(?,?)',(session['user_id'],place_name)); conn.commit(); flash('Place saved to your collection.', 'success')
    finally: conn.close()
    return redirect(request.referrer or url_for('discover'))

@app.route('/remove-saved/<int:saved_id>', methods=['POST'])
@login_required
def remove_saved(saved_id):
    conn=get_db(); conn.execute('DELETE FROM saved_places WHERE id=? AND user_id=?',(saved_id,session['user_id'])); conn.commit(); conn.close(); flash('Saved place removed.', 'info'); return redirect(url_for('dashboard'))

@app.route('/planner', methods=['GET','POST'])
@login_required
def planner():
    if request.method=='POST':
        title=request.form.get('title','My trip').strip() or 'My trip'
        trip_date=request.form.get('trip_date','')
        group_size=max(1,safe_int(request.form.get('group_size',1), 1))
        budget=max(0.0,safe_float(request.form.get('budget',0), 0.0))
        start=request.form.get('start_location','').strip()
        notes=request.form.get('notes','').strip()
        names=request.form.getlist('stop_name[]')
        dates=request.form.getlist('stop_date[]')
        starts=request.form.getlist('start_time[]')
        ends=request.form.getlist('end_time[]')
        transports=request.form.getlist('transport[]')
        costs=request.form.getlist('cost[]')
        entry_costs=request.form.getlist('entry_cost[]')
        stopnotes=request.form.getlist('stop_notes[]')
        conn=get_db()
        cur=conn.execute('INSERT INTO itineraries(user_id,title,trip_date,group_size,budget,start_location,notes,created_at) VALUES(?,?,?,?,?,?,?,?)',
            (session['user_id'],title,trip_date,group_size,budget,start,notes,datetime.now().isoformat()))
        trip_id=cur.lastrowid
        for i,name in enumerate(names):
            if not name.strip(): continue
            ec = safe_float(entry_costs[i] if i < len(entry_costs) else 0, 0.0)
            conn.execute('INSERT INTO itinerary_stops(itinerary_id,place_name,visit_date,start_time,end_time,transport,estimated_cost,entry_cost,notes,sort_order) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (trip_id,name.strip(),dates[i] if i<len(dates) else trip_date,
                 starts[i] if i<len(starts) else '',ends[i] if i<len(ends) else '',
                 transports[i] if i<len(transports) else 'public',
                 safe_float(costs[i] if i<len(costs) else 0, 0.0), ec,
                 stopnotes[i] if i<len(stopnotes) else '',i))
        conn.commit(); conn.close()
        flash('Your itinerary has been saved!', 'success')
        return redirect(url_for('trip_detail',trip_id=trip_id))
    add_place = request.args.get('add_place','')
    return render_template('planner.html', places=SAMPLE_PLACES, add_place=add_place, all_places=SAMPLE_PLACES)

@app.route('/trip/<int:trip_id>/add-stop', methods=['POST'])
@login_required
def add_stop_to_trip(trip_id):
    conn = get_db()
    trip = conn.execute('SELECT * FROM itineraries WHERE id=? AND user_id=?',(trip_id,session['user_id'])).fetchone()
    if not trip: conn.close(); return jsonify({'ok': False, 'error': 'Not found'}), 404
    data = request.get_json(silent=True) or {}
    place_name = data.get('place_name','').strip()
    if not place_name: conn.close(); return jsonify({'ok': False, 'error': 'No place name'}), 400
    count = conn.execute('SELECT COUNT(*) FROM itinerary_stops WHERE itinerary_id=?',(trip_id,)).fetchone()[0]
    conn.execute('INSERT INTO itinerary_stops(itinerary_id,place_name,sort_order) VALUES(?,?,?)',(trip_id,place_name,count))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

@app.route('/trip/<int:trip_id>')
@login_required
def trip_detail(trip_id):
    conn=get_db(); trip=conn.execute('SELECT * FROM itineraries WHERE id=? AND user_id=?',(trip_id,session['user_id'])).fetchone()
    if not trip: conn.close(); flash('Trip not found.', 'error'); return redirect(url_for('dashboard'))
    stops=conn.execute('SELECT * FROM itinerary_stops WHERE itinerary_id=? ORDER BY sort_order,id',(trip_id,)).fetchall(); conn.close()
    # Enrich stops with place data
    place_map = {p['name']: p for p in SAMPLE_PLACES}
    enriched = []
    for s in stops:
        sd = dict(s)
        pd = place_map.get(s['place_name'], {})
        sd['best_time'] = pd.get('best_time', '')
        sd['rush_info'] = pd.get('rush_info', '')
        sd['visit_duration'] = float(pd.get('visit_duration', 1.5) or 1.5)
        sd['estimated_cost'] = float(sd.get('estimated_cost') or 0)
        sd['entry_cost'] = float(sd.get('entry_cost') or 0)
        sd['time_order'] = time_order(sd['best_time'])
        enriched.append(sd)
    return render_template('trip_detail.html', trip=trip, stops=enriched, all_places=SAMPLE_PLACES)

@app.route('/trip/<int:trip_id>/delete', methods=['POST'])
@login_required
def delete_trip(trip_id):
    conn=get_db(); conn.execute('DELETE FROM itinerary_stops WHERE itinerary_id IN (SELECT id FROM itineraries WHERE id=? AND user_id=?)',(trip_id,session['user_id'])); conn.execute('DELETE FROM itineraries WHERE id=? AND user_id=?',(trip_id,session['user_id'])); conn.commit(); conn.close(); flash('Trip deleted.', 'info'); return redirect(url_for('dashboard'))

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    conn=get_db()
    if request.method=='POST':
        name=request.form.get('name','').strip(); home=request.form.get('home_location','').strip()
        if name: conn.execute('UPDATE users SET name=?,home_location=? WHERE id=?',(name,home,session['user_id'])); conn.commit(); flash('Profile updated.', 'success')
    user=conn.execute('SELECT id,name,email,home_location,created_at FROM users WHERE id=?',(session['user_id'],)).fetchone(); conn.close()
    return render_template('profile.html', user=user)

@app.route('/api/places')
def api_places():
    return jsonify({'source':'curated prototype sample data','places':SAMPLE_PLACES})

@app.route('/api/itineraries')
@login_required
def api_itineraries():
    conn = get_db()
    trips = conn.execute('SELECT id,title,trip_date,group_size FROM itineraries WHERE user_id=? ORDER BY created_at DESC',(session['user_id'],)).fetchall()
    conn.close()
    return jsonify({'trips': [dict(t) for t in trips]})
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
