from flask import Flask, request, jsonify
from supabase import create_client
import imagehash
from PIL import Image
import io
import base64
import traceback
import sys

app = Flask(__name__)

# ============================================================
# CONFIGURAZIONE SUPABASE
# ============================================================

SUPABASE_URL = "https://ktpvmpiiibotqzjfytrr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt0cHZtcGlpaWJvdHF6amZ5dHJyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc1MDU5MzAsImV4cCI6MjEwMzA4MTkzMH0.3TKQttphJbAqoI6fZQhP6X49ggQGZqnJmAPRb8MxQCU"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# FUNZIONE PER CALCOLARE IL PHASH
# ============================================================

def calcola_phash(img_data):
    try:
        img = Image.open(io.BytesIO(img_data))
        return str(imagehash.phash(img))
    except Exception as e:
        print(f"ERRORE calcola_phash: {e}")
        return None

# ============================================================
# ENDPOINT PER IL RICONOSCIMENTO
# ============================================================

@app.route('/riconosci', methods=['POST'])
def riconosci():
    try:
        # 1. Log di cosa riceviamo
        print("📥 Ricevuta richiesta POST /riconosci")
        
        # 2. Leggi il JSON
        data = request.get_json()
        if not data:
            print("❌ Nessun JSON ricevuto")
            return jsonify({'errore': 'Nessun JSON ricevuto'}), 400
        
        print(f"📦 JSON ricevuto: {list(data.keys())}")
        
        # 3. Controlla il campo immagine
        img_base64 = data.get('immagine')
        if not img_base64:
            print("❌ Campo 'immagine' mancante")
            return jsonify({'errore': 'Nessuna immagine fornita'}), 400
        
        print(f"📊 Base64 ricevuto, lunghezza: {len(img_base64)}")
        
        # 4. Decodifica Base64
        try:
            img_data = base64.b64decode(img_base64)
            print(f"📊 Immagine decodificata, dimensione: {len(img_data)} bytes")
        except Exception as e:
            print(f"❌ Errore decodifica Base64: {e}")
            return jsonify({'errore': 'Base64 non valido'}), 400
        
        # 5. Calcola PHASH
        phash = calcola_phash(img_data)
        if not phash:
            print("❌ Impossibile calcolare PHASH")
            return jsonify({'errore': 'Impossibile calcolare PHASH'}), 400
        
        print(f"✅ PHASH calcolato: {phash}")
        
        # 6. Cerca in Supabase
        try:
            response = supabase.table("captcha_phash_py").select("cid").eq("phash", phash).execute()
            print(f"📊 Supabase risponde: {len(response.data)} record")
        except Exception as e:
            print(f"❌ Errore Supabase: {e}")
            return jsonify({'errore': f'Errore Supabase: {str(e)}'}), 500
        
        # 7. Restituisci risultato
        if response.data:
            cid = response.data[0]['cid']
            print(f"✅ CID trovato: {cid}")
            return jsonify({'cid': cid, 'phash': phash})
        else:
            print(f"⚠️ PHASH non trovato: {phash}")
            return jsonify({'cid': None, 'phash': phash})
            
    except Exception as e:
        # Cattura TUTTI gli errori e mostra il traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"❌ ERRORE GENERALE: {error_msg}")
        return jsonify({'errore': str(e), 'traceback': traceback.format_exc()}), 500

# ============================================================
# ENDPOINT PER SALVARE UN NUOVO CAPTCHA
# ============================================================

@app.route('/salva', methods=['POST'])
def salva():
    try:
        data = request.get_json()
        phash = data.get('phash')
        cid = data.get('cid')
        
        if not phash or not cid:
            return jsonify({'errore': 'phash e cid obbligatori'}), 400
        
        supabase.table("captcha_phash_py").insert({
            "phash": phash,
            "cid": int(cid)
        }).execute()
        
        return jsonify({'successo': True})
        
    except Exception as e:
        return jsonify({'errore': str(e)}), 500

# ============================================================
# ENDPOINT PER VERIFICARE LO STATO
# ============================================================

@app.route('/stato', methods=['GET'])
def stato():
    try:
        response = supabase.table("captcha_phash_py").select("*").execute()
        return jsonify({'totale': len(response.data), 'record': response.data})
    except Exception as e:
        return jsonify({'errore': str(e)}), 500

# ============================================================
# ENDPOINT PER LA HOMEPAGE
# ============================================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'servizio': 'captcha-riconoscitore',
        'stato': 'attivo',
        'endpoint': {
            '/riconosci': 'POST - Riconosce un captcha',
            '/salva': 'POST - Salva un nuovo captcha',
            '/stato': 'GET - Visualizza lo stato del database'
        }
    })

# ============================================================
# AVVIO
# ============================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
