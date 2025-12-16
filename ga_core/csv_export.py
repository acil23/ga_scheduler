import pandas as pd
import os

def export_schedule_to_csv(individual, data, filename="hasil_jadwal_terbaik.csv"):
    slots_lookup = {s['slot_id']: s for s in data['slots']}
    rooms_lookup = {r['room_id']: r for r in data['rooms']}
    
    formatted_data = []
    
    for gene in individual.chromosome:
        slot_data = slots_lookup[gene['slot_id']]
        room_data = rooms_lookup[gene['room_id']]
        
        row = {
            "ID Kelas": gene['class_id'],
            "Kode MK": gene['kode_mk'],
            "Mata Kuliah": gene['nama_mk'], # Nama sudah bersih dari suffix kelas
            "SKS": gene['sks'],
            "Kelas": gene.get('parallel', '-'), # A, B, C...
            "Dosen": gene['dosen'],
            "Hari": slot_data['Hari'],
            "Jam Mulai": slot_data['Mulai'],
            "Jam Selesai": slot_data['Selesai'],
            "Ruangan": room_data['Ruang'],
            "Prioritas Dosen": gene.get('dosen_priority', '?')
        }
        formatted_data.append(row)
        
    df = pd.DataFrame(formatted_data)
    
    # Sorting: Hari -> Jam -> Ruang
    hari_map = {'senin': 1, 'selasa': 2, 'rabu': 3, 'kamis': 4, 'jumat': 5, 'sabtu': 6}
    df['hari_num'] = df['Hari'].str.lower().map(hari_map).fillna(99)
    df = df.sort_values(by=['hari_num', 'Jam Mulai', 'Ruangan']).drop(columns=['hari_num'])
    
    path = os.path.join(os.getcwd(), filename)
    df.to_csv(path, index=False)
    print(f"\n📄 Jadwal Updated diexport ke: {path}")