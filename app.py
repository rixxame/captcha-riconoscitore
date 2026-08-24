from flask import Flask, request, jsonify
from supabase import create_client
import imagehash
from PIL import Image
import io
import json
import os
import base64

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
        return None

# ============================================================
# ENDPOINT PER IL RICONOSCIMENTO
# ============================================================

@app.route('/riconosci', methods=['POST'])
def riconosci():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'errore': 'Nessun JSON ricevuto'}), 400
        
        img_base64 = data.get('immagine')
        if not img_base64:
            return jsonify({'errore': 'Nessuna immagine fornita'}), 400
        
        img_data = base64.b64decode(img_base64)
        phash = calcola_phash(img_data)
        
        if not phash:
            return jsonify({'errore': 'Impossibile calcolare PHASH'}), 400
        
        response = supabase.table("captcha_phash_py").select("cid").eq("phash", phash).execute()
        
        if response.data:
            cid = response.data[0]['cid']
            return jsonify({'cid': cid, 'phash': phash})
        else:
            return jsonify({'cid': None, 'phash': phash})
            
    except Exception as e:
        return jsonify({'errore': str(e)}), 500

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
    response = supabase.table("captcha_phash_py").select("*").execute()
    return jsonify({'totale': len(response.data), 'record': response.data})

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
