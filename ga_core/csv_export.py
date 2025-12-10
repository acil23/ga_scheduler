import pandas as pd
import os

def export_schedule_to_csv(individual, data, filename="hasil_jadwal_terbaik.csv"):
    """
    Mengubah Kromosom (ID) menjadi Data Frame yang bisa dibaca manusia,
    lalu simpan ke CSV.
    """
    # Siapkan Lookup Data (Biar cepat konversi ID ke Nama)
    slots_lookup = {s['slot_id']: s for s in data['slots']}
    rooms_lookup = {r['room_id']: r for r in data['rooms']}
    
    formatted_data = []
    
    # Loop setiap gen (mata kuliah) dalam jadwal terbaik
    for gene in individual.chromosome:
        slot_data = slots_lookup[gene['slot_id']]
        room_data = rooms_lookup[gene['room_id']]
        
        # Susun baris data
        row = {
            "ID Kelas": gene['class_id'],
            "Kode MK": gene['kode_mk'],
            "Mata Kuliah": gene['nama_mk'],
            "Dosen": gene['dosen'],
            "SKS": gene['sks'],
            "Kelas": gene.get('parallel', '-'), # A, B, C...
            
            # Info Waktu & Tempat
            "Hari": slot_data['Hari'],
            "Jam Mulai": slot_data['Mulai'],
            "Jam Selesai": slot_data['Selesai'],
            "Ruangan": room_data['Ruang'],
            "Kapasitas Ruang": room_data['Kapasitas'],
            "Jumlah Mhs": gene['jumlah_mhs'],
            
            # Cek apakah Dosen Sesuai Kompetensi (Prioritas 1 = Bagus)
            "Prioritas Dosen": gene.get('dosen_priority', '?')
        }
        formatted_data.append(row)
        
    # Buat DataFrame Pandas
    df = pd.csv_export = pd.DataFrame(formatted_data)
    
    # Sorting agar rapi (Hari -> Jam -> Ruang)
    # Mapping hari ke angka agar urut Senin-Jumat
    hari_map = {'senin': 1, 'selasa': 2, 'rabu': 3, 'kamis': 4, 'jumat': 5, 'sabtu': 6}
    df['hari_num'] = df['Hari'].str.lower().map(hari_map).fillna(99)
    
    df = df.sort_values(by=['hari_num', 'Jam Mulai', 'Ruangan'])
    df = df.drop(columns=['hari_num']) # Hapus kolom bantu
    
    # Simpan ke CSV
    path = os.path.join(os.getcwd(), filename)
    df.to_csv(path, index=False)
    
    print(f"\n📄 Jadwal berhasil diexport ke: {path}")
    return df