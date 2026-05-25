# test_app.py
import pytest
import app
from server_flask import server

# 1. Menguji fungsi internal (Unit Test)
def test_clean_text():
    """Memastikan teks kotor HTML dan simbol aneh bisa dibersihkan"""
    teks_kotor = "<p>Halo!!! Ini diskon 50% @#$</p>"
    hasil = app.clean_text(teks_kotor)
    
    # Assert (Pastikan) hasilnya sesuai harapan
    assert "Halo!!! Ini diskon 50%" in hasil
    assert "<p>" not in hasil

# Fixture: Menyiapkan "Klien Tiruan" untuk mengakses web tanpa menyalakan server beneran
@pytest.fixture
def client():
    server.config['TESTING'] = True
    with server.test_client() as client:
        yield client

# 2. Menguji halaman web (Integration Test)
def test_homepage(client):
    """Memastikan halaman utama bisa diakses (Status 200 OK)"""
    
    # KODE BARU: Kita simulasikan robot test sudah login
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_name'] = 'TestUser'

    # Setelah "login", baru kita coba akses halamannya
    response = client.get('/chat')
    
    # Pastikan statusnya sukses (200)
    assert response.status_code == 200
    # Pastikan ada kata ShopAssist di dalam halaman tersebut (dalam format bytes 'b')
    assert b"ShopAssist" in response.data

# 3. Menguji API Data Produk
def test_api_products(client):
    """Memastikan API JSON berjalan dengan baik"""
    response = client.get('/api/products')
    
    assert response.status_code == 200
    assert response.is_json
    
    # Ambil data JSON-nya
    data = response.get_json()
    assert data["status"] == "success"
    assert "total_products" in data

# 4. Menguji API Usability Testing (Feedback)
def test_submit_feedback(client):
    """Memastikan fitur tombol jempol up/down berfungsi dan tersimpan"""
    
    # Langkah 1: Kita harus mengirim pesan pura-pura dulu agar sesi chat terbentuk
    client.post('/api/chat', json={'message': 'Tolong rekomendasikan laptop'})
    
    # Langkah 2: Kita simulasikan user menekan tombol "Jempol Ke Atas" (up)
    # pada balasan pertama (index ke-0)
    data_feedback = {
        "chat_index": 0,
        "feedback": "up"
    }
    
    response = client.post('/submit_feedback', json=data_feedback)
    
    # Langkah 3: Pastikan server menjawab dengan sukses (200 OK)
    assert response.status_code == 200
    
    # Pastikan isi jawaban dari server adalah status success
    data = response.get_json()
    assert data["status"] == "success"