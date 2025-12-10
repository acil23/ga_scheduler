import random
import copy
from ga_core.individual import Individual

# ============================
# 1. SELEKSI (TOURNAMENT)
# ============================
def tournament_selection(population, k=3):
    """
    Memilih 1 orang tua terbaik dari 'k' kandidat acak.
    """
    # Ambil k individu secara acak
    candidates = random.sample(population, k)
    
    # Cari yang fitness-nya paling tinggi (terbaik)
    best = max(candidates, key=lambda ind: ind.fitness)
    return best

# ============================
# 2. CROSSOVER (KAWIN SILANG)
# ============================
def crossover(parent1, parent2, crossover_rate=0.8):
    """
    Menggabungkan gen dari 2 orang tua.
    Metode: Uniform Crossover (Tiap MK dilempar koin, ikut P1 atau P2).
    """
    # Cek peluang, jika tidak kejadian, kembalikan copy orang tua (kloning)
    if random.random() > crossover_rate:
        return copy.deepcopy(parent1), copy.deepcopy(parent2)

    # Siapkan anak
    child1 = copy.deepcopy(parent1)
    child2 = copy.deepcopy(parent2)
    
    # Tukar gen per mata kuliah
    # Ingat: chromosome adalah list of dicts. Panjangnya sama.
    num_genes = len(parent1.chromosome)
    
    for i in range(num_genes):
        # 50% peluang tukar gen
        if random.random() < 0.5:
            # Swap gen i antara anak 1 dan anak 2
            child1.chromosome[i], child2.chromosome[i] = child2.chromosome[i], child1.chromosome[i]
            
    # Reset fitness karena kromosom berubah (harus dihitung ulang nanti)
    child1.fitness = 0.0
    child1.conflicts = []
    child2.fitness = 0.0
    child2.conflicts = []
    
    return child1, child2

# ============================
# 3. MUTATION (MUTASI)
# ============================
def mutation(individual, all_slots, all_rooms, mutation_rate=0.1):
    """
    Mengubah gen secara acak dengan peluang kecil.
    Tujuannya agar GA tidak 'macet' di solusi yang itu-itu saja.
    """
    # Loop setiap gen (setiap mata kuliah)
    for gene in individual.chromosome:
        if random.random() < mutation_rate:
            # Lakukan Mutasi!
            # Kita ganti Slot Waktu ATAU Ruangan (atau keduanya)
            
            # 50% peluang ganti Slot
            if random.random() < 0.5:
                new_slot = random.choice(all_slots)
                gene['slot_id'] = new_slot['slot_id']
                
            # 50% peluang ganti Ruang
            else:
                new_room = random.choice(all_rooms)
                gene['room_id'] = new_room['room_id']
    
    # Reset fitness karena ada perubahan
    individual.fitness = 0.0
    individual.conflicts = []