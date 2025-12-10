import pandas as pd
import os
import math

# ===============================
# KONFIGURASI PATH & ENVIRONMENT
# ===============================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CURRENT_DIR, '..', 'data')

# Konfigurasi Semester yang akan dijadwalkan
SEMESTER_ACTIVE = "Ganjil"  # Options: "Ganjil", "Genap"
ROOM_CAPACITY_DEFAULT = 40  # Kapasitas default untuk perhitungan kelas paralel

# ===============================
# 1. LOAD TIME SLOTS (TANPA SESI)
# ===============================
def load_time_slots(path):
    """
    Load data slot waktu.
    Output murni: slot_id, hari, jam_mulai, jam_selesai, sks_val.
    """
    df = pd.read_csv(path)
    
    # Rename kolom agar standar
    df = df.rename(columns={
        "hari": "Hari",
        "jam_mulai": "Mulai",
        "jam_selesai": "Selesai",
        "sks": "sks_val"
    })
    
    # Pastikan tidak ada kolom 'Sesi'
    if 'Sesi' in df.columns:
        df = df.drop(columns=['Sesi'])
        
    # Generate ID unik
    df["slot_id"] = df.index 
    
    return df.to_dict(orient="records")

# ===============================
# 2. LOAD ROOMS
# ===============================
def load_rooms(path):
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Ruang Kelas": "Ruang", 
        "Kapasitas Max (Mahasiswa)": "Kapasitas"
    })
    df["room_id"] = df.index
    return df.to_dict(orient="records")

# ===============================
# 3. HELPER: JUMLAH MAHASISWA
# ===============================
def load_student_counts(path):
    """
    Mengembalikan mapping {Semester_Ke: Jumlah_Mahasiswa}
    Asumsi Tahun Baru = 2025 (Semester 1)
    """
    df = pd.read_csv(path)
    df = df[df['Angkatan'] != 'Total']
    
    current_year = 2025
    mapping = {}
    
    for _, row in df.iterrows():
        try:
            angkatan = int(row['Angkatan'])
            jumlah = int(row['Jumlah Mahasiswa TIF'])
            # Hitung ini semester ke berapa
            sem = (current_year - angkatan) * 2 + 1
            mapping[sem] = jumlah
        except ValueError:
            continue
            
    return mapping

# ===============================
# 4. HELPER: MAPPING DOSEN
# ===============================
def load_dosen_mapping(path):
    df = pd.read_csv(path)
    return dict(zip(df["Full_Name"], df["Normalized_Name"]))

# ===============================
# 5. LOAD PREFERENSI MENGAJAR (BARU)
# ===============================
def load_teaching_preference(path, dosen_map):
    """
    Memuat data kecocokan dosen terhadap mata kuliah.
    Output: Dictionary {(NamaDosen, KodeMK): Prioritas}
    Prioritas 1 = Sangat Kompeten/Berminat
    """
    df = pd.read_csv(path)
    
    # Normalisasi nama dosen
    df["Nama Dosen"] = df["Nama Dosen"].apply(lambda x: dosen_map.get(x, x))
    
    pref_map = {}
    for _, row in df.iterrows():
        dosen = row["Nama Dosen"]
        kode_mk = row["Kode MK"]
        prioritas = row["Prioritas"] # Biasanya 1, 2, dst
        
        # Simpan dalam dictionary key tuple
        pref_map[(dosen, kode_mk)] = prioritas
        
    return pref_map

# ===============================
# 6. LOAD MATA KULIAH AKTIF
# ===============================
def load_pengampu_mk(path, dosen_map):
    df = pd.read_csv(path)
    df = df.rename(columns={"Nama Dosen": "Dosen", "Kode MK": "Kode_MK"})
    df["Dosen"] = df["Dosen"].apply(lambda x: dosen_map.get(x, x))
    return df.groupby("Kode_MK")["Dosen"].apply(list).to_dict()

