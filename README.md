<h1>Temu Coach</h1>

<ul>
  <li>Anggota Kelompok</li>
  <br>
  <ul>
    <li>Mohammad Aly Haidarulloh - 2406425804</li>
    <li>Alvino Revaldi - 2406438933</li>
    <li>Erico Putra Bani Mahendra - 2406423181</li>
    <li>Benedictus Lucky Win Ziraluo - 2406355174</li>
    <li>Muhammad Rayyan Basalamah - 2406496372</li>
  </ul>
  <br>

  <li>Deskripsi Website</li>
  <br>
  <p>
    Temu Coach adalah sebuah platform inovatif yang dirancang untuk memudahkan pengguna dalam mencari dan mengakses pelatih olahraga sepak bola sesuai kebutuhan mereka, baik untuk latihan individu maupun kelompok. Melalui platform ini, pengguna dapat menjelajahi katalog coach yang lengkap, melihat detail profil setiap coach termasuk keahlian, pengalaman, dan testimoni, sehingga mempermudah proses pemilihan pelatih yang tepat.
    Selain itu, Temu Coach juga menyediakan fitur booking yang praktis, memungkinkan pengguna untuk langsung memesan sesi pelatihan dengan coach pilihan mereka. Pengguna dapat mengelola jadwal latihan melalui halaman khusus yang menampilkan appointment yang telah diblok, sehingga setiap sesi dapat diatur dengan rapi. Platform ini juga dilengkapi dengan fitur login, register, dan profile, sehingga pengalaman pengguna menjadi personal dan aman. Dengan Temu Coach, proses menemukan, memesan, dan mengikuti pelatihan olahraga menjadi lebih mudah, efisien, dan menyenangkan.
  </p>
  <br>

  <li>Daftar Modul</li>
  <ul>
    <li>Booking Coach</li>
    <li>Review & Rating</li>
    <li>Schedule Coach</li>
    <li>Chat</li>
    <li>Admin</li>
  </ul>
  <br>

  <li>Dataset</li>
  <br>
  <ul>
    <li>Initial dataset</li>
    <a href="https://www.kaggle.com/datasets/vaske93/football-coaches-stats-and-tropheys">
      Link
    </a>
    <li>Optimized dataset</li>
    <a href="https://docs.google.com/spreadsheets/d/1VpbFWbfDfLLzqHnxs6drkVwHoHVLWPuYqq38j0243AM/edit?usp=drive_link">
      Link
    </a>
  </ul>
  <br>

  <li>Role atau Peran User</li>
  <ul>
    <li>Customer</li>
    <ol>
      <li>Bisa melakukan booking coach</li>
      <li>Bisa memberi review dan rating pada coach</li>
      <li>Bisa mengelola booking</li>
      <li>Bisa melakukan chat dengan coach</li>
      <li>Bisa melaporkan coach</li>
    </ol>
    <li>Coach</li>
    <ol>
      <li>Bisa membuat, mengedit, dan menghapus jadwal</li>
      <li>Bisa melakukan chat dengan customer</li>
    </ol>
    <li>Admin</li>
    <ol>
      <li>Bisa melakukan ban pada coach</li>
      <li>Bisa meng-cancel report</li>
      <li>Bisa meng-acc coach yang register</li>
    </ol>
  </ul>
  <br>

  <li>Tautan Deployment PWS</li>
  <a href="https://erico-putra-temucoach.pbp.cs.ui.ac.id/">
    Link Website
  </a>
  <br>

  <li>Tautan Design Website (Figma)</li>
  <a href="https://www.figma.com/design/Kl4YECItsI2E932xoYIP8O/TemuCoach-UI-UX-Design?node-id=0-1&p=f&t=wNcKrVE8xbU9RZCe-0">
    Link
  </a>
  <br>

  <li>Getting Started</li>
  <br>
  <p>
    Berikut langkah-langkah untuk menjalankan proyek ini secara lokal:
  </p>

  <ol>
    <li><strong>Clone repository</strong></li>
    <pre><code>git clone https://github.com/[username]/temu-coach.git
cd temu-coach
    </code></pre>

    <li><strong>Buat dan aktifkan virtual environment</strong></li>
    <pre><code>python -m venv venv
venv\Scripts\activate      # untuk Windows
source venv/bin/activate   # untuk Mac/Linux  
    </code></pre>

    <li><strong>Install dependencies</strong></li>
    <pre><code>pip install -r requirements.txt
    </code></pre>

    <li><strong>Jalankan migrasi database</strong></li>
    <pre><code>python manage.py makemigrations
python manage.py migrate
    </code></pre>

    <li><strong>Jalankan aplikasi secara lokal</strong></li>
    <pre><code>python manage.py runserver
    </code></pre>
    <p>Kemudian buka <a href="http://localhost:8000">http://localhost:8000</a> di browser.</p>

    <li><strong>Menjalankan test suite</strong></li>
    <pre><code>python manage.py test
    </code></pre>
  </ol>
</ul>
