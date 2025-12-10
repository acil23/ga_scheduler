from ga_core.data_loader import load_all_data
from ga_core.ga_engine import GeneticAlgorithm
from ga_core.csv_export import export_schedule_to_csv
import time

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

if __name__ == "__main__":
    main()