from flask import Flask, request, render_template_string
from inference_engine import load_knowledge_base, forward_chaining_with_cf
import os

app = Flask(__name__)

# Muat knowledge base
KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
kb = load_knowledge_base(KB_PATH)

# ==================== TEMPLATE HALAMAN ====================

INDEX_HTML = """    
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Sistem Pakar Diagnosa Penyakit Lambung</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    body {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #e3f2fd, #ffffff);
        color: #333;
        margin: 0;
        padding: 0;
    }
    header {
        background-color: #1976d2;
        color: white;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    }
    header h1 {
        margin: 0;
        font-weight: 600;
    }
    main {
        max-width: 900px;
        background: #fff;
        margin: 40px auto;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .q {
        margin-bottom: 18px;
        padding: 14px;
        background: #f9f9f9;
        border-radius: 10px;
        transition: all 0.2s ease;
    }
    .q:hover {
        background: #cbe0fc;
    }
    label {
        margin-right: 20px;
        font-size: 0.95rem;
    }
    .btn {
        background-color: #1976d2;
        color: white;
        padding: 12px 24px;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    .btn:hover {
        background-color: #125ea8;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    footer {
        text-align: center;
        color: #888;
        font-size: 0.85rem;
        margin: 30px 0;
    }
</style>
</head>
<body>
    <header>
        <h1>Sistem Pakar Diagnosa Penyakit Lambung</h1>
        <p>Jawab pertanyaan berikut sesuai gejala yang Anda alami.</p>
    </header>

    <main>
        <form method="post" action="{{ url_for('evaluate') }}">
            {% for cid, text in conditions %}
            <div class="q">
                <strong>{{ loop.index }}. {{ text }}</strong><br>
                <label><input type="radio" name="{{ cid }}" value="ya" required> Ya</label>
                <label><input type="radio" name="{{ cid }}" value="tidak" required checked> Tidak</label>
            </div>
            {% endfor %}
            <button class="btn" type="submit">🔍 Submit Diagnosa</button>
        </form>
    </main>

    <footer>
        &copy; 2025 Sistem Pakar Lambung | Dibuat oleh Ridho dan Rafly 
    </footer>
</body>
</html>
"""
RESULT_HTML = """
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Hasil Diagnosa</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { font-family: 'Poppins', sans-serif; background: #f1f8ff; margin:0; padding:0; }
    header { background-color: #1976d2; color: white; padding: 20px; text-align: center; font-size: 26px; }
    main { max-width: 900px; background: #fff; margin: 40px auto; padding: 30px 40px; 
           border-radius: 20px; box-shadow: 0 4px 30px rgba(0,0,0,0.08); }
    .utama { background:#e9f4ff; padding: 18px 20px; border-left: 6px solid #1976d2;
             border-radius: 12px; margin-bottom: 28px; }
    .detail { background:#fafafa; padding: 12px 18px; border-radius:10px; margin-bottom: 15px; }
    h2, h3 { color:#0d47a1; font-weight:600; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 10px; text-align:center; }
    th { background: #1976d2; color:white; }
    .btn {
        display:inline-block; background:#1976d2; color:white; padding:10px 26px;
        border-radius:10px; text-decoration:none; font-size:1rem;
        margin-top:25px; transition:0.3s;
    }
    .btn:hover { background:#125ea8; }
    footer { text-align:center; margin:30px 0 10px; color:#666; font-size:14px; }
</style>
</head>
<body>

<header>Hasil Diagnosa</header>

<main>

{% if results %}
    <div class="utama">
        <strong>Penyakit Dominan: {{ results[0]['penyakit'] }}</strong><br>
        Nilai CF: <strong>{{ results[0]['cf'] }}</strong>
    </div>

    <h3>Detail Kemungkinan Penyakit</h3>
    {% for r in results %}
    <div class="detail">
        <strong>{{ loop.index }}. {{ r['penyakit'] }}</strong><br>
        Nilai CF: {{ r['cf'] }}
    </div>
    {% endfor %}
{% else %}
    <p>Tidak ditemukan penyakit yang cocok dengan gejala Anda.</p>
{% endif %}

    <h3 style="margin-top:35px;">Tabel Skala Keyakinan (Certainty Factor)</h3>

    <table>
        <tr><th>Tingkat Keyakinan</th><th>Nilai CF</th></tr>
        <tr><td>Pasti Tidak</td><td>0.0</td></tr>
        <tr><td>Hampir Pasti Tidak</td><td>0.1</td></tr>
        <tr><td>Kemungkinan Besar Tidak</td><td>0.2</td></tr>
        <tr><td>Mungkin Tidak</td><td>0.3</td></tr>
        <tr><td>Tidak Tahu</td><td>0.4</td></tr>
        <tr><td>Mungkin</td><td>0.5</td></tr>
        <tr><td>Kemungkinan Besar</td><td>0.6</td></tr>
        <tr><td>Hampir Pasti</td><td>0.8</td></tr>
        <tr><td>Pasti</td><td>1.0</td></tr>
    </table>

    <center><a class="btn" href="{{ url_for('index') }}">⬅ Kembali</a></center>
</main>

<footer>© 2025 Sistem Pakar Lambung</footer>

</body>
</html>
"""


# ==================== ROUTE APLIKASI ====================

@app.route("/", methods=["GET"])
def index():
    conditions = [(cid, data["text"]) for cid, data in kb["conditions"].items()]
    conditions.sort()
    return render_template_string(INDEX_HTML, conditions=conditions)

@app.route("/evaluate", methods=["POST"])
def evaluate():
    answers = {cid: (request.form.get(cid, "tidak").lower() == "ya") for cid in kb["conditions"].keys()}
    results = forward_chaining_with_cf(answers, kb)
    return render_template_string(RESULT_HTML, results=results)

if __name__ == "__main__":
    app.run(debug=True)
