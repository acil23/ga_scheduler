import random
import copy

class LocalSearch:
    def __init__(self, fitness_calculator, candidates, pref_info):
        self.fitness_calc = fitness_calculator
        self.candidates = candidates
        self.pref_info = pref_info

    def is_dosen_busy(self, chromosome, dosen_name, slot_id):
        """Cek apakah dosen sedang mengajar di slot waktu tertentu"""
        for gene in chromosome:
            if gene['dosen'] == dosen_name and gene['slot_id'] == slot_id:
                return True
        return False

    def resolve_conflicts(self, individual, all_slots, all_rooms):
        """
        FASE 1: FIHC (First Improvement Hill Climbing)
        Fokus: Menghilangkan [Tabrakan Ruang] dan [Tabrakan Dosen]
        """
        current_fitness, conflicts = self.fitness_calc.calculate(individual.chromosome)
        if not conflicts: return individual # Sudah aman

        # Identifikasi gen yang bermasalah
        problematic_indices = []
        for i, gene in enumerate(individual.chromosome):
            mk_name = gene['nama_mk']
            dosen_name = gene['dosen']
            # Cek apakah gene ini disebut dalam list konflik
            is_problem = False
            for msg in conflicts:
                if mk_name in msg or dosen_name in msg:
                    is_problem = True
                    break
            if is_problem:
                problematic_indices.append(i)
        
        # Jika tidak bisa parsing nama, ambil acak
        if not problematic_indices:
            problematic_indices = random.sample(range(len(individual.chromosome)), min(10, len(individual.chromosome)))

        # COBA PERBAIKI
        for idx in problematic_indices:
            original_gene = copy.deepcopy(individual.chromosome[idx])
            
            # Coba pindah ke 10 slot/ruang acak
            for _ in range(10):
                # Mutasi kecil: Ganti Slot atau Ruang
                if random.random() < 0.5:
                    individual.chromosome[idx]['slot_id'] = random.choice(all_slots)['slot_id']
                else:
                    individual.chromosome[idx]['room_id'] = random.choice(all_rooms)['room_id']
                
                new_fitness, new_conflicts = self.fitness_calc.calculate(individual.chromosome)
                
                # Jika konflik BERKURANG, simpan perubahan (Hill Climbing)
                if len(new_conflicts) < len(conflicts):
                    current_fitness = new_fitness
                    conflicts = new_conflicts
                    break # Lanjut ke gen bermasalah berikutnya
                else:
                    # Revert (Balikin)
                    individual.chromosome[idx] = copy.deepcopy(original_gene)
        
        individual.fitness = current_fitness
        individual.conflicts = conflicts
        return individual

    def apply_load_balancing(self, individual):
        """
        FASE 2: SAFE LOAD BALANCING
        Fokus: Ratakan beban TAPI cek dulu jadwalnya bentrok gak
        """
        # 1. Hitung Beban
        workload = {}
        for gene in individual.chromosome:
            d = gene['dosen']
            if "Unknown" in d: continue
            workload[d] = workload.get(d, 0) + gene['sks']

        if not workload: return individual

        # 2. Loop Balancing
        for _ in range(20): # Coba 20 kali per individu
            sorted_dosen = sorted(workload.items(), key=lambda x: x[1], reverse=True)
            overloaded_dosen, max_load = sorted_dosen[0]
            underloaded_dosen, min_load = sorted_dosen[-1]
            
            avg_load = sum(workload.values()) / len(workload)
            if (max_load - avg_load) < 2: break 

            # Cari Matkul si Overload
            genes_of_overloaded = [g for g in individual.chromosome if g['dosen'] == overloaded_dosen]
            random.shuffle(genes_of_overloaded)
            
            for gene in genes_of_overloaded:
                kode_mk = gene['kode_mk']
                sks_mk = gene['sks']
                slot_saat_ini = gene['slot_id']
                
                possible_candidates = self.candidates.get(kode_mk, [])
                
                # Cari target
                target_dosen = None
                if underloaded_dosen in possible_candidates:
                    target_dosen = underloaded_dosen
                else:
                    valid_subs = [d for d in possible_candidates if workload.get(d, 0) < avg_load]
                    if valid_subs: target_dosen = random.choice(valid_subs)
                
                if target_dosen:
                    # --- SAFETY CHECK (KUNCI PERBAIKAN) ---
                    # Sebelum tukar, cek apakah Target Dosen SIBUK di jam itu?
                    if self.is_dosen_busy(individual.chromosome, target_dosen, slot_saat_ini):
                        continue # Skip, cari matkul lain / target lain
                    
                    # Jika aman, EKSEKUSI
                    old_dosen = gene['dosen']
                    gene['dosen'] = target_dosen
                    info = self.pref_info.get((target_dosen, kode_mk), {'prioritas': 99})
                    gene['dosen_priority'] = info['prioritas']
                    
                    workload[old_dosen] -= sks_mk
                    workload[target_dosen] = workload.get(target_dosen, 0) + sks_mk
                    break 
            
        return individual