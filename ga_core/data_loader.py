import pandas as pd
import os
import math
import random

# ===============================
# KONFIGURASI
# ===============================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CURRENT_DIR, '..', 'data')
SEMESTER_ACTIVE = "Ganjil" 
ROOM_CAPACITY_DEFAULT = 40 

# ===============================
# 1. LOAD DATA DASAR
# ===============================
def load_time_slots(path):
    df = pd.read_csv(path)
    df = df.rename(columns={"hari": "Hari", "jam_mulai": "Mulai", "jam_selesai": "Selesai", "sks": "sks_val"})
    if 'Sesi' in df.columns: df = df.drop(columns=['Sesi'])
    df["slot_id"] = df.index
    return df.to_dict(orient="records")

def load_rooms(path):
    df = pd.read_csv(path)
    df = df.rename(columns={"Ruang Kelas": "Ruang", "Kapasitas Max (Mahasiswa)": "Kapasitas"})
    df["room_id"] = df.index
    return df.to_dict(orient="records")

def load_student_counts(path):
    df = pd.read_csv(path)
    df = df[df['Angkatan'] != 'Total']
    current_year = 2025
    mapping = {}
    for _, row in df.iterrows():
        try:
            angkatan = int(row['Angkatan'])
            sem = (current_year - angkatan) * 2 + 1
            mapping[sem] = int(row['Jumlah Mahasiswa TIF'])
        except ValueError: continue
    return mapping

# ===============================
# 2. LOAD PREFERENSI (DATA FLEXIBILITY)
# ===============================
def load_preference_data(path):
    df = pd.read_csv(path)
    candidates_dict = {}
    pref_info = {}
    
    for _, row in df.iterrows():
        dosen = str(row['Nama Dosen']).strip()
        kode_mk = str(row['Kode MK']).strip()
        prioritas = int(row['Prioritas'])
        role = str(row['Berminat'])
        
        if kode_mk not in candidates_dict:
            candidates_dict[kode_mk] = []
        # Hindari duplikasi nama di list kandidat
        if dosen not in candidates_dict[kode_mk]:
            candidates_dict[kode_mk].append(dosen)
            
        pref_info[(dosen, kode_mk)] = {'prioritas': prioritas, 'role': role}
        
    return candidates_dict, pref_info

# ===============================
# 3. CLASS CREATION
# ===============================
def create_class_objects(kode, nama_mk_clean, sks_total, sem, parallel, assigned_dosen, pref_info, counter):
    sks_parts = []
    if sks_total == 4: sks_parts = [2, 2]
    elif sks_total == 5: sks_parts = [3, 2]
    elif sks_total == 6: sks_parts = [3, 3]
    else: sks_parts = [sks_total]

    new_classes = []
    info = pref_info.get((assigned_dosen, kode), None)
    
    # Validasi Prioritas
    final_prio = 99
    if info:
        prio = info['prioritas']
        role_str = info['role']
        valid_roles = ["Koordinator Pengelola", "Pengelola", "Pengampu"]
        if any(r in role_str for r in valid_roles):
            final_prio = prio

    for i, sks_part in enumerate(sks_parts):
        part_suffix = f" (Sesi {i+1})" if len(sks_parts) > 1 else ""
        obj = {
            "class_id": counter + i,
            "kode_mk": kode,
            "nama_mk": nama_mk_clean + part_suffix,
            "sks": sks_part,
            "sks_asli": sks_total,
            "dosen": assigned_dosen, 
            "dosen_priority": final_prio,
            "jumlah_mhs": ROOM_CAPACITY_DEFAULT,
            "semester": sem,
            "parallel": parallel,
            "is_split": len(sks_parts) > 1
        }
        new_classes.append(obj)
    return new_classes, counter + len(new_classes)

