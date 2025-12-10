class FitnessCalculator:
    def __init__(self, slots, rooms):
        self.rooms = {r['room_id']: r for r in rooms}
        
        # --- PRE-PROCESSING SLOTS (PENTING) ---
        # Kita ubah setiap slot menjadi format menit agar mudah dicek tabrakannya
        # Contoh: Senin 07:00 -> Senin, menit ke-420
        self.slot_details = {}
        for s in slots:
            # Parse Jam Mulai & Selesai
            start_min = self._time_to_minutes(s['Mulai'])
            end_min = self._time_to_minutes(s['Selesai'])
            
            self.slot_details[s['slot_id']] = {
                'hari': s['Hari'],
                'start': start_min,
                'end': end_min,
                'raw': s # Simpan data asli untuk debug log
            }
        
        # Bobot Penalty
        self.WEIGHT_HARD = 1000  # Naikkan biar GA takut sekali sama tabrakan
        self.WEIGHT_SOFT = 10

    def _time_to_minutes(self, time_str):
        """Ubah '07:30' jadi 450 menit."""
        h, m = map(int, time_str.split(':')[:2])
        return h * 60 + m

    def check_overlap(self, slot1_id, slot2_id):
        """
        Mendeteksi apakah dua slot waktu TABRAKAN secara fisik.
        Return True jika tabrakan.
        """
        # Jika ID sama, pasti tabrakan
        if slot1_id == slot2_id:
            return True
            
        s1 = self.slot_details[slot1_id]
        s2 = self.slot_details[slot2_id]
        
        # Jika hari beda, aman
        if s1['hari'] != s2['hari']:
            return False
            
        # Logika Tabrakan Waktu:
        # (Start1 < End2) AND (Start2 < End1)
        return (s1['start'] < s2['end']) and (s2['start'] < s1['end'])

    def calculate(self, chromosome):
        conflicts = []
        penalty_score = 0
        
        # Kelompokkan Gen berdasarkan Ruang & Dosen untuk efisiensi cek
        # Key: room_id, Value: List of genes
        genes_by_room = {}
        genes_by_dosen = {}
        
        for gene in chromosome:
            # 1. Cek Kapasitas (O(N))
            room_cap = self.rooms[gene['room_id']]['Kapasitas']
            if gene['jumlah_mhs'] > room_cap:
                penalty_score += self.WEIGHT_HARD
                conflicts.append(f"[Kapasitas] {gene['nama_mk']} excess")

            # 2. Preferensi Dosen (O(N))
            prio = gene.get('dosen_priority', 99)
            if prio > 1:
                penalty_score += (prio * self.WEIGHT_SOFT)
            
            # Grouping untuk cek tabrakan
            r_id = gene['room_id']
            if r_id not in genes_by_room: genes_by_room[r_id] = []
            genes_by_room[r_id].append(gene)
            
            d_name = gene['dosen']
            if d_name not in genes_by_dosen: genes_by_dosen[d_name] = []
            genes_by_dosen[d_name].append(gene)

        # --- CEK TABRAKAN RUANG (O(M^2) per room) ---
        for r_id, class_list in genes_by_room.items():
            # Bandingkan setiap pasangan kelas di ruangan ini
            for i in range(len(class_list)):
                for j in range(i + 1, len(class_list)):
                    gene_a = class_list[i]
                    gene_b = class_list[j]
                    
                    # Cek Overlap Fisik
                    if self.check_overlap(gene_a['slot_id'], gene_b['slot_id']):
                        penalty_score += self.WEIGHT_HARD
                        
                        # Info Detail
                        s1 = self.slot_details[gene_a['slot_id']]
                        msg = f"[Tabrakan Ruang] {self.rooms[r_id]['Ruang']} ({s1['hari']}): {gene_a['nama_mk']} vs {gene_b['nama_mk']}"
                        conflicts.append(msg)

        # --- CEK TABRAKAN DOSEN (O(K^2) per dosen) ---
        for d_name, class_list in genes_by_dosen.items():
            if "Unknown" in d_name: continue
            
            for i in range(len(class_list)):
                for j in range(i + 1, len(class_list)):
                    gene_a = class_list[i]
                    gene_b = class_list[j]
                    
                    if self.check_overlap(gene_a['slot_id'], gene_b['slot_id']):
                        penalty_score += self.WEIGHT_HARD
                        s1 = self.slot_details[gene_a['slot_id']]
                        msg = f"[Tabrakan Dosen] {d_name} ({s1['hari']}): {gene_a['nama_mk']} vs {gene_b['nama_mk']}"
                        conflicts.append(msg)

        fitness = 1.0 / (1.0 + penalty_score)
        return fitness, conflicts