def load_mk_active(path_wajib, path_pilihan, pengampu_dict, student_counts, pref_map):
    classes = []
    class_id_counter = 0
    
    # --- A. PROSES MK WAJIB ---
    df_wajib = pd.read_csv(path_wajib)
    df_wajib.columns = [c.lower() for c in df_wajib.columns]
    
    for _, row in df_wajib.iterrows():
        sem = row['semester']
        kode = row['kode mk']
        
        # Filter Semester Wajib (Hanya 1, 3, 5 jika Ganjil)
        if sem > 5: continue
        target_sem_mod = 1 if SEMESTER_ACTIVE == "Ganjil" else 0
        if sem % 2 != target_sem_mod: continue
            
        # Hitung Paralel
        total_mhs = student_counts.get(sem, 0)
        num_classes = math.ceil(total_mhs / ROOM_CAPACITY_DEFAULT)
        if num_classes == 0: num_classes = 1
        
        # Ambil list pengampu
        possible_dosens = pengampu_dict.get(kode, ["Unknown Dosen"])
        
        # Generate Kelas Paralel
        for i in range(num_classes):
            suffix = chr(65 + i) # A, B, C...
            
            # Strategi Penunjukan Dosen Awal:
            # Kita ambil dosen secara round-robin dari daftar pengampu yang tersedia
            dosen_selected = possible_dosens[i % len(possible_dosens)]
            
            # Cek Prioritas Dosen tersebut (opsional, untuk info saja saat load)
            prio = pref_map.get((dosen_selected, kode), 99) # 99 jika tidak ada data
            
            classes.append({
                "class_id": class_id_counter,
                "kode_mk": kode,
                "nama_mk": f"{row['nama mk']} - {suffix}",
                "sks": row['sks'],
                "dosen": dosen_selected,
                "dosen_priority": prio, # Simpan ini untuk perhitungan Fitness nanti
                "jumlah_mhs": ROOM_CAPACITY_DEFAULT,
                "jenis": "Wajib",
                "semester": sem
            })
            class_id_counter += 1

    # --- B. PROSES MK PILIHAN ---
    df_pilihan = pd.read_csv(path_pilihan)
    df_pilihan.columns = [c.lower() for c in df_pilihan.columns]
    
    for _, row in df_pilihan.iterrows():
        sem_str = row['semester']
        is_valid = False
        if SEMESTER_ACTIVE == "Ganjil" and "Ganjil" in sem_str: is_valid = True
        elif SEMESTER_ACTIVE == "Genap" and "Genap" in sem_str: is_valid = True
            
        if not is_valid: continue
            
        kode = row['kode mk']
        possible_dosens = pengampu_dict.get(kode, ["Unknown Dosen"])
        dosen_selected = possible_dosens[0] # Ambil yang pertama
        prio = pref_map.get((dosen_selected, kode), 99)

        classes.append({
            "class_id": class_id_counter,
            "kode_mk": kode,
            "nama_mk": f"{row['nama mk']} - A", # Pilihan cuma 1 kelas (A)
            "sks": row['sks'],
            "dosen": dosen_selected,
            "dosen_priority": prio,
            "jumlah_mhs": ROOM_CAPACITY_DEFAULT,
            "jenis": "Pilihan",
            "semester": "Pilihan"
        })
        class_id_counter += 1
        
    return classes

# ===============================
# 7. FUNGSI UTAMA (MAIN LOADER)
# ===============================
def load_all_data():
    print(f"\n[Data Loader] Loading Semester: {SEMESTER_ACTIVE}")
    
    # 1. Load Resources Dasar
    slots = load_time_slots(os.path.join(DATA_PATH, "Time_Slots v2.csv"))
    rooms = load_rooms(os.path.join(DATA_PATH, "Ruang Kelas.csv"))
    
    # 2. Load Info Dosen & Mahasiswa
    mhs_counts = load_student_counts(os.path.join(DATA_PATH, "Jumlah Mahasiswa TIF.csv"))
    map_dosen = load_dosen_mapping(os.path.join(DATA_PATH, "Dosen_Mapping_Normalized.csv"))
    
    # 3. Load Hubungan Dosen-MK (Pengampu & Preferensi)
    pengampu = load_pengampu_mk(os.path.join(DATA_PATH, "Pengelola Prodi TIF.csv"), map_dosen)
    pref_map = load_teaching_preference(os.path.join(DATA_PATH, "Preferensi MK dosen TIFv2.csv"), map_dosen)
    
    # 4. Generate Kelas
    classes = load_mk_active(
        os.path.join(DATA_PATH, "MK Wajib TIF_All Semester.csv"),
        os.path.join(DATA_PATH, "MK Pilihan TIF_All Semester.csv"),
        pengampu,
        mhs_counts,
        pref_map
    )

    print(f"✅ LOAD SUKSES:")
    print(f"   - Slots : {len(slots)} (Tanpa Sesi)")
    print(f"   - Rooms : {len(rooms)}")
    print(f"   - Kelas : {len(classes)} (Wajib + Pilihan)")
    print(f"   - Prefs : {len(pref_map)} record preferensi dosen")
    
    return {
        "slots": slots,
        "rooms": rooms,
        "classes": classes,
        "preferences": pref_map
    }

# ===============================
# TEST RUN
# ===============================
if __name__ == "__main__":
    data = load_all_data()
    
    print("\n[Preview 1 Slot Waktu]:")
    print(data['slots'][0])
    
    print("\n[Preview 1 Kelas (Cek Atribut Dosen & Prioritas)]:")
    print(data['classes'][0])