# ===============================
# 4. GENERATOR KELAS (DENGAN SKS THRESHOLD)
# ===============================
def load_mk_active(path_wajib, path_pilihan, candidates_dict, pref_info, student_counts):
    classes = []
    counter = 0
    dosen_workload_tracker = {} 

    # --- FUNGSI PINTAR PEMILIHAN DOSEN ---
    def get_best_dosen(kode_mk, sks_mk):
        candidates = candidates_dict.get(kode_mk, [])
        if not candidates: return "Unknown Dosen"
        
        # 1. Shuffle kandidat untuk fairness acak
        random.shuffle(candidates)
        
        # 2. CARI KANDIDAT YANG BELUM "KENYANG" (< 12 SKS)
        # Prioritaskan mereka dulu tanpa peduli "Prioritas Preferensi"
        underloaded_candidates = []
        for d in candidates:
            load = dosen_workload_tracker.get(d, 0)
            if load + sks_mk <= 12: # Batas aman
                # Simpan kandidat + skor prioritasnya
                prio = pref_info.get((d, kode_mk), {'prioritas': 99})['prioritas']
                underloaded_candidates.append((d, prio))
        
        # Jika ada kandidat yang masih kosong/sedikit beban, PILIH MEREKA DULU!
        if underloaded_candidates:
            # Urutkan berdasarkan prioritas (1 terbaik), tapi hanya di antara yang underloaded
            underloaded_candidates.sort(key=lambda x: x[1]) 
            chosen = underloaded_candidates[0][0]
            dosen_workload_tracker[chosen] = dosen_workload_tracker.get(chosen, 0) + sks_mk
            return chosen

        # 3. JIKA SEMUA SUDAH > 12 SKS (Overload Massal)
        # Baru kita cari yang "Paling Sedikit Overload-nya"
        best_candidate = candidates[0]
        min_load = float('inf')
        
        for d in candidates:
            current_load = dosen_workload_tracker.get(d, 0)
            if current_load < min_load:
                min_load = current_load
                best_candidate = d
                
        dosen_workload_tracker[best_candidate] = dosen_workload_tracker.get(best_candidate, 0) + sks_mk
        return best_candidate
    # -------------------------------------

    # 1. LOAD SEMUA DATA DULU
    df_w = pd.read_csv(path_wajib)
    df_w.columns = [c.lower() for c in df_w.columns]
    
    df_p = pd.read_csv(path_pilihan)
    df_p.columns = [c.lower() for c in df_p.columns]

    # 2. GABUNGKAN MK WAJIB & PILIHAN AGAR BISA DIACAK TOTAL
    # Kita butuh list of dictionary untuk diproses
    all_mk_to_process = []

    # Prepare Wajib
    for _, row in df_w.iterrows():
        sem = row['semester']
        if sem > 7: continue
        target_mod = 1 if SEMESTER_ACTIVE == "Ganjil" else 0
        if sem % 2 != target_mod: continue
        
        total_mhs = student_counts.get(sem, 0)
        num_classes = math.ceil(total_mhs / ROOM_CAPACITY_DEFAULT)
        if num_classes == 0: num_classes = 1
        
        for i in range(num_classes):
            all_mk_to_process.append({
                'type': 'Wajib',
                'row': row,
                'suffix': chr(65 + i),
                'sem_label': sem
            })

    # Prepare Pilihan
    for _, row in df_p.iterrows():
        sem_str = row['semester']
        valid = (SEMESTER_ACTIVE == "Ganjil" and "Ganjil" in sem_str) or \
                (SEMESTER_ACTIVE == "Genap" and "Genap" in sem_str)
        if valid:
            all_mk_to_process.append({
                'type': 'Pilihan',
                'row': row,
                'suffix': 'A',
                'sem_label': 'Pilihan'
            })

    # 3. ACAK URUTAN (SHUFFLE) - KUNCI FAIRNESS
    # Agar dosen 'A' tidak selalu dapat jatah duluan
    random.shuffle(all_mk_to_process)

    # 4. PROSES PEMBENTUKAN KELAS
    for item in all_mk_to_process:
        row = item['row']
        kode = row['kode mk']
        sks = row['sks']
        nama = row['nama mk']
        suffix = item['suffix']
        sem_label = item['sem_label']
        
        # Pilih Dosen (Smart Load Balancing)
        assigned_dosen = get_best_dosen(kode, sks)
        
        new_objs, counter = create_class_objects(
            kode, nama, sks, sem_label, suffix, assigned_dosen, pref_info, counter
        )
        classes.extend(new_objs)

    return classes

def load_all_data():
    print(f"\n[Data Loader] Loading Semester: {SEMESTER_ACTIVE} (Smart SKS Thresholding)")
    slots = load_time_slots(os.path.join(DATA_PATH, "Time_Slots v2.csv"))
    rooms = load_rooms(os.path.join(DATA_PATH, "Ruang Kelas.csv"))
    mhs_counts = load_student_counts(os.path.join(DATA_PATH, "Jumlah Mahasiswa TIF.csv"))
    candidates, pref_info = load_preference_data(os.path.join(DATA_PATH, "Preferensi MK dosen TIFv2.csv"))
    
    classes = load_mk_active(
        os.path.join(DATA_PATH, "MK Wajib TIF_All Semester.csv"),
        os.path.join(DATA_PATH, "MK Pilihan TIF_All Semester.csv"),
        candidates, pref_info, mhs_counts
    )

    print(f"✅ Data Loaded: {len(classes)} Sesi Kelas terbentuk.")
    return {
        "slots": slots, "rooms": rooms, "classes": classes,
        "candidates": candidates, "pref_info": pref_info
    }


# Untuk debugging hasil data loader nya

# ===============================
# 5. EXPORT KE CSV (TAMBAHAN)
# ===============================
def save_results_to_csv(data_result, output_folder="hasil_output"):
    # Buat folder jika belum ada
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 1. Simpan Data Kelas (Yang paling penting)
    # Ini berisi mata kuliah yang sudah dipecah SKS-nya dan dipasangkan dengan dosen
    if "classes" in data_result:
        df_classes = pd.DataFrame(data_result["classes"])
        
        # Urutkan biar rapi (opsional): Semester -> Nama MK -> Kelas
        if not df_classes.empty:
            df_classes = df_classes.sort_values(by=["semester", "nama_mk", "class_id"])
            
        file_name = os.path.join(output_path, "1_final_classes_generated.csv")
        df_classes.to_csv(file_name, index=False)
        print(f"✅ [CSV] Data Kelas berhasil disimpan di: {file_name}")

    # 2. Simpan Data Lainnya (Opsional: Slot & Ruang)
    # Berguna untuk memastikan data mentah terbaca dengan benar
    if "slots" in data_result:
        pd.DataFrame(data_result["slots"]).to_csv(os.path.join(output_path, "2_debug_slots.csv"), index=False)
    
    if "rooms" in data_result:
        pd.DataFrame(data_result["rooms"]).to_csv(os.path.join(output_path, "3_debug_rooms.csv"), index=False)

# ===============================
# MAIN EXECUTION (CONTOH CARA PAKAI)
# ===============================
if __name__ == "__main__":
    # 1. Load semua data
    data = load_all_data()
    
    # 2. Cetak ke CSV
    save_results_to_csv(data)