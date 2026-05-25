# server_flask.py
from flask import Flask, render_template, request, redirect, jsonify, session
from functools import wraps
import base64
import webbrowser
from threading import Timer
import app
import scraper
import time
import uuid 
import json # <--- Tambahan import untuk membaca file JSON
import os   # <--- Tambahan import untuk mengecek keberadaan file

server = Flask(__name__)

# --- KONFIGURASI KEAMANAN ---
# Menggunakan uuid.uuid4().hex agar setiap kali aplikasi dijalankan ulang, 
# kunci rahasia berubah secara acak. Ini akan menghapus sesi lama di browser 
# dan memaksa pengguna untuk memasukkan email terlebih dahulu setiap kali masuk.
server.secret_key = uuid.uuid4().hex
USERS_FILE = "users.json" # Nama file database akun kita

# --- FUNGSI DATABASE SEMENTARA (JSON) ---
def load_users():
    """Fungsi untuk membaca data user dari file users.json"""
    if not os.path.exists(USERS_FILE):
        # Jika file belum ada, buat file baru dengan data default
        default_users = {
            "evans@shop.com": "password123",
            "admin@shop.com": "admin123"
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f, indent=4)
        return default_users
    
    # Jika sudah ada, baca dan kembalikan datanya
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users_data):
    """Fungsi untuk menyimpan data user baru ke dalam file users.json"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=4)

# --- PENJAGA HALAMAN (DECORATOR) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# --- SISTEM MULTI-SESI ---
chat_sessions = []
active_session_id = str(uuid.uuid4())

# ==========================================
# --- ROUTE LOGIN & LOGOUT ---
# ==========================================
@server.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect('/')
        
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Ambil data akun terbaru dari file users.json
        users_db = load_users()
        
        # Pengecekan data akun dari file JSON
        if email in users_db and users_db[email] == password:
            session['logged_in'] = True
            session['user_email'] = email
            session['user_name'] = email.split('@')[0].capitalize() 
            return redirect('/')
        else:
            error = "Email atau password salah. Silakan coba lagi."
            
    return render_template('login.html', error=error)

@server.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ==========================================
# --- ROUTE PENGATURAN AKUN (PERMANEN) ---
# ==========================================
@server.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    message = None
    if request.method == 'POST':
        new_email = request.form.get('new_email')
        new_password = request.form.get('new_password')
        old_email = session.get('user_email')
        
        # 1. Ambil data database akun saat ini dari file
        users_db = load_users()
        
        # 2. Hapus email lama dari database jika ada
        if old_email in users_db:
            users_db.pop(old_email)
            
        # 3. Masukkan data email & password baru
        users_db[new_email] = new_password
        
        # 4. Simpan kembali secara permanen ke file users.json
        save_users(users_db)
        
        # 5. Perbarui session aktif agar UI langsung berubah
        session['user_email'] = new_email
        session['user_name'] = new_email.split('@')[0].capitalize()
        
        message = "Data akun berhasil diperbarui secara permanen!"
        
    return render_template('settings.html', message=message, current_email=session.get('user_email'))

# ==========================================
# --- ROUTE HALAMAN UTAMA ---
# ==========================================
@server.route('/')
@login_required
def shop_home():
    products = app.load_products("products.json")
    return render_template('shop.html', products=products)

@server.route('/chat', methods=['GET', 'POST'])
@login_required
def home():
    global chat_sessions, active_session_id
    error_msg = None
    products = []
    
    current_session = next((s for s in chat_sessions if s["id"] == active_session_id), None)
    
    if request.method == 'POST':
        if not current_session:
            current_session = {
                "id": active_session_id, 
                "title": "Obrolan Baru", 
                "messages": [],
                "preferences": {
                    "merek_favorit": set(),
                    "kategori_minat": set(),
                    "budget": "Bebas"
                }
            }
            chat_sessions.insert(0, current_session)
            
        chat_memory = current_session["messages"]
        session_prefs = current_session["preferences"]
        
        raw_query = request.form.get('message', '')
        user_query = app.clean_text(raw_query)
        user_image_file = request.files.get('user_image')
        query_huruf_kecil = user_query.lower()

        # ==========================================
        # Deteksi Preferensi Otomatis Menggunakan AI
        # ==========================================
        extracted_prefs = app.extract_text_preferences(user_query)
        
        if extracted_prefs:
            print(f"✅ Preferensi terdeteksi dari teks: {extracted_prefs}")
            
            # Tambahkan merek jika terdeteksi (dan bukan null/kosong)
            if extracted_prefs.get('merek') and str(extracted_prefs['merek']).lower() != 'null':
                session_prefs["merek_favorit"].add(str(extracted_prefs['merek']).title())
                
            # Tambahkan kategori jika terdeteksi
            if extracted_prefs.get('kategori') and str(extracted_prefs['kategori']).lower() != 'null':
                session_prefs["kategori_minat"].add(str(extracted_prefs['kategori']).title())
                
            # Perbarui budget jika terdeteksi
            if extracted_prefs.get('budget') and str(extracted_prefs['budget']).lower() != 'null':
                session_prefs["budget"] = str(extracted_prefs['budget']).title()
        # ==========================================

        # Pemilihan Algoritma
        if any(kata in query_huruf_kecil for kata in ['bandingkan', 'perbandingan', 'beda', 'vs', 'mending mana', 'pilih mana']):
            summary_algo = 'comparative'
        elif any(kata in query_huruf_kecil for kata in ['singkat', 'ringkas', 'padat', 'kesimpulan', 'intinya']):
            summary_algo = 'abstractive'
        elif any(kata in query_huruf_kecil for kata in ['spesifikasi', 'spek', 'detail', 'poin penting', 'teknis']):
            summary_algo = 'extractive'
        elif any(kata in query_huruf_kecil for kata in [
            'rekomendasi', 'saran', 'cocok', 'rekomendasikan', 'pilihan terbaik', 'bagusnya',
            'laptop', 'hp', 'smartphone', 'jam', 'watch', 'smartwatch', 'earphone', 'tws', 
            'headset', 'ssd', 'penyimpanan', 'hardisk', 'tas', 'dompet', 'brankas',
            'samsung', 'apple', 'asus', 'acer', 'huawei', 'realme', 'mac', 'ipad', 'galaxy'
        ]):
            summary_algo = 'recommendation'
        else:
            summary_algo = 'general'
            
        data_source = 'json_lokal'
        if any(kata in query_huruf_kecil for kata in ['buku', 'web', 'internet', 'online', 'live', 'luar']):
            data_source = 'web_scraping'
        
        if data_source == 'json_lokal':
            products = app.load_products("products.json")
        elif data_source == 'web_scraping':
            url_target = "https://books.toscrape.com/"
            products = scraper.scrape_toko_online(url_target)
            if not products:
                error_msg = "Gagal mengambil data dari website. Pastikan koneksi aman."

        user_image_bytes = None
        image_mime = ""

        if user_image_file and user_image_file.filename != '':
            image_mime = user_image_file.mimetype
            user_image_bytes = user_image_file.read() 

        # Panggil AI
        if user_query and not error_msg:
            start_time = time.time()
            ai_response, has_error, eval_data = app.ask_ai(
                user_query, products, chat_memory, user_image_bytes, summary_algo, session_prefs
            )
            latency = round(time.time() - start_time, 2) 

            display_base64 = ""
            if user_image_bytes:
                display_base64 = base64.b64encode(user_image_bytes).decode('utf-8')

            chat_memory.append({
                "user": user_query,
                "ai": ai_response,
                "image": display_base64,
                "image_mime": image_mime,
                "algo": summary_algo,   
                "latency": latency,     
                "eval": eval_data       
            })
            
            if len(chat_memory) == 1:
                new_title = user_query[:25] + "..." if len(user_query) > 25 else user_query
                current_session["title"] = new_title
                
    else:
        if current_session:
            chat_memory = current_session["messages"]
            session_prefs = current_session["preferences"]
        else:
            chat_memory = []
            session_prefs = {"merek_favorit": set(), "kategori_minat": set(), "budget": "Bebas"}

    prefs_for_html = {
        "merek_favorit": list(session_prefs["merek_favorit"]),
        "kategori_minat": list(session_prefs["kategori_minat"]),
        "budget": session_prefs["budget"]
    }

    user_name = session.get('user_name', 'User')

    return render_template('index.html', 
                           chat_history=chat_memory, 
                           error_msg=error_msg, 
                           prefs=prefs_for_html, 
                           sessions=chat_sessions, 
                           active_session_id=active_session_id,
                           user_name=user_name)

@server.route('/switch_chat/<session_id>')
@login_required
def switch_chat(session_id):
    global active_session_id
    active_session_id = session_id
    return redirect('/chat')

@server.route('/new_chat')
@login_required
def new_chat():
    global active_session_id
    active_session_id = str(uuid.uuid4())
    return redirect('/chat')

@server.route('/delete_multiple', methods=['POST'])
@login_required
def delete_multiple_chats():
    global chat_sessions, active_session_id
    selected_ids = request.form.getlist('selected_chats')
    
    chat_sessions = [s for s in chat_sessions if s["id"] not in selected_ids]
    
    if not chat_sessions or active_session_id in selected_ids:
        active_session_id = str(uuid.uuid4())
            
    return redirect('/chat')

# =======================================================
# --- API ENDPOINTS ---
# =======================================================
@server.route('/api/products', methods=['GET'])
def api_get_products():
    try:
        products = app.load_products("products.json")
        return jsonify({"status": "success", "total_products": len(products), "data": products}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@server.route('/api/preferences', methods=['GET'])
def api_get_preferences():
    current_session = next((s for s in chat_sessions if s["id"] == active_session_id), None)
    if current_session:
        prefs = current_session["preferences"]
    else:
        prefs = {"merek_favorit": set(), "kategori_minat": set(), "budget": "Bebas"}
        
    prefs_for_json = {
        "merek_favorit": list(prefs["merek_favorit"]),
        "kategori_minat": list(prefs["kategori_minat"]),
        "budget": prefs["budget"]
    }
    return jsonify({"status": "success", "preferences": prefs_for_json}), 200

@server.route('/api/chat', methods=['POST'])
def api_chat():
    global chat_sessions, active_session_id
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"status": "error", "message": "Format JSON salah."}), 400
        
    raw_query = data.get('message', '')
    user_query = app.clean_text(raw_query)
    
    if not user_query.strip():
        return jsonify({"status": "error", "message": "Pesan tidak boleh kosong."}), 400
    
    current_session = next((s for s in chat_sessions if s["id"] == active_session_id), None)
    if not current_session:
        current_session = {
            "id": active_session_id, 
            "title": user_query[:25] + "...", 
            "messages": [],
            "preferences": {"merek_favorit": set(), "kategori_minat": set(), "budget": "Bebas"}
        }
        chat_sessions.insert(0, current_session)
        
    chat_memory = current_session["messages"]
    session_prefs = current_session["preferences"]
    
    summary_algo = 'recommendation' 
    products = app.load_products("products.json")
    start_time = time.time()
    
    ai_response, has_error, eval_data = app.ask_ai(
        user_query, products, chat_memory, None, summary_algo, session_prefs
    )
    
    latency = round(time.time() - start_time, 2)
    if has_error:
        return jsonify({"status": "error", "message": ai_response}), 500
        
    chat_memory.append({
        "user": user_query,
        "ai": ai_response,
        "image": "", "image_mime": "", "algo": summary_algo,
        "latency": latency, "eval": eval_data
    })
    
    return jsonify({
        "status": "success",
        "data": {
            "user_query": user_query,
            "ai_response_html": ai_response,
            "latency": latency
        }
    }), 200

@server.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    global chat_sessions, active_session_id
    data = request.get_json()
    if not data: return jsonify({"status": "error", "message": "Tidak ada data"}), 400
        
    chat_idx = data.get('chat_index')
    feedback_type = data.get('feedback')
    
    current_session = next((s for s in chat_sessions if s["id"] == active_session_id), None)
    if current_session and chat_idx is not None and 0 <= chat_idx < len(current_session["messages"]):
        current_session["messages"][chat_idx]['usability_feedback'] = feedback_type
        return jsonify({"status": "success"})
        
    return jsonify({"status": "error", "message": "Indeks tidak valid"}), 400

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    print("🚀 Server Flask berjalan...")
    Timer(1, open_browser).start()
    server.run(debug=True)