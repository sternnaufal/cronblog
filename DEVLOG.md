# Devlog

Catatan pengembangan cronblog. Berbeda dari `CHANGELOG.md` yang ringkas,
devlog mencatat alasan, temuan teknis, dan keputusan di balik perubahan.

---

## 2026-11-03 — v1.1.0: otomasi penuh di server

### Konteks

Bot dipasang di VPS Debian 13 dan dijalankan otomatis lewat cron setiap hari
jam 12.00 WIB. Provider AI memakai gateway OpenAI-compatible (cfrouter),
bukan API lokal seperti 9router/Ollama.

### Temuan teknis

1. **Gateway memutus request non-streaming di ~90 detik.**
   Request artikel penuh selalu berakhir `502 Bad Gateway` setelah ±90 detik,
   padahal request pendek berhasil. Solusinya memakai `stream=True` dan
   mengumpulkan delta chunk. Dengan streaming, artikel 18 ribu karakter
   selesai dalam ~105 detik tanpa putus.

2. **Blogger API v3 tidak mendukung Search Description.**
   Field `customMetaData` yang dulu dipakai sudah deprecated. Saat diuji,
   `posts.patch` mengembalikan `customMetaData: None` dan nilainya tidak
   tersimpan saat dibaca ulang. Meta description per artikel karena itu tidak
   bisa diisi lewat API resmi.

3. **Refresh token OAuth mati setelah 7 hari saat status Testing.**
   Token yang dibuat sebelum aplikasi dipublish tidak bisa dipakai lagi
   (`invalid_grant`). Solusinya mengubah OAuth consent ke **In production**
   sebelum generate token baru.

4. **RSS umum menghasilkan topik di luar niche.**
   Google News umum sempat menghasilkan topik vape dan banjir. Feed diganti
   ke sumber teknologi/internet dan prompt diberi aturan niche eksplisit.

5. **Label terlalu umum.**
   Prompt lama hanya mengizinkan satu label dari daftar statis. Akibatnya
   topik baru seperti Kubernetes tetap masuk ke label lama. Sekarang bot
   membaca taksonomi blog dari feed publik dan membuat label baru bila perlu.

### Keputusan desain

- **Queue manual diprioritaskan di atas RSS.** Pemilik blog bisa menentukan
  topik lewat `blog_title_queue.txt`. Topik baru dihapus setelah publish
  berhasil, bukan setelah generate, supaya kegagalan tidak menghilangkan ide.
- **Label dinamis 3-5 per artikel.** Label pertama wajib spesifik ke topik
  utama; sisanya kategori luas. Ini menjaga taksonomi tetap rapi tanpa
  mengunci topik baru.
- **Streaming hanya untuk custom API.** Fallback Gemini/OpenAI tidak
  mengalami masalah timeout yang sama, jadi tidak diubah agar diff tetap kecil.
- **`--dry-run` tidak butuh OAuth Blogger.** Memudahkan pengujian pipeline
  dan generate artikel sebelum kredensial siap.

### Catatan operasional

- Cron server: `0 12 * * *` (Asia/Jakarta).
- Log: `logs/cron.log`, dirotasi mingguan oleh logrotate.
- `run.sh` memakai `flock` supaya run tidak tumpang tindih.
- File sensitif (`.env`, `token.json`, `client_secret.json`) tidak masuk repo.

### TODO berikutnya

- [ ] Meta description otomatis lewat edit tema Blogger (`data:post.snippet`).
- [ ] Pantau biaya token per artikel dan tambahkan ringkasan pemakaian.
- [ ] Tambahkan test unit untuk `topic_queue` dan ekstraksi label.
- [ ] Opsi rotasi beberapa topik queue per run (`MAX_ARTICLES_PER_RUN > 1`).
