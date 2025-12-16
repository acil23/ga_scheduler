import numpy as np

class FitnessCalculator:
    def __init__(self, slots, rooms):
        self.rooms = {r['room_id']: r for r in rooms}
        
        # Pre-process slots to minutes
        self.slot_details = {}
        for s in slots:
            start_min = self._time_to_minutes(s['Mulai'])
            end_min = self._time_to_minutes(s['Selesai'])
            self.slot_details[s['slot_id']] = {
                'hari': s['Hari'], 'start': start_min, 'end': end_min
            }
        
        # --- KONFIGURASI BOBOT PENALTY ---
        self.WEIGHT_HARD = 1000        # Tabrakan (Mutlak)
        self.WEIGHT_SOFT_PRIO_2 = 2   # Prioritas 2 (Sedikit Penalti)
        self.WEIGHT_SOFT_UNKNOWN = 50  # Prioritas 99 (Penalti Besar/Salah Dosen)
        self.WEIGHT_SOFT_FAIR = 100     # Fairness

    def _time_to_minutes(self, time_str):
        h, m = map(int, time_str.split(':')[:2])
        return h * 60 + m

    def check_overlap(self, slot1_id, slot2_id):
        if slot1_id == slot2_id: return True
        s1, s2 = self.slot_details[slot1_id], self.slot_details[slot2_id]
        if s1['hari'] != s2['hari']: return False
        return (s1['start'] < s2['end']) and (s2['start'] < s1['end'])

    def calculate(self, chromosome):
        conflicts = []
        penalty_score = 0
        
        genes_by_room = {}
        genes_by_dosen = {}
        dosen_workload = {} 
        
        for gene in chromosome:
            # 1. Cek Kapasitas
            if gene['jumlah_mhs'] > self.rooms[gene['room_id']]['Kapasitas']:
                penalty_score += self.WEIGHT_HARD
                conflicts.append(f"[Kapasitas] {gene['nama_mk']} excess")

            # 2. Preferensi Dosen (Soft Constraint)
            prio = gene.get('dosen_priority', 99)
            
            if prio == 1:
                pass # Sempurna, 0 Penalty
            elif prio == 2:
                penalty_score += self.WEIGHT_SOFT_PRIO_2
            else:
                # Prio 99 atau lainnya (Bukan prioritas/Salah Dosen)
                penalty_score += self.WEIGHT_SOFT_UNKNOWN
            
            # Grouping
            r_id = gene['room_id']
            if r_id not in genes_by_room: genes_by_room[r_id] = []
            genes_by_room[r_id].append(gene)
            
            d_name = gene['dosen']
            if d_name not in genes_by_dosen: genes_by_dosen[d_name] = []
            genes_by_dosen[d_name].append(gene)
            
            # Hitung Workload (SKS)
            if "Unknown" not in d_name:
                dosen_workload[d_name] = dosen_workload.get(d_name, 0) + gene['sks']

        # 3. Cek Tabrakan Ruang
        for r_id, class_list in genes_by_room.items():
            for i in range(len(class_list)):
                for j in range(i + 1, len(class_list)):
                    if self.check_overlap(class_list[i]['slot_id'], class_list[j]['slot_id']):
                        penalty_score += self.WEIGHT_HARD
                        conflicts.append(f"[Tabrakan Ruang] {class_list[i]['nama_mk']} vs {class_list[j]['nama_mk']}")

        # 4. Cek Tabrakan Dosen
        for d_name, class_list in genes_by_dosen.items():
            if "Unknown" in d_name: continue
            for i in range(len(class_list)):
                for j in range(i + 1, len(class_list)):
                    if self.check_overlap(class_list[i]['slot_id'], class_list[j]['slot_id']):
                        penalty_score += self.WEIGHT_HARD
                        conflicts.append(f"[Tabrakan Dosen] {d_name}: {class_list[i]['nama_mk']} vs {class_list[j]['nama_mk']}")
        
        # 5. FAIRNESS
        if dosen_workload:
            loads = list(dosen_workload.values())
            std_dev = np.std(loads)
            
            # AMBANG BATAS TOLERANSI: SD 2.5
            # Jika SD > 2.5, hukuman naik drastis (Eksponensial)
            if std_dev > 2.5:
                penalty_score += (std_dev ** 3) * 100
            else:
                penalty_score += (std_dev * 50)

        fitness = 1.0 / (1.0 + penalty_score)
        return fitness, conflicts