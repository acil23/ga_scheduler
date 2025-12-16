from ga_core.data_loader import load_all_data
from ga_core.ga_engine import GeneticAlgorithm
from ga_core.csv_export import export_schedule_to_csv
import time
import numpy as np

def print_statistical_report(individual):
    """
    Menghitung dan menampilkan statistik beban kerja dosen (Fairness).
    """
    print("\n" + "="*40)
    print("       LAPORAN STATISTIK BEBAN DOSEN")
    print("="*40)
    
    # 1. Hitung Total SKS per Dosen
    dosen_workload = {}
    
    for gene in individual.chromosome:
        dosen = gene['dosen']
        sks = gene['sks']
        
        # Skip jika dosennya "Unknown" atau placeholder
        if "Unknown" in dosen or "Belum" in dosen:
            continue
            
        dosen_workload[dosen] = dosen_workload.get(dosen, 0) + sks
        
    # 2. Tampilkan Rincian
    print(f"{'NAMA DOSEN':<35} | {'SKS':<5}")
    print("-" * 43)
    
    # Urutkan berdasarkan beban SKS (tertinggi ke terendah)
    sorted_load = sorted(dosen_workload.items(), key=lambda x: x[1], reverse=True)
    
    for dosen, total_sks in sorted_load:
        print(f"{dosen:<35} | {total_sks:<5}")
        
    # 3. Hitung Fairness (Standar Deviasi)
    loads = list(dosen_workload.values())
    if loads:
        avg_load = np.mean(loads)
        std_dev = np.std(loads)
        min_load = np.min(loads)
        max_load = np.max(loads)
        
        print("-" * 43)
        print(f"Rata-rata Beban : {avg_load:.2f} SKS")
        print(f"Tertinggi       : {max_load} SKS")
        print(f"Terendah        : {min_load} SKS")
        print(f"Standar Deviasi : {std_dev:.4f}  <-- INDIKATOR FAIRNESS")
        print("="*40)
        
        if std_dev < 2.0:
            print("✅ Status Fairness: SANGAT BAIK (Merata)")
        elif std_dev < 4.0:
            print("⚠️ Status Fairness: CUKUP (Ada ketimpangan)")
        else:
            print("❌ Status Fairness: BURUK (Sangat timpang)")
    else:
        print("Data beban dosen kosong.")

def main():
    # 1. Load Data
    data = load_all_data()
    
    # 2. Konfigurasi Parameter GA
    ga_params = {
        'pop_size': 30,          # Jumlah penduduk (makin banyak makin lambat tapi variatif)
        'max_generations': 200,  # Berapa kali evolusi
        'crossover_rate': 0.8,   # Peluang kawin silang
        'mutation_rate': 0.05,   # Peluang mutasi (kecil saja)
        'elitism': 2             # Simpan 2 terbaik agar tidak hilang
    }
    
    # 3. Inisialisasi Engine
    engine = GeneticAlgorithm(data, ga_params)
    
    # 4. Jalankan!
    start_time = time.time()
    best_schedule = engine.run()
    end_time = time.time()
    
    # 5. Laporan Hasil
    print("\n=== LAPORAN HASIL AKHIR ===")
    print(f"Durasi Proses: {end_time - start_time:.2f} detik")
    print(f"Fitness Akhir: {best_schedule.fitness:.5f}")
    print(f"Total Konflik: {len(best_schedule.conflicts)}")
    
    if best_schedule.conflicts:
        print("\n❌ SISA KONFLIK YANG BELUM TERSELESAIKAN:")
        for msg in best_schedule.conflicts[:10]: # Tampilkan 10 saja biar ga penuh
            print(f"  - {msg}")
    else:
        print("\n✅ JADWAL SEMPURNA! Tidak ada pelanggaran aturan.")

    # 6. (Opsional) Export ke CSV bisa ditambahkan nanti di sini
    print("\n=== MENYIMPAN HASIL JADWAL ===")
    export_schedule_to_csv(best_schedule, data, filename="Jadwal_Final_Skripsi.csv")

    print_statistical_report(best_schedule)

if __name__ == "__main__":
    main()