import pandas as pd
import os

def check_flexibility():
    print("=== DIAGNOSA FLEKSIBILITAS JADWAL ===")
    
    # 1. Load File Preferensi
    path_pref = "data/Preferensi MK dosen TIFv2.csv"
    try:
        df_pref = pd.read_csv(path_pref)
    except FileNotFoundError:
        print(f"❌ File tidak ditemukan: {path_pref}")
        return

    # 2. Hitung Kandidat per MK
    # Kita ingin tahu: Satu MK itu diperebutkan berapa orang?
    candidates = {}
    for _, row in df_pref.iterrows():
        kode = str(row['Kode MK']).strip()
        dosen = str(row['Nama Dosen']).strip()
        
        if kode not in candidates:
            candidates[kode] = set()
        candidates[kode].add(dosen)
        
    # 3. Analisis Hasil
    total_mk = len(candidates)
    mk_single = 0
    mk_multi = 0
    
    print(f"\nTotal Mata Kuliah Terdaftar di Preferensi: {total_mk}")
    
    print("\n--- DAFTAR MK YANG 'TERKUNCI' (Hanya 1 Dosen) ---")
    print("GA tidak bisa menyeimbangkan beban untuk MK ini:")
    for kode, dosen_set in candidates.items():
        if len(dosen_set) == 1:
            mk_single += 1
            print(f"  🔒 {kode}: {list(dosen_set)[0]}")
        else:
            mk_multi += 1
            
    print("\n--- STATISTIK ---")
    print(f"MK Terkunci (1 Dosen)  : {mk_single} ({mk_single/total_mk*100:.1f}%)")
    print(f"MK Fleksibel (>1 Dosen): {mk_multi} ({mk_multi/total_mk*100:.1f}%)")
    
    if mk_single > mk_multi:
        print("\n⚠️ KESIMPULAN: Masalah Data.")
        print("Sebagian besar MK hanya punya 1 kandidat.")
        print("Fairness (SD) TIDAK AKAN BISA BAGUS karena tidak ada opsi tukar dosen.")
    else:
        print("\n✅ KESIMPULAN: Data Bagus.")
        print("Banyak opsi tukar dosen. Masalah ada di codingan Load Balancing.")

if __name__ == "__main__":
    check_flexibility()