import pandas as pd

def check_bottleneck():
    print("=== DIAGNOSA KEBUNTUAN FAIRNESS ===")
    
    # 1. Load Preferensi
    df = pd.read_csv("data/Preferensi MK dosen TIFv2.csv")
    
    # Mapping: Siapa bisa ngajar apa
    # { 'Dosen A': {'MK1', 'MK2'}, 'Dosen B': {'MK3'} }
    dosen_skills = {}
    mk_candidates = {}
    
    for _, row in df.iterrows():
        dosen = str(row['Nama Dosen']).strip()
        mk = str(row['Kode MK']).strip()
        nama_mk = str(row['Nama MK']).strip()
        
        if dosen not in dosen_skills: dosen_skills[dosen] = set()
        dosen_skills[dosen].add(mk)
        
        if mk not in mk_candidates: mk_candidates[mk] = []
        mk_candidates[mk].append(dosen)

    # 2. INPUT DATA DARI HASIL REPORT KAMU (SAMPLE)
    # Dosen Overload (>15 SKS) vs Underload (<10 SKS)
    overload_group = ["Nurudin Santoso", "Herman Tolle", "Eko Sakti Pramukantoro"]
    underload_group = ["Agi Putra Kharisma", "Mahendra Data", "Eko Setiawan"]
    
    print(f"\nAnalisis Transfer SKS dari {overload_group} ke {underload_group}")
    print("-" * 60)
    
    bisa_tukar = False
    
    for dosen_kaya in overload_group:
        print(f"\n🔍 Cek Mata Kuliah milik {dosen_kaya}:")
        mks = dosen_skills.get(dosen_kaya, [])
        
        found_transfer = False
        for mk in mks:
            # Siapa lagi yang bisa ngajar MK ini?
            kandidat_lain = mk_candidates.get(mk, [])
            
            # Cek apakah ada orang miskin di daftar kandidat?
            irisan = [d for d in kandidat_lain if d in underload_group]
            
            if irisan:
                print(f"  ✅ BISA DITRANSFER: MK {mk} -> Bisa diambil oleh {irisan}")
                found_transfer = True
                bisa_tukar = True
            else:
                # print(f"  🔒 TERKUNCI: MK {mk} hanya bisa diambil oleh {kandidat_lain}")
                pass
                
        if not found_transfer:
            print("  ❌ TIDAK ADA SATUPUN MK DOSEN INI YANG BISA DIAMBIL DOSEN UNDERLOAD.")
            
    print("-" * 60)
    if not bisa_tukar:
        print("KESIMPULAN: Masalah Data! Dosen Underload tidak punya kompetensi (di CSV) untuk mengambil MK milik Dosen Overload.")
        print("SOLUSI: Edit CSV Preferensi, tambahkan nama Dosen Underload ke MK tersebut (Prio 2).")
    else:
        print("KESIMPULAN: Data Aman! Masalah ada di Algoritma Mutasi GA yang kurang pintar.")

if __name__ == "__main__":
    check_bottleneck()