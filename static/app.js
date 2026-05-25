let isSubmitting = false;

// Fungsi untuk memunculkan efek loading visual secara universal
function showLoadingVisuals(userText) {
    // 1. Ubah tombol kirim utama menjadi lingkaran loading yang mulus (seperti di video)
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>'; 
    }

    // 2. Siapkan wadah chat
    let historyContainer = document.getElementById('chat-history-container');
    const welcomeContainer = document.querySelector('.welcome-container');

    // Sembunyikan pesan sambutan jika ada
    if (welcomeContainer) welcomeContainer.style.display = 'none';

    // Buat wadah obrolan jika belum ada
    if (!historyContainer) {
        historyContainer = document.createElement('div');
        historyContainer.id = 'chat-history-container';
        historyContainer.className = 'chat-history-container';
        const contentArea = document.querySelector('.content-area');
        if (contentArea) contentArea.appendChild(historyContainer);
    }

    // 3. Munculkan teks dari pengguna secara instan
    if (userText && userText.trim() !== '') {
        const userBubble = `
            <div class="chat-wrapper user-wrapper" style="opacity: 0.7;">
                <div class="chat-message user-message">${userText}</div>
            </div>
        `;
        historyContainer.insertAdjacentHTML('beforeend', userBubble);
    }

    // 4. Munculkan animasi mengetik AI (titik-titik melompat)
    const loadingBubble = `
        <div class="chat-wrapper ai-wrapper">
            <div class="chat-message ai-message">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
    historyContainer.insertAdjacentHTML('beforeend', loadingBubble);

    // 5. Gulir (scroll) ke bawah otomatis
    const bottomDiv = document.getElementById('bottom-of-chat');
    if (bottomDiv) {
        bottomDiv.scrollIntoView({ behavior: 'smooth' });
    } else {
        window.scrollTo(0, document.body.scrollHeight);
    }
}

// Fungsi khusus saat tombol "Rekomendasi Cerdas" ditekan
function triggerSmartRecommendation(btnElement) {
    if (isSubmitting) return;
    isSubmitting = true;
    
    // Ubah tombol rekomendasi menjadi animasi loading melingkar
    btnElement.disabled = true;
    btnElement.innerHTML = '<i class="fas fa-circle-notch fa-spin" style="color: var(--accent-color);"></i> Memproses...';
    btnElement.style.opacity = '0.7';

    const messageInput = document.getElementById('messageInput');
    const textToSubmit = 'Beri saya rekomendasi produk yang cocok berdasarkan obrolan kita sejauh ini';
    
    if (messageInput) {
        messageInput.value = textToSubmit;
    }

    // Panggil efek visual loading
    showLoadingVisuals(textToSubmit);

    // Kirim form ke server
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.submit(); 
    }
}

// Fungsi untuk menampilkan pratinjau gambar di chat dengan efek loading
function handleChatImagePreview(event) {
    const input = event.target; 
    const previewContainer = document.getElementById('chat_preview_container'); 
    const previewImage = document.getElementById('chat_preview_img'); 
    const removeBtn = document.getElementById('remove_chat_img_btn');
    const wrapper = previewContainer.querySelector('.preview-wrapper');

    if (input.files && input.files[0]) {
        const file = input.files[0];

        if (file.type.startsWith('image/')) {
            // 1. Munculkan wadah utama, tapi sembunyikan gambar & tombol X sementara
            previewContainer.style.display = 'block';
            previewImage.style.display = 'none';
            if (removeBtn) removeBtn.style.display = 'none';

            // 2. Buat elemen loading melingkar (spinner) jika belum ada
            let loadingSpinner = document.getElementById('preview_loading_spinner');
            if (!loadingSpinner) {
                loadingSpinner = document.createElement('div');
                loadingSpinner.id = 'preview_loading_spinner';
                loadingSpinner.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
                wrapper.prepend(loadingSpinner);
            } else {
                loadingSpinner.style.display = 'flex';
            }

            const reader = new FileReader();

            reader.onload = function(e) {
                // 3. Beri sedikit jeda (simulasi loading seperti di video) agar efeknya terasa
                setTimeout(() => {
                    // Sembunyikan spinner loading
                    if (loadingSpinner) loadingSpinner.style.display = 'none';
                    
                    // Munculkan gambar asli
                    previewImage.src = e.target.result;
                    previewImage.style.display = 'block';
                    
                    // Munculkan tombol X
                    if (removeBtn) removeBtn.style.display = 'flex'; 
                }, 600); // 600ms jeda animasi (bisa kamu perbesar jika ingin lebih lama)
            };

            reader.readAsDataURL(file);
        } else {
            alert("Harap pilih file gambar.");
            input.value = ""; 
        }
    } else {
        // Jika user membatalkan pilihan
        previewContainer.style.display = 'none';
    }
}

// Fungsi untuk menghapus gambar saat tombol 'X' ditekan
function removeChatImage() {
    const input = document.getElementById('file-upload');
    const previewContainer = document.getElementById('chat_preview_container');
    
    input.value = ""; // Kosongkan file yang sudah dipilih
    previewContainer.style.display = 'none'; // Sembunyikan kembali pratinjau
}

document.addEventListener('DOMContentLoaded', function() {
    // 1. Tangkap elemen input file dari form chat
    const chatFileInput = document.getElementById('file-upload');
    if (chatFileInput) {
        chatFileInput.addEventListener('change', handleChatImagePreview);
    }

    // 2. Tangkap tombol X pada pratinjau
    const removeBtn = document.getElementById('remove_chat_img_btn');
    if (removeBtn) {
        removeBtn.addEventListener('click', removeChatImage);
    }

    // 3. Cegah Double Submit & Tampilkan Animasi Loading
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', function(event) {
            if (isSubmitting) {
                event.preventDefault(); 
                return;
            }
            isSubmitting = true; 
            const messageInput = document.getElementById('messageInput');
            showLoadingVisuals(messageInput ? messageInput.value : '');
        });
    }

    // ==========================================
    // 4. KODE BARU: Animasi Jawaban AI (Slide-Up Murni, Tanpa Turun Otomatis)
    // ==========================================
    const aiContents = document.querySelectorAll('.ai-content');
    if (aiContents.length > 0) {
        // Ambil elemen jawaban AI yang PALING TERAKHIR
        const lastAiContent = aiContents[aiContents.length - 1];
        const lastAiWrapper = lastAiContent.closest('.ai-wrapper');
        
        // 1. PARKIR INSTAN TANPA ANIMASI
        // Layar akan langsung bersiap di atas jawaban baru.
        if (lastAiWrapper) {
            const elementPosition = lastAiWrapper.getBoundingClientRect().top + window.scrollY;
            window.scrollTo({
                top: elementPosition - 20, 
                behavior: 'auto'
            });
        }

        // 2. Ambil semua bagian teks utuh, list poin, dan gambar
        const elementsToReveal = lastAiContent.querySelectorAll('p, li, img, h1, h2, h3, h4, blockquote');
        
        if (elementsToReveal.length > 0) {
            // Sembunyikan dengan opacity DAN geser sedikit ke bawah 20px
            elementsToReveal.forEach(el => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(20px)'; 
                el.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
            });
            
            const evalMetrics = lastAiWrapper ? lastAiWrapper.querySelector('.eval-metrics') : null;
            const usabilityFeedback = lastAiWrapper ? lastAiWrapper.querySelector('.usability-feedback') : null;
            
            if (evalMetrics) evalMetrics.style.opacity = '0';
            if (usabilityFeedback) usabilityFeedback.style.opacity = '0';

            let index = 0;
            
            // 3. Munculkan teks utuh satu per satu secara tenang (Slide-Up)
            function revealNextElement() {
                if (index < elementsToReveal.length) {
                    const currentEl = elementsToReveal[index]; 
                    
                    // Meluncur naik ke posisi asli secara tenang
                    currentEl.style.opacity = '1';
                    currentEl.style.transform = 'translateY(0)'; 
                    
                    // KITA HAPUS SEMUA LOGIKA AUTO-SCROLL DI SINI
                    // Layar tidak akan terdorong turun sama sekali.
                    
                    index++;
                    setTimeout(revealNextElement, 150); // Jeda antar elemen (150ms)
                } else {
                    // Tampilkan metrik & tombol jempol setelah semua teks selesai
                    if (evalMetrics) {
                        evalMetrics.style.transition = 'opacity 0.5s ease-in';
                        evalMetrics.style.opacity = '1';
                    }
                    if (usabilityFeedback) {
                        usabilityFeedback.style.transition = 'opacity 0.5s ease-in';
                        usabilityFeedback.style.opacity = '1';
                    }
                    
                    // KITA JUGA MENGHAPUS GULIRAN OTOMATIS DI AKHIR ANIMASI
                    // Agar layar benar-benar statis sampai kamu menggulirnya sendiri.
                }
            }
            
            // Mulai munculkan teks 300ms setelah halaman dimuat
            setTimeout(revealNextElement, 300);
        }
    }
});

// ============================
// FUNGSI MODAL PREFERENSI
// ============================

// Fungsi untuk membuka dan mengisi data ke dalam modal
function showPreferenceModal(title, contentData) {
    const modal = document.getElementById('prefModal');
    const modalTitle = document.getElementById('prefModalTitle');
    const modalBody = document.getElementById('prefModalBody');

    // Set judul popup
    modalTitle.textContent = "Riwayat " + title;
    
    // Cek apakah ada data preferensi
    if (contentData && contentData !== 'Belum ada' && contentData !== 'Bebas') {
        // Pisahkan teks yang dibatasi koma menjadi array
        const items = contentData.split(', ');
        
        // Buat format HTML berupa daftar (bullet points)
        let htmlList = '<ul style="padding-left: 20px; margin-top: 10px;">';
        items.forEach(item => {
            htmlList += `<li style="margin-bottom: 8px;"><strong>${item}</strong></li>`;
        });
        htmlList += '</ul>';
        
        modalBody.innerHTML = `<p>Berdasarkan obrolan sejauh ini, kami mendeteksi minatmu pada:</p> ${htmlList}`;
    } else {
        // Jika belum ada data
        modalBody.innerHTML = `
            <p>Belum ada riwayat terdeteksi untuk <strong>${title}</strong>.</p>
            <p style="color: var(--text-secondary); font-size: 12px; margin-top: 15px;">
                <i class="fas fa-info-circle"></i> Mulai ngobrol dengan ShopAssist agar kami bisa mengenali preferensimu!
            </p>
        `;
    }

    // Tampilkan modal
    modal.style.display = 'flex'; 
}

// Fungsi untuk menutup modal
function closePreferenceModal() {
    const modal = document.getElementById('prefModal');
    modal.style.display = 'none';
}

// Tambahkan event agar modal tertutup jika user mengklik area gelap (luar kotak)
window.addEventListener('click', function(event) {
    const modal = document.getElementById('prefModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

// ============================
// FUNGSI USABILITY TESTING (FEEDBACK)
// ============================

// Fungsi untuk mengirim (dan membatalkan) evaluasi jempol ke server
function sendFeedback(chatIndex, feedbackType, buttonElement) {
    // 1. Cek apakah tombol yang diklik sedang dalam keadaan aktif
    let isAlreadyActive = false;
    if (feedbackType === 'up' && buttonElement.classList.contains('active-up')) {
        isAlreadyActive = true;
    } else if (feedbackType === 'down' && buttonElement.classList.contains('active-down')) {
        isAlreadyActive = true;
    }

    // 2. Jika sudah aktif, user ingin membatalkan (kita kirim null ke server)
    const finalFeedback = isAlreadyActive ? null : feedbackType;

    // 3. Siapkan data yang akan dikirim ke Flask
    const data = {
        chat_index: parseInt(chatIndex),
        feedback: finalFeedback
    };

    // 4. Kirim data ke endpoint API di Flask secara diam-diam
    fetch('/submit_feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            // 5. Ubah warna tombol untuk memberikan respon visual ke pengguna
            const feedbackContainer = buttonElement.parentElement;
            
            // Hapus status aktif dari semua tombol di dalam wadah tersebut
            const allButtons = feedbackContainer.querySelectorAll('.feedback-btn');
            allButtons.forEach(btn => {
                btn.classList.remove('active-up', 'active-down');
            });
            
            // Jika BUKAN pembatalan, berikan warna aktif pada tombol yang baru diklik
            if (!isAlreadyActive) {
                if (feedbackType === 'up') {
                    buttonElement.classList.add('active-up');
                } else if (feedbackType === 'down') {
                    buttonElement.classList.add('active-down');
                }
                console.log("✅ Usability feedback berhasil dicatat!");
            } else {
                console.log("❎ Usability feedback dibatalkan!");
            }
        } else {
            console.error("❌ Gagal menyimpan feedback:", result.message);
        }
    })
    .catch(error => {
        console.error("❌ Terjadi kesalahan jaringan saat mengirim feedback:", error);
    });